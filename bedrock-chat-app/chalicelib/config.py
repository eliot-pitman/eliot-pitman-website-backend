"""
Configuration settings for the Bedrock chat application.
Update these values as needed for different deployments.
"""

import os

# AWS Configuration
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')
AWS_ACCOUNT_ID = os.environ.get('AWS_ACCOUNT_ID', '491891987197')

# Knowledge Base Configuration
KNOWLEDGE_BASE_ID = os.environ.get('KNOWLEDGE_BASE_ID', 'GNWDQH0467')

# Model Configuration
MODEL_ID = os.environ.get(
    'MODEL_ID',
    f'arn:aws:bedrock:us-east-1:{AWS_ACCOUNT_ID}:inference-profile/us.deepseek.r1-v1:0'
)

# Inference Configuration
TEMPERATURE = float(os.environ.get('TEMPERATURE', '1'))
TOP_P = float(os.environ.get('TOP_P', '1'))
MAX_TOKENS = int(os.environ.get('MAX_TOKENS', '2048'))
LATENCY = os.environ.get('LATENCY', 'standard')

# Retrieval Configuration
NUM_RETRIEVAL_RESULTS = int(os.environ.get('NUM_RETRIEVAL_RESULTS', '5'))

# Stop Sequences
STOP_SEQUENCES = ['\nObservation']
