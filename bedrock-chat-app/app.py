from chalice import Chalice, BadRequestError
import boto3
import os

# Configuration
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')
AWS_ACCOUNT_ID = os.environ.get('AWS_ACCOUNT_ID', '491891987197')
KNOWLEDGE_BASE_ID = os.environ.get('KNOWLEDGE_BASE_ID', 'GNWDQH0467')
MODEL_ID = os.environ.get('MODEL_ID', 'arn:aws:bedrock:us-east-1:491891987197:inference-profile/us.deepseek.r1-v1:0')
TEMPERATURE = float(os.environ.get('TEMPERATURE', '1'))
TOP_P = float(os.environ.get('TOP_P', '1'))
MAX_TOKENS = int(os.environ.get('MAX_TOKENS', '2048'))
LATENCY = os.environ.get('LATENCY', 'standard')
NUM_RETRIEVAL_RESULTS = int(os.environ.get('NUM_RETRIEVAL_RESULTS', '5'))
STOP_SEQUENCES = ['\nObservation']

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
    
    # Initialize Bedrock Runtime client
    bedrock_runtime = boto3.client(
        service_name='bedrock-runtime',
        region_name=AWS_REGION
    )
    
    # Initialize Bedrock Agent Runtime client for knowledge base retrieval
    bedrock_agent_runtime = boto3.client(
        service_name='bedrock-agent-runtime',
        region_name=AWS_REGION
    )
    
    try:
        # First, retrieve relevant documents from the knowledge base
        retrieval_results = bedrock_agent_runtime.retrieve(
            knowledgeBaseId=KNOWLEDGE_BASE_ID,
            retrievalConfiguration={
                'vectorSearchConfiguration': {
                    'numberOfResults': NUM_RETRIEVAL_RESULTS
                }
            },
            retrievalQuery={
                'text': user_message
            }
        )
        
        # Extract retrieved content for context
        context = ""
        if 'retrievalResults' in retrieval_results:
            for i, result in enumerate(retrieval_results['retrievalResults'], 1):
                content = result.get('content', {}).get('text', '')
                context += f"\n[{i}] {content}"
        
        # Prepare the message with context
        full_message = f"User question: {user_message}\n\nRelevant context:\n{context}" if context else user_message
        
        # Make API call to Bedrock Runtime using converse
        response = bedrock_runtime.converse(
            modelId=MODEL_ID,
            messages=[
                {
                    'role': 'user',
                    'content': [
                        {
                            'text': full_message
                        }
                    ]
                }
            ],
            inferenceConfig={
                'temperature': TEMPERATURE
            },
            additionalModelRequestFields={},
            performanceConfig={
                'latency': LATENCY
            }
        )
        
        # Parse response from converse API
        ai_response = 'No response generated'
        if 'output' in response and 'message' in response['output']:
            content = response['output']['message'].get('content', [])
            if content and 'text' in content[0]:
                ai_response = content[0]['text']
        
        return {
            'response': ai_response
        }
    
    except Exception as e:
        # Log error with details for debugging
        error_message = str(e)
        app.log.error(f"Error calling Bedrock Agent Runtime API: {error_message}")
        # Return error details in development
        raise BadRequestError(f"Error: {error_message}")


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
