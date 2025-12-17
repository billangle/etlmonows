#!/usr/bin/env python3

"""
AWS Glue Cost Report (Markdown)

Summarize AWS Glue DPU usage for ALL JOBS in the account/region,
filtered to runs starting from 00:00 UTC on the start date.

Outputs:
- A Markdown report with:
  - Reporting window start/end timestamps
  - Total successful DPU hours
  - Total failed DPU hours
  - Estimated cost using GLUE_DPU_RATE
  - Top N failed runs by DPU hours (MAX_FAILED_RUNS)
- Output filename includes human-readable date range:
    glue_cost_report_YYYY-MM-DD_to_YYYY-MM-DD.md
"""

import boto3
from datetime import datetime, timedelta, timezone

# ---------------- CONFIG ----------------
GLUE_DPU_RATE = 0.44        # USD per DPU-hour
DAYS_BACK = 30              # Lookback window in days
MAX_FAILED_RUNS = 50       # Number of failed runs to display
# ----------------------------------------

glue = boto3.client("glue")


def list_all_jobs():
    job_names = []
    paginator = glue.get_paginator("list_jobs")
    for page in paginator.paginate():
        job_names.extend(page.get("JobNames", []))
    return job_names


def get_job_definition(job_name: str):
    resp = glue.get_job(JobName=job_name)
    job = resp["Job"]

    max_capacity = job.get("MaxCapacity")
    worker_type = job.get("WorkerType")
    num_workers = job.get("NumberOfWorkers")
    script_location = job.get("Command", {}).get("ScriptLocation", "")

    return max_capacity, worker_type, num_workers, script_location


def dpu_hours_for_run(run: dict, job_max_capacity=None, worker_type=None, num_workers=None) -> float:
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


def money(x: float) -> str:
    return f"${x:,.2f}"


def main():
    # End time = now (UTC)
    end_time = datetime.now(timezone.utc)

    # Start date = (today - DAYS_BACK) at 00:00 UTC
    start_date = (end_time.date() - timedelta(days=DAYS_BACK))
    start_time = datetime(
        year=start_date.year,
        month=start_date.month,
        day=start_date.day,
        hour=0,
        minute=0,
        second=0,
        tzinfo=timezone.utc,
    )

    # Human-readable date range for filename
    start_str = start_time.strftime("%Y-%m-%d")
    end_str = end_time.strftime("%Y-%m-%d")
    output_file = f"glue_cost_report_{start_str}_to_{end_str}.md"

    job_names = list_all_jobs()
    if not job_names:
        print("No Glue jobs found.")
        return

    total_success_dpu = 0.0
    total_failed_dpu = 0.0
    counted_runs = 0
    failed_runs_details = []

    for job_name in job_names:
        max_cap, worker_type, num_workers, script_location = get_job_definition(job_name)

        paginator = glue.get_paginator("get_job_runs")
        for page in paginator.paginate(JobName=job_name):
            for run in page.get("JobRuns", []):
                started_on = run.get("StartedOn")
                if started_on and started_on < start_time:
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

    md = []
    md.append("# AWS Glue Cost Report\n")

    md.append("## Reporting Window\n")
    md.append(f"- **Start (UTC):** {start_time.isoformat()}")
    md.append(f"- **End (UTC):** {end_time.isoformat()}")
    md.append(f"- **Lookback:** Last **{DAYS_BACK}** days (start pinned to 00:00 UTC)\n")

    md.append("## Summary\n")
    md.append(f"- **Glue jobs scanned:** {len(job_names):,}")
    md.append(f"- **Runs analyzed (in window):** {counted_runs:,}")
    md.append(f"- **Successful DPU hours:** {total_success_dpu:,.3f}")
    md.append(f"- **Failed DPU hours:** {total_failed_dpu:,.3f}")
    md.append(f"- **Total DPU hours:** {total_dpu:,.3f}\n")

    md.append(f"## Estimated Cost (at {money(GLUE_DPU_RATE)} per DPU-hour)\n")
    md.append(f"- **Successful runs cost:** {money(success_cost)}")
    md.append(f"- **Failed runs cost:** {money(failed_cost)}")
    md.append(f"- **Total Glue cost:** {money(total_cost)}\n")

    md.append(f"## Top {MAX_FAILED_RUNS} Failed Runs by DPU Hours\n")
    if not top_failed:
        md.append("No failed runs found in this period.\n")
    else:
        for i, fr in enumerate(top_failed, start=1):
            md.append(f"### #{i}\n")
            md.append(f"- **Job name:** `{fr['job_name']}`")
            md.append(f"- **Run ID:** `{fr['run_id']}`")
            md.append(f"- **DPU hours:** {fr['dpu_hours']:.3f}")
            md.append(f"- **Script:** `{fr['script_location']}`\n")

    with open(output_file, "w") as f:
        f.write("\n".join(md))

    print(f"\nGenerated README report: {output_file}")
    print("Done.\n")


if __name__ == "__main__":
    main()
