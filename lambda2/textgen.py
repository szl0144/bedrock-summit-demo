import json
import boto3
import http
import os
import logging
from botocore.exceptions import ClientError

LOG = logging.getLogger()
LOG.setLevel(logging.INFO)

region_name = os.getenv("regionName", "us-east-1")
model_id = os.getenv("modelId", "amazon.titan-text-premier-v1:0")
bedrock_agent_runtime = boto3.client(service_name="bedrock-agent-runtime", region_name=region_name)
bedrock_runtime = boto3.client(service_name="bedrock-runtime", region_name=region_name)

def retrieveAndGenerate(input_text, kbId):
    try:
        response = bedrock_agent_runtime.retrieve_and_generate(
            input={
                'text': input_text
            },
            retrieveAndGenerateConfiguration={
                'type': 'KNOWLEDGE_BASE',
                'knowledgeBaseConfiguration': {
                    'knowledgeBaseId': kbId,
                    'modelArn': 'arn:aws:bedrock:us-east-1::foundation-model/amazon.titan-text-premier-v1:0'
                }
            }
        )
        return response
    except ClientError as e:
        LOG.error(f"Error in retrieveAndGenerate: {e}")
        raise

def lambda_handler(event, context):
    prompt = event.get("input")
    
    if not prompt:
        return {
            "statusCode": http.HTTPStatus.BAD_REQUEST,
            "body": json.dumps({"error": "Input prompt is missing"})
        }
    
    try:
        response_kb = retrieveAndGenerate(prompt, "AATA6BCT0U")["output"]["text"]
        
        return {
            "statusCode": http.HTTPStatus.OK,
            "body": json.dumps({"Answer": response_kb})
        }
        
    except ClientError as e:
        error_message = f"Exception raised while execution: {e}"
        LOG.error(error_message)
        
        return {
            "statusCode": http.HTTPStatus.INTERNAL_SERVER_ERROR,
            "body": json.dumps({"error": "Internal Server Error", "details": error_message})
        }
    except Exception as e:
        error_message = f"Unexpected error: {e}"
        LOG.error(error_message)
        
        return {
            "statusCode": http.HTTPStatus.INTERNAL_SERVER_ERROR,
            "body": json.dumps({"error": "Internal Server Error", "details": error_message})
        }