#!/usr/bin/env python3

"""
Summarize AWS Glue DPU usage for ALL JOBS in the account/region.

Outputs:
- Total successful DPU hours across all Glue jobs
- Total failed DPU hours across all Glue jobs
- Top 20 failed runs by DPU hours

Requirements:
- pip install boto3
- Valid AWS credentials (CloudShell works automatically)
"""

import boto3
from collections import defaultdict

GLUE_DPU_RATE = 0.44  # USD per DPU-hour

glue = boto3.client("glue")


def list_all_jobs():
    """Return all Glue job names in the account/region."""
    job_names = []
    paginator = glue.get_paginator("list_jobs")
    for page in paginator.paginate():
        job_names.extend(page.get("JobNames", []))
    return job_names


def get_job_definition(job_name: str):
    """
    Get job-level info:
      - MaxCapacity
      - WorkerType
      - NumberOfWorkers
      - Script S3 location
    """
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
    """
    Compute DPU hours for a single run.

    Prefer exact metric DPUSeconds when available.
    Otherwise approximate using ExecutionTime × capacity.
    """
    # 1) Exact metric for autoscaling/flex jobs
    dpu_seconds = run.get("DPUSeconds")
    if dpu_seconds is not None:
        return dpu_seconds / 3600.0

    # 2) Approximate for older/static jobs
    exec_time_sec = run.get("ExecutionTime") or 0

    worker_to_dpu = {"G.025X": 0.25, "G.1X": 1, "G.2X": 2}

    if worker_type and num_workers:
        dpu_capacity = worker_to_dpu.get(worker_type, 1) * num_workers
    elif job_max_capacity:
        dpu_capacity = job_max_capacity
    else:
        # Fallback: old Glue jobs default to 10 DPUs unless overridden
        dpu_capacity = 10

    return exec_time_sec * dpu_capacity / 3600.0


def main():
    job_names = list_all_jobs()
    if not job_names:
        print("No Glue jobs found.")
        return

    print(f"Found {len(job_names)} total Glue jobs.")

    total_success_dpu = 0.0
    total_failed_dpu = 0.0

    failed_runs_details = []
    counted_runs = 0

    for job_name in job_names:
        max_cap, worker_type, num_workers, script_location = get_job_definition(job_name)

        paginator = glue.get_paginator("get_job_runs")
        for page in paginator.paginate(JobName=job_name):
            for run in page.get("JobRuns", []):
                state = run.get("JobRunState")
                run_id = run.get("Id") or run.get("JobRunId")
                counted_runs += 1

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

    # Sort and pick top 20 failed runs
    failed_runs_details.sort(key=lambda x: x["dpu_hours"], reverse=True)
    top_failed = failed_runs_details[:20]

    # Summary
    total_dpu = total_success_dpu + total_failed_dpu

    print("\n=== SUMMARY (ALL Glue Jobs) ===")
    print(f"Runs analyzed:             {counted_runs}")
    print(f"Total successful DPU hours: {total_success_dpu:,.3f}")
    print(f"Total failed DPU hours:     {total_failed_dpu:,.3f}")
    print(f"Total DPU hours:            {total_dpu:,.3f}")

    # Cost estimate
    success_cost = total_success_dpu * GLUE_DPU_RATE
    failed_cost = total_failed_dpu * GLUE_DPU_RATE
    total_cost = success_cost + failed_cost

    print("\nEstimated cost (rate ${:.2f}/DPU-hour):".format(GLUE_DPU_RATE))
    print(f"  Successful runs cost: ${success_cost:,.2f}")
    print(f"  Failed runs cost:     ${failed_cost:,.2f}")
    print(f"  Overall cost:         ${total_cost:,.2f}")

    print("\n=== TOP 20 FAILED RUNS BY DPU HOURS ===")
    if not top_failed:
        print("No failed runs found.")
        return

    for i, fr in enumerate(top_failed, start=1):
        print(f"\n#{i}")
        print(f"  Job name:        {fr['job_name']}")
        print(f"  Run ID:          {fr['run_id']}")
        print(f"  DPU hours:       {fr['dpu_hours']:.3f}")
        print(f"  Script location: {fr['script_location']}")

    print("\nDone.\n")


if __name__ == "__main__":
    main()
