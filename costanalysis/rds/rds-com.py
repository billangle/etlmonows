#!/usr/bin/env python3
"""
Combined RDS Cost + Per-Instance Cost + Instance Events Report (max 14 days)

Outputs a single Markdown report that includes:
1) Total RDS cost (Cost Explorer, SERVICE filter)
2) Per DB instance cost (Cost Explorer resource-level, fixed vs dynamic)
3) All DB instance events (RDS DescribeEvents) in same window,
   grouped by day with a count (one line per day).

Constraints:
- RDS DescribeEvents is capped to 14 days. We enforce DAYS_BACK <= 14.
- Start time pinned to 00:00 UTC.
"""

import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone, date
from decimal import Decimal
import boto3
from botocore.exceptions import ClientError

# ---------------- CONFIG ----------------
DAYS_BACK = 14  # MUST be <= 14
MAX_INSTANCES_IN_SUMMARY = 50
MAX_LINE_ITEMS_PER_INSTANCE = 10
MAX_EVENT_MESSAGE_PREVIEW = 2  # show up to N distinct messages per day rollup
OUTPUT_PREFIX = "rds_cost_and_events_report"
# ----------------------------------------

SERVICE_VALUE = "Amazon Relational Database Service"

STATE_FIXED = "FIXED"
STATE_DYNAMIC = "DYNAMIC"

# Broad-ish fixed/dynamic heuristic (tune to your CUR/CE usage types if needed)
FIXED_TOKENS = ["instance", "storage", "gp2", "gp3", "io1", "io2", "piops", "provisioned"]
DYNAMIC_TOKENS = ["iops", "io usage", "backup", "snapshot", "data transfer", "xfer", "performance insights", "proxy", "monitoring"]

def dec(x) -> Decimal:
    try:
        return Decimal(str(x))
    except Exception:
        return Decimal("0")

def money(x: Decimal) -> str:
    return f"${x:,.2f}"

def utc_window(days_back: int):
    if days_back > 14:
        raise ValueError("DAYS_BACK must be <= 14 due to RDS DescribeEvents retention/limits.")
    end_time = datetime.now(timezone.utc)
    start_date = end_time.date() - timedelta(days=days_back)
    start_time = datetime(start_date.year, start_date.month, start_date.day, 0, 0, 0, tzinfo=timezone.utc)
    return start_time, end_time

def ce_time_period(start_time: datetime, end_time: datetime):
    # CE end is exclusive; include today by adding 1 day
    return {"Start": start_time.date().isoformat(), "End": (end_time.date() + timedelta(days=1)).isoformat()}

def classify_usage_type(usage_type: str) -> str:
    ut = (usage_type or "").lower()
    if any(t in ut for t in FIXED_TOKENS):
        return STATE_FIXED
    if any(t in ut for t in DYNAMIC_TOKENS):
        return STATE_DYNAMIC
    # Default to dynamic for unknowns (safer for triage)
    return STATE_DYNAMIC

def build_output_filename(start_time: datetime, end_time: datetime) -> str:
    start_str = start_time.strftime("%Y-%m-%d")
    end_str = end_time.strftime("%Y-%m-%d")
    return f"{OUTPUT_PREFIX}_{start_str}_to_{end_str}.md"

# ----------- COST EXPLORER: TOTAL RDS COST -----------
def get_total_rds_cost(ce, start_time: datetime, end_time: datetime) -> Decimal:
    resp = ce.get_cost_and_usage(
        TimePeriod=ce_time_period(start_time, end_time),
        Granularity="DAILY",
        Metrics=["UnblendedCost"],
        Filter={"Dimensions": {"Key": "SERVICE", "Values": [SERVICE_VALUE]}},
    )

    total = Decimal("0")
    for day in resp.get("ResultsByTime", []):
        amt = day.get("Total", {}).get("UnblendedCost", {}).get("Amount", "0")
        total += dec(amt)
    return total

# ----------- COST EXPLORER: PER-INSTANCE COST -----------
def get_per_instance_cost(ce, start_time: datetime, end_time: datetime):
    """
    Returns:
      per_instance_cost[resource_id] = {FIXED: Decimal, DYNAMIC: Decimal}
      per_instance_usage[resource_id][(bucket, usage_type)] = Decimal
    """
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

    per_instance = {}
    per_usage = {}

    for day in resp.get("ResultsByTime", []):
        for g in day.get("Groups", []):
            keys = g.get("Keys", [])
            if len(keys) != 2:
                continue
            resource_id, usage_type = keys[0], keys[1]
            cost = dec(g["Metrics"]["UnblendedCost"]["Amount"])
            bucket = classify_usage_type(usage_type)

            per_instance.setdefault(resource_id, {STATE_FIXED: Decimal("0"), STATE_DYNAMIC: Decimal("0")})
            per_instance[resource_id][bucket] += cost

            per_usage.setdefault(resource_id, {})
            per_usage[resource_id].setdefault((bucket, usage_type), Decimal("0"))
            per_usage[resource_id][(bucket, usage_type)] += cost

    return per_instance, per_usage

