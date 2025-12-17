#!/usr/bin/env python3

"""
Summarize AWS Glue DPU usage for ALL JOBS in the account/region,
filtered to ONLY the last N days (DAYS_BACK).

Outputs:
- A README.md report with:
  - Total successful DPU hours
  - Total failed DPU hours
  - Estimated cost
  - Top 20 failed runs with details

Requires:
- pip install boto3
- AWS CloudShell or any environment with valid credentials
"""

import boto3
from datetime import datetime, timedelta, timezone

GLUE_DPU_RATE = 0.44   # USD per DPU-hour
DAYS_BACK = 30         # Lookback window (days)
MAX_FAILED_RUNS = 20  # Top N failed runs to report
OUTPUT_FILE = "glue_cost_report.md"

glue = boto3.client("glue")


def list_all_jobs():
    """Return all Glue job names in the region."""
    job_names = []
    paginator = glue.get_paginator("list_jobs")
    for page in paginator.paginate():
        job_names.extend(page.get("JobNames", []))
    return job_names


def get_job_definition(job_name: str):
    """Retrieve job-level metadata."""
    resp = glue.get_job(JobName=job_name)
    job = resp["Job"]

    max_capacity = job.get("MaxCapacity")
    worker_type = job.get("WorkerType")
    num_workers = job.get("NumberOfWorkers")
    script_location = job.get("Command", {}).get("ScriptLocation", "")

    return max_capacity, worker_type, num_workers, script_location


def dpu_hours_for_run(run: dict,
                      job_max_capacity=None,
                      worker_type=None,
                      num_workers=None) -> float:
    """Compute DPU hours for a single run."""
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
        dpu_capacity = 10  # fallback

    return exec_time_sec * dpu_capacity / 3600.0


def main():
    cutoff = datetime.now(timezone.utc) - timedelta(days=DAYS_BACK)

    job_names = list_all_jobs()
    if not job_names:
        print("No Glue jobs found.")
        return

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
    top_failed = failed_runs_details[:MAX_FAILED_RUNS]
    total_dpu = total_success_dpu + total_failed_dpu

    success_cost = total_success_dpu * GLUE_DPU_RATE
    failed_cost = total_failed_dpu * GLUE_DPU_RATE
    total_cost = success_cost + failed_cost

    # --- BUILD README.md CONTENT ---
    md = []
    md.append(f"# AWS Glue Cost Report — Last {DAYS_BACK} Days\n")
    md.append("This report summarizes DPU usage and estimated cost for **all Glue jobs** "
              f"in the last **{DAYS_BACK} days**.\n")

    md.append("## Summary\n")
    md.append(f"- **Runs analyzed:** {counted_runs:,}")
    md.append(f"- **Successful DPU hours:** {total_success_dpu:,.3f}")
    md.append(f"- **Failed DPU hours:** {total_failed_dpu:,.3f}")
    md.append(f"- **Total DPU hours:** {total_dpu:,.3f}\n")

    md.append(f"## Estimated Cost (at ${GLUE_DPU_RATE:.2f} per DPU-hour)\n")
    md.append(f"- **Success cost:** ${success_cost:,.2f}")
    md.append(f"- **Failed cost:** ${failed_cost:,.2f}")
    md.append(f"- **Total cost:** ${total_cost:,.2f}\n")

    md.append(f"## Top {MAX_FAILED_RUNS} Failed Runs by DPU Hours (Last {DAYS_BACK} Days)\n")
    if not top_failed:
        md.append("No failed runs found.\n")
    else:
        for i, fr in enumerate(top_failed, start=1):
            md.append(f"### #{i}\n")
            md.append(f"- **Job name:** `{fr['job_name']}`")
            md.append(f"- **Run ID:** `{fr['run_id']}`")
            md.append(f"- **DPU hours:** {fr['dpu_hours']:.3f}")
            md.append(f"- **Script:** `{fr['script_location']}`\n")

    # Write README.md
    with open(OUTPUT_FILE, "w") as f:
        f.write("\n".join(md))

    print(f"\nGenerated Markdown report: {OUTPUT_FILE}\n")
    print("Done.\n")


if __name__ == "__main__":
    main()
