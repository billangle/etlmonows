#!/usr/bin/env python3
"""
RDS Per-DB-Instance Fixed vs Dynamic Cost Report
INCLUDING:
- Last reboot time (RDS Events, max 14 days)
- CloudTrail fallback for API-initiated reboots
- Days since last reboot
- Clear N/A reasoning

Output:
- Markdown report with human-readable date range in filename
"""

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

RDS_EVENTS_MAX_MINUTES = 20160  # 14 days
# ----------------------------------------

SERVICE_VALUE = "Amazon Relational Database Service"

STATE_FIXED = "FIXED"
STATE_DYNAMIC = "DYNAMIC"

EVENT_KEYWORDS = [
    "reboot", "restart", "restarted", "failover",
    "maintenance", "recovered", "recovery", "started",
    "availability", "promoted"
]

CLOUDTRAIL_EVENTNAMES = [
    "RebootDBInstance",
    "FailoverDBCluster",
    "FailoverDBInstance",
    "ModifyDBInstance",
]


# ---------------- HELPERS ----------------
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
    return {
        "Start": start_time.date().isoformat(),
        "End": (end_time.date() + timedelta(days=1)).isoformat()
    }


def classify_usage_type(usage_type: str) -> str:
    ut = (usage_type or "").lower()
    if any(k in ut for k in ["instance", "storage", "gp2", "gp3", "io1", "io2", "piops", "provisioned"]):
        return STATE_FIXED
    return STATE_DYNAMIC


def msg_matches(msg: str) -> bool:
    m = (msg or "").lower()
    return any(k in m for k in EVENT_KEYWORDS)


# ---------------- REBOOT LOOKUPS ----------------
def last_reboot_from_rds_events(rds, db_id: str, days_back: int):
    minutes = min(days_back * 1440, RDS_EVENTS_MAX_MINUTES)
    try:
        events = rds.describe_events(
            SourceType="db-instance",
            SourceIdentifier=db_id,
            Duration=minutes
        ).get("Events", [])
    except ClientError:
        return None, None, None

    matches = [e for e in events if msg_matches(e.get("Message", ""))]
    if not matches:
        return None, None, None

    last = max(matches, key=lambda e: e["Date"])
    return last["Date"], last.get("Message", ""), "RDS_EVENTS"


def last_reboot_from_cloudtrail(db_id: str, start: datetime, end: datetime):
    ct = boto3.client("cloudtrail")
    best = None

    for name in CLOUDTRAIL_EVENTNAMES:
        try:
            resp = ct.lookup_events(
                LookupAttributes=[{"AttributeKey": "EventName", "AttributeValue": name}],
                StartTime=start,
                EndTime=end,
                MaxResults=50
            )
        except ClientError:
            continue

        for e in resp.get("Events", []):
            if not any(r.get("ResourceName") == db_id for r in e.get("Resources", [])):
                continue
            t = e.get("EventTime")
            if not best or t > best[0]:
                best = (t, name + " (CloudTrail)")

    if best:
        return best[0], best[1], "CLOUDTRAIL"
    return None, None, None


def build_db_metadata(days_back: int, cost_start: datetime, cost_end: datetime):
    rds = boto3.client("rds")
    meta = {}

    paginator = rds.get_paginator("describe_db_instances")
    for page in paginator.paginate():
        for db in page.get("DBInstances", []):
            db_id = db["DBInstanceIdentifier"]
            arn = db["DBInstanceArn"]
            engine = db.get("Engine", "")

            t1, m1, s1 = last_reboot_from_rds_events(rds, db_id, days_back)
            t2, m2, s2 = last_reboot_from_cloudtrail(db_id, cost_start, cost_end)

            chosen = None
            if t1 and (not t2 or t1 >= t2):
                chosen = (t1, m1, s1)
            elif t2:
                chosen = (t2, m2, s2)

            if chosen:
                reboot_time, reboot_msg, reboot_src = chosen
                days_since = (datetime.now(timezone.utc) - reboot_time).days
                note = None
            else:
                reboot_time = reboot_msg = reboot_src = None
                days_since = None
                note = (
                    "N/A (no reboot/restart/failover events returned; "
                    "RDS Events retain max 14 days)"
                )

            meta[arn] = {
                "id": db_id,
                "engine": engine,
                "last_reboot": reboot_time,
                "reboot_message": reboot_msg,
                "reboot_source": reboot_src,
                "days_since_reboot": days_since,
                "note": note,
            }

    return meta


