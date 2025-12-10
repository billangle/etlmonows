
import * as iam from "aws-cdk-lib/aws-iam"
import { Function, Runtime, AssetCode, ILayerVersion } from "aws-cdk-lib/aws-lambda"
import { Duration, StackProps } from "aws-cdk-lib"
import { Construct } from "constructs"
import * as tasks from 'aws-cdk-lib/aws-stepfunctions-tasks';

interface LambdaApiStackProps extends StackProps {
    functionName: string,
    functionCode: string,
    role: iam.IRole,
    environment: any,
    layers: ILayerVersion[],
    outputPath: string,
    projectName: string,
}

export class FpacLambdaTask extends Construct {
    public lambdaFunction: Function
    public task: tasks.LambdaInvoke

    constructor(scope: Construct, id: string, props: LambdaApiStackProps) {
        super(scope, id)


        this.lambdaFunction = new Function(this, props.functionName, {
            functionName: props.functionName,
            handler: "index.handler",
            runtime: Runtime.NODEJS_LATEST,
            code: new AssetCode(props.functionCode),
            memorySize: 512,
            role: props.role,
            timeout: Duration.seconds(30),
            environment: props.environment,
            layers: props.layers,
       
        })


     this.task = new tasks.LambdaInvoke(this, `${props.projectName}-LogResults`, {
      lambdaFunction: this.lambdaFunction,
      outputPath: props.outputPath,
    });



    }
}