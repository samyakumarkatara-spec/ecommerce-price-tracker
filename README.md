# E-commerce Price Tracker

A Docker-based data platform that ingests product data from public e-commerce APIs, normalizes it with Pandas, stores raw files in MinIO (AWS S3-compatible object storage), maintains historical prices in PostgreSQL, generates reports, and orchestrates the workflow with Apache Airflow.

## Architecture

```text
Public APIs
    |
    v
Apache Airflow
    |
    +--> MinIO / S3: raw JSON and reports
    |
    +--> Pandas: cleaning and normalization
    |
    v
PostgreSQL: daily price history
    |
    v
Streamlit dashboard
```

## Services

| Service | URL | Purpose |
|---|---|---|
| Airflow | http://localhost:8080 | Workflow orchestration |
| MinIO Console | http://localhost:9001 | Object storage |
| MinIO API | http://localhost:9000 | S3-compatible endpoint |
| Streamlit Dashboard | http://localhost:8501 | Data visualization |
| PostgreSQL | localhost:5432 | Historical price database |

## Local Credentials

These credentials are for the local Docker development environment only. Do not use them in production.

### Airflow

- Username: `admin`
- Password: `admin`

### MinIO

- Username: `admin`
- Password: `password123`
- S3 endpoint: `http://localhost:9000`

### PostgreSQL

- Host: `localhost`
- Port: `5432`
- Database: `pricedb`
- Username: `airflow`
- Password: `airflow`

## Prerequisites

- Docker Desktop
- Docker Compose
- Internet access for the public APIs and initial image downloads

## Setup

1. Clone the repository and enter the project directory:

   ```bash
   git clone <repository-url>
   cd ecommerce-price-tracker
   ```

2. Start all services:

   ```bash
   docker compose up -d
   ```

3. Verify that the containers are running:

   ```bash
   docker compose ps
   ```

4. Open Airflow at http://localhost:8080 and sign in with the credentials above.

5. Enable and trigger the `ecommerce_price_tracker` DAG.

6. Open the dashboard at http://localhost:8501.

## MinIO Buckets

The pipeline uses:

- `raw-zone` — raw API response JSON
- `reports` — generated daily JSON and CSV reports

Both buckets are created automatically when required.

## Pipeline Tasks

The `ecommerce_price_tracker` DAG runs daily and performs these steps:

1. `fetch_and_store_apis` — collects product data and stores raw responses in MinIO.
2. `process_and_load_db` — cleans, normalizes, and upserts daily records in PostgreSQL.
3. `monitor_data_quality` — checks for duplicate snapshots and invalid prices.
4. `generate_daily_report` — writes summary and price-fluctuation reports to MinIO.

## Useful Commands

Start or restart the stack:

```bash
docker compose up -d
```

Check service status:

```bash
docker compose ps
```

Inspect Airflow task states:

```bash
docker exec airflow_scheduler airflow dags list-runs -d ecommerce_price_tracker
docker exec airflow_scheduler airflow tasks states-for-dag-run ecommerce_price_tracker <run-id>
```

Query the PostgreSQL table:

```bash
docker exec postgres_db psql -U airflow -d pricedb -c "SELECT * FROM price_history LIMIT 20;"
```

View dashboard logs:

```bash
docker logs -f price_dashboard
```

Stop the stack:

```bash
docker compose down
```

Remove containers and persistent data volumes:

```bash
docker compose down -v
```

## Dataset Sources

The pipeline currently consumes public product data from:

- Fake Store API
- DummyJSON

Ensure that your use of each API complies with its published terms and permitted-use policy.

## Project Structure

```text
.
├── docker-compose.yml
├── dashboard.py
└── src
    └── ingestion
        ├── api_fetcher.py
        ├── processing
        ├── storage
        ├── reporting.py
        └── dags
            └── price_tracker_pipeline.py
```

## Security

Replace all development passwords before deploying outside a local environment. Prefer Docker secrets or an environment file excluded from Git. Do not expose PostgreSQL, MinIO, or Airflow ports to the public internet without authentication, TLS, and firewall controls.
