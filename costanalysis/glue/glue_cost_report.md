# AWS Glue Cost Report — Last 30 Days

This report summarizes DPU usage and estimated cost for **all Glue jobs** in the last **30 days**.

## Summary

- **Runs analyzed:** 72,034
- **Successful DPU hours:** 15,144.039
- **Failed DPU hours:** 3,833.646
- **Total DPU hours:** 18,977.685

## Estimated Cost (at $0.44 per DPU-hour)

- **Success cost:** $6,663.38
- **Failed cost:** $1,686.80
- **Total cost:** $8,350.18

## Top 20 Failed Runs by DPU Hours (Last 30 Days)

### #1

- **Job name:** `FSA-PROD-FR-to-STG-INSERTS`
- **Run ID:** `jr_987e02aeb92f4d9623a50c5a1d9c510d53b36b386ddbafbdd42b446affa64625`
- **DPU hours:** 131.456
- **Script:** `s3://c108-prod-fpacfsa-landing-scripts/farm_records/scripts/glue/FSA-PROD-FR-to-STG-INSERTS.py`

### #2

- **Job name:** `FSA-PROD-FLPIDS-CREATE-CSV`
- **Run ID:** `jr_f1bd4112fa4b01497d217a0c5de0ee9724ec036c83e707c20d621418f62d9009`
- **DPU hours:** 113.044
- **Script:** `s3://c108-prod-fpacfsa-landing-scripts/scripts/glue/FSA-PROD-FLPIDS-CREATE-CSV.py`

### #3

- **Job name:** `FSA-PROD-FLPIDS-CREATE-CSV`
- **Run ID:** `jr_546c9ea1b80f34d71db6ec50337a9a9b6c127375634063a6cbddd995c3b8ed5e`
- **DPU hours:** 99.333
- **Script:** `s3://c108-prod-fpacfsa-landing-scripts/scripts/glue/FSA-PROD-FLPIDS-CREATE-CSV.py`

### #4

- **Job name:** `FSA-PROD-FarmRecords-EDV-s3Parquet-INCR`
- **Run ID:** `jr_c8c67884bbf3ffd23271b5cde6683f03f9e77bda56430c28cdd5f746436b8343`
- **DPU hours:** 85.765
- **Script:** `s3://c108-prod-fpacfsa-landing-scripts/farm_records/scripts/glue/FSA-PROD-FarmRecords-EDV-s3Parquet-INCR.py`

### #5

- **Job name:** `FSA-PROD-FLPIDS-CREATE-CSV`
- **Run ID:** `jr_fe3f242874a47b69a42f3f3a347b2878728326f0c50a709356414bd7feac59f8`
- **DPU hours:** 56.706
- **Script:** `s3://c108-prod-fpacfsa-landing-scripts/scripts/glue/FSA-PROD-FLPIDS-CREATE-CSV.py`

### #6

- **Job name:** `FSA-PROD-FarmRecords-STG-EDV`
- **Run ID:** `jr_f6995d7fa64e12e489fb88791c9199df8253d7ad02004bd8e384c3c6a6ef4ac7`
- **DPU hours:** 48.986
- **Script:** `s3://c108-prod-fpacfsa-landing-scripts/farm_records/scripts/glue/FSA-PROD-FarmRecords-STG-EDV.py`

### #7

- **Job name:** `FSA-PROD-BP-SAPFETCH`
- **Run ID:** `jr_dc783424ec1aa8848fb4cb32c9305b0f7c2a9cc5ae8730657768255b3c6b943e`
- **DPU hours:** 41.833
- **Script:** `s3://c108-prod-fpacfsa-landing-scripts/scripts/glue/FSA-PROD-BP-SAPFETCH.py`

### #8

- **Job name:** `FSA-PROD-FLPIDS-CREATE-CSV`
- **Run ID:** `jr_95d0f7e798bb066ee5420b7b1a81b7f6c8240ced55ec1ddb68f4408337ef471c`
- **DPU hours:** 27.817
- **Script:** `s3://c108-prod-fpacfsa-landing-scripts/scripts/glue/FSA-PROD-FLPIDS-CREATE-CSV.py`

### #9

- **Job name:** `FSA-PROD-FWADM-fund_management_obligation_fact_incremental`
- **Run ID:** `jr_592789aa9dc67da4f0b79e030f564205739d3fe4aab657b2a9d28b6d3dbc9eed`
- **DPU hours:** 23.978
- **Script:** `s3://c108-prod-fpacfsa-landing-scripts/dmart/FSA-PROD-FWADM-fund_management_obligation_fact_incremental.py`

### #10

