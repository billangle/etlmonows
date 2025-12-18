#!/usr/bin/env python3
"""
RDS PostgreSQL Fixed vs Dynamic Cost Report (Cost Explorer)

What it does:
- Queries AWS Cost Explorer (actual billed spend) for the last N days
  (start pinned to 00:00 UTC of the start date).
- Filters to Amazon RDS service.
- Groups by USAGE_TYPE.
- Classifies spend into FIXED vs DYNAMIC buckets.
- Writes a Markdown report with human-readable date range in filename.

Notes:
- Cost Explorer is a global endpoint (ce.us-east-1). Boto3 handles this.
- You must have Cost Explorer enabled and permission: ce:GetCostAndUsage.
- "PostgreSQL only" filtering from billing data is not perfect because RDS usage
  types often do not include engine explicitly. This script provides a best-effort
  filter that you can tune.

References:
- Cost Explorer GetCostAndUsage API :contentReference[oaicite:3]{index=3}
- RDS billing components overview :contentReference[oaicite:4]{index=4}
"""

import re
import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import boto3

# ---------------- CONFIG ----------------
DAYS_BACK = 30
# Optional: set True to attempt to narrow down to likely PostgreSQL-related usage types.
# Leave False to report ALL RDS costs (recommended if you want completeness).
FILTER_POSTGRES_BEST_EFFORT = False

# Report details
OUTPUT_PREFIX = "rds_postgres_cost_report"
TOP_LINE_ITEMS = 50  # how many usage-types to list in the detail section
# ----------------------------------------


def utc_midnight_days_back(days_back: int):
    """Return (start_time_utc_midnight, end_time_now_utc)."""
    end_time = datetime.now(timezone.utc)
    start_date = end_time.date() - timedelta(days=days_back)
    start_time = datetime(start_date.year, start_date.month, start_date.day, 0, 0, 0, tzinfo=timezone.utc)
    return start_time, end_time


def money(x: Decimal) -> str:
    return f"${x:,.2f}"


def dec(s) -> Decimal:
    try:
        return Decimal(str(s))
    except Exception:
        return Decimal("0")


def build_ce_time_period(start_time: datetime, end_time: datetime):
    """
    Cost Explorer expects YYYY-MM-DD and End is exclusive.
    We'll set End to (end_date + 1 day) so we include 'today' up to now
    in daily granularity.
    """
    start = start_time.date().isoformat()
    end_exclusive = (end_time.date() + timedelta(days=1)).isoformat()
    return {"Start": start, "End": end_exclusive}


def ce_client():
    # Cost Explorer is effectively us-east-1; boto3 will route correctly.
    return boto3.client("ce", region_name="us-east-1")


def classify_usage_type(usage_type: str):
    """
    Heuristic classification:
      FIXED = capacity-like, predictable baseline
      DYNAMIC = activity/traffic/retention-driven or add-on features

    You should tune these patterns based on your own CUR/CE usage types.
    """
    ut = usage_type.lower()

    # FIXED patterns (instance-hours, storage GB-month, provisioned IOPS)
    fixed_patterns = [
        r"\brds:dbinstance",          # instance usage (often appears as RDS:dbInstance...)
        r"\brds:instance",            # some accounts show 'RDS:InstanceUsage'
        r"\brds:storage",             # RDS:StorageUsage / Storage
        r"\brds:gp2storage",          # old gp2 naming
        r"\brds:gp3storage",
        r"\brds:io1storage",
        r"\brds:io2storage",
        r"\brds:provisionediops",     # provisioned IOPS often baseline-like
        r"\brds:piops",               # sometimes appears as PIOPS usage
    ]

    # DYNAMIC patterns (io requests, backups, snapshots, transfer, extras)
    dynamic_patterns = [
        r"\brds:iousage",             # IO requests/ops
        r"\brds:iorequest",           # variations
        r"\brds:chargedbackupusage",  # backup storage billed :contentReference[oaicite:5]{index=5}
        r"\brds:backup",              # generic backup naming
        r"\bsnapshot",                # snapshot storage/copy
        r"\bdataxfer\b|\bdata transfer\b|\bdatatransfer\b|\bxfer\b",
        r"\brds:performanceinsights|\bpi\b",   # Performance Insights add-on
        r"\brds:proxy",                        # RDS Proxy
        r"\brds:monitoring|\benhanced monitoring\b",
        r"\brds:export",                       # snapshot export, etc.
    ]

    if any(re.search(p, ut) for p in fixed_patterns):
        return "FIXED"
    if any(re.search(p, ut) for p in dynamic_patterns):
        return "DYNAMIC"

    # Default bucket: treat unknown as DYNAMIC (safer for cost-control)
    return "DYNAMIC"


def postgres_best_effort_usage_type_filter(usage_type: str) -> bool:
    """
    Best-effort filtering if you *only* want likely PostgreSQL.
    Many RDS usage types are engine-agnostic; this filter may exclude legitimate costs.
    Use with caution.
    """
    ut = usage_type.lower()
    # Common tokens seen in some usage types/line items; you MUST tune for your org.
    return ("postgres" in ut) or ("postgresql" in ut)


