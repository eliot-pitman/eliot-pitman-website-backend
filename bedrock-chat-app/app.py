from chalice import Chalice, BadRequestError
import boto3
import os
import sqlite3
import json
import numpy as np

# Configuration
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')
AWS_ACCOUNT_ID = os.environ.get('AWS_ACCOUNT_ID', '491891987197')
MODEL_ID = os.environ.get('MODEL_ID', 'arn:aws:bedrock:us-east-1:491891987197:inference-profile/us.deepseek.r1-v1:0')
TEMPERATURE = float(os.environ.get('TEMPERATURE', '1'))
TOP_P = float(os.environ.get('TOP_P', '1'))
MAX_TOKENS = int(os.environ.get('MAX_TOKENS', '2048'))
LATENCY = os.environ.get('LATENCY', 'standard')
NUM_RETRIEVAL_RESULTS = int(os.environ.get('NUM_RETRIEVAL_RESULTS', '5'))
S3_BUCKET = os.environ.get('S3_BUCKET', 'vector-bucket-eliot-pitman')
DB_LOCAL_PATH = "/tmp/vector_store.db"

app = Chalice(app_name='bedrock-chat-app')

# --- Retrieval helpers ---

def get_db():
    if not os.path.exists(DB_LOCAL_PATH):
        app.log.info("Downloading vector store from S3...")
        boto3.client("s3").download_file(S3_BUCKET, "vector_store.db", DB_LOCAL_PATH)
    return sqlite3.connect(DB_LOCAL_PATH)

def embed_text(text):
    bedrock = boto3.client("bedrock-runtime", region_name=AWS_REGION)
    response = bedrock.invoke_model(
        modelId="amazon.titan-embed-text-v2:0",
        body=json.dumps({"inputText": text})
    )
    return np.array(json.loads(response["body"].read())["embedding"])

def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def retrieve(query, top_k=NUM_RETRIEVAL_RESULTS):
    conn = get_db()
    rows = conn.execute("SELECT source, chunk_text, embedding FROM embeddings").fetchall()
    conn.close()
    query_vec = embed_text(query)
    scored = sorted(
        [(cosine_similarity(query_vec, np.array(json.loads(emb))), src, txt)
         for src, txt, emb in rows],
        reverse=True
    )
    return scored[:top_k]


@app.route('/chat', methods=['POST'], cors=True)
def chat():
    request = app.current_request

    if not request.json_body:
        raise BadRequestError("Request body is required")

    user_message = request.json_body.get('message')
    if not user_message:
        raise BadRequestError("Message field is required")

    bedrock_runtime = boto3.client(
        service_name='bedrock-runtime',
        region_name=AWS_REGION
    )

    try:
        # Retrieve relevant chunks from SQLite
        results = retrieve(user_message)
        context = ""
        for i, (score, source, text) in enumerate(results, 1):
            context += f"\n[{i}] {text}"

        # Prepare message with context
        full_message = f"User question: {user_message}\n\nRelevant context:\n{context}" if context else user_message

        # Call Bedrock
        response = bedrock_runtime.converse(
            modelId=MODEL_ID,
            messages=[
                {
                    'role': 'user',
                    'content': [{'text': full_message}]
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

        # Parse response
        ai_response = 'No response generated'
        if 'output' in response and 'message' in response['output']:
            content = response['output']['message'].get('content', [])
            if content and 'text' in content[0]:
                ai_response = content[0]['text']

        return {'response': ai_response}

    except Exception as e:
        error_message = str(e)
        app.log.error(f"Error: {error_message}")
        raise BadRequestError(f"Error: {error_message}")


@app.route('/')
def index():
    return {'hello': 'world'}