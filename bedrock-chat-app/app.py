from chalice import Chalice, BadRequestError
import boto3
import json
import os

app = Chalice(app_name='bedrock-chat-app')


@app.route('/chat', methods=['POST'], cors=True)
def chat():
    """
    Chat endpoint that accepts user text and makes API call to AWS Bedrock Agent Runtime.
    Uses retrieve-and-generate to query a knowledge base.
    
    Expected request body:
    {
        "message": "User's chat message"
    }
    
    Returns:
    {
        "response": "AI response text"
    }
    """
    request = app.current_request
    
    # Validate request body
    if not request.json_body:
        raise BadRequestError("Request body is required")
    
    user_message = request.json_body.get('message')
    if not user_message:
        raise BadRequestError("Message field is required")
    
    # Initialize Bedrock Agent Runtime client
    # Region can be configured via environment variable or use default
    region = os.environ.get('AWS_REGION', 'us-east-1')
    bedrock_agent_runtime = boto3.client(
        service_name='bedrock-agent-runtime',
        region_name=region
    )
    
    # Knowledge base configuration - can be configured via environment variables
    knowledge_base_id = os.environ.get('KNOWLEDGE_BASE_ID', 'GNWDQH0467')
    model_arn = os.environ.get('MODEL_ARN', 'arn:aws:bedrock:us-east-1::foundation-model/deepseek.r1-v1:0')
    
    try:
        # Make API call to Bedrock Agent Runtime
        response = bedrock_agent_runtime.retrieve_and_generate(
            input={
                'text': user_message
            },
            retrieveAndGenerateConfiguration={
                'type': 'KNOWLEDGE_BASE',
                'knowledgeBaseConfiguration': {
                    'knowledgeBaseId': knowledge_base_id,
                    'modelArn': model_arn
                }
            }
        )
        
        # Parse response
        output = response.get('output', {})
        ai_response = output.get('text', 'No response generated')
        
        return {
            'response': ai_response
        }
    
    except Exception as e:
        # Log error with details for debugging
        app.log.error(f"Error calling Bedrock Agent Runtime API: {str(e)}")
        # Return generic error message to client for security
        raise BadRequestError("Unable to process chat request. Please try again later.")


@app.route('/')
def index():
    return {'hello': 'world'}


# The view function above will return {"hello": "world"}
# whenever you make an HTTP GET request to '/'.
#
# Here are a few more examples:
#
# @app.route('/hello/{name}')
# def hello_name(name):
#    # '/hello/james' -> {"hello": "james"}
#    return {'hello': name}
#
# @app.route('/users', methods=['POST'])
# def create_user():
#     # This is the JSON body the user sent in their POST request.
#     user_as_json = app.current_request.json_body
#     # We'll echo the json body back to the user in a 'user' key.
#     return {'user': user_as_json}
#
# See the README documentation for more examples.
#
