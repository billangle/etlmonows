import {v4 as uuidv4} from 'uuid'; 
import {
	DynamoDBClient,
	PutItemCommand,
} from "@aws-sdk/client-dynamodb";
import {
	marshall,
	unmarshall
} from "@aws-sdk/util-dynamodb";
import { Utils } from "/opt/nodejs/Utils.mjs";

const ddb = new DynamoDBClient();
const utils = new Utils();

export const handler = async (event) => {
  // Accept either { jobDetails, timestamp } payload or the raw logged structure
  const jobDetails = event.jobDetails || (event.logged && event.logged.jobDetails) || event;
  const timestamp = new Date().toISOString();
  const jobId = uuidv4();
  const tableName = process.env.TABLE_NAME;
  const project = process.env.PROJECT;

  console.log("PutGlueResult: event: " + JSON.stringify(event));


  if (!jobId) {
    throw new Error('Missing JobRunId in jobDetails');
  }
  const item = {
    jobId: jobId,
    jobState: "IN_PROGRESS", 
    timestamp: timestamp,
    project: project,
    fullResponse: jobDetails,
  };
  
    const putItem = new PutItemCommand({
                TableName: tableName,
                Item: marshall(item)
            });
            try {
                await ddb.send(putItem);
            } catch (e) {
                console.error ("ERROR: ImageProcess: saveToDynamo  : e: " + e);
            }
  
  return { ok: true, jobId };
};