# ----------- RDS METADATA + EVENTS -----------
def list_db_instances_with_arn():
    rds = boto3.client("rds")
    instances = []
    paginator = rds.get_paginator("describe_db_instances")
    for page in paginator.paginate():
        for db in page.get("DBInstances", []):
            instances.append({
                "id": db["DBInstanceIdentifier"],
                "arn": db["DBInstanceArn"],
                "engine": db.get("Engine", ""),
            })
    return instances

def get_instance_events_grouped_by_day(db_id: str, minutes: int):
    """
    Returns dict[date] = {"count": int, "top_messages": [str]}
    Group by event Date (UTC date). If multiple events same day => one line w/ count.
    """
    rds = boto3.client("rds")
    try:
        events = rds.describe_events(
            SourceType="db-instance",
            SourceIdentifier=db_id,
            Duration=int(minutes),
        ).get("Events", [])
    except ClientError:
        return {}

    # group by day
    by_day_msgs = defaultdict(list)
    for e in events:
        d = e["Date"].date()  # UTC date
        by_day_msgs[d].append(e.get("Message", "").strip())

    # reduce to count + preview
    grouped = {}
    for d, msgs in by_day_msgs.items():
        c = len(msgs)
        # show top N most common distinct messages
        counts = Counter(msgs)
        top = [m for (m, _) in counts.most_common(MAX_EVENT_MESSAGE_PREVIEW)]
        grouped[d] = {"count": c, "top_messages": top}

    return dict(grouped)

