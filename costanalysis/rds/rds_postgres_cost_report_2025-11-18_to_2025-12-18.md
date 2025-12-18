# RDS PostgreSQL Fixed vs Dynamic Cost Report

## Reporting Window

- **Start (UTC, pinned to 00:00):** 2025-11-18T00:00:00+00:00
- **End (UTC):** 2025-12-18T13:17:44.305276+00:00
- **Lookback:** Last **30** days

## Scope

- **Service filter:** Amazon Relational Database Service (RDS)

- **Engine filter:** None (includes all RDS engines present in billing data)

## Fixed vs Dynamic Cost Summary

- **Fixed cost (baseline capacity):** $0.00
- **Dynamic cost (activity/retention/add-ons):** $13,101.99
- **Total RDS cost (in scope):** $13,101.99

### Percent Split

- **Fixed:** 0.0%
- **Dynamic:** 100.0%

## Line Items (Top 50 by spend)

| UsageType | Bucket | Cost |
|---|---:|---:|
| `Aurora:StorageIOUsage` | DYNAMIC | $5,561.42 |
| `Aurora:ServerlessV2Usage` | DYNAMIC | $5,065.96 |
| `Multi-AZUsage:db.r5d.2xl` | DYNAMIC | $1,371.23 |
| `Aurora:StorageUsage` | DYNAMIC | $844.98 |
| `RDS:Multi-AZ-GP2-Storage` | DYNAMIC | $201.78 |
| `Aurora:BackupUsage` | DYNAMIC | $56.61 |
| `DataTransfer-Out-Bytes` | DYNAMIC | $0.00 |
| `DataTransfer-In-Bytes` | DYNAMIC | $0.00 |
| `USE1-DataTransfer-xAZ-In-Bytes` | DYNAMIC | $0.00 |
| `USE1-DataTransfer-xAZ-Out-Bytes` | DYNAMIC | $0.00 |

## Notes on Classification

- This report uses **Cost Explorer actual billed cost** (UnblendedCost) grouped by **USAGE_TYPE**. :contentReference[oaicite:7]{index=7}
- RDS charges include instance compute, storage, and backup storage (among others). :contentReference[oaicite:8]{index=8}
- Backup storage often appears as `RDS:ChargedBackupUsage` and is visible when grouping by usage type. :contentReference[oaicite:9]{index=9}
- If you want perfect accuracy by engine and resource, the next step is CUR (Cost & Usage Report) + resource tags.
