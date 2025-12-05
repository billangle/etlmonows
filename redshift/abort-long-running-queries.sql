CREATE OR REPLACE QUERY MONITORING RULE abort_20_min_queries
ACTION ABORT
WHEN query_duration > interval '20 minutes';
