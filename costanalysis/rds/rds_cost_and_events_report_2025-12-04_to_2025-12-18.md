# RDS Cost + Per-Instance Cost + Events Report

## Reporting Window

- **Start (UTC, pinned to 00:00):** 2025-12-04T00:00:00+00:00
- **End (UTC):** 2025-12-18T20:09:34.901209+00:00
- **Lookback:** Last **14** days (max 14 days)

## Total RDS Cost (Cost Explorer)

- **Total RDS cost:** $6,734.11

## Per-Instance Cost Summary (Cost Explorer resource attribution)

- **Attributed total (sum of instances):** $6,734.11
- **Attributed fixed:** $3,489.61
- **Attributed dynamic:** $3,244.50
- **Unattributed (Total - Attributed):** $0.00

> Note: Cost Explorer resource-level attribution may not account for every RDS line item; the “unattributed” bucket shows what didn’t map to a DB instance resource id.

### Top 50 Instances by Total Cost

| DB Instance | Engine | Fixed | Dynamic | Total | ResourceId |
|---|---|---:|---:|---:|---|
| `arn:aws:rds:us-east-1:253490756794:cluster:cluster-vtslk3oxadrszhpgibuav33huu` |  | $3,816.12 | $45.04 | $3,861.15 | `arn:aws:rds:us-east-1:253490756794:cluster:cluster-vtslk3oxadrszhpgibuav33huu` |
| `disc-fsa-prod-db-pg-instance-1-us-east-1a` | aurora-postgresql | $0.00 | $1,459.95 | $1,459.95 | `arn:aws:rds:us-east-1:253490756794:db:disc-fsa-prod-db-pg-instance-1-us-east-1a` |
| `disc-fsa-prod-db-pg-instance-1` | aurora-postgresql | $0.00 | $1,418.11 | $1,418.11 | `arn:aws:rds:us-east-1:253490756794:db:disc-fsa-prod-db-pg-instance-1` |
| `disc-fsa-prod-oracle-oas` | oracle-ee | $104.80 | $722.41 | $827.21 | `arn:aws:rds:us-east-1:253490756794:db:disc-fsa-prod-oracle-oas` |
| `NoResourceId` |  | $-431.30 | $-401.01 | $-832.31 | `NoResourceId` |

## Per-Instance Details

### arn:aws:rds:us-east-1:253490756794:cluster:cluster-vtslk3oxadrszhpgibuav33huu

- **Engine:** 
- **Fixed:** $3,816.12
- **Dynamic:** $45.04
- **Total:** $3,861.15
- **ResourceId:** `arn:aws:rds:us-east-1:253490756794:cluster:cluster-vtslk3oxadrszhpgibuav33huu`

**Top 10 usage types:**

| Bucket | UsageType | Cost |
|---|---|---:|
| FIXED | `Aurora:StorageIOUsage` | $3,370.59 |
| FIXED | `Aurora:StorageUsage` | $445.52 |
| DYNAMIC | `Aurora:BackupUsage` | $45.04 |

**Events (all) — grouped by day (last 14 days):**

- No events returned in this window.

### disc-fsa-prod-db-pg-instance-1-us-east-1a

- **Engine:** aurora-postgresql
- **Fixed:** $0.00
- **Dynamic:** $1,459.95
- **Total:** $1,459.95
- **ResourceId:** `arn:aws:rds:us-east-1:253490756794:db:disc-fsa-prod-db-pg-instance-1-us-east-1a`

**Top 10 usage types:**

| Bucket | UsageType | Cost |
|---|---|---:|
| DYNAMIC | `Aurora:ServerlessV2Usage` | $1,459.95 |
| DYNAMIC | `DataTransfer-Out-Bytes` | $0.00 |
| DYNAMIC | `DataTransfer-In-Bytes` | $0.00 |
| DYNAMIC | `USE1-DataTransfer-xAZ-In-Bytes` | $0.00 |
| DYNAMIC | `USE1-DataTransfer-xAZ-Out-Bytes` | $0.00 |

**Events (all) — grouped by day (last 14 days):**

- No events returned in this window.

### disc-fsa-prod-db-pg-instance-1

