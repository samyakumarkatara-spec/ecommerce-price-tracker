import json
import os
from datetime import datetime, timezone

import boto3
import pandas as pd
from sqlalchemy import create_engine


def generate_daily_report():
    db_url = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://airflow:airflow@postgres:5432/pricedb",
    )
    engine = create_engine(db_url)

    summary = pd.read_sql("""
        SELECT source_name, COUNT(*) AS product_count,
               ROUND(AVG(price)::numeric, 2) AS average_price,
               MIN(price) AS minimum_price, MAX(price) AS maximum_price
        FROM price_history
        WHERE snapshot_date = CURRENT_DATE
        GROUP BY source_name
        ORDER BY source_name
    """, engine)

    fluctuations = pd.read_sql("""
        WITH ordered AS (
            SELECT source_name, source_product_id, title, price, snapshot_date,
                   LAG(price) OVER (
                       PARTITION BY source_name, source_product_id
                       ORDER BY snapshot_date
                   ) AS previous_price
            FROM price_history
        )
        SELECT source_name, source_product_id, title, previous_price, price,
               ROUND((price - previous_price)::numeric, 2) AS price_change,
               snapshot_date
        FROM ordered
        WHERE previous_price IS NOT NULL AND price <> previous_price
        ORDER BY ABS(price - previous_price) DESC
        LIMIT 100
    """, engine)

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M-%S")
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": summary.to_dict(orient="records"),
        "price_fluctuations": fluctuations.to_dict(orient="records"),
    }

    s3 = boto3.client(
        "s3",
        endpoint_url=os.getenv("S3_ENDPOINT_URL", "http://minio:9000"),
        aws_access_key_id=os.getenv("MINIO_ROOT_USER", "admin"),
        aws_secret_access_key=os.getenv("MINIO_ROOT_PASSWORD", "password123"),
        region_name="us-east-1",
    )

    try:
        s3.head_bucket(Bucket="reports")
    except Exception:
        s3.create_bucket(Bucket="reports")

    json_key = f"daily/{timestamp}.json"
    csv_key = f"daily/{timestamp}_summary.csv"
    s3.put_object(Bucket="reports", Key=json_key, Body=json.dumps(report, default=str, indent=2))
    s3.put_object(Bucket="reports", Key=csv_key, Body=summary.to_csv(index=False))
    print(f"Generated report: s3://reports/{json_key}")
    return report
