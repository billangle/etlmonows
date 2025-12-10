
import { StackProps } from "aws-cdk-lib"
import { Construct } from "constructs"
import * as tasks from 'aws-cdk-lib/aws-stepfunctions-tasks';
import * as glue_l1 from 'aws-cdk-lib/aws-glue';
import * as cdk from 'aws-cdk-lib';

interface LambdaApiStackProps extends StackProps {
  crawlerName: string,
  roleArn: string,
  databaseName: string,
  projectName: string,
  stepTrigger: glue_l1.CfnTrigger,
  deployEnv: string,
  finalBucketName: string,
  workflowName: string,
}


/** NOTE - this doesn't work - for some reason the crawler can't be put in a construct  */
/** Mayeb the construc can work when the Crawler is not L1 */

export class FpacCrawler extends Construct {
 //  public crawler: glue_l1.CfnCrawler
    //public crawlerTrigger: glue_l1.CfnTrigger
   //public startCrawlerTask: tasks.GlueStartCrawlerRun
    
 
    constructor(scope: Construct, id: string, props: LambdaApiStackProps) {
        super(scope, id)



  /*
            const crawlerName = `FSA-${props.deployEnv}-${props.projectName}-CRAWLER`;
            this.crawler = new glue_l1.CfnCrawler(this, `${props.projectName}-ProcessedCrawler`, {
                name: crawlerName,
                role: props.roleArn,
                databaseName: props.databaseName,
                targets: {
                    s3Targets: [{
                    path: `s3://${props.finalBucketName}/`,
                    }],
                },
                schemaChangePolicy: {
                    updateBehavior: 'UPDATE_IN_DATABASE',
                    deleteBehavior: 'DEPRECATE_IN_DATABASE',
                },
            });
*/

            // Conditional trigger: run crawler when ETL job succeeds
            /*
           this.crawlerTrigger = new glue_l1.CfnTrigger(this, `${props.projectName}-CrawlerTrigger`, {
                name: `${cdk.Stack.of(this).stackName}-crawler-trigger`,
                type: 'CONDITIONAL',
                workflowName: props.workflowName,
                predicate: {
                    conditions: [{
                    jobName: `crawler-job-${props.workflowName}`,
                    state: 'SUCCEEDED',
                    logicalOperator: 'EQUALS',
                    }],
                },
                actions: [{
                    crawlerName: this.crawler.name,
                }],
            });
            this.crawlerTrigger.addDependency(props.stepTrigger);
            this.crawlerTrigger.addDependency(this.crawler);
            */

/*
         this.startCrawlerTask = new tasks.GlueStartCrawlerRun(this, `Start ${props.projectName} Processed Crawler`, {
            crawlerName: this.crawler.name!,
            resultPath: '$.glueResult',
        });

*/
    }
}