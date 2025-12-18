#!/usr/bin/env python3
import argparse
import boto3
import sys
import time
from datetime import datetime, timedelta, timezone, date
from collections import defaultdict

# ----------------------------
# Helpers
# ----------------------------
def utc_now():
    return datetime.now(timezone.utc)

def parse_yyyy_mm_dd(s: str) -> date:
    return datetime.strptime(s, "%Y-%m-%d").date()

def daterange(d0: date, d1: date):
    cur = d0
    while cur <= d1:
        yield cur
        cur += timedelta(days=1)

def day_window_utc(d: date):
    start = datetime(d.year, d.month, d.day, 0, 0, 0, tzinfo=timezone.utc)
    end = start + timedelta(days=1)
    return start, end

def retryable_call(fn, max_attempts=6, base_sleep=0.4):
    """
    Simple exponential backoff for throttling / transient errors.
    """
    attempt = 0
    while True:
        attempt += 1
        try:
            return fn()
        except Exception as e:
            msg = str(e)
            # Back off on common AWS transient failures
            transient = any(x in msg for x in [
                "Throttling", "Rate exceeded", "TooManyRequestsException",
                "RequestLimitExceeded", "ServiceUnavailable", "InternalError"
            ])
            if (not transient) or attempt >= max_attempts:
                raise
            sleep_s = base_sleep * (2 ** (attempt - 1))
            time.sleep(sleep_s)

def safe_region(session, fallback="us-east-1"):
    r = session.region_name
    return r if r else fallback

