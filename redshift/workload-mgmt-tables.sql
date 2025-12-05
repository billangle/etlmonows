-- Currently running queries
SELECT pid, user_name, query, starttime, substring, wlm_queue_start_time
FROM stv_recents
ORDER BY starttime DESC;

-- Queries consuming CPU
SELECT query, service_class, total_exec_time, exec_time, cpu_time, queue_time
FROM svl_qlog
ORDER BY cpu_time DESC
LIMIT 10;

-- Blockers / locks
SELECT *
FROM svv_transaction_locks;
