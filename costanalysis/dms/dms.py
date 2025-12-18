import boto3
from datetime import datetime, timedelta, timezone
from collections import defaultdict

LOOKBACK_DAYS = 14
REGION = boto3.session.Session().region_name

dms = boto3.client("dms", region_name=REGION)
cw = boto3.client("cloudwatch", region_name=REGION)
ce = boto3.client("ce")

end_date = datetime.now(timezone.utc)
start_date = end_date - timedelta(days=LOOKBACK_DAYS)

# -----------------------------
# Fetch replication tasks
# -----------------------------
tasks = []
paginator = dms.get_paginator("describe_replication_tasks")
for page in paginator.paginate():
    tasks.extend(page["ReplicationTasks"])

task_ids = [t["ReplicationTaskIdentifier"] for t in tasks]

# -----------------------------
# Collect task metrics
# -----------------------------
daily_stats = defaultdict(lambda: {
    "success": 0,
    "failure": 0,
    "runtime": []
})

for task_id in task_ids:
    # Success metric
    success = cw.get_metric_statistics(
        Namespace="AWS/DMS",
        MetricName="ReplicationTaskRunning",
        Dimensions=[{"Name": "ReplicationTaskIdentifier", "Value": task_id}],
        StartTime=start_date,
        EndTime=end_date,
        Period=86400,
        Statistics=["Sum"]
    )

    for dp in success["Datapoints"]:
        day = dp["Timestamp"].date()
        if dp["Sum"] > 0:
            daily_stats[day]["success"] += 1

    # Failure metric
    failure = cw.get_metric_statistics(
        Namespace="AWS/DMS",
        MetricName="ReplicationTaskFailed",
        Dimensions=[{"Name": "ReplicationTaskIdentifier", "Value": task_id}],
        StartTime=start_date,
        EndTime=end_date,
        Period=86400,
        Statistics=["Sum"]
    )

    for dp in failure["Datapoints"]:
        day = dp["Timestamp"].date()
        if dp["Sum"] > 0:
            daily_stats[day]["failure"] += 1

# -----------------------------
# Fetch DMS Costs
# -----------------------------
cost_response = ce.get_cost_and_usage(
    TimePeriod={
        "Start": start_date.strftime("%Y-%m-%d"),
        "End": end_date.strftime("%Y-%m-%d")
    },
    Granularity="DAILY",
    Metrics=["UnblendedCost"],
    Filter={
        "Dimensions": {
            "Key": "SERVICE",
            "Values": ["AWS Database Migration Service"]
        }
    }
)

daily_costs = {}
for day in cost_response["ResultsByTime"]:
    date_key = datetime.strptime(day["TimePeriod"]["Start"], "%Y-%m-%d").date()
    daily_costs[date_key] = float(
        day["Total"]["UnblendedCost"]["Amount"]
    )

# -----------------------------
# Print Report
# -----------------------------
print("\nAWS DMS SUCCESS / FAILURE / COST REPORT\n")
print("Date       Success Fail Total   DMS Cost ($)")
print("------------------------------------------------")

for day in sorted(daily_stats.keys()):
    s = daily_stats[day]["success"]
    f = daily_stats[day]["failure"]
    total = s + f
    cost = daily_costs.get(day, 0.0)

    print(f"{day}   {s:<7} {f:<5} {total:<7} {cost:>10.2f}")
