import os
import pandas as pd
from sqlalchemy import create_engine

def load_to_postgres(df: pd.DataFrame):
    # Database URL pointing to our Docker PostgreSQL instance
    db_url = os.getenv("DATABASE_URL", "postgresql+psycopg2://airflow:airflow@postgres:5432/pricedb")
    engine = create_engine(db_url)
    
    # Append price records to historical table
    df.to_sql('price_history', engine, if_exists='append', index=False)
    print(f"Successfully loaded {len(df)} records into PostgreSQL price_history.")