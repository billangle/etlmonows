# RDS Cost Report by DB Instance (Fixed vs Dynamic)

## Reporting Window

- **Start (UTC, pinned to 00:00):** 2025-12-04T00:00:00+00:00
- **End (UTC):** 2025-12-18T13:31:57.810294+00:00
- **Lookback:** Last **14** days

## Totals (All DB Instances)

- **Fixed:** $0.00
- **Dynamic:** $6,734.11
- **Total:** $6,734.11

## Per-Instance Summary (Top 50 by total cost)

| DB Instance | Fixed | Dynamic | Total | ResourceId |
|---|---:|---:|---:|---|
| `arn:aws:rds:us-east-1:253490756794:cluster:cluster-vtslk3oxadrszhpgibuav33huu` | $0.00 | $3,861.15 | $3,861.15 | `arn:aws:rds:us-east-1:253490756794:cluster:cluster-vtslk3oxadrszhpgibuav33huu` |
| `disc-fsa-prod-db-pg-instance-1-us-east-1a (aurora-postgresql)` | $0.00 | $1,459.95 | $1,459.95 | `arn:aws:rds:us-east-1:253490756794:db:disc-fsa-prod-db-pg-instance-1-us-east-1a` |
| `disc-fsa-prod-db-pg-instance-1 (aurora-postgresql)` | $0.00 | $1,418.11 | $1,418.11 | `arn:aws:rds:us-east-1:253490756794:db:disc-fsa-prod-db-pg-instance-1` |
| `disc-fsa-prod-oracle-oas (oracle-ee)` | $0.00 | $827.21 | $827.21 | `arn:aws:rds:us-east-1:253490756794:db:disc-fsa-prod-oracle-oas` |
| `NoResourceId` | $0.00 | $-832.31 | $-832.31 | `NoResourceId` |

## Top Non-Zero Instances (Detail: top usage-types per instance)

### arn:aws:rds:us-east-1:253490756794:cluster:cluster-vtslk3oxadrszhpgibuav33huu

- **Fixed:** $0.00
- **Dynamic:** $3,861.15
- **Total:** $3,861.15
- **ResourceId:** `arn:aws:rds:us-east-1:253490756794:cluster:cluster-vtslk3oxadrszhpgibuav33huu`

**Top 10 usage-types:**

| Bucket | UsageType | Cost |
|---|---|---:|
| DYNAMIC | `Aurora:StorageIOUsage` | $3,370.59 |
| DYNAMIC | `Aurora:StorageUsage` | $445.52 |
| DYNAMIC | `Aurora:BackupUsage` | $45.04 |

### disc-fsa-prod-db-pg-instance-1-us-east-1a (aurora-postgresql)

- **Fixed:** $0.00
- **Dynamic:** $1,459.95
- **Total:** $1,459.95
- **ResourceId:** `arn:aws:rds:us-east-1:253490756794:db:disc-fsa-prod-db-pg-instance-1-us-east-1a`

**Top 10 usage-types:**

| Bucket | UsageType | Cost |
|---|---|---:|
| DYNAMIC | `Aurora:ServerlessV2Usage` | $1,459.95 |
| DYNAMIC | `DataTransfer-Out-Bytes` | $0.00 |
| DYNAMIC | `DataTransfer-In-Bytes` | $0.00 |
| DYNAMIC | `USE1-DataTransfer-xAZ-In-Bytes` | $0.00 |
| DYNAMIC | `USE1-DataTransfer-xAZ-Out-Bytes` | $0.00 |

### disc-fsa-prod-db-pg-instance-1 (aurora-postgresql)

- **Fixed:** $0.00
- **Dynamic:** $1,418.11
- **Total:** $1,418.11
- **ResourceId:** `arn:aws:rds:us-east-1:253490756794:db:disc-fsa-prod-db-pg-instance-1`

**Top 10 usage-types:**

| Bucket | UsageType | Cost |
|---|---|---:|
| DYNAMIC | `Aurora:ServerlessV2Usage` | $1,418.11 |
| DYNAMIC | `DataTransfer-Out-Bytes` | $0.00 |
| DYNAMIC | `DataTransfer-In-Bytes` | $0.00 |

### disc-fsa-prod-oracle-oas (oracle-ee)

- **Fixed:** $0.00
- **Dynamic:** $827.21
- **Total:** $827.21
- **ResourceId:** `arn:aws:rds:us-east-1:253490756794:db:disc-fsa-prod-oracle-oas`

**Top 10 usage-types:**

| Bucket | UsageType | Cost |
|---|---|---:|
| DYNAMIC | `Multi-AZUsage:db.r5d.2xl` | $722.41 |
| DYNAMIC | `RDS:Multi-AZ-GP2-Storage` | $104.80 |
| DYNAMIC | `DataTransfer-Out-Bytes` | $0.00 |
| DYNAMIC | `DataTransfer-In-Bytes` | $0.00 |

## Notes

- This report uses **Cost Explorer resource-level attribution** (`GetCostAndUsageWithResources`) grouped by `RESOURCE_ID`. :contentReference[oaicite:7]{index=7}
- Cost Explorer supports filtering/grouping by **Resources** (resource IDs). :contentReference[oaicite:8]{index=8}
- If you need perfect month-long per-instance accuracy in all cases, use **CUR** and query `lineItem/ResourceId` (Athena). :contentReference[oaicite:9]{index=9}