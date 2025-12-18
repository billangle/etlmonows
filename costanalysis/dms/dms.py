import boto3
from datetime import datetime, timedelta, timezone, date
from collections import defaultdict

LOOKBACK_DAYS = 14
REGION = boto3.session.Session().region_name or "us-east-1"

dms = boto3.client("dms", region_name=REGION)
cw  = boto3.client("cloudwatch", region_name=REGION)
ce  = boto3.client("ce")

end_time = datetime.now(timezone.utc)
start_time = end_time - timedelta(days=LOOKBACK_DAYS)

def daterange(d0: date, d1: date):
    cur = d0
    while cur <= d1:
        yield cur
        cur += timedelta(days=1)

# -------------------------
# 1) Get tasks and build task -> instance identifier mapping
# -------------------------
tasks = []
for page in dms.get_paginator("describe_replication_tasks").paginate():
    tasks.extend(page.get("ReplicationTasks", []))

instances = []
for page in dms.get_paginator("describe_replication_instances").paginate():
    instances.extend(page.get("ReplicationInstances", []))

# ARN -> Identifier map
inst_arn_to_id = {i["ReplicationInstanceArn"]: i["ReplicationInstanceIdentifier"] for i in instances}

task_dim_pairs = []
for t in tasks:
    task_id = t["ReplicationTaskIdentifier"]
    inst_arn = t.get("ReplicationInstanceArn")
    inst_id = inst_arn_to_id.get(inst_arn)
    if inst_id:
        task_dim_pairs.append((inst_id, task_id))

# -------------------------
# 2) Daily aggregation scaffold (always prints all days)
# -------------------------
daily = {}
for d in daterange(start_time.date(), end_time.date()):
    daily[d] = {"task_cpu_samples": 0, "task_cpu_active_samples": 0, "dms_cost": 0.0}

# -------------------------
# 3) Query a task-level metric that is known to require BOTH dimensions
#    Use Task CPUUtilization (exists per DMS monitoring docs)
# -------------------------
METRIC = "CPUUtilization"   # task CPUUtilization
NAMESPACE = "AWS/DMS"
PERIOD = 300                # 5 min samples (adjust if needed)

for inst_id, task_id in task_dim_pairs:
    resp = cw.get_metric_statistics(
        Namespace=NAMESPACE,
        MetricName=METRIC,
        Dimensions=[
            {"Name": "ReplicationInstanceIdentifier", "Value": inst_id},
            {"Name": "ReplicationTaskIdentifier", "Value": task_id},
        ],
        StartTime=start_time,
        EndTime=end_time,
        Period=PERIOD,
        Statistics=["Average"],
    )

    for dp in resp.get("Datapoints", []):
        d = dp["Timestamp"].date()
        if d not in daily:
            continue
        daily[d]["task_cpu_samples"] += 1
        # Treat CPU > 0 as “task active” (tunable threshold)
        if dp["Average"] > 0.0:
            daily[d]["task_cpu_active_samples"] += 1

# Convert “active samples” to approximate active minutes
# (active_samples * PERIOD seconds) / 60
for d in daily:
    daily[d]["active_minutes_est"] = (daily[d]["task_cpu_active_samples"] * PERIOD) / 60.0

# -------------------------
# 4) Add DMS daily cost from Cost Explorer
# -------------------------
cost = ce.get_cost_and_usage(
    TimePeriod={
        "Start": start_time.date().strftime("%Y-%m-%d"),
        "End": (end_time.date() + timedelta(days=1)).strftime("%Y-%m-%d"),  # end exclusive
    },
    Granularity="DAILY",
    Metrics=["UnblendedCost"],
    Filter={"Dimensions": {"Key": "SERVICE", "Values": ["AWS Database Migration Service"]}},
)

for day in cost.get("ResultsByTime", []):
    d = datetime.strptime(day["TimePeriod"]["Start"], "%Y-%m-%d").date()
    amt = float(day["Total"]["UnblendedCost"]["Amount"])
    if d in daily:
        daily[d]["dms_cost"] = amt

# -------------------------
# 5) Print report
# -------------------------
print("\nAWS DMS DAILY ACTIVITY (METRICS) + COST REPORT\n")
print("Date         Active Minutes (est)   DMS Cost ($)")
print("-------------------------------------------------")
for d in sorted(daily.keys()):
    print(f"{d}   {daily[d]['active_minutes_est']:>18.1f}   {daily[d]['dms_cost']:>10.2f}")

print(f"\nRegion: {REGION}")
print(f"Tasks seen: {len(tasks)}")
print(f"Task/instance metric pairs used: {len(task_dim_pairs)}")
