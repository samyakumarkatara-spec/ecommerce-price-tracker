import os

import pandas as pd
import streamlit as st
from sqlalchemy import create_engine


st.set_page_config(page_title="E-commerce Price Tracker", layout="wide")
st.title("E-commerce Price Tracker")

DB_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://airflow:airflow@localhost:5432/pricedb",
).replace("postgresql://", "postgresql+psycopg2://")
engine = create_engine(DB_URL)
prices = pd.read_sql("SELECT * FROM price_history ORDER BY snapshot_date DESC", engine)

if prices.empty:
    st.info("No price data is available yet.")
    st.stop()

prices["snapshot_date"] = pd.to_datetime(prices["snapshot_date"])
prices["source_name"] = prices["source_name"].astype(str)
prices["category"] = prices["category"].astype(str)

st.sidebar.header("Filters")
sources = st.sidebar.multiselect("Sources", sorted(prices["source_name"].unique()), default=sorted(prices["source_name"].unique()))
categories = st.sidebar.multiselect("Categories", sorted(prices["category"].unique()))
filtered = prices[prices["source_name"].isin(sources)]
if categories:
    filtered = filtered[filtered["category"].isin(categories)]

col1, col2, col3 = st.columns(3)
col1.metric("Price Records", len(filtered))
col2.metric("Products", filtered[["source_name", "source_product_id"]].drop_duplicates().shape[0])
col3.metric("Average Price", f"{filtered['price'].mean():.2f}")

st.subheader("Daily Average Price by Source")
daily = filtered.groupby(["snapshot_date", "source_name"], as_index=False)["price"].mean()
st.line_chart(daily, x="snapshot_date", y="price", color="source_name")

st.subheader("Price History")
st.dataframe(filtered.sort_values(["snapshot_date", "source_name", "title"], ascending=[False, True, True]), use_container_width=True)
