from aws_cdk import (
    Duration,    
    aws_iam as iam,    
    aws_lambda as lambda_,
    aws_apigateway as apigateway,
    aws_s3 as s3,
    Stack,
    App,
    CfnOutput
)
from constructs import Construct
import sqlite3
from sqlite3 import OperationalError

def execute_query_compliant(request):
    import sqlite3
    name = request.GET.get("name")
    if not name:
        return None
    query = "SELECT * FROM Users WHERE name = ?"
    with sqlite3.connect("example.db") as connection:
        cursor = connection.cursor()
        cursor.execute(query, (name,))
        result = cursor.fetchall()
        return result

class CdklambdaStack(Stack):

    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        self.valid_bucket = s3.Bucket(self, 'valid-bucket',
                                      versioned=True,
                                      bucket_name='processed-docs-bucket-shaoyi',
                                      encryption=s3.BucketEncryption.S3_MANAGED,
                                      block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
                                      enforce_ssl=True)

        lambda_layer = lambda_.LayerVersion(
            self, "LambdaLayer",
            code=lambda_.Code.from_asset("python"),
            compatible_runtimes=[lambda_.Runtime.PYTHON_3_9]
        )

        common_lambda_config = {
            'runtime': lambda_.Runtime.PYTHON_3_9,
            'timeout': Duration.minutes(10),
            'memory_size': 8192,
            'layers': [lambda_layer]
        }

        trigger_imggen = lambda_.Function(self, 'file-upload-trigger',
                                          handler='imggen.lambda_handler',
                                          code=lambda_.Code.from_asset('lambda1'),
                                          function_name="start-imggen",
                                          **common_lambda_config)

        trigger_textgen = lambda_.Function(self, 'textgen-trigger',
                                            handler='textgen.lambda_handler',
                                            code=lambda_.Code.from_asset('lambda2'),
                                            function_name="start-textgen",
                                            **common_lambda_config)

        common_cors_options = apigateway.CorsOptions(
            allow_origins=apigateway.Cors.ALL_ORIGINS,
            allow_headers=[
                'Content-Type',
                'X-Amz-Date',
                'Authorization',
                'X-Api-Key',
            ],
            allow_methods=['OPTIONS', 'POST']
        )

        textapi = apigateway.RestApi(
            self, 'TextApi',
            description='text generation api gateway',
            deploy_options={"stage_name": 'dev'},
            default_cors_preflight_options=common_cors_options
        )

        imgapi = apigateway.RestApi(
            self, 'ImgApi',
            description='image generation api gateway',
            deploy_options={"stage_name": 'dev'},
            default_cors_preflight_options=common_cors_options
        )

        common_integration_response = apigateway.IntegrationResponse(
            status_code="200",
            response_parameters={
                'method.response.header.Access-Control-Allow-Origin': "'*'"
            }
        )

        common_method_response = apigateway.MethodResponse(
            status_code="200",
            response_parameters={
                'method.response.header.Access-Control-Allow-Origin': True,
            },
            response_models={
                'application/json': apigateway.Model.EMPTY_MODEL,
            }
        )

        integration_textgen = apigateway.LambdaIntegration(
            trigger_textgen, 
            proxy=False,
            integration_responses=[common_integration_response]
        )

        textapi.root.add_method("POST", integration_textgen, method_responses=[common_method_response])

        integration_imggen = apigateway.LambdaIntegration(
            trigger_imggen, 
            proxy=False,
            integration_responses=[common_integration_response]
        )

        imgapi.root.add_method("POST", integration_imggen, method_responses=[common_method_response])

        common_policy = iam.PolicyStatement(
            actions=[
                's3:GetObject',
                's3:PutObject',
                's3:ListBucket',
                's3:DeleteObject',
                'bedrock:ListFoundationModels',
                'bedrock:GetFoundationModel',
                'bedrock:InvokeModel',
                'bedrock:InvokeModelWithResponseStream',
                'bedrock:RetrieveAndGenerate'
            ],
            resources=[
                self.valid_bucket.bucket_arn,
                f"{self.valid_bucket.bucket_arn}/*",
                "arn:aws:bedrock:*:*:foundation-model/*"
            ]
        )

        for trigger in [trigger_imggen, trigger_textgen]:
            trigger.add_to_role_policy(common_policy)

        CfnOutput(self, 'TextApiInvokeUrl', value=textapi.url)
        CfnOutput(self, 'ImgApiInvokeUrl', value=imgapi.url)

app = App()
CdklambdaStack(app, "CdkbedrockStack")
app.synth()