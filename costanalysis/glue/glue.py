#!/usr/bin/env python3

"""
Summarize AWS Glue DPU usage for all jobs whose names start with 'FSA-PROD'
for the last N days.

Outputs:
- Total successful DPU hours across all matching jobs
- Total failed DPU hours across all matching jobs
- Top 20 failed runs by DPU hours (job, run id, hours, script location)
"""

import boto3
from collections import defaultdict
from datetime import datetime, timedelta, timezone

PREFIX = "FSA"
DAYS_BACK = 30  # look back this many days from now
GLUE_DPU_RATE = 0.44  # USD per DPU-hour

glue = boto3.client("glue")


def list_jobs_with_prefix(prefix: str):
    job_names = []
    paginator = glue.get_paginator("list_jobs")
    for page in paginator.paginate():
        for name in page.get("JobNames", []):
            if name.startswith(prefix):
                job_names.append(name)
    return job_names


def get_job_definition(job_name: str):
    resp = glue.get_job(JobName=job_name)
    job = resp["Job"]

    max_capacity = job.get("MaxCapacity")
    worker_type = job.get("WorkerType")
    num_workers = job.get("NumberOfWorkers")

    command = job.get("Command", {})
    script_location = command.get("ScriptLocation", "")

    return max_capacity, worker_type, num_workers, script_location


def dpu_hours_for_run(run: dict,
                      job_max_capacity=None,
                      worker_type=None,
                      num_workers=None) -> float:
    dpu_seconds = run.get("DPUSeconds")
    if dpu_seconds is not None:
        return dpu_seconds / 3600.0

    exec_time_sec = run.get("ExecutionTime") or 0

    worker_to_dpu = {"G.025X": 0.25, "G.1X": 1, "G.2X": 2}
    if worker_type and num_workers:
        dpu_capacity = worker_to_dpu.get(worker_type, 1) * num_workers
    elif job_max_capacity:
        dpu_capacity = job_max_capacity
    else:
        dpu_capacity = 10  # fallback guess

    return exec_time_sec * dpu_capacity / 3600.0


def main():
    cutoff = datetime.now(timezone.utc) - timedelta(days=DAYS_BACK)

    job_names = list_jobs_with_prefix(PREFIX)
    if not job_names:
        print(f"No jobs found starting with prefix '{PREFIX}'")
        return

    print(f"Found {len(job_names)} jobs starting with '{PREFIX}'")
    print(f"Including runs with StartedOn >= {cutoff.isoformat()}")

    total_success_dpu = 0.0
    total_failed_dpu = 0.0

    failed_runs_details = []
    counted_runs = 0

    for job_name in job_names:
        max_cap, worker_type, num_workers, script_location = get_job_definition(job_name)

        paginator = glue.get_paginator("get_job_runs")
        for page in paginator.paginate(JobName=job_name):
            for run in page.get("JobRuns", []):
                started_on = run.get("StartedOn")
                if started_on and started_on < cutoff:
                    # older than our window – skip
                    continue

                state = run.get("JobRunState")
                run_id = run.get("Id") or run.get("JobRunId")

                dpu_h = dpu_hours_for_run(
                    run,
                    job_max_capacity=max_cap,
                    worker_type=worker_type,
                    num_workers=num_workers,
                )

                counted_runs += 1

                if state == "SUCCEEDED":
                    total_success_dpu += dpu_h
                elif state == "FAILED":
                    total_failed_dpu += dpu_h
                    failed_runs_details.append({
                        "job_name": job_name,
                        "run_id": run_id,
                        "dpu_hours": dpu_h,
                        "script_location": script_location,
                    })

    failed_runs_details.sort(key=lambda x: x["dpu_hours"], reverse=True)
    top_failed = failed_runs_details[:20]

    total_dpu = total_success_dpu + total_failed_dpu

    print("\n=== SUMMARY (jobs starting with 'FSA-PROD', last"
          f" {DAYS_BACK} days) ===")
    print(f"Runs counted in window: {counted_runs}")
    print(f"Total successful DPU hours: {total_success_dpu:,.3f}")
    print(f"Total failed DPU hours:    {total_failed_dpu:,.3f}")
    print(f"Total DPU hours:           {total_dpu:,.3f}")

    success_cost = total_success_dpu * GLUE_DPU_RATE
    failed_cost = total_failed_dpu * GLUE_DPU_RATE
    total_cost = success_cost + failed_cost

    print("\nEstimated cost (rate ${:.2f} per DPU-hour):".format(GLUE_DPU_RATE))
    print(f"  Success cost: ${success_cost:,.2f}")
    print(f"  Failed  cost: ${failed_cost:,.2f}")
    print(f"  Total  cost:  ${total_cost:,.2f}")

    print("\n=== TOP 20 FAILED RUNS BY DPU HOURS (within window) ===")
    if not top_failed:
        print("No failed runs found in this time window.")
        return

    for i, fr in enumerate(top_failed, start=1):
        print(f"\n#{i}")
        print(f"  Job name:        {fr['job_name']}")
        print(f"  Run ID:          {fr['run_id']}")
        print(f"  DPU hours:       {fr['dpu_hours']:.3f}")
        print(f"  Script location: {fr['script_location']}")


if __name__ == "__main__":
    main()
