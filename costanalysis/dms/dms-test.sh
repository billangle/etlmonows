#! /bin/bash

aws dms describe-events \
  --source-type replication-task \
  --start-time "$(date -u -v-10d '+%Y-%m-%dT%H:%M:%SZ')" \
  --end-time   "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" \
  --max-records 100 \
  --region us-east-1
