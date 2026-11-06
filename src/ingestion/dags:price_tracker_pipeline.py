from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator

# Import custom python modules
from src.ingestion.api_fetcher import fetch_and_store_apis

default_args = {
    'owner': 'data_engineer',
    'depends_on_past': False,
    'start_date': datetime(2026, 1, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

def dummy_processing_task():
    print("Processing raw data from S3, cleaning, and writing to Postgres...")

with DAG(
    'ecommerce_price_tracker',
    default_args=default_args,
    description='Automated pipeline for collecting and tracking e-commerce prices',
    schedule_interval='@daily',
    catchup=False,
) as dag:

    ingest_task = PythonOperator(
        task_id='fetch_and_store_apis',
        python_callable=fetch_and_store_apis,
    )

    process_task = PythonOperator(
        task_id='process_and_load_db',
        python_callable=dummy_processing_task,
    )

    ingest_task >> process_task