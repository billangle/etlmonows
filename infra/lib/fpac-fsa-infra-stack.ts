
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

export class FpacFsaInfraStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: EtlStackProps) {
    super(scope, id, props);

    // Buckets for raw input and processed output data

    const landingBucketConstruct = new S3(this, `${props.deployEnv}-${props.configData.landingBucketName}-` , {
      env: props.deployEnv,
      base_name: props.configData.landingBucketName,
    }); 
    const landingBucket = landingBucketConstruct.DataBucket;

    const cleanBucketConstruct = new S3(this, `${props.deployEnv}-${props.configData.cleanBucketName}` , {
      env: props.deployEnv,
      base_name: props.configData.cleanBucketName,
    });
    const cleanBucket = cleanBucketConstruct.DataBucket;

    const finalBucketConstruct = new S3(this, `${props.deployEnv}-${props.configData.finalBucketName}` , {
      env: props.deployEnv,
      base_name: props.configData.finalBucketName,
    });
    const finalBucket = finalBucketConstruct.DataBucket;

    // ==== Lambda Layers =====

    const thirdPartyLayer = new lambda.LayerVersion(this, 'fpac-cdk-thirdparty-layer', {
      compatibleRuntimes: [
        lambda.Runtime.NODEJS_22_X,
        lambda.Runtime.NODEJS_LATEST,
      ],
      code: new AssetCode(`../shared/layer/fpacfsa/thirdparty`),
      layerVersionName: "fpac-cdk-thirdparty-layer-ssm",
      description: 'FPAC Thirdparty CDK Lambda Layer',
    });

  

  // DynamoDB Table for tracking ETL job metadata and status

    const etlJobsTable = new FpacDynamoDb(this, `FpacFsaEtlJobsTable-${props.deployEnv}`, {
      tablename: props.configData.dynamoTableName,
      key: 'jobId',
    });

// IAM Role for Glue Jobs

    const glueJobRole = new iam.Role(this, `FpacFsaStackGlueJobRole-${props.deployEnv}`, {
      assumedBy: new iam.ServicePrincipal('glue.amazonaws.com'),
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSGlueServiceRole'),
      ],
        });

        // Add S3 and SSM permissions
      glueJobRole.addToPolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: [
        's3:GetObject',
        's3:ListBucket',
        'ssm:GetParameter',
      ],
      resources: ['*']
        }));


     const glueRoleARNStr = `arn:aws:iam::${cdk.Stack.of(this).account}:role/${props.configData.glueRoleName}`;
     const glueJobRole2 = iam.Role.fromRoleArn(this, 'GlueJobRoleFromARN', glueRoleARNStr, { mutable: false });




    // Allow Glue job to read the script and buckets
    landingBucket.grantReadWrite(glueJobRole);
    cleanBucket.grantReadWrite(glueJobRole);
    finalBucket.grantReadWrite(glueJobRole);

    
    const fpacFsaLambdaExecutionRole = new iam.Role(this, `FpacFsaLambdaExecutionRole-${props.deployEnv}`, {
      assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaBasicExecutionRole'),
      ],
    });

    fpacFsaLambdaExecutionRole.addToPolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: [
        's3:GetObject',
        's3:ListBucket',
        'lambda:InvokeFunction',
        'ssm:GetParameter',
        'ssm:PutParameter'
      ],
      resources: ['*']
    }));


    const lambdaRoleARNStr = `arn:aws:iam::${cdk.Stack.of(this).account}:role/${props.configData.lambdaRoleName}`;
    const fpacFsaLambdaExecutionRole2 = iam.Role.fromRoleArn(this, 'FpacFsaLambdaExecutionRoleFromARN', lambdaRoleARNStr, { mutable: false });
    

    // ===== Glue Data Catalog (Database) – L1 =====
   
    const databaseName = props.configData.databaseName;
    const glueDb = new glue_l1.CfnDatabase(this, databaseName, {
      catalogId: cdk.Stack.of(this).account,
      databaseInput: { name: databaseName },
    });


    // Store important resource ARNs/names in SSM Parameters for retrieval by ETL jobs
    const glueRoleARN = glueJobRole.roleArn;
    const ssmEtlGlueJobRole = new StringParameter (this, `fpacFsaGlueJobRoleSSM-${props.deployEnv}`, {
      parameterName: 'fpacFsaGlueJobRoleSSMArn',
      stringValue: glueRoleARN
   });

     const glueRoleARN2 = glueJobRole2.roleArn;
    const ssmEtlGlueJobRole2 = new StringParameter (this, `fpacFsaGlueJobRoleSSM-${props.deployEnv}2`, {
      parameterName: 'fpacFsaGlueJobRoleSSMArn2',
      stringValue: glueRoleARN2
   });


   const landingBucketName = landingBucket.bucketName
    const ssmInputBucketARN = new StringParameter (this, `fpacFsaInputBucketSSM-${props.deployEnv}`, {
      parameterName: 'fpacFsaLandingBucketSSMName',
      stringValue: landingBucketName
   });

   const cleanBucketName = cleanBucket.bucketName;
    const ssmOutputBucketName = new StringParameter (this, `fpacFsaOutputBucketSSM-${props.deployEnv}`, {
      parameterName: 'fpacFsaCleanBucketSSMName',
      stringValue: cleanBucketName
   });

    const finalBucketName = finalBucket.bucketName;
    const ssmFinalBucketName = new StringParameter (this, `fpacFsaFinalBucketSSM-${props.deployEnv}`, {
      parameterName: 'fpacFsaFinalBucketSSMName',
      stringValue: finalBucketName
    });

    const databaseARN = `arn:aws:glue:${props.configData.region}:${cdk.Stack.of(this).account}:database/${databaseName}`;
    const ssmDatabaseARN = new StringParameter (this, 'fpacFsaDatabaseARNSSM', {
      parameterName: 'fpacFsaDatabaseARNSSM',
      stringValue: databaseARN
   });

  const fpacFsaLambdaExecutionRoleARN = fpacFsaLambdaExecutionRole.roleArn;
  const ssmEtlRoleARN = new StringParameter(this, `fpacFsaLambdaExecuteRoleARN-${props.deployEnv}`, {
    parameterName: 'fpacFsaLambdaExecuteRoleARN',
    stringValue: fpacFsaLambdaExecutionRoleARN
  });

   const fpacFsaLambdaExecutionRoleARN2 = fpacFsaLambdaExecutionRole.roleArn;
  const ssmEtlRoleARN2 = new StringParameter(this, `fpacFsaLambdaExecuteRoleARN-${props.deployEnv}2`, {
    parameterName: 'fpacFsaLambdaExecuteRoleARN2',
    stringValue: fpacFsaLambdaExecutionRoleARN2
  });


  const fpacfsaThirdPartyLayerArn = thirdPartyLayer.layerVersionArn;
  const ssmThirdPartyLayerArn = new StringParameter(this, `fpacfsaThirdPartyLayerArn-${props.deployEnv}`, {
    parameterName: 'fpacfsaThirdPartyLayerArn',
    stringValue: fpacfsaThirdPartyLayerArn
  });
 
    // Outputs



    new cdk.CfnOutput(this, 'LandingBucketName', { value: landingBucket.bucketName });
    new cdk.CfnOutput(this, 'CleanBucketName', { value: cleanBucket.bucketName });
    new cdk.CfnOutput(this, 'FinalBucketName', { value: finalBucket.bucketName });

  }
}