# ----------------------------
# Main
# ----------------------------
def main():
    p = argparse.ArgumentParser(description="AWS DMS daily activity + cost report (day-chunked CloudWatch queries).")
    p.add_argument("--region", default=None, help="AWS region (defaults to session region)")
    p.add_argument("--days", type=int, default=14, help="Lookback days (default: 14)")
    p.add_argument("--start-date", default=None, help="Start date YYYY-MM-DD (overrides --days)")
    p.add_argument("--end-date", default=None, help="End date YYYY-MM-DD inclusive (default: today UTC)")
    p.add_argument("--period", type=int, default=300, help="CloudWatch period seconds (default: 300)")
    p.add_argument("--cpu-threshold", type=float, default=0.0, help="CPU avg threshold to count as 'active' (default: 0.0)")
    p.add_argument("--metric", default="CPUUtilization", help="MetricName (default: CPUUtilization)")
    p.add_argument("--namespace", default="AWS/DMS", help="CloudWatch namespace (default: AWS/DMS)")
    p.add_argument("--csv", default=None, help="Optional CSV output path")
    args = p.parse_args()

    session = boto3.session.Session()
    region = args.region or safe_region(session)

    dms = session.client("dms", region_name=region)
    cw  = session.client("cloudwatch", region_name=region)
    ce  = session.client("ce", region_name=region)  # CE is global-ish but region param is fine

    # Determine date window
    if args.start_date:
        start_d = parse_yyyy_mm_dd(args.start_date)
        end_d = parse_yyyy_mm_dd(args.end_date) if args.end_date else utc_now().date()
    else:
        end_d = utc_now().date()
        start_d = end_d - timedelta(days=max(0, args.days - 1))

    if start_d > end_d:
        print("ERROR: start-date is after end-date", file=sys.stderr)
        sys.exit(2)

    # ---- 1) Fetch replication instances
    instances = []
    paginator = dms.get_paginator("describe_replication_instances")
    for page in retryable_call(lambda: paginator.paginate().__iter__()):
        instances.extend(page.get("ReplicationInstances", []))

    inst_arn_to_id = {i["ReplicationInstanceArn"]: i["ReplicationInstanceIdentifier"] for i in instances}

    # ---- 2) Fetch replication tasks and map to instance identifiers
    tasks = []
    paginator = dms.get_paginator("describe_replication_tasks")
    for page in retryable_call(lambda: paginator.paginate().__iter__()):
        tasks.extend(page.get("ReplicationTasks", []))

    task_dim_pairs = []
    missing_inst = 0
    for t in tasks:
        task_id = t.get("ReplicationTaskIdentifier")
        inst_arn = t.get("ReplicationInstanceArn")
        inst_id = inst_arn_to_id.get(inst_arn)
        if task_id and inst_id:
            task_dim_pairs.append((inst_id, task_id))
        else:
            missing_inst += 1

    # Daily aggregation: one row per day
    daily = {}
    for d in daterange(start_d, end_d):
        daily[d] = {
            "active_tasks_set": set(),
            "samples": 0,
            "active_samples": 0,
            "active_minutes_est": 0.0,
            "dms_cost": 0.0,
        }

    # ---- 3) Day-chunked CloudWatch queries (prevents 1440 datapoint limit)
    # For each day, for each task/instance pair, pull datapoints for that day.
    # This can be a lot of API calls if you have many tasks; but it will work reliably.
    # (If you want it faster later, we can switch to GetMetricData batching.)
    period = args.period
    threshold = args.cpu_threshold

    print(f"Region: {region}")
    print(f"Window (UTC): {start_d} -> {end_d} (inclusive)")
    print(f"Tasks: {len(tasks)} | Task/instance pairs used: {len(task_dim_pairs)} | Missing instance mapping: {missing_inst}")
    print(f"Metric: {args.namespace}/{args.metric} | Period: {period}s | Active if Average > {threshold}\n")

    for d in daterange(start_d, end_d):
        day_start, day_end = day_window_utc(d)

        for inst_id, task_id in task_dim_pairs:
            def do_call():
                return cw.get_metric_statistics(
                    Namespace=args.namespace,
                    MetricName=args.metric,
                    Dimensions=[
                        {"Name": "ReplicationInstanceIdentifier", "Value": inst_id},
                        {"Name": "ReplicationTaskIdentifier", "Value": task_id},
                    ],
                    StartTime=day_start,
                    EndTime=day_end,
                    Period=period,
                    Statistics=["Average"],
                )

            try:
                resp = retryable_call(do_call)
            except Exception as e:
                # Don’t kill the whole report—log and continue
                print(f"WARN: CW metric query failed for {d} inst={inst_id} task={task_id}: {e}", file=sys.stderr)
                continue

            dps = resp.get("Datapoints", [])
            if not dps:
                continue

            # Count samples for this day
            daily[d]["samples"] += len(dps)

            # Active samples: Average > threshold
            active_count = 0
            for dp in dps:
                if dp.get("Average", 0.0) > threshold:
                    active_count += 1

            if active_count > 0:
                daily[d]["active_samples"] += active_count
                daily[d]["active_tasks_set"].add(task_id)

    # Convert active_samples to active_minutes_est
    for d in daily:
        daily[d]["active_minutes_est"] = (daily[d]["active_samples"] * period) / 60.0

    # ---- 4) Pull daily DMS cost (Cost Explorer: end is exclusive)
    # CE requires Start/End strings; End must be day AFTER end_d.
    ce_start = start_d.strftime("%Y-%m-%d")
    ce_end = (end_d + timedelta(days=1)).strftime("%Y-%m-%d")

    try:
        ce_resp = retryable_call(lambda: ce.get_cost_and_usage(
            TimePeriod={"Start": ce_start, "End": ce_end},
            Granularity="DAILY",
            Metrics=["UnblendedCost"],
            Filter={"Dimensions": {"Key": "SERVICE", "Values": ["AWS Database Migration Service"]}},
        ))
        for day in ce_resp.get("ResultsByTime", []):
            dd = datetime.strptime(day["TimePeriod"]["Start"], "%Y-%m-%d").date()
            amt = float(day["Total"]["UnblendedCost"]["Amount"])
            if dd in daily:
                daily[dd]["dms_cost"] = amt
    except Exception as e:
        print(f"WARN: Cost Explorer query failed (costs will be 0.0): {e}", file=sys.stderr)

    # ---- 5) Print report (always prints all days)
    print("AWS DMS DAILY ACTIVITY + COST REPORT (UTC)")
    print("Date         ActiveTasks  ActiveMinutes(est)  Samples  ActiveSamples  DMSCost($)")
    print("---------------------------------------------------------------------------------")

    rows = []
    for d in sorted(daily.keys()):
        row = daily[d]
        active_tasks = len(row["active_tasks_set"])
        active_min = row["active_minutes_est"]
        samples = row["samples"]
        active_samples = row["active_samples"]
        cost = row["dms_cost"]

        print(f"{d}   {active_tasks:>11}   {active_min:>17.1f}  {samples:>7}  {active_samples:>12}  {cost:>9.2f}")

        rows.append((d, active_tasks, active_min, samples, active_samples, cost))

    # ---- 6) Optional CSV
    if args.csv:
        try:
            import csv
            with open(args.csv, "w", newline="") as f:
                w = csv.writer(f)
                w.writerow(["date", "active_tasks", "active_minutes_est", "samples", "active_samples", "dms_cost_usd"])
                for d, active_tasks, active_min, samples, active_samples, cost in rows:
                    w.writerow([d.isoformat(), active_tasks, f"{active_min:.1f}", samples, active_samples, f"{cost:.2f}"])
            print(f"\nWrote CSV: {args.csv}")
        except Exception as e:
            print(f"WARN: Failed to write CSV: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()
