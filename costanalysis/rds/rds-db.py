#!/usr/bin/env python3
"""
RDS Per-DB-Instance Fixed vs Dynamic Cost Report
INCLUDING Last Reboot Time (RDS Events, max 14 days) + CloudTrail fallback

Key points:
- Cost window: DAYS_BACK (e.g., 30 days) from 00:00 UTC start date to now.
- RDS Events: only available for the past 14 days (max Duration = 20160 minutes). :contentReference[oaicite:1]{index=1}
- Last reboot is derived from:
    1) RDS DescribeEvents (best for system/maintenance/failover too)
    2) CloudTrail LookupEvents for RebootDBInstance (best for "who triggered it", longer lookback than 14d if your trail retains it)
- Report includes source of reboot info and explains N/A.

Permissions needed:
- ce:GetCostAndUsageWithResources
- rds:DescribeDBInstances
- rds:DescribeEvents
- cloudtrail:LookupEvents  (optional but recommended for fallback)
"""

import re
import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import boto3
from botocore.exceptions import ClientError

# ---------------- CONFIG ----------------
DAYS_BACK = 30
MAX_INSTANCES_IN_SUMMARY = 50
MAX_LINE_ITEMS_PER_INSTANCE = 10
OUTPUT_PREFIX = "rds_instance_cost_report"

# RDS events retention max = 14 days => 20160 minutes. :contentReference[oaicite:2]{index=2}
RDS_EVENTS_MAX_MINUTES = 20160

# Event keyword matching (expanded to reduce false N/A)
EVENT_KEYWORDS = [
    "reboot", "restarted", "restart", "starting", "started",
    "failover", "recovered", "recovery", "maintenance", "patch",
    "stopped", "stop", "availability", "switch", "promoted"
]

# CloudTrail event names to consider for reboot-ish activity
CLOUDTRAIL_EVENTNAMES = [
    "RebootDBInstance",
    # Some orgs also want these as "reboot-like" operational restarts:
    "FailoverDBCluster",
    "FailoverDBInstance",
    "ModifyDBInstance",
]
# ----------------------------------------

SERVICE_VALUE = "Amazon Relational Database Service"

STATE_FIXED = "FIXED"
STATE_DYNAMIC = "DYNAMIC"


def dec(x) -> Decimal:
    try:
        return Decimal(str(x))
    except Exception:
        return Decimal("0")


def money(x: Decimal) -> str:
    return f"${x:,.2f}"


def utc_window(days_back: int):
    end_time = datetime.now(timezone.utc)
    start_date = end_time.date() - timedelta(days=days_back)
    start_time = datetime(
        start_date.year, start_date.month, start_date.day,
        0, 0, 0, tzinfo=timezone.utc
    )
    return start_time, end_time


def ce_time_period(start_time: datetime, end_time: datetime):
    # CE End is exclusive; include today's date
    return {"Start": start_time.date().isoformat(), "End": (end_time.date() + timedelta(days=1)).isoformat()}


def classify_usage_type(usage_type: str) -> str:
    ut = (usage_type or "").lower()
    # Simple heuristic; keep as-is unless you want more precise patterns
    if any(x in ut for x in ["instance", "storage", "gp3", "gp2", "io1", "io2", "piops", "provisioned"]):
        return STATE_FIXED
    return STATE_DYNAMIC


def _msg_matches(msg: str) -> bool:
    m = (msg or "").lower()
    return any(k in m for k in EVENT_KEYWORDS)


def get_last_reboot_from_rds_events(rds, db_id: str, days_back: int):
    """
    Returns (timestamp, message, source) for most recent reboot-like event
    from RDS Events, within allowed retention (max 14 days).
    """
    minutes = min(days_back * 1440, RDS_EVENTS_MAX_MINUTES)
    try:
        events = rds.describe_events(
            SourceType="db-instance",
            SourceIdentifier=db_id,
            Duration=minutes
        ).get("Events", [])
    except ClientError:
        return None, None, None

    reboot_events = [e for e in events if _msg_matches(e.get("Message", ""))]
    if not reboot_events:
        return None, None, None

    last = max(reboot_events, key=lambda e: e["Date"])
    return last["Date"], last.get("Message", ""), "RDS_EVENTS"


