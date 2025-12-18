# RDS Cost Report by DB Instance (with Last Reboot)

## Reporting Window

- **Start (UTC):** 2025-12-04T00:00:00+00:00
- **End (UTC):** 2025-12-18T14:00:01.940934+00:00
- **Lookback:** Last 14 days

## Per-Instance Summary

| DB Instance | Engine | Fixed | Dynamic | Total | Last Reboot (UTC) | Days Since | Source |
|---|---|---:|---:|---:|---|---:|---|
| `arn:aws:rds:us-east-1:253490756794:cluster:cluster-vtslk3oxadrszhpgibuav33huu` |  | $3,816.12 | $45.04 | $3,861.15 | N/A | N/A |  |
| `disc-fsa-prod-db-pg-instance-1-us-east-1a` | aurora-postgresql | $0.00 | $1,459.95 | $1,459.95 | N/A | N/A |  |
| `disc-fsa-prod-db-pg-instance-1` | aurora-postgresql | $0.00 | $1,418.11 | $1,418.11 | N/A | N/A |  |
| `disc-fsa-prod-oracle-oas` | oracle-ee | $104.80 | $722.41 | $827.21 | N/A | N/A |  |
| `NoResourceId` |  | $-431.30 | $-401.01 | $-832.31 | N/A | N/A |  |

## Instance Details

### arn:aws:rds:us-east-1:253490756794:cluster:cluster-vtslk3oxadrszhpgibuav33huu

- **Engine:** 
- **Fixed cost:** $3,816.12
- **Dynamic cost:** $45.04
- **Total cost:** $3,861.15
- **ResourceId:** `arn:aws:rds:us-east-1:253490756794:cluster:cluster-vtslk3oxadrszhpgibuav33huu`
- **Last reboot:** None

**Top usage types:**

| Bucket | UsageType | Cost |
|---|---|---:|
| FIXED | `Aurora:StorageIOUsage` | $3,370.59 |
| FIXED | `Aurora:StorageUsage` | $445.52 |
| DYNAMIC | `Aurora:BackupUsage` | $45.04 |

### disc-fsa-prod-db-pg-instance-1-us-east-1a

- **Engine:** aurora-postgresql
- **Fixed cost:** $0.00
- **Dynamic cost:** $1,459.95
- **Total cost:** $1,459.95
- **ResourceId:** `arn:aws:rds:us-east-1:253490756794:db:disc-fsa-prod-db-pg-instance-1-us-east-1a`
- **Last reboot:** N/A (no reboot/restart/failover events returned; RDS Events retain max 14 days)

**Top usage types:**

| Bucket | UsageType | Cost |
|---|---|---:|
| DYNAMIC | `Aurora:ServerlessV2Usage` | $1,459.95 |
| DYNAMIC | `DataTransfer-Out-Bytes` | $0.00 |
| DYNAMIC | `DataTransfer-In-Bytes` | $0.00 |
| DYNAMIC | `USE1-DataTransfer-xAZ-In-Bytes` | $0.00 |
| DYNAMIC | `USE1-DataTransfer-xAZ-Out-Bytes` | $0.00 |

### disc-fsa-prod-db-pg-instance-1

- **Engine:** aurora-postgresql
- **Fixed cost:** $0.00
- **Dynamic cost:** $1,418.11
- **Total cost:** $1,418.11
- **ResourceId:** `arn:aws:rds:us-east-1:253490756794:db:disc-fsa-prod-db-pg-instance-1`
- **Last reboot:** N/A (no reboot/restart/failover events returned; RDS Events retain max 14 days)

**Top usage types:**

| Bucket | UsageType | Cost |
|---|---|---:|
| DYNAMIC | `Aurora:ServerlessV2Usage` | $1,418.11 |
| DYNAMIC | `DataTransfer-Out-Bytes` | $0.00 |
| DYNAMIC | `DataTransfer-In-Bytes` | $0.00 |

### disc-fsa-prod-oracle-oas

- **Engine:** oracle-ee
- **Fixed cost:** $104.80
- **Dynamic cost:** $722.41
- **Total cost:** $827.21
- **ResourceId:** `arn:aws:rds:us-east-1:253490756794:db:disc-fsa-prod-oracle-oas`
- **Last reboot:** N/A (no reboot/restart/failover events returned; RDS Events retain max 14 days)

**Top usage types:**

| Bucket | UsageType | Cost |
|---|---|---:|
| DYNAMIC | `Multi-AZUsage:db.r5d.2xl` | $722.41 |
| FIXED | `RDS:Multi-AZ-GP2-Storage` | $104.80 |
| DYNAMIC | `DataTransfer-Out-Bytes` | $0.00 |
| DYNAMIC | `DataTransfer-In-Bytes` | $0.00 |

### NoResourceId

- **Engine:** 
- **Fixed cost:** $-431.30
- **Dynamic cost:** $-401.01
- **Total cost:** $-832.31
- **ResourceId:** `NoResourceId`
- **Last reboot:** None

**Top usage types:**

| Bucket | UsageType | Cost |
|---|---|---:|
| DYNAMIC | `DataTransfer-Out-Bytes` | $-0.00 |
| DYNAMIC | `Aurora:BackupUsage` | $-4.95 |
| FIXED | `RDS:Multi-AZ-GP2-Storage` | $-11.53 |
| FIXED | `Aurora:StorageUsage` | $-49.01 |
| DYNAMIC | `Multi-AZUsage:db.r5d.2xl` | $-79.46 |
| DYNAMIC | `Aurora:ServerlessV2Usage` | $-316.59 |
| FIXED | `Aurora:StorageIOUsage` | $-370.76 |
