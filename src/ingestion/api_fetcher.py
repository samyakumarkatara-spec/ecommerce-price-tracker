import json
import os
import boto3
import requests
from datetime import datetime, timezone

def fetch_and_store_apis():
    endpoints = {
        "fakestore": "https://fakestoreapi.com/products",
        "dummyjson": "https://dummyjson.com/products?limit=50"
    }

    s3 = boto3.client(
        's3',
        endpoint_url=os.getenv('S3_ENDPOINT_URL', 'http://minio:9000'),
        aws_access_key_id=os.getenv('MINIO_ROOT_USER', 'admin'),
        aws_secret_access_key=os.getenv('MINIO_ROOT_PASSWORD', 'password123'),
        region_name='us-east-1'
    )
    
    # Ensure raw-zone bucket exists
    try:
        s3.head_bucket(Bucket='raw-zone')
    except Exception:
        s3.create_bucket(Bucket='raw-zone')
    
    timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d_%H-%M-%S')
    
    for source_name, url in endpoints.items():
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            s3_key = f"raw/{source_name}/{timestamp}.json"
            
            s3.put_object(
                Bucket="raw-zone",
                Key=s3_key,
                Body=json.dumps(data)
            )
            print(f"Successfully ingested from {source_name} to S3 path: {s3_key}")
        else:
            print(f"Failed to fetch from {source_name}, Status: {response.status_code}")