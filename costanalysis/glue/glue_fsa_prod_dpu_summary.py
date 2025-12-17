#!/usr/bin/env python3
"""
Summarize AWS Glue DPU usage for all jobs whose names start with 'FSA-PROD'.

Outputs:
- Total successful DPU hours across all matching jobs
- Total failed DPU hours across all matching jobs
- Top 20 failed runs by DPU hours (job, run id, hours, script location)

Requirements:
  pip install boto3
  AWS credentials/region configured (e.g., via `aws configure`)
"""

import boto3
from collections import defaultdict

PREFIX = "FSA"
# If you want to see cost as well, set this (standard Glue price in USD per DPU-hour)
GLUE_DPU_RATE = 0.44

glue = boto3.client("glue")


def list_jobs_with_prefix(prefix: str):
    """Return all Glue job names starting with the given prefix."""
    job_names = []
    paginator = glue.get_paginator("list_jobs")
    for page in paginator.paginate():
        for name in page.get("JobNames", []):
            if name.startswith(prefix):
                job_names.append(name)
    return job_names


def get_job_definition(job_name: str):
    """
    Get job-level settings used to approximate DPU usage if DPUSeconds is missing.
    """
    resp = glue.get_job(JobName=job_name)
    job = resp["Job"]

    max_capacity = job.get("MaxCapacity")
    worker_type = job.get("WorkerType")
    num_workers = job.get("NumberOfWorkers")

    # Script location (S3 path) is useful to identify the code.
    command = job.get("Command", {})
    script_location = command.get("ScriptLocation", "")

    return max_capacity, worker_type, num_workers, script_location


def dpu_hours_for_run(run: dict,
                      job_max_capacity=None,
                      worker_type=None,
                      num_workers=None) -> float:
    """
    Compute DPU hours for a single Glue job run.

    Prefer run['DPUSeconds'] if available (auto-scaling/FLEX jobs).
    Otherwise approximate using ExecutionTime * capacity.
    """
    # 1) Exact billing metric if present
    dpu_seconds = run.get("DPUSeconds")
    if dpu_seconds is not None:
        return dpu_seconds / 3600.0

    # 2) Fallback: approximate from ExecutionTime * capacity
    exec_time_sec = run.get("ExecutionTime") or 0

    # WorkerType → DPU per worker (AWS standard mapping)
    worker_to_dpu = {"G.025X": 0.25, "G.1X": 1, "G.2X": 2}
    if worker_type and num_workers:
        dpu_capacity = worker_to_dpu.get(worker_type, 1) * num_workers
    elif job_max_capacity:
        dpu_capacity = job_max_capacity
    else:
        # Last-resort default if nothing is set; adjust if you know your defaults.
        dpu_capacity = 10

    return exec_time_sec * dpu_capacity / 3600.0


def main():
    job_names = list_jobs_with_prefix(PREFIX)
    if not job_names:
        print(f"No jobs found starting with prefix '{PREFIX}'")
        return

    print(f"Found {len(job_names)} jobs starting with '{PREFIX}'")

    total_success_dpu = 0.0
    total_failed_dpu = 0.0

    # Collect details on failed runs for "top 20"
    failed_runs_details = []

    for job_name in job_names:
        max_cap, worker_type, num_workers, script_location = get_job_definition(job_name)

        paginator = glue.get_paginator("get_job_runs")
        for page in paginator.paginate(JobName=job_name):
            for run in page.get("JobRuns", []):
                state = run.get("JobRunState")
                run_id = run.get("Id") or run.get("JobRunId")

                dpu_h = dpu_hours_for_run(
                    run,
                    job_max_capacity=max_cap,
                    worker_type=worker_type,
                    num_workers=num_workers,
                )

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

    # Sort failed runs by DPU hours (descending) and take top 20
    failed_runs_details.sort(key=lambda x: x["dpu_hours"], reverse=True)
    top_failed = failed_runs_details[:20]

    total_dpu = total_success_dpu + total_failed_dpu

    print("\n=== SUMMARY (all jobs starting with 'FSA-PROD') ===")
    print(f"Total successful DPU hours: {total_success_dpu:,.3f}")
    print(f"Total failed DPU hours:    {total_failed_dpu:,.3f}")
    print(f"Total DPU hours:           {total_dpu:,.3f}")

    # Optional: cost estimate
    total_success_cost = total_success_dpu * GLUE_DPU_RATE
    total_failed_cost = total_failed_dpu * GLUE_DPU_RATE
    total_cost = total_success_cost + total_failed_cost

    print("\nEstimated cost (rate ${:.2f} per DPU-hour):".format(GLUE_DPU_RATE))
    print(f"  Success cost: ${total_success_cost:,.2f}")
    print(f"  Failed  cost: ${total_failed_cost:,.2f}")
    print(f"  Total  cost:  ${total_cost:,.2f}")

    print("\n=== TOP 20 FAILED RUNS BY DPU HOURS ===")
    if not top_failed:
        print("No failed runs found.")
        return

    for i, fr in enumerate(top_failed, start=1):
        print(f"\n#{i}")
        print(f"  Job name:       {fr['job_name']}")
        print(f"  Run ID:         {fr['run_id']}")
        print(f"  DPU hours:      {fr['dpu_hours']:.3f}")
        print(f"  Script location:{' ' if fr['script_location'] else ''}{fr['script_location']}")

    # If you also want a CSV of failed runs, uncomment below.
    # import csv
    # with open("fsa_prod_failed_runs_top20.csv", "w", newline="") as f:
    #     writer = csv.DictWriter(f, fieldnames=["job_name", "run_id", "dpu_hours", "script_location"])
    #     writer.writeheader()
    #     writer.writerows(top_failed)
    # print("\nWrote fsa_prod_failed_runs_top20.csv")


if __name__ == "__main__":
    main()
