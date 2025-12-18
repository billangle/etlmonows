import boto3
from datetime import datetime, timedelta, timezone, date

LOOKBACK_DAYS = 14  # recommend <= 14 (keeps reports fast and consistent)
REGION = boto3.session.Session().region_name

dms = boto3.client("dms", region_name=REGION)
ce  = boto3.client("ce")

end_time = datetime.now(timezone.utc)
start_time = end_time - timedelta(days=LOOKBACK_DAYS)

# ---- helpers
def daterange(d0: date, d1: date):
    cur = d0
    while cur <= d1:
        yield cur
        cur += timedelta(days=1)

def get_all_events(source_type: str):
    """Pull all DMS events in the time window (handles pagination)."""
    events = []
    paginator = dms.get_paginator("describe_events")
    for page in paginator.paginate(
        SourceType=source_type,
        StartTime=start_time,
        EndTime=end_time,
        MaxRecords=100
    ):
        events.extend(page.get("Events", []))
    return events

# ---- 1) Pull replication-task events (this is the key fix)
events = get_all_events("replication-task")

# DMS event IDs we care about (documented):
# - DMS-EVENT-0069: task started
# - DMS-EVENT-0078: task failed
# (AWS also emits "task stopped" etc., but not needed for success/failure counts)
START_EVENT_ID = "DMS-EVENT-0069"
FAIL_EVENT_ID  = "DMS-EVENT-0078"

daily = {}
start_day = start_time.date()
end_day = end_time.date()

for d in daterange(start_day, end_day):
    daily[d] = {"success": 0, "failure": 0, "total": 0, "cost": 0.0}

# Count by scanning event messages (event ID is typically in the message text)
for ev in events:
    ev_date = ev["Date"].date()
    msg = ev.get("Message", "")
    if ev_date not in daily:
        continue

    if START_EVENT_ID in msg:
        daily[ev_date]["success"] += 1
        daily[ev_date]["total"] += 1
    elif FAIL_EVENT_ID in msg:
        daily[ev_date]["failure"] += 1
        daily[ev_date]["total"] += 1

# ---- 2) Pull daily DMS cost from Cost Explorer
cost = ce.get_cost_and_usage(
    TimePeriod={
        "Start": start_day.strftime("%Y-%m-%d"),
        # CE end is exclusive
        "End": (end_day + timedelta(days=1)).strftime("%Y-%m-%d"),
    },
    Granularity="DAILY",
    Metrics=["UnblendedCost"],
    Filter={"Dimensions": {"Key": "SERVICE", "Values": ["AWS Database Migration Service"]}},
)

for day in cost["ResultsByTime"]:
    d = datetime.strptime(day["TimePeriod"]["Start"], "%Y-%m-%d").date()
    amt = float(day["Total"]["UnblendedCost"]["Amount"])
    if d in daily:
        daily[d]["cost"] = amt

# ---- Print report (always prints all days, even if 0)
print("\nAWS DMS DAILY SUCCESS / FAILURE / COST REPORT\n")
print("Date         Success  Failure  Total   DMS Cost ($)")
print("-----------------------------------------------------")
for d in sorted(daily.keys()):
    row = daily[d]
    print(f"{d}   {row['success']:>7}  {row['failure']:>7}  {row['total']:>5}   {row['cost']:>11.2f}")

print(f"\nRegion: {REGION}")
print(f"Window: {start_time.isoformat()} -> {end_time.isoformat()}")
print(f"Events scanned: {len(events)}")