# ---------------- MAIN ----------------
def main():
    start_time, end_time = utc_window(DAYS_BACK)
    start_str = start_time.strftime("%Y-%m-%d")
    end_str = end_time.strftime("%Y-%m-%d")
    output_file = f"{OUTPUT_PREFIX}_{start_str}_to_{end_str}.md"

    ce = boto3.client("ce", region_name="us-east-1")
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
        print("Cost Explorer query failed")
        print(e)
        sys.exit(1)

    per_instance = {}
    per_usage = {}

    for day in resp.get("ResultsByTime", []):
        for g in day.get("Groups", []):
            arn, usage = g["Keys"]
            cost = dec(g["Metrics"]["UnblendedCost"]["Amount"])
            bucket = classify_usage_type(usage)

            per_instance.setdefault(arn, {STATE_FIXED: Decimal("0"), STATE_DYNAMIC: Decimal("0")})
            per_instance[arn][bucket] += cost

            per_usage.setdefault(arn, {})
            per_usage[arn].setdefault((bucket, usage), Decimal("0"))
            per_usage[arn][(bucket, usage)] += cost

    rows = []
    for arn, costs in per_instance.items():
        meta = rds_meta.get(arn, {})
        fixed = costs[STATE_FIXED]
        dynamic = costs[STATE_DYNAMIC]
        total = fixed + dynamic

        rows.append((
            meta.get("id", arn),
            meta.get("engine", ""),
            fixed,
            dynamic,
            total,
            meta.get("last_reboot"),
            meta.get("days_since_reboot"),
            meta.get("reboot_source"),
            meta.get("reboot_message"),
            meta.get("note"),
            arn
        ))

    rows.sort(key=lambda x: x[4], reverse=True)

    # ---------------- MARKDOWN ----------------
    md = []
    md.append("# RDS Cost Report by DB Instance (with Last Reboot)\n")

    md.append("## Reporting Window\n")
    md.append(f"- **Start (UTC):** {start_time.isoformat()}")
    md.append(f"- **End (UTC):** {end_time.isoformat()}")
    md.append(f"- **Lookback:** Last {DAYS_BACK} days\n")

    md.append("## Per-Instance Summary\n")
    md.append("| DB Instance | Engine | Fixed | Dynamic | Total | Last Reboot (UTC) | Days Since | Source |")
    md.append("|---|---|---:|---:|---:|---|---:|---|")

    for r in rows[:MAX_INSTANCES_IN_SUMMARY]:
        reboot = r[5].isoformat() if r[5] else "N/A"
        days = r[6] if r[6] is not None else "N/A"
        src = r[7] or ""
        md.append(
            f"| `{r[0]}` | {r[1]} | {money(r[2])} | {money(r[3])} | "
            f"{money(r[4])} | {reboot} | {days} | {src} |"
        )

    md.append("\n## Instance Details\n")
    for r in rows[:MAX_INSTANCES_IN_SUMMARY]:
        md.append(f"### {r[0]}\n")
        md.append(f"- **Engine:** {r[1]}")
        md.append(f"- **Fixed cost:** {money(r[2])}")
        md.append(f"- **Dynamic cost:** {money(r[3])}")
        md.append(f"- **Total cost:** {money(r[4])}")
        md.append(f"- **ResourceId:** `{r[10]}`")

        if r[5]:
            md.append(f"- **Last reboot:** {r[5].isoformat()}")
            md.append(f"- **Days since reboot:** {r[6]}")
            md.append(f"- **Reboot source:** {r[7]}")
            if r[8]:
                md.append(f"- **Reboot message:** {r[8]}")
        else:
            md.append(f"- **Last reboot:** {r[9]}")

        items = sorted(
            per_usage.get(r[10], {}).items(),
            key=lambda x: x[1],
            reverse=True
        )[:MAX_LINE_ITEMS_PER_INSTANCE]

        md.append("\n**Top usage types:**\n")
        md.append("| Bucket | UsageType | Cost |")
        md.append("|---|---|---:|")
        for (bucket, ut), c in items:
            md.append(f"| {bucket} | `{ut}` | {money(c)} |")
        md.append("")

    with open(output_file, "w") as f:
        f.write("\n".join(md))

    print(f"Generated report: {output_file}")


if __name__ == "__main__":
    main()
