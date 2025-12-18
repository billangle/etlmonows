#!/usr/bin/env python3
"""
RDS per-DB-instance fixed vs dynamic cost report (Cost Explorer Resources API)

- Uses Cost Explorer GetCostAndUsageWithResources (RESOURCE_ID) to attribute cost to DB instances.
- Filters to Amazon RDS.
- Groups by RESOURCE_ID and USAGE_TYPE.
- Classifies USAGE_TYPE into FIXED vs DYNAMIC (heuristic).
- Outputs a Markdown report whose filename includes a human-readable date range.
- Start time pinned to 00:00 UTC on the start date.

Docs:
- GetCostAndUsageWithResources requires grouping by or filtering by ResourceId. :contentReference[oaicite:3]{index=3}
- Cost Explorer supports filtering by Resources (RESOURCE_ID). :contentReference[oaicite:4]{index=4}
"""

import re
import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import boto3
from botocore.exceptions import ClientError

# ---------------- CONFIG ----------------
DAYS_BACK = 14
GLUE_STYLE_RATE = None  # set to a Decimal like Decimal("0.44") if you want a synthetic rate; otherwise use real billed costs.

MAX_INSTANCES_IN_SUMMARY = 50     # show top N instances by total cost
MAX_LINE_ITEMS_PER_INSTANCE = 10  # show top N usage-types per instance in the detail section
OUTPUT_PREFIX = "rds_instance_cost_report"
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
    start_time = datetime(start_date.year, start_date.month, start_date.day, 0, 0, 0, tzinfo=timezone.utc)
    return start_time, end_time

def ce_time_period(start_time: datetime, end_time: datetime):
    # CE End is exclusive; extend to include today's date
    return {"Start": start_time.date().isoformat(), "End": (end_time.date() + timedelta(days=1)).isoformat()}

def classify_usage_type(usage_type: str) -> str:
    ut = (usage_type or "").lower()

    fixed_patterns = [
        r"\brds:dbinstance", r"\brds:instanceusage", r"\brds:inst",  # compute
        r"\brds:storage", r"\brds:gp2storage", r"\brds:gp3storage",
        r"\brds:io1storage", r"\brds:io2storage",                    # storage
        r"\brds:provisionediops", r"\brds:piops",                    # provisioned IOPS (often baseline-ish)
    ]

    dynamic_patterns = [
        r"\brds:iousage", r"\brds:iorequest",                        # variable IO
        r"\brds:chargedbackupusage", r"\brds:backup",                # backup storage often variable :contentReference[oaicite:5]{index=5}
        r"\bsnapshot\b",                                             # snapshot storage/copy
        r"\bdataxfer\b|\bdatatransfer\b|\bdata transfer\b|\bxfer\b", # transfer
        r"\brds:performanceinsights|\bperformance insights\b|\brds:pi\b",
        r"\brds:proxy\b",
        r"\benhanced monitoring\b|\bmonitoring\b",
    ]

    if any(re.search(p, ut) for p in fixed_patterns):
        return STATE_FIXED
    if any(re.search(p, ut) for p in dynamic_patterns):
        return STATE_DYNAMIC

    # Default: treat unknown as DYNAMIC (safer for cost-control triage)
    return STATE_DYNAMIC

def build_db_arn_map():
    """
    Build mapping: DBInstanceArn -> DBInstanceIdentifier (and engine)
    """
    rds = boto3.client("rds")
    mapping = {}
    paginator = rds.get_paginator("describe_db_instances")
    for page in paginator.paginate():
        for db in page.get("DBInstances", []):
            arn = db.get("DBInstanceArn")
            ident = db.get("DBInstanceIdentifier")
            engine = db.get("Engine")
            if arn and ident:
                mapping[arn] = {"identifier": ident, "engine": engine}
    return mapping

