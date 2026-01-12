# Personal Website Backend

Welcome to my Python backend used to interact with AWS services such as Bedrock.

## Chat Endpoint

The `/chat` endpoint allows you to send messages to AWS Bedrock Agent Runtime and receive AI-generated responses from a knowledge base.

### Endpoint Details

- **URL**: `/chat`
- **Method**: `POST`
- **Content-Type**: `application/json`

### Request Body

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

### Environment Variables

The following environment variables can be configured:

- `AWS_REGION`: AWS region for Bedrock service (default: `us-east-1`)
- `KNOWLEDGE_BASE_ID`: Bedrock knowledge base ID (default: `GNWDQH0467`)
- `MODEL_ARN`: Model ARN to use for retrieval (default: `arn:aws:bedrock:us-east-1::foundation-model/deepseek.r1-v1:0`)

### AWS Credentials

This application uses boto3 to interact with AWS Bedrock Agent Runtime. Ensure you have AWS credentials configured via:
- AWS credentials file (`~/.aws/credentials`)
- Environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`)
- IAM role (when running on AWS infrastructure)

### Example Usage

```bash
curl -X POST https://your-api-endpoint/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What information is in my knowledge base?"}'
```

### Required IAM Permissions

The AWS credentials used must have permissions to retrieve and generate from Bedrock knowledge bases:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:RetrieveAndGenerate",
        "bedrock:Retrieve"
      ],
      "Resource": "*"
    }
  ]
}
```

## Development

### Install Dependencies

```bash
cd bedrock-chat-app
python3 -m venv chalice-env
source chalice-env/bin/activate
pip install -r requirements.txt
```

### Local Testing

```bash
cd bedrock-chat-app
chalice local
```

This starts a local development server at `http://localhost:8000`

### Deploy to AWS

```bash
cd bedrock-chat-app

# Configure AWS credentials
export AWS_REGION=us-east-1
export AWS_ACCOUNT_ID=491891987197
export KNOWLEDGE_BASE_ID=GNWDQH0467
export MODEL_ID=arn:aws:bedrock:us-east-1:491891987197:inference-profile/us.deepseek.r1-v1:0

# Deploy
chalice deploy
```

After deployment, you'll receive a REST API URL. Use it to make requests:

```bash
curl -X POST https://<api-id>.execute-api.us-east-1.amazonaws.com/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "test"}'
```

#### Configuration

All configuration is managed in `.chalice/config.json` and `.chalice/config-prod.json`:
- `config.json`: Chalice deployment settings
- `config-prod.json`: IAM policy for Lambda execution role

#### Troubleshooting

- **"Missing Authentication Token"**: Check that routes have `NONE` authorization in API Gateway
- **"Access Denied" errors**: Verify IAM policy in `.chalice/config-prod.json` has all required Bedrock permissions
- **"Module not found"**: Ensure all dependencies are in `requirements.txt` and Chalice deployment includes them
