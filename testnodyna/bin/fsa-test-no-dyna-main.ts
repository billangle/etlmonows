#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import * as fs from 'fs';
import {FpacFsaTestNoDynaStack } from '../lib/fpac-fsa-test-no-dyna-stack';

const app = new cdk.App();

let environment=process.env.DEPLOY_ENV || '';
const envdata = fs.readFileSync("../config/" + environment+ '/cdk-spec.json', 'utf8');
const configData = JSON.parse(envdata);

new FpacFsaTestNoDynaStack(app, `FpacFsaTestNoDynaStack-${environment}`, {
  env: {
    account: process.env.CDK_ACCOUNT,
    region: configData.region,
  
  },
    configData: configData,
    deployEnv: environment,
});