def get_rds_cost_by_usage_type(start_time: datetime, end_time: datetime):
    ce = ce_client()
    time_period = build_ce_time_period(start_time, end_time)

    # Cost Explorer query: group by USAGE_TYPE for Amazon RDS
    # Docs: GetCostAndUsage supports grouping by dimensions like SERVICE, USAGE_TYPE. :contentReference[oaicite:6]{index=6}
    resp = ce.get_cost_and_usage(
        TimePeriod=time_period,
        Granularity="DAILY",
        Metrics=["UnblendedCost"],
        Filter={
            "Dimensions": {
                "Key": "SERVICE",
                "Values": ["Amazon Relational Database Service"]
            }
        },
        GroupBy=[{"Type": "DIMENSION", "Key": "USAGE_TYPE"}],
    )

    # Aggregate daily groups into total per usage type
    totals = {}
    for day in resp.get("ResultsByTime", []):
        for g in day.get("Groups", []):
            ut = g.get("Keys", ["UNKNOWN"])[0]
            amt = dec(g["Metrics"]["UnblendedCost"]["Amount"])
            totals[ut] = totals.get(ut, Decimal("0")) + amt

    # Optional: narrow to best-effort postgres usage types
    if FILTER_POSTGRES_BEST_EFFORT:
        totals = {k: v for k, v in totals.items() if postgres_best_effort_usage_type_filter(k)}

    return totals


def main():
    start_time, end_time = utc_midnight_days_back(DAYS_BACK)
    start_str = start_time.strftime("%Y-%m-%d")
    end_str = end_time.strftime("%Y-%m-%d")

    output_file = f"{OUTPUT_PREFIX}_{start_str}_to_{end_str}.md"

    try:
        totals_by_ut = get_rds_cost_by_usage_type(start_time, end_time)
    except Exception as e:
        print(f"ERROR calling Cost Explorer. Do you have ce:GetCostAndUsage permission and CE enabled?\n{e}")
        sys.exit(1)

    # Classify into fixed/dynamic
    fixed_total = Decimal("0")
    dynamic_total = Decimal("0")

    line_items = []
    for ut, cost in totals_by_ut.items():
        bucket = classify_usage_type(ut)
        if bucket == "FIXED":
            fixed_total += cost
        else:
            dynamic_total += cost
        line_items.append((ut, bucket, cost))

    line_items.sort(key=lambda x: x[2], reverse=True)

    grand_total = fixed_total + dynamic_total

    # Markdown report
    md = []
    md.append("# RDS PostgreSQL Fixed vs Dynamic Cost Report\n")

    md.append("## Reporting Window\n")
    md.append(f"- **Start (UTC, pinned to 00:00):** {start_time.isoformat()}")
    md.append(f"- **End (UTC):** {end_time.isoformat()}")
    md.append(f"- **Lookback:** Last **{DAYS_BACK}** days\n")

    md.append("## Scope\n")
    md.append("- **Service filter:** Amazon Relational Database Service (RDS)\n")
    if FILTER_POSTGRES_BEST_EFFORT:
        md.append("- **Engine filter:** Best-effort based on `USAGE_TYPE` text matching (may undercount)\n")
    else:
        md.append("- **Engine filter:** None (includes all RDS engines present in billing data)\n")

    md.append("## Fixed vs Dynamic Cost Summary\n")
    md.append(f"- **Fixed cost (baseline capacity):** {money(fixed_total)}")
    md.append(f"- **Dynamic cost (activity/retention/add-ons):** {money(dynamic_total)}")
    md.append(f"- **Total RDS cost (in scope):** {money(grand_total)}\n")

    if grand_total > 0:
        fixed_pct = (fixed_total / grand_total) * Decimal("100")
        dyn_pct = (dynamic_total / grand_total) * Decimal("100")
        md.append("### Percent Split\n")
        md.append(f"- **Fixed:** {fixed_pct:.1f}%")
        md.append(f"- **Dynamic:** {dyn_pct:.1f}%\n")

    md.append(f"## Line Items (Top {TOP_LINE_ITEMS} by spend)\n")
    md.append("| UsageType | Bucket | Cost |")
    md.append("|---|---:|---:|")
    for ut, bucket, cost in line_items[:TOP_LINE_ITEMS]:
        md.append(f"| `{ut}` | {bucket} | {money(cost)} |")

    md.append("\n## Notes on Classification\n")
    md.append("- This report uses **Cost Explorer actual billed cost** (UnblendedCost) grouped by **USAGE_TYPE**. :contentReference[oaicite:7]{index=7}")
    md.append("- RDS charges include instance compute, storage, and backup storage (among others). :contentReference[oaicite:8]{index=8}")
    md.append("- Backup storage often appears as `RDS:ChargedBackupUsage` and is visible when grouping by usage type. :contentReference[oaicite:9]{index=9}")
    md.append("- If you want perfect accuracy by engine and resource, the next step is CUR (Cost & Usage Report) + resource tags.\n")

    with open(output_file, "w") as f:
        f.write("\n".join(md))

    print(f"Generated report: {output_file}")


if __name__ == "__main__":
    main()
