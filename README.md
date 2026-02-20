# Personal Website Backend

Python backend for a chat API powered by AWS Bedrock + custom retrieval.

## What Changed

- Replaced Bedrock Knowledge Base retrieval with a custom SQLite vector store retrieval flow.
- Added `scripts/build_vectors.py` to generate embeddings from local `knowledge_base/*.txt` files.
- Added S3-backed vector DB loading in the API (`vector_store.db` is downloaded to `/tmp` in Lambda).
- Added runtime tuning environment variables in Chalice config.
- Added `numpy` dependency for cosine similarity scoring.

## How It Works

1. `scripts/build_vectors.py` reads files from `knowledge_base/`.
2. Each file is chunked and embedded using `amazon.titan-embed-text-v2:0`.
3. Embeddings are saved to `vector_store.db` and uploaded to S3.
4. `/chat` embeds the user query, retrieves top matching chunks from SQLite, and sends context to Bedrock `converse`.

## Chat Endpoint

- **URL**: `/chat`
- **Method**: `POST`
- **Content-Type**: `application/json`

### Request

```json
{
  "message": "Your message here"
}
```

### Response

```json
{
  "response": "AI-generated response text"
}
```

## Environment Variables

Configured in `bedrock-chat-app/.chalice/config.json` (defaults also exist in `bedrock-chat-app/app.py`):

- `AWS_REGION` (default: `us-east-1`)
- `AWS_ACCOUNT_ID`
- `MODEL_ID` (Bedrock model / inference profile ARN)
- `TEMPERATURE`
- `TOP_P`
- `MAX_TOKENS`
- `LATENCY`
- `NUM_RETRIEVAL_RESULTS`
- `S3_BUCKET` (stores `vector_store.db`)

## Development

### 1) Install Dependencies

```bash
cd bedrock-chat-app
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2) Build and Upload Vector Store

From the repository root:

```bash
python scripts/build_vectors.py
```

This generates `vector_store.db` and uploads it to `s3://$S3_BUCKET/vector_store.db`.

### 3) Run Locally

```bash
cd bedrock-chat-app
chalice local
```

Local server: `http://localhost:8000`

## Deploy

```bash
cd bedrock-chat-app
chalice deploy
```

After deploy:

```bash
curl -X POST https://<api-id>.execute-api.us-east-1.amazonaws.com/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "test"}'
```

## Required AWS Permissions

At minimum, credentials/role should allow:

- Bedrock runtime model invocation (`bedrock:InvokeModel`)
- S3 read access for Lambda to `vector_store.db` (`s3:GetObject`)
- S3 write access for build script uploads (`s3:PutObject`)

## Project Structure

- `bedrock-chat-app/app.py`: Chalice app and retrieval + chat logic
- `bedrock-chat-app/.chalice/config.json`: stage config and env vars
- `scripts/build_vectors.py`: embedding pipeline + SQLite DB creation
- `knowledge_base/`: source `.txt` documents for retrieval