- **Job name:** `FSA-PROD-FarmRecords-STG-EDV`
- **Run ID:** `jr_4c2e6d8eb2a3bd61fbfbcdbdae3a0030b825b9f0f15983feaedeea217fd1f8ba`
- **DPU hours:** 22.624
- **Script:** `s3://c108-prod-fpacfsa-landing-scripts/farm_records/scripts/glue/FSA-PROD-FarmRecords-STG-EDV.py`

### #11

- **Job name:** `FSA-PROD-FarmRecords-Athena-to-PG-FRR`
- **Run ID:** `jr_978b381553d9c048bf2af7d76470faecf76eefd590e90732e3955527ed2248db`
- **DPU hours:** 16.991
- **Script:** `s3://c108-prod-fpacfsa-landing-zone/farm_records/scripts/glue/FSA-PROD-FarmRecords-Athena-to-PG-FRR.py`

### #12

- **Job name:** `FSA-PROD-FarmRecords-ctf-sum-stg-NE2026`
- **Run ID:** `jr_7c2a16bfff41d73c05c585bd5201b9c11723a1ab4ae7a015f7b7158104421663`
- **DPU hours:** 15.403
- **Script:** `s3://c108-prod-fpacfsa-landing-zone/farm_records/scripts/glue/FSA-PROD-FarmRecords-ctf-sum-stg-NE2026.py`

### #13

- **Job name:** `FSA-PROD-FLPIDS-CREATE-CSV`
- **Run ID:** `jr_da8c74d1d5f5af3579e47465d6c45f6a4f78d0d2b4f02eba9a16ea432a7ea82c`
- **DPU hours:** 15.267
- **Script:** `s3://c108-prod-fpacfsa-landing-scripts/scripts/glue/FSA-PROD-FLPIDS-CREATE-CSV.py`

### #14

- **Job name:** `FSA-PROD-FarmRecords-ctf-sum-stg-NE2026`
- **Run ID:** `jr_4c57d05d791038f045b1a608873dc76b9c031ff4c0260c044767df1104455cca`
- **DPU hours:** 15.258
- **Script:** `s3://c108-prod-fpacfsa-landing-zone/farm_records/scripts/glue/FSA-PROD-FarmRecords-ctf-sum-stg-NE2026.py`

### #15

- **Job name:** `FSA-PROD-FarmRecords-ctf-sum-stg-NE2026`
- **Run ID:** `jr_5b8a43f0ffe988c0df6135bc76033753e5d64c6acb322e32a5b8cfed3a0220ad`
- **DPU hours:** 14.961
- **Script:** `s3://c108-prod-fpacfsa-landing-zone/farm_records/scripts/glue/FSA-PROD-FarmRecords-ctf-sum-stg-NE2026.py`

### #16

- **Job name:** `FSA-PROD-FarmRecords-ctf-sum-stg`
- **Run ID:** `jr_0ec2380032ce831fa724594787d922c2299547b158da205970bba693ec412157`
- **DPU hours:** 14.883
- **Script:** `s3://c108-prod-fpacfsa-landing-zone/farm_records/scripts/glue/FSA-PROD-FarmRecords-ctf-sum-stg.py`

### #17

- **Job name:** `FSA-PROD-FarmRecords-ctf-sum-stg`
- **Run ID:** `jr_955a99e6c669fd92766b9dd1ddb245a7d95bcea5f921b1e3225805656a0d514e`
- **DPU hours:** 14.686
- **Script:** `s3://c108-prod-fpacfsa-landing-zone/farm_records/scripts/glue/FSA-PROD-FarmRecords-ctf-sum-stg.py`

### #18

- **Job name:** `FSA-PROD-FR-to-STG-INSERTS`
- **Run ID:** `jr_97535c2c719b6350a3836f9d82ea10a2b16233e01b1e65a1ed4529389ff85be4`
- **DPU hours:** 14.656
- **Script:** `s3://c108-prod-fpacfsa-landing-scripts/farm_records/scripts/glue/FSA-PROD-FR-to-STG-INSERTS.py`

### #19

- **Job name:** `FSA-PROD-FLPIDS-CREATE-CSV`
- **Run ID:** `jr_859f10f7bd6b0f41ee0b47e4453b8c5bdff163b3441466445b9bdfd317614684`
- **DPU hours:** 13.167
- **Script:** `s3://c108-prod-fpacfsa-landing-scripts/scripts/glue/FSA-PROD-FLPIDS-CREATE-CSV.py`

### #20

- **Job name:** `FSA-PROD-FarmRecords-ctf-sum-stg`
- **Run ID:** `jr_1c1d631038f0e24a12a1e5f2a42de5299c8f41a9679ae50b7f1b42d1feecfd93`
- **DPU hours:** 13.072
- **Script:** `s3://c108-prod-fpacfsa-landing-zone/farm_records/scripts/glue/FSA-PROD-FarmRecords-ctf-sum-stg.py`
