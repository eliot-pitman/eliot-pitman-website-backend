# Personal Website Backend

Welcome to my Python backend used to interact with AWS services such as Bedrock.

## Chat Endpoint

The `/chat` endpoint allows you to send messages to AWS Bedrock and receive AI-generated responses.

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
- `BEDROCK_MODEL_ID`: Bedrock model ID to use (default: `anthropic.claude-3-sonnet-20240229-v1:0`)

### AWS Credentials

This application uses boto3 to interact with AWS Bedrock. Ensure you have AWS credentials configured via:
- AWS credentials file (`~/.aws/credentials`)
- Environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`)
- IAM role (when running on AWS infrastructure)

### Example Usage

```bash
curl -X POST https://your-api-endpoint/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, how are you?"}'
```

### Required IAM Permissions

The AWS credentials used must have permissions to invoke Bedrock models:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel"
      ],
      "Resource": "arn:aws:bedrock:*:*:model/*"
    }
  ]
}
```

## Development

### Install Dependencies

```bash
cd bedrock-chat-app
pip install -r requirements.txt
```

### Local Testing

```bash
chalice local
```

### Deploy

```bash
chalice deploy
```
