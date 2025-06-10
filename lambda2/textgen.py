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
    try:
        prompt = event.get("input")
        
        if not prompt or not isinstance(prompt, str) or not prompt.strip():
            return {
                "statusCode": http.HTTPStatus.BAD_REQUEST,
                "body": json.dumps({"error": "Valid input prompt is required"})
            }

        kb_id = os.getenv("KNOWLEDGE_BASE_ID", "AATA6BCT0U")
        response_kb = retrieveAndGenerate(prompt.strip(), kb_id)["output"]["text"]
        
        return {
            "statusCode": http.HTTPStatus.OK,
            "body": json.dumps({"Answer": response_kb})
        }
        
    except ClientError as e:
        error_message = f"AWS service error: {str(e)}"
        LOG.error(error_message)
        return {
            "statusCode": http.HTTPStatus.INTERNAL_SERVER_ERROR,
            "body": json.dumps({"error": "Internal Server Error"})
        }
    except Exception as e:
        error_message = f"Unexpected error: {str(e)}"
        LOG.error(error_message)
        return {
            "statusCode": http.HTTPStatus.INTERNAL_SERVER_ERROR,
            "body": json.dumps({"error": "Internal Server Error"})
        }