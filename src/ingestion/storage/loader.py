import os

import pandas as pd
from sqlalchemy import create_engine, text


def load_to_postgres(df: pd.DataFrame):
    db_url = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://airflow:airflow@postgres:5432/pricedb",
    )
    engine = create_engine(db_url)

    with engine.begin() as connection:
        connection.execute(text("""
            ALTER TABLE price_history
            ADD COLUMN IF NOT EXISTS snapshot_date DATE DEFAULT CURRENT_DATE
        """))
        connection.execute(text("""
            ALTER TABLE price_history
            ADD COLUMN IF NOT EXISTS observed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        """))
        connection.execute(text("""
            WITH ranked AS (
                SELECT ctid, ROW_NUMBER() OVER (
                    PARTITION BY source_name, source_product_id, snapshot_date
                    ORDER BY observed_at DESC NULLS LAST, ctid DESC
                ) AS row_number
                FROM price_history
            )
            DELETE FROM price_history
            WHERE ctid IN (SELECT ctid FROM ranked WHERE row_number > 1)
        """))
        connection.execute(text("""
            CREATE UNIQUE INDEX IF NOT EXISTS uq_price_daily
            ON price_history (source_name, source_product_id, snapshot_date)
        """))

    records = df.copy()
    records["snapshot_date"] = pd.Timestamp.now(tz="UTC").date()
    records["observed_at"] = pd.Timestamp.now(tz="UTC")
    records = records.where(pd.notna(records), None)

    with engine.begin() as connection:
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS price_history (
                source_product_id TEXT,
                source_name TEXT,
                title TEXT,
                brand TEXT,
                category TEXT,
                price NUMERIC,
                snapshot_date DATE DEFAULT CURRENT_DATE,
                observed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))

        for record in records.to_dict(orient="records"):
            connection.execute(text("""
                INSERT INTO price_history
                    (source_product_id, source_name, title, brand, category, price,
                     snapshot_date, observed_at)
                VALUES
                    (:source_product_id, :source_name, :title, :brand, :category, :price,
                     :snapshot_date, :observed_at)
                ON CONFLICT (source_name, source_product_id, snapshot_date)
                DO UPDATE SET
                    title = EXCLUDED.title,
                    brand = EXCLUDED.brand,
                    category = EXCLUDED.category,
                    price = EXCLUDED.price,
                    observed_at = EXCLUDED.observed_at
            """), record)

    print(f"Upserted {len(records)} daily product-price records into PostgreSQL.")