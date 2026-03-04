# Chatbot Conversation Logging & Troubleshooting Guide

## Overview

This document covers the conversation logging feature added to the Bedrock chatbot backend, and a reference of known issues and fixes encountered during the RAG migration.

---

## Conversation Logging

### What Was Added

Every chat request is now logged as a JSON file in S3. Logs are written by the `log_conversation()` helper in `app.py` and stored in a `conversations/` prefix in the same S3 bucket as the vector store.

### Storage Location

```
s3://vector-bucket-eliot-pitman/conversations/{timestamp}_{uuid}.json
```

Each file contains:

```json
{
  "timestamp": "2026-02-20T21-45-31",
  "user_message": "user's question here",
  "bot_response": "assistant's response here"
}
```

### Reviewing Conversations

List all logged conversations:

```bash
aws s3 ls s3://vector-bucket-eliot-pitman/conversations/
```

Read a specific conversation:

```bash
aws s3 cp s3://vector-bucket-eliot-pitman/conversations/2026-02-20T21-45-31_abc123.json -
```

Download all conversations locally:

```bash
aws s3 sync s3://vector-bucket-eliot-pitman/conversations/ ./conversations/
```

### IAM Requirement

The Lambda execution role requires `s3:PutObject` on the bucket. This is included in the `vector-store-lambda-policy` attached to `bedrock-chat-app-dev-api_handler`. If logging silently fails, verify this permission is in place:

```bash
aws iam list-attached-role-policies --role-name bedrock-chat-app-dev-api_handler
```

### Important Notes

- Logging failures are caught silently — a logging error will not cause the chat response to fail
- Logs are not encrypted at rest beyond default S3 server-side encryption
- There is no retention policy set — logs will accumulate indefinitely. Consider adding an S3 lifecycle rule if storage cost becomes a concern

---

## Known Issues & Fixes

### 1. Chalice Deploy Wipes Environment Variables

**Symptom:** After running `chalice deploy`, the Lambda env vars are reset to null and the function returns 403 or 500 errors.

**Cause:** Chalice overwrites Lambda configuration on every deploy unless env vars are defined in `.chalice/config.json`.

**Fix:** Ensure all environment variables are defined in `.chalice/config.json` under the `environment_variables` key for each stage. Never set env vars manually via the AWS console or CLI as the sole source of truth — always keep them in config.json.

```json
"environment_variables": {
  "AWS_ACCOUNT_ID": "491891987197",
  "MODEL_ID": "arn:aws:bedrock:us-east-1:491891987197:inference-profile/us.deepseek.r1-v1:0",
  "TEMPERATURE": "1",
  "TOP_P": "1",
  "MAX_TOKENS": "2048",
  "LATENCY": "standard",
  "NUM_RETRIEVAL_RESULTS": "5",
  "S3_BUCKET": "vector-bucket-eliot-pitman"
}
```

---

### 2. Chalice Deploy Fails — Cannot Delete IAM Role

**Symptom:**
```
DeleteConflictException: Cannot delete entity, must detach all policies first.
```

**Cause:** Manually attached IAM policies conflict with Chalice's attempt to recreate the role during deploy.

**Fix:** Detach all manually attached policies before deploying. List them first:

```bash
aws iam list-attached-role-policies --role-name bedrock-chat-app-dev-api_handler
aws iam list-role-policies --role-name bedrock-chat-app-dev-api_handler
```

Detach managed policies:

```bash
aws iam detach-role-policy \
  --role-name bedrock-chat-app-dev-api_handler \
  --policy-arn arn:aws:iam::491891987197:policy/vector-store-lambda-policy
```

Delete inline policies:

```bash
aws iam delete-role-policy \
  --role-name bedrock-chat-app-dev-api_handler \
  --policy-name allow-s3-put
```

Then redeploy. Going forward, the `config.json` uses `"autogen_policy": false` with `"iam_policy_file": "config-prod.json"` so Chalice manages permissions via that file instead.

---

### 3. KMS Access Denied on Lambda Invoke

**Symptom:**
```
KMSAccessDeniedException: Lambda was unable to decrypt the environment variables
arn:aws:kms:us-east-1:491891987197:key/7c1c582d-79d4-4c68-a907-1142d829f49c
```

**Cause:** A previous deployment encrypted Lambda env vars with a customer-managed KMS key. When the IAM role was recreated by Chalice, the new role lacked permission to decrypt using that key. The KMS key also has a restrictive resource-based policy that prevents even the Administrator IAM user from granting access.

**Fix:** Clear the env vars to remove the KMS association, then reset them without a KMS key:

```bash
export AWS_PAGER="" && aws lambda update-function-configuration \
  --function-name bedrock-chat-app-dev \
  --environment "Variables={}"
```