def main():
    start_time, end_time = utc_window(DAYS_BACK)
    start_str = start_time.strftime("%Y-%m-%d")
    end_str = end_time.strftime("%Y-%m-%d")
    output_file = f"{OUTPUT_PREFIX}_{start_str}_to_{end_str}.md"

    # Cost Explorer client endpoint is ce.us-east-1 (global-ish); region_name not your RDS region. :contentReference[oaicite:6]{index=6}
    ce = boto3.client("ce", region_name="us-east-1")

    # Optional: map resource ARN -> identifier
    arn_map = {}
    try:
        arn_map = build_db_arn_map()
    except ClientError:
        # not fatal; we'll just show raw resource IDs
        arn_map = {}

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
        print("Cost Explorer resource-level query failed.")
        print("Most common causes:")
        print("  - Missing permission: ce:GetCostAndUsageWithResources")
        print("  - Cost Explorer not enabled / not available for resource-level breakdown in your payer/account")
        print("Fallback for perfect per-instance monthly cost is CUR + Athena (lineItem/ResourceId).")
        print(f"\nAWS error:\n{e}")
        sys.exit(1)

    # Aggregate: instance -> bucket(fixed/dynamic) -> cost; also keep per-usage-type breakdown
    per_instance = {}
    per_instance_usage = {}

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

            per_instance_usage.setdefault(resource_id, {})
            per_instance_usage[resource_id].setdefault((bucket, usage_type), Decimal("0"))
            per_instance_usage[resource_id][(bucket, usage_type)] += cost

    # Build sortable summary
    summary_rows = []
    for rid, buckets in per_instance.items():
        fixed = buckets.get(STATE_FIXED, Decimal("0"))
        dynamic = buckets.get(STATE_DYNAMIC, Decimal("0"))
        total = fixed + dynamic

        label = rid
        meta = arn_map.get(rid)
        if meta:
            label = f"{meta['identifier']} ({meta.get('engine','')})"

        summary_rows.append((rid, label, fixed, dynamic, total))

    summary_rows.sort(key=lambda x: x[4], reverse=True)

    grand_fixed = sum((r[2] for r in summary_rows), Decimal("0"))
    grand_dynamic = sum((r[3] for r in summary_rows), Decimal("0"))
    grand_total = grand_fixed + grand_dynamic

    # Markdown output
    md = []
    md.append("# RDS Cost Report by DB Instance (Fixed vs Dynamic)\n")
    md.append("## Reporting Window\n")
    md.append(f"- **Start (UTC, pinned to 00:00):** {start_time.isoformat()}")
    md.append(f"- **End (UTC):** {end_time.isoformat()}")
    md.append(f"- **Lookback:** Last **{DAYS_BACK}** days\n")

    md.append("## Totals (All DB Instances)\n")
    md.append(f"- **Fixed:** {money(grand_fixed)}")
    md.append(f"- **Dynamic:** {money(grand_dynamic)}")
    md.append(f"- **Total:** {money(grand_total)}\n")

    md.append(f"## Per-Instance Summary (Top {MAX_INSTANCES_IN_SUMMARY} by total cost)\n")
    md.append("| DB Instance | Fixed | Dynamic | Total | ResourceId |")
    md.append("|---|---:|---:|---:|---|")
    for rid, label, fixed, dynamic, total in summary_rows[:MAX_INSTANCES_IN_SUMMARY]:
        md.append(f"| `{label}` | {money(fixed)} | {money(dynamic)} | {money(total)} | `{rid}` |")

    md.append("\n## Top Non-Zero Instances (Detail: top usage-types per instance)\n")
    for rid, label, fixed, dynamic, total in summary_rows[:MAX_INSTANCES_IN_SUMMARY]:
        if total <= 0:
            continue

        md.append(f"### {label}\n")
        md.append(f"- **Fixed:** {money(fixed)}")
        md.append(f"- **Dynamic:** {money(dynamic)}")
        md.append(f"- **Total:** {money(total)}")
        md.append(f"- **ResourceId:** `{rid}`\n")

        # Top usage types for this resource
        items = []
        for (bucket, ut), cost in per_instance_usage.get(rid, {}).items():
            items.append((bucket, ut, cost))
        items.sort(key=lambda x: x[2], reverse=True)

        md.append(f"**Top {MAX_LINE_ITEMS_PER_INSTANCE} usage-types:**\n")
        md.append("| Bucket | UsageType | Cost |")
        md.append("|---|---|---:|")
        for bucket, ut, cost in items[:MAX_LINE_ITEMS_PER_INSTANCE]:
            md.append(f"| {bucket} | `{ut}` | {money(cost)} |")
        md.append("")

    md.append("## Notes\n")
    md.append("- This report uses **Cost Explorer resource-level attribution** (`GetCostAndUsageWithResources`) grouped by `RESOURCE_ID`. :contentReference[oaicite:7]{index=7}")
    md.append("- Cost Explorer supports filtering/grouping by **Resources** (resource IDs). :contentReference[oaicite:8]{index=8}")
    md.append("- If you need perfect month-long per-instance accuracy in all cases, use **CUR** and query `lineItem/ResourceId` (Athena). :contentReference[oaicite:9]{index=9}")

    with open(output_file, "w") as f:
        f.write("\n".join(md))

    print(f"Generated report: {output_file}")

if __name__ == "__main__":
    main()
