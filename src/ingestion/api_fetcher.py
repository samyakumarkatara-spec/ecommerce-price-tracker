import json
import boto3
import requests
from datetime import datetime, timezone

def fetch_and_store_apis():
    endpoints = {
        "fakestore": "https://fakestoreapi.com/products",
        "dummyjson": "https://dummyjson.com/products?limit=50"
    }
    
    # S3 / MinIO client setup (pointing to local Docker container)
    s3 = boto3.client(
        's3',
        endpoint_url='http://minio:9000',
        aws_access_key_id='admin',
        aws_secret_access_key='password123'
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