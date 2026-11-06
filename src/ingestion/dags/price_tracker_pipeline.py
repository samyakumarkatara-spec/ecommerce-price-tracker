from datetime import datetime, timedelta
import json

import boto3
import pandas as pd
from airflow import DAG
from airflow.operators.python import PythonOperator

from src.ingestion.api_fetcher import fetch_and_store_apis
from src.ingestion.processing.processor import clean_and_normalize
from src.ingestion.storage.loader import load_to_postgres
from src.ingestion.reporting import generate_daily_report


def process_and_load_db():
    s3 = boto3.client(
        "s3",
        endpoint_url="http://minio:9000",
        aws_access_key_id="admin",
        aws_secret_access_key="password123",
        region_name="us-east-1",
    )

    items = s3.list_objects_v2(Bucket="raw-zone").get("Contents", [])
    latest_by_source = {}
    for item in items:
        key = item["Key"]
        parts = key.split("/")
        if len(parts) != 3:
            continue
        source_name = parts[1]
        latest_by_source[source_name] = max(
            latest_by_source.get(source_name, {"Key": ""}), item, key=lambda value: value["Key"]
        )

    all_products = []
    for source_name, item in latest_by_source.items():
        response = s3.get_object(Bucket="raw-zone", Key=item["Key"])
        payload = json.loads(response["Body"].read())
        if isinstance(payload, dict) and source_name == "dummyjson":
            payload = payload.get("products", [])
        all_products.append(clean_and_normalize(payload, source_name))

    if not all_products:
        print("No raw objects found in MinIO.")
        return

    load_to_postgres(pd.concat(all_products, ignore_index=True))


def dummy_processing_task():
    process_and_load_db()


def monitor_data_quality():
    db_url = "postgresql+psycopg2://airflow:airflow@postgres:5432/pricedb"
    from sqlalchemy import create_engine, text

    engine = create_engine(db_url)
    with engine.connect() as connection:
        total = connection.execute(text("SELECT COUNT(*) FROM price_history")).scalar_one()
        duplicates = connection.execute(text("""
            SELECT COUNT(*) FROM (
                SELECT source_name, source_product_id, snapshot_date, COUNT(*)
                FROM price_history
                GROUP BY source_name, source_product_id, snapshot_date
                HAVING COUNT(*) > 1
            ) duplicates
        """)).scalar_one()
        invalid_prices = connection.execute(text("""
            SELECT COUNT(*) FROM price_history WHERE price IS NULL OR price < 0
        """)).scalar_one()

    print(f"Data quality: rows={total}, duplicates={duplicates}, invalid_prices={invalid_prices}")
    if duplicates or invalid_prices:
        raise ValueError("Price history data-quality checks failed")


default_args = {
    "owner": "data_engineer",
    "depends_on_past": False,
    "start_date": datetime(2026, 1, 1),
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    "ecommerce_price_tracker",
    default_args=default_args,
    description="Automated pipeline for collecting and tracking e-commerce prices",
    schedule_interval="@daily",
    catchup=False,
) as dag:
    ingest_task = PythonOperator(
        task_id="fetch_and_store_apis",
        python_callable=fetch_and_store_apis,
    )
    process_task = PythonOperator(
        task_id="process_and_load_db",
        python_callable=process_and_load_db,
    )
    data_quality_task = PythonOperator(
        task_id="monitor_data_quality",
        python_callable=monitor_data_quality,
    )
    report_task = PythonOperator(
        task_id="generate_daily_report",
        python_callable=generate_daily_report,
    )
    ingest_task >> process_task >> data_quality_task >> report_task