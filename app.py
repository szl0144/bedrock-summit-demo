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
        return
    query = "SELECT * FROM Users WHERE name = ?;"
    with sqlite3.connect("example.db") as connection:
        cursor = connection.cursor()
        cursor.execute(query, (name,))
        connection.commit()

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

        python_lambda_kwargs = {
            'handler': 'imggen.lambda_handler',
            'runtime': lambda_.Runtime.PYTHON_3_9,
            'timeout': Duration.minutes(10),
            'memory_size': 8192,
            'layers': [lambda_layer]
        }

        python_lambda_kwargs_textgen = {
            'handler': 'textgen.lambda_handler',
            'runtime': lambda_.Runtime.PYTHON_3_9,
            'timeout': Duration.minutes(10),
            'memory_size': 8192,
            'layers': [lambda_layer]
        }

        trigger_imggen = lambda_.Function(self, 'file-upload-trigger', **python_lambda_kwargs,
                                          code=lambda_.Code.from_asset('lambda1'),
                                          function_name="start-imggen")

        trigger_textgen = lambda_.Function(self, 'textgen-trigger', **python_lambda_kwargs_textgen,
                                            code=lambda_.Code.from_asset('lambda2'),
                                            function_name="start-textgen")

        cors_options = apigateway.CorsOptions(
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
            description='example api gateway',
            deploy_options={
                "stage_name": 'dev'
            },
            default_cors_preflight_options=cors_options
        )

        imgapi = apigateway.RestApi(
            self, 'ImgApi',
            description='example api gateway',
            deploy_options={
                "stage_name": 'dev'
            },
            default_cors_preflight_options=cors_options
        )

        integration_response = apigateway.IntegrationResponse(
            status_code="200",
            response_parameters={
                'method.response.header.Access-Control-Allow-Origin': "'*'"
            }
        )

        method_response = apigateway.MethodResponse(
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
            integration_responses=[integration_response]
        )

        textapi.root.add_method("POST", integration_textgen, method_responses=[method_response])

        integration_imggen = apigateway.LambdaIntegration(
            trigger_imggen, 
            proxy=False,
            integration_responses=[integration_response]
        )

        imgapi.root.add_method("POST", integration_imggen, method_responses=[method_response])

        policy_statement = iam.PolicyStatement(
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
            resources=['*']
        )

        trigger_imggen.add_to_role_policy(policy_statement)
        trigger_textgen.add_to_role_policy(policy_statement)

        CfnOutput(self, 'TextApiInvokeUrl', value=textapi.url)
        CfnOutput(self, 'ImgApiInvokeUrl', value=imgapi.url)

app = App()
CdklambdaStack(app, "CdkbedrockStack")
app.synth()