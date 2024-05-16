import json
import boto3
import http
import os
import logging
from botocore.exceptions import ClientError

LOG = logging.getLogger()
LOG.setLevel(logging.INFO)

# Generate text using Amazon Titan Text premier models on Amazon Bedrock.
region_name = os.getenv("regionName", "us-east-1") #Test With Code Generations
model_id = os.getenv("modelId", "amazon.titan-text-premier-v1:0") #Test With Code Generations
bedrock_agent_runtime = boto3.client(service_name="bedrock-agent-runtime", region_name=region_name)   #Test With Code Generations
bedrock_runtime = boto3.client(service_name="bedrock-runtime", region_name=region_name)   #Test With Code Generations

def retrieveAndGenerate(input, kbId):
    return bedrock_agent_runtime.retrieve_and_generate(
        input={
            'text': input
        },
        retrieveAndGenerateConfiguration={
            'type': 'KNOWLEDGE_BASE',
            'knowledgeBaseConfiguration': {
                'knowledgeBaseId': kbId,
                'modelArn': 'arn:aws:bedrock:us-east-1::foundation-model/amazon.titan-text-premier-v1:0'
                }
            }
        )


def lambda_handler(event, context):
    accept = 'application/json' #Test With Code Generations
    content_type = 'application/json' #Test With Code Generations
    prompt = event.get("input")
    print(prompt)

    if not prompt:
        return {
            "statusCode": http.HTTPStatus.BAD_REQUEST,
            "body": json.dumps({"error": "Input prompt is missing"})
        }
    # Generate text using Amazon Titan Text models on Amazon Bedrock.
    
    
    
    body = json.dumps({
            "inputText": prompt,
            "textGenerationConfig": {
                "maxTokenCount": 3072,
                "stopSequences": [],
                "temperature": 0.7,
                "topP": 0.9
            }
    })
    try:
        response_kb = retrieveAndGenerate(prompt, "AATA6BCT0U")["output"]["text"]
        print(response_kb)
        """
        response = bedrock_runtime.invoke_model(     
            body=body,
            modelId=model_id,
            accept=accept,
            contentType=content_type,
        )  #Test With Code Generations
        response_body = json.loads(response.get("body").read()) #Test With Code Generations
        answer = response_body['results'][0]['outputText'] #Test With Code Generations
        print(answer)
        """
        return {
            "statusCode": http.HTTPStatus.OK,
            "body": json.dumps({"Answer": response_kb})
        }   #Test With Code Generations
        
        
    except ClientError as e:
        error_message = f"Exception raised while execution: {e}"
        LOG.error(error_message)
        
        return {
            "statusCode": http.HTTPStatus.INTERNAL_SERVER_ERROR,
            "body": json.dumps({"error": "Internal Server Error", "details": error_message})
        }