- **Engine:** aurora-postgresql
- **Fixed:** $0.00
- **Dynamic:** $1,418.11
- **Total:** $1,418.11
- **ResourceId:** `arn:aws:rds:us-east-1:253490756794:db:disc-fsa-prod-db-pg-instance-1`

**Top 10 usage types:**

| Bucket | UsageType | Cost |
|---|---|---:|
| DYNAMIC | `Aurora:ServerlessV2Usage` | $1,418.11 |
| DYNAMIC | `DataTransfer-Out-Bytes` | $0.00 |
| DYNAMIC | `DataTransfer-In-Bytes` | $0.00 |

**Events (all) — grouped by day (last 14 days):**

| Date (UTC) | Event Count | Message Preview |
|---|---:|---|
| 2025-12-05 | 1 | The free storage capacity for DB Instance: disc-fsa-prod-db-pg-instance-1 is low at 6% of the provisioned storage [Provisioned Storage: 604.16 GB, Free Storage: 37.04 GB]. You may want to increase the… |

### disc-fsa-prod-oracle-oas

- **Engine:** oracle-ee
- **Fixed:** $104.80
- **Dynamic:** $722.41
- **Total:** $827.21
- **ResourceId:** `arn:aws:rds:us-east-1:253490756794:db:disc-fsa-prod-oracle-oas`

**Top 10 usage types:**

| Bucket | UsageType | Cost |
|---|---|---:|
| DYNAMIC | `Multi-AZUsage:db.r5d.2xl` | $722.41 |
| FIXED | `RDS:Multi-AZ-GP2-Storage` | $104.80 |
| DYNAMIC | `DataTransfer-Out-Bytes` | $0.00 |
| DYNAMIC | `DataTransfer-In-Bytes` | $0.00 |

**Events (all) — grouped by day (last 14 days):**

| Date (UTC) | Event Count | Message Preview |
|---|---:|---|
| 2025-12-12 | 1 | Storage size 1000 GiB is approaching the maximum storage threshold 1250 GiB. Increase the maximum storage threshold. |
| 2025-12-11 | 14 | Storage size 1000 GiB is approaching the maximum storage threshold 1250 GiB. Increase the maximum storage threshold. ; Backing up DB instance |
| 2025-12-10 | 14 | Storage size 1000 GiB is approaching the maximum storage threshold 1250 GiB. Increase the maximum storage threshold. ; Backing up DB instance |
| 2025-12-09 | 13 | Storage size 1000 GiB is approaching the maximum storage threshold 1250 GiB. Increase the maximum storage threshold. ; Backing up DB instance |
| 2025-12-08 | 14 | Storage size 1000 GiB is approaching the maximum storage threshold 1250 GiB. Increase the maximum storage threshold. ; Backing up DB instance |
| 2025-12-07 | 14 | Storage size 1000 GiB is approaching the maximum storage threshold 1250 GiB. Increase the maximum storage threshold. ; Backing up DB instance |
| 2025-12-06 | 14 | Storage size 1000 GiB is approaching the maximum storage threshold 1250 GiB. Increase the maximum storage threshold. ; Backing up DB instance |
| 2025-12-05 | 14 | Storage size 1000 GiB is approaching the maximum storage threshold 1250 GiB. Increase the maximum storage threshold. ; Backing up DB instance |
| 2025-12-04 | 2 | Storage size 1000 GiB is approaching the maximum storage threshold 1250 GiB. Increase the maximum storage threshold. |

### NoResourceId

- **Engine:** 
- **Fixed:** $-431.30
- **Dynamic:** $-401.01
- **Total:** $-832.31
- **ResourceId:** `NoResourceId`

**Top 10 usage types:**

| Bucket | UsageType | Cost |
|---|---|---:|
| DYNAMIC | `DataTransfer-Out-Bytes` | $-0.00 |
| DYNAMIC | `Aurora:BackupUsage` | $-4.95 |
| FIXED | `RDS:Multi-AZ-GP2-Storage` | $-11.53 |
| FIXED | `Aurora:StorageUsage` | $-49.01 |
| DYNAMIC | `Multi-AZUsage:db.r5d.2xl` | $-79.46 |
| DYNAMIC | `Aurora:ServerlessV2Usage` | $-316.59 |
| FIXED | `Aurora:StorageIOUsage` | $-370.76 |

**Events (all) — grouped by day (last 14 days):**

- No events returned in this window.