# ----------- REPORT -----------
def main():
    try:
        start_time, end_time = utc_window(DAYS_BACK)
    except ValueError as ve:
        print(str(ve))
        sys.exit(1)

    output_file = build_output_filename(start_time, end_time)
    events_minutes = DAYS_BACK * 1440  # always <= 20160 since DAYS_BACK <= 14

    ce = boto3.client("ce", region_name="us-east-1")

    # Total RDS cost
    try:
        total_rds_cost = get_total_rds_cost(ce, start_time, end_time)
    except ClientError as e:
        print("ERROR: Cost Explorer get_cost_and_usage failed (need ce:GetCostAndUsage).")
        print(e)
        sys.exit(1)

    # Per instance cost
    try:
        per_instance, per_usage = get_per_instance_cost(ce, start_time, end_time)
    except ClientError as e:
        print("ERROR: Cost Explorer resource-level query failed (need ce:GetCostAndUsageWithResources).")
        print(e)
        sys.exit(1)

    # DB list + events
    try:
        dbs = list_db_instances_with_arn()
    except ClientError as e:
        print("ERROR: describe_db_instances failed (need rds:DescribeDBInstances).")
        print(e)
        sys.exit(1)

    arn_to_meta = {d["arn"]: d for d in dbs}
    id_to_meta = {d["id"]: d for d in dbs}

    # Build combined per-instance rows (only those that show up in CE resource attribution)
    rows = []
    for resource_id, buckets in per_instance.items():
        meta = arn_to_meta.get(resource_id, {"id": resource_id, "engine": "", "arn": resource_id})
        fixed = buckets.get(STATE_FIXED, Decimal("0"))
        dynamic = buckets.get(STATE_DYNAMIC, Decimal("0"))
        total = fixed + dynamic
        rows.append((meta["id"], meta.get("engine", ""), fixed, dynamic, total, resource_id))

    rows.sort(key=lambda x: x[4], reverse=True)

    # Totals from per-instance attribution (may be < total_rds_cost if CE resource attribution is incomplete)
    attrib_fixed = sum((r[2] for r in rows), Decimal("0"))
    attrib_dynamic = sum((r[3] for r in rows), Decimal("0"))
    attrib_total = attrib_fixed + attrib_dynamic
    unattributed = total_rds_cost - attrib_total

    # Events for ALL instances (even those not present in CE resource view)
    events_by_instance = {}
    for d in dbs:
        events_by_instance[d["id"]] = get_instance_events_grouped_by_day(d["id"], events_minutes)

    # Markdown
    md = []
    md.append("# RDS Cost + Per-Instance Cost + Events Report\n")

    md.append("## Reporting Window\n")
    md.append(f"- **Start (UTC, pinned to 00:00):** {start_time.isoformat()}")
    md.append(f"- **End (UTC):** {end_time.isoformat()}")
    md.append(f"- **Lookback:** Last **{DAYS_BACK}** days (max 14 days)\n")

    md.append("## Total RDS Cost (Cost Explorer)\n")
    md.append(f"- **Total RDS cost:** {money(total_rds_cost)}\n")

    md.append("## Per-Instance Cost Summary (Cost Explorer resource attribution)\n")
    md.append(f"- **Attributed total (sum of instances):** {money(attrib_total)}")
    md.append(f"- **Attributed fixed:** {money(attrib_fixed)}")
    md.append(f"- **Attributed dynamic:** {money(attrib_dynamic)}")
    md.append(f"- **Unattributed (Total - Attributed):** {money(unattributed)}")
    md.append("")
    md.append("> Note: Cost Explorer resource-level attribution may not account for every RDS line item; the “unattributed” bucket shows what didn’t map to a DB instance resource id.\n")

    md.append(f"### Top {MAX_INSTANCES_IN_SUMMARY} Instances by Total Cost\n")
    md.append("| DB Instance | Engine | Fixed | Dynamic | Total | ResourceId |")
    md.append("|---|---|---:|---:|---:|---|")
    for (db_id, engine, fixed, dynamic, total, rid) in rows[:MAX_INSTANCES_IN_SUMMARY]:
        md.append(f"| `{db_id}` | {engine} | {money(fixed)} | {money(dynamic)} | {money(total)} | `{rid}` |")

    md.append("\n## Per-Instance Details\n")
    for (db_id, engine, fixed, dynamic, total, rid) in rows[:MAX_INSTANCES_IN_SUMMARY]:
        md.append(f"### {db_id}\n")
        md.append(f"- **Engine:** {engine}")
        md.append(f"- **Fixed:** {money(fixed)}")
        md.append(f"- **Dynamic:** {money(dynamic)}")
        md.append(f"- **Total:** {money(total)}")
        md.append(f"- **ResourceId:** `{rid}`\n")

        # Top usage types
        items = []
        for (bucket, ut), c in per_usage.get(rid, {}).items():
            items.append((bucket, ut, c))
        items.sort(key=lambda x: x[2], reverse=True)

        md.append(f"**Top {MAX_LINE_ITEMS_PER_INSTANCE} usage types:**\n")
        md.append("| Bucket | UsageType | Cost |")
        md.append("|---|---|---:|")
        for bucket, ut, c in items[:MAX_LINE_ITEMS_PER_INSTANCE]:
            md.append(f"| {bucket} | `{ut}` | {money(c)} |")
        md.append("")

        # Events rollup (ALL events)
        ev = events_by_instance.get(db_id, {})
        md.append(f"**Events (all) — grouped by day (last {DAYS_BACK} days):**\n")
        if not ev:
            md.append("- No events returned in this window.\n")
        else:
            md.append("| Date (UTC) | Event Count | Message Preview |")
            md.append("|---|---:|---|")
            for d in sorted(ev.keys(), reverse=True):
                count = ev[d]["count"]
                preview = " ; ".join(ev[d]["top_messages"]) if ev[d]["top_messages"] else ""
                # keep preview readable
                if len(preview) > 200:
                    preview = preview[:200] + "…"
                md.append(f"| {d.isoformat()} | {count} | {preview} |")
            md.append("")

    # Also add an "Events-only" section for instances not in CE attribution (optional but useful)
    attributed_ids = {r[0] for r in rows}
    other_instances = [d for d in dbs if d["id"] not in attributed_ids]
    if other_instances:
        md.append("\n## Instances With Events But No Cost Attribution\n")
        md.append("These DB instances had events returned, but did not appear in the Cost Explorer resource-level cost attribution set.\n")
        for d in other_instances:
            ev = events_by_instance.get(d["id"], {})
            if not ev:
                continue
            md.append(f"### {d['id']}\n")
            md.append(f"- **Engine:** {d.get('engine','')}")
            md.append("| Date (UTC) | Event Count | Message Preview |")
            md.append("|---|---:|---|")
            for day_key in sorted(ev.keys(), reverse=True):
                count = ev[day_key]["count"]
                preview = " ; ".join(ev[day_key]["top_messages"]) if ev[day_key]["top_messages"] else ""
                if len(preview) > 200:
                    preview = preview[:200] + "…"
                md.append(f"| {day_key.isoformat()} | {count} | {preview} |")
            md.append("")

    with open(output_file, "w") as f:
        f.write("\n".join(md))

    print(f"Generated report: {output_file}")


if __name__ == "__main__":
    main()