def get_last_reboot_from_cloudtrail(db_id: str, start_time: datetime, end_time: datetime):
    """
    CloudTrail fallback: finds latest relevant API action for this DB identifier.
    This is useful when RDS Events can't go back beyond 14 days.
    Returns (timestamp, message, source).
    """
    try:
        ct = boto3.client("cloudtrail")
    except Exception:
        return None, None, None

    best = None  # (event_time, description)
    for ev_name in CLOUDTRAIL_EVENTNAMES:
        try:
            resp = ct.lookup_events(
                LookupAttributes=[{"AttributeKey": "EventName", "AttributeValue": ev_name}],
                StartTime=start_time,
                EndTime=end_time,
                MaxResults=50
            )
        except ClientError:
            continue

        for e in resp.get("Events", []):
            # CloudTrail provides Resources with names; match DB identifier
            resources = e.get("Resources", []) or []
            if not any((r.get("ResourceName") == db_id) for r in resources):
                continue

            t = e.get("EventTime")
            if not t:
                continue

            desc = f"{ev_name} (CloudTrail)"
            if best is None or t > best[0]:
                best = (t, desc)

    if best:
        return best[0], best[1], "CLOUDTRAIL"
    return None, None, None


def build_db_metadata(days_back: int, cost_start: datetime, cost_end: datetime):
    """
    Mapping DBInstanceArn -> {
      id, engine, last_reboot_time, last_reboot_msg, last_reboot_source, last_reboot_note
    }
    """
    rds = boto3.client("rds")
    meta = {}

    paginator = rds.get_paginator("describe_db_instances")
    for page in paginator.paginate():
        for db in page.get("DBInstances", []):
            db_id = db["DBInstanceIdentifier"]
            arn = db["DBInstanceArn"]
            engine = db.get("Engine", "")

            # 1) RDS Events (max 14 days)
            t1, m1, s1 = get_last_reboot_from_rds_events(rds, db_id, days_back)

            # 2) CloudTrail fallback (within cost window)
            t2, m2, s2 = get_last_reboot_from_cloudtrail(db_id, cost_start, cost_end)

            # pick the most recent timestamp among sources
            chosen_t, chosen_m, chosen_s = None, None, None
            if t1 and (not t2 or t1 >= t2):
                chosen_t, chosen_m, chosen_s = t1, m1, s1
            elif t2:
                chosen_t, chosen_m, chosen_s = t2, m2, s2

            note = None
            if not chosen_t:
                note = (
                    f"N/A (no matching reboot/restart/failover events returned; "
                    f"RDS Events only retain up to 14 days / {RDS_EVENTS_MAX_MINUTES} minutes)"
                )

            meta[arn] = {
                "id": db_id,
                "engine": engine,
                "last_reboot": chosen_t,
                "reboot_message": chosen_m,
                "reboot_source": chosen_s,
                "reboot_note": note,
            }

    return meta


