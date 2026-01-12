from chalice import Chalice, BadRequestError
import boto3
import json
import os

app = Chalice(app_name='bedrock-chat-app')


@app.route('/chat', methods=['POST'], cors=True)
def chat():
    """
    Chat endpoint that accepts user text and makes API call to AWS Bedrock.
    
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
    
    # Initialize Bedrock client
    # Region can be configured via environment variable or use default
    region = os.environ.get('AWS_REGION', 'us-east-1')
    bedrock_runtime = boto3.client(
        service_name='bedrock-runtime',
        region_name=region
    )
    
    # Model ID - using Claude 3 Sonnet as an example
    # This can be configured via environment variable
    model_id = os.environ.get('BEDROCK_MODEL_ID', 'anthropic.claude-3-sonnet-20240229-v1:0')
    
    # Prepare the request body for Bedrock
    request_body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1024,
        "messages": [
            {
                "role": "user",
                "content": user_message
            }
        ]
    }
    
    try:
        # Make API call to Bedrock
        response = bedrock_runtime.invoke_model(
            modelId=model_id,
            body=json.dumps(request_body)
        )
        
        # Parse response
        response_body = json.loads(response['body'].read())
        content = response_body.get('content', [])
        
        # Safely extract the AI response
        if content and len(content) > 0:
            ai_response = content[0].get('text', 'No response generated')
        else:
            ai_response = 'No response generated'
        
        return {
            'response': ai_response
        }
    
    except Exception as e:
        # Log error with details for debugging
        app.log.error(f"Error calling Bedrock API: {str(e)}")
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
