import sqlite3
import json
import boto3
import numpy as np
import os

S3_BUCKET = "vector-bucket-eliot-pitman"
REGION = "us-east-1"
DB_PATH = "vector_store.db"
KNOWLEDGE_BASE_DIR = "knowledge_base"

bedrock = boto3.client("bedrock-runtime", region_name=REGION)

def embed(text):
    response = bedrock.invoke_model(
        modelId="amazon.titan-embed-text-v2:0",
        body=json.dumps({"inputText": text})
    )
    return json.loads(response["body"].read())["embedding"]

def chunk_text(text, chunk_size=500, overlap=50):
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i:i + chunk_size])
        if chunk:
            chunks.append(chunk)
    return chunks

def build():
    # Remove old db if exists
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE embeddings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT,
            chunk_text TEXT,
            embedding TEXT
        )
    """)

    files = [f for f in os.listdir(KNOWLEDGE_BASE_DIR) if f.endswith(".txt")]
    
    if not files:
        print("No .txt files found in knowledge_base/")
        return

    for filename in files:
        path = os.path.join(KNOWLEDGE_BASE_DIR, filename)
        print(f"Processing {filename}...")
        
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()

        chunks = chunk_text(text)
        print(f"  {len(chunks)} chunks found")

        for i, chunk in enumerate(chunks):
            vec = embed(chunk)
            conn.execute(
                "INSERT INTO embeddings (source, chunk_text, embedding) VALUES (?, ?, ?)",
                (filename, chunk, json.dumps(vec))
            )
            print(f"  Embedded chunk {i + 1}/{len(chunks)}")

        conn.commit()

    conn.close()
    print(f"\nSQLite db built successfully.")

    # Upload to S3
    print(f"Uploading to s3://{S3_BUCKET}/vector_store.db ...")
    boto3.client("s3").upload_file(DB_PATH, S3_BUCKET, "vector_store.db")
    print("Done!")

if __name__ == "__main__":
    build()