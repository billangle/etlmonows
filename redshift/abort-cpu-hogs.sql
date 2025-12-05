CREATE OR REPLACE QUERY MONITORING RULE abort_cpu_hogs
ACTION ABORT
WHEN cpu_time > 1200000; -- 1.2M ms = 20 minutes of CPU consumption
