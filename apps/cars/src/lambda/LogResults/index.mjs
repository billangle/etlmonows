
import { Utils } from "/opt/nodejs/Utils.mjs";


const utils = new Utils();

export const handler = async (event) => {
  // Accept either { jobDetails, timestamp } payload or the raw logged structure
  //const jobDetails = event.logged.jobDetails;
  //const jobId = event.jobId;

  const jobDetails = event.logged.jobDetails;
  const jobId = event.step1Result.Output.jobId;
   //const jobId = '';
  const tableName = process.env.TABLE_NAME;
  const project = process.env.PROJECT;

  console.log("PLogResults: event: " + JSON.stringify(event) + " jobId: " + jobId + " tableName: " + tableName + " project: " + project);

   await utils.updatePipelineStatus(jobId, tableName, jobDetails, project,  event.glueResult.JobRunState);
  
  return event;
};