def main():
    start_time, end_time = utc_window(DAYS_BACK)
    start_str = start_time.strftime("%Y-%m-%d")
    end_str = end_time.strftime("%Y-%m-%d")
    output_file = f"{OUTPUT_PREFIX}_{start_str}_to_{end_str}.md"

    ce = boto3.client("ce", region_name="us-east-1")

    # Build DB metadata incl. last reboot (RDS Events + CloudTrail fallback)
    rds_meta = build_db_metadata(DAYS_BACK, start_time, end_time)

    try:
        resp = ce.get_cost_and_usage_with_resources(
            TimePeriod=ce_time_period(start_time, end_time),
            Granularity="DAILY",
            Metrics=["UnblendedCost"],
            Filter={"Dimensions": {"Key": "SERVICE", "Values": [SERVICE_VALUE]}},
            GroupBy=[
                {"Type": "DIMENSION", "Key": "RESOURCE_ID"},
                {"Type": "DIMENSION", "Key": "USAGE_TYPE"},
            ],
        )
    except ClientError as e:
        print("ERROR: Cost Explorer resource-level query failed")
        print(e)
        sys.exit(1)

    per_instance = {}
    per_instance_usage = {}

    for day in resp.get("ResultsByTime", []):
        for g in day.get("Groups", []):
            if len(g.get("Keys", [])) != 2:
                continue
            arn, usage = g["Keys"]
            cost = dec(g["Metrics"]["UnblendedCost"]["Amount"])
            bucket = classify_usage_type(usage)

            per_instance.setdefault(arn, {STATE_FIXED: Decimal("0"), STATE_DYNAMIC: Decimal("0")})
            per_instance[arn][bucket] += cost

            per_instance_usage.setdefault(arn, {})
            per_instance_usage[arn].setdefault((bucket, usage), Decimal("0"))
            per_instance_usage[arn][(bucket, usage)] += cost

    rows = []
    for arn, costs in per_instance.items():
        meta = rds_meta.get(arn, {"id": arn, "engine": ""})
        fixed = costs.get(STATE_FIXED, Decimal("0"))
        dynamic = costs.get(STATE_DYNAMIC, Decimal("0"))
        total = fixed + dynamic

        rows.append((
            meta.get("id", arn),
            meta.get("engine", ""),
            fixed,
            dynamic,
            total,
            meta.get("last_reboot"),
            meta.get("reboot_source"),
            meta.get("reboot_message"),
            meta.get("reboot_note"),
            arn
        ))

    rows.sort(key=lambda x: x[4], reverse=True)

    md = []
    md.append("# RDS Cost Report by DB Instance (with Last Reboot)\n")

    md.append("## Reporting Window\n")
    md.append(f"- **Start (UTC, pinned to 00:00):** {start_time.isoformat()}")
    md.append(f"- **End (UTC):** {end_time.isoformat()}")
    md.append(f"- **Lookback:** Last **{DAYS_BACK}** days\n")

    md.append("## Last Reboot Data Sources\n")
    md.append(f"- **RDS Events**: retained for **past 14 days**; set Duration up to **{RDS_EVENTS_MAX_MINUTES} minutes**. :contentReference[oaicite:3]{index=3}")
    md.append("- **CloudTrail fallback**: captures API-initiated actions (e.g., RebootDBInstance), if available in your trail.\n")

    md.append("## Per-Instance Summary\n")
    md.append("| DB Instance | Engine | Fixed | Dynamic | Total | Last Reboot (UTC) | Source |")
    md.append("|---|---|---:|---:|---:|---|---|")

    for r in rows[:MAX_INSTANCES_IN_SUMMARY]:
        reboot = r[5].isoformat() if r[5] else "N/A"
        src = r[6] if r[6] else ""
        md.append(f"| `{r[0]}` | {r[1]} | {money(r[2])} | {money(r[3])} | {money(r[4])} | {reboot} | {src} |")

    md.append("\n## Instance Details\n")
    for r in rows[:MAX_INSTANCES_IN_SUMMARY]:
        db_id, engine, fixed, dynamic, total, reboot_t, reboot_src, reboot_msg, reboot_note, arn = r
        md.append(f"### {db_id}\n")
        md.append(f"- **Engine:** {engine}")
        md.append(f"- **Fixed cost:** {money(fixed)}")
        md.append(f"- **Dynamic cost:** {money(dynamic)}")
        md.append(f"- **Total cost:** {money(total)}")
        md.append(f"- **ResourceId:** `{arn}`")

        if reboot_t:
            md.append(f"- **Last reboot:** {reboot_t.isoformat()}")
            md.append(f"- **Reboot source:** `{reboot_src}`")
            if reboot_msg:
                md.append(f"- **Reboot message:** {reboot_msg}")
        else:
            md.append(f"- **Last reboot:** {reboot_note}")

        # Top usage-types
        items = []
        for (bucket, ut), c in per_instance_usage.get(arn, {}).items():
            items.append((bucket, ut, c))
        items.sort(key=lambda x: x[2], reverse=True)

        md.append(f"\n**Top {MAX_LINE_ITEMS_PER_INSTANCE} usage-types:**\n")
        md.append("| Bucket | UsageType | Cost |")
        md.append("|---|---|---:|")
        for bucket, ut, c in items[:MAX_LINE_ITEMS_PER_INSTANCE]:
            md.append(f"| {bucket} | `{ut}` | {money(c)} |")
        md.append("")

    with open(output_file, "w") as f:
        f.write("\n".join(md))

    print(f"Generated report: {output_file}")


if __name__ == "__main__":
    main()
