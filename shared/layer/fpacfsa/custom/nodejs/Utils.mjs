
import { DynamoDBClient } from "@aws-sdk/client-dynamodb";
import { Agent as httpsAgent } from 'https';
import {
  ExecuteStatementCommand,
  DynamoDBDocumentClient,
  UpdateCommand
} from "@aws-sdk/lib-dynamodb";
import  { getSignedUrl } from "@aws-sdk/s3-request-presigner";
import { GetObjectCommand, PutObjectCommand, S3Client } from "@aws-sdk/client-s3";



const client = new DynamoDBClient({
    httpOptions: {
        connectTimeout: 4000,
        agent: new httpsAgent({ keepAlive: true }),
    }
});
const docClient = DynamoDBDocumentClient.from(client);
const s3Client = new S3Client({  httpOptions: {
    connectTimeout: 4000,
    agent: new httpsAgent({ keepAlive: true }),
}});


export class Utils {


 

   getBucketRealName (baseBucketOutput,env) {
    let bucket = baseBucketOutput;
    if (env !== "none") {
        bucket =`${baseBucketOutput}-${env}`;
    }

    return bucket;

  }




    async getBucketData (bucket, key) {

        const s3ClientRead = new S3Client({});

        let bucketData=null;
  
           const command = new GetObjectCommand({
                 Bucket: bucket,
                 Key: key,
           });
     
           try {
     
               let proInfoDataIn = await s3ClientRead.send(command);
               let outData =  await proInfoDataIn.Body.transformToString();
                bucketData = JSON.parse(outData);
             
     
      
           } catch (e) {
               console.error ("GETBUCKETDATA Error : " + key + " : " + bucket + " : "  +e);
           }
           finally {
            s3ClientRead.destroy();
           }
     
        
         return bucketData;
     

    }

    async getS3SignedUrl (bucket, key) {

        const s3ClientRead = new S3Client({});

        let signurl="";
  
           const command = new GetObjectCommand({
                 Bucket: bucket,
                 Key: key,
           });
     
           try {
     
             signurl = await getSignedUrl (s3ClientRead, command, {expiresIn: 120});
            
      
           } catch (e) {
               console.error ("Signed URL Error : " + key + " : " + bucket + " : "  +e);
           }
           finally {
            s3ClientRead.destroy();
           }
     
        
         return signurl;
     

    }

   


    async saveToS3 (bucketName, fileName, fileData) {

        const s3ClientWrite = new S3Client({});

       console.log ("SAVE TO S3: " + bucketName + " : " + fileName + " data: " + fileData + " : " + this.retryS3 );
        const command = new PutObjectCommand({
            Bucket: bucketName,
            Key: fileName,
            Body: fileData,
        });
        
        try {
            const response = await s3ClientWrite.send(command);
            console.log("SAVE TO S3: saved " + bucketName + " : " + fileName);
        } catch (err) {
            console.error("ERROR SAVING TO S3 - saved " + bucketName + " : " + fileName + " : " + err);     
        }
        finally {
            s3ClientWrite.destroy();
        }
    }



    async updatePipelineStatus (jobId, tablename, response, project, jobstate) {
        let commandR;
        try {
        
            commandR = new UpdateCommand({
                TableName: tablename,
                Key: {
                  jobId: jobId,
                  project: project
                },
                UpdateExpression: "set jobState = :jobstate, fullResponse = :response",
                ExpressionAttributeValues: {
                  ":response": response,
                  ":jobstate": jobstate
                },
                ReturnValues: "ALL_NEW",
              });
            
             let res = await docClient.send(commandR);
        } catch (e) {
            console.error("Error updating row: " + jobId + " : " + JSON.stringify(commandR) + " e: " + e);
        }
        

    }

    async updateManyReportRow (uuid, ReportType, reportList, status, subject) {
        let commandR;
        try {
        
            commandR = new UpdateCommand({
                TableName: "APIReportEvents",
                Key: {
                  UUID: uuid,
                  ReportType: ReportType
                },
                UpdateExpression: "set OutputFileList = :files, MyStatus = :status, EmailSubject = :subject",
                ExpressionAttributeValues: {
                  ":files": reportList,
                  ":status": status,
                  ":subject": subject,
                },
                ReturnValues: "ALL_NEW",
              });
            
             let res = await docClient.send(commandR);
        } catch (e) {
            console.error("Error updating row: " + uuid + " : " + JSON.stringify(commandR) + " e: " + e);
        }
        

    }


    

    async getTopicData (topicId) {
        let dataR = {
            Items: []
        };

        try {
            let commandR = new ExecuteStatementCommand({
                Statement: `select * from Topics where TopicId=?`,
                Parameters: [topicId],
                ConsistentRead: true,
            });
            
            dataR = await docClient.send(commandR);
        } catch (e) {
            console.error ("Error getting Topics: " + topicId + " :e " +e);
        }

        if (dataR.Items.length !==0 ) {
          return dataR.Items[0];
         }
         else {
            return null;
         }

    }
   

}