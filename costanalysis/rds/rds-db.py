#!/usr/bin/env python3

"""
RDS Per-DB-Instance Fixed vs Dynamic Cost Report
INCLUDING Last Reboot Time (from RDS Events)

- Uses Cost Explorer resource-level data
- Attributes cost by DB instance
- Splits Fixed vs Dynamic
- Adds last reboot timestamp + message per instance
- Outputs Markdown with human-readable date range in filename
"""

import re
import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import boto3
from botocore.exceptions import ClientError

# ---------------- CONFIG ----------------
DAYS_BACK = 14
MAX_INSTANCES_IN_SUMMARY = 50
MAX_LINE_ITEMS_PER_INSTANCE = 10
OUTPUT_PREFIX = "rds_instance_cost_report"
# ----------------------------------------

SERVICE_VALUE = "Amazon Relational Database Service"

STATE_FIXED = "FIXED"
STATE_DYNAMIC = "DYNAMIC"

REBOOT_KEYWORDS = ["reboot", "restart", "failover"]

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
    start_time = datetime(start_date.year, start_date.month, start_date.day, 0, 0, 0, tzinfo=timezone.utc)
    return start_time, end_time

def ce_time_period(start_time: datetime, end_time: datetime):
    return {
        "Start": start_time.date().isoformat(),
        "End": (end_time.date() + timedelta(days=1)).isoformat()
    }

def classify_usage_type(usage_type: str) -> str:
    ut = (usage_type or "").lower()
    if any(x in ut for x in ["instance", "storage", "gp3", "gp2", "io1", "io2", "piops"]):
        return STATE_FIXED
    return STATE_DYNAMIC

def get_last_reboot(rds, db_id):
    """
    Returns (timestamp, message) of the most recent reboot-like event.
    """
    try:
        events = rds.describe_events(
            SourceType="db-instance",
            SourceIdentifier=db_id,
            Duration=43200  # last 30 days
        ).get("Events", [])
    except ClientError:
        return None, None

    reboot_events = [
        e for e in events
        if any(k in e["Message"].lower() for k in REBOOT_KEYWORDS)
    ]

    if not reboot_events:
        return None, None

    last = sorted(reboot_events, key=lambda e: e["Date"])[-1]
    return last["Date"], last["Message"]

def build_db_metadata():
    rds = boto3.client("rds")
    meta = {}

    paginator = rds.get_paginator("describe_db_instances")
    for page in paginator.paginate():
        for db in page["DBInstances"]:
            db_id = db["DBInstanceIdentifier"]
            arn = db["DBInstanceArn"]
            engine = db["Engine"]

            reboot_time, reboot_msg = get_last_reboot(rds, db_id)

            meta[arn] = {
                "id": db_id,
                "engine": engine,
                "last_reboot": reboot_time,
                "reboot_message": reboot_msg,
            }

    return meta

def main():
    start_time, end_time = utc_window(DAYS_BACK)
    start_str = start_time.strftime("%Y-%m-%d")
    end_str = end_time.strftime("%Y-%m-%d")
    output_file = f"{OUTPUT_PREFIX}_{start_str}_to_{end_str}.md"

    ce = boto3.client("ce", region_name="us-east-1")
    rds_meta = build_db_metadata()

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

    for day in resp["ResultsByTime"]:
        for g in day["Groups"]:
            arn, usage = g["Keys"]
            cost = dec(g["Metrics"]["UnblendedCost"]["Amount"])
            bucket = classify_usage_type(usage)

            per_instance.setdefault(arn, {STATE_FIXED: Decimal("0"), STATE_DYNAMIC: Decimal("0")})
            per_instance[arn][bucket] += cost

    rows = []
    for arn, costs in per_instance.items():
        meta = rds_meta.get(arn, {})
        total = costs[STATE_FIXED] + costs[STATE_DYNAMIC]
        rows.append((
            meta.get("id", arn),
            meta.get("engine", ""),
            costs[STATE_FIXED],
            costs[STATE_DYNAMIC],
            total,
            meta.get("last_reboot"),
            meta.get("reboot_message"),
            arn
        ))

    rows.sort(key=lambda x: x[4], reverse=True)

    # ---------------- Markdown ----------------
    md = []
    md.append("# RDS Cost Report by DB Instance (with Last Reboot)\n")

    md.append("## Reporting Window\n")
    md.append(f"- **Start (UTC):** {start_time.isoformat()}")
    md.append(f"- **End (UTC):** {end_time.isoformat()}\n")

    md.append("## Per-Instance Summary\n")
    md.append("| DB Instance | Engine | Fixed | Dynamic | Total | Last Reboot (UTC) |")
    md.append("|---|---|---:|---:|---:|---|")

    for r in rows[:MAX_INSTANCES_IN_SUMMARY]:
        reboot = r[5].isoformat() if r[5] else "N/A"
        md.append(
            f"| `{r[0]}` | {r[1]} | {money(r[2])} | {money(r[3])} | {money(r[4])} | {reboot} |"
        )

    md.append("\n## Instance Details\n")
    for r in rows[:MAX_INSTANCES_IN_SUMMARY]:
        md.append(f"### {r[0]}\n")
        md.append(f"- **Engine:** {r[1]}")
        md.append(f"- **Fixed cost:** {money(r[2])}")
        md.append(f"- **Dynamic cost:** {money(r[3])}")
        md.append(f"- **Total cost:** {money(r[4])}")
        if r[5]:
            md.append(f"- **Last reboot:** {r[5].isoformat()}")
            md.append(f"- **Reboot reason:** {r[6]}")
        else:
            md.append("- **Last reboot:** Not found in last 30 days")
        md.append("")

    with open(output_file, "w") as f:
        f.write("\n".join(md))

    print(f"Generated report: {output_file}")

if __name__ == "__main__":
    main()