Wait 15 seconds, then reset:

```bash
export AWS_PAGER="" && aws lambda update-function-configuration \
  --function-name bedrock-chat-app-dev \
  --environment "Variables={AWS_ACCOUNT_ID=491891987197,MODEL_ID=arn:aws:bedrock:us-east-1:491891987197:inference-profile/us.deepseek.r1-v1:0,TEMPERATURE=1,TOP_P=1,MAX_TOKENS=2048,LATENCY=standard,NUM_RETRIEVAL_RESULTS=5,S3_BUCKET=vector-bucket-eliot-pitman}"
```

**Prevention:** Never manually set a KMS key on the Lambda function. Keep env vars managed through `config.json` only.

---

### 4. Lambda Has No CloudWatch Logs

**Symptom:** `aws logs tail` returns nothing after invocations.

**Cause:** The Lambda execution role is missing `AWSLambdaBasicExecutionRole` which grants CloudWatch Logs write permissions.

**Fix:**

```bash
aws iam attach-role-policy \
  --role-name bedrock-chat-app-dev-api_handler \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
```

**Note:** This policy is included in `config-prod.json` going forward so it will be applied automatically on deploy.

---

### 5. S3 Access Forbidden (403) on Vector Store

**Symptom:**
```
BadRequestError: An error occurred (403) when calling the HeadObject operation: Forbidden
```

**Cause:** The Lambda execution role is missing S3 permissions, usually after Chalice recreates the role.

**Fix:** Reattach the vector store policy:

```bash
aws iam attach-role-policy \
  --role-name bedrock-chat-app-dev-api_handler \
  --policy-arn arn:aws:iam::491891987197:policy/vector-store-lambda-policy
```

If the policy was deleted, recreate it:

```bash
aws iam create-policy \
  --policy-name vector-store-lambda-policy \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Action": ["s3:GetObject", "s3:PutObject"],
        "Resource": "arn:aws:s3:::vector-bucket-eliot-pitman/*"
      }
    ]
  }'
```

---

### 6. numpy Not Found in Lambda

**Symptom:**
```
Runtime.ImportModuleError: Unable to import module 'app': No module named 'numpy'
```

**Cause:** numpy is not included in the deployment package.

**Fix:** Ensure `requirements.txt` contains numpy and redeploy:

```
boto3>=1.28.0
numpy
```

```bash
.venv/bin/chalice deploy
```

---

### 7. Stale Vector Store Served to Lambda

**Symptom:** Lambda returns responses based on old knowledge base content after running the build script.

**Cause:** Lambda caches the SQLite file in `/tmp` across warm invocations. The cache-busting logic compares S3 `LastModified` timestamps to determine if a re-download is needed.

**Fix:** The `get_db()` function in `app.py` handles this automatically by checking the S3 `LastModified` timestamp. If stale responses persist, force a Lambda cold start by deploying a trivial change or updating a env var.

---

## Quick Reference — AWS CLI Commands

| Task | Command |
|---|---|
| Check Lambda role | `aws lambda get-function-configuration --function-name bedrock-chat-app-dev --query "Role"` |
| Check env vars | `aws lambda get-function-configuration --function-name bedrock-chat-app-dev --query "Environment"` |
| Check KMS key | `aws lambda get-function-configuration --function-name bedrock-chat-app-dev --query "KMSKeyArn"` |
| List role policies | `aws iam list-attached-role-policies --role-name bedrock-chat-app-dev-api_handler` |
| View recent logs | `aws logs tail /aws/lambda/bedrock-chat-app-dev --since 5m` |
| Invoke Lambda directly | See test payload below |
| List conversations | `aws s3 ls s3://vector-bucket-eliot-pitman/conversations/` |
| Throttle Lambda to zero | `aws lambda put-function-concurrency --function-name bedrock-chat-app-dev --reserved-concurrent-executions 0` |
| Re-enable Lambda | `aws lambda delete-function-concurrency --function-name bedrock-chat-app-dev` |

### Full Lambda Test Payload

```bash
export AWS_PAGER="" && aws lambda invoke \
  --function-name bedrock-chat-app-dev \
  --payload '{"httpMethod": "POST", "path": "/chat", "headers": {"Content-Type": "application/json"}, "body": "{\"message\": \"test\"}", "requestContext": {"httpMethod": "POST", "resourcePath": "/chat"}, "multiValueQueryStringParameters": null, "queryStringParameters": null, "pathParameters": null, "stageVariables": null, "multiValueHeaders": {"Content-Type": ["application/json"]}}' \
  --cli-binary-format raw-in-base64-out \
  output.json && cat output.json
```

### Production curl Test

```bash
curl -X POST https://zu8schqs01.execute-api.us-east-1.amazonaws.com/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "your test question here"}'
```
