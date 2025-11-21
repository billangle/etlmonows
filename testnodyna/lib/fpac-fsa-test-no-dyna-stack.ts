
import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
//import * as s3 from 'aws-cdk-lib/aws-s3';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as glue_l1 from 'aws-cdk-lib/aws-glue'; // L1s for database/crawler/workflow/trigger
import { StringParameter } from 'aws-cdk-lib/aws-ssm';
import { S3 } from './constructs/DataEtlS3';
import * as s3deploy from 'aws-cdk-lib/aws-s3-deployment';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import { AssetCode } from "aws-cdk-lib/aws-lambda"
import { FpacDynamoDb } from './constructs/FpacDynamoDb';

interface ConfigurationData {
  landingBucketName: string;
  cleanBucketName: string;
  finalBucketName: string;
  databaseName: string;
  region: string;
  dynamoTableName: string;
  glueRoleName: string;
  lambdaRoleName: string;
};

interface EtlStackProps extends cdk.StackProps {
  configData: ConfigurationData;
  deployEnv: string;
}

export class FpacFsaTestNoDynaStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: EtlStackProps) {
    super(scope, id, props);


  // DynamoDB Table for tracking ETL job metadata and status

    const etlJobsTable = new FpacDynamoDb(this, `FpacFsaNoDynaTable-${props.deployEnv}`, {
      tablename: `NoDyna${props.configData.dynamoTableName}`,
      key: 'jobId',
    });



  }
}
