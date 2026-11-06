import pandas as pd
import re


def clean_and_normalize(raw_data, source_name: str) -> pd.DataFrame:
    if isinstance(raw_data, dict) and source_name == "dummyjson":
        raw_data = raw_data.get("products", [])

    df = pd.DataFrame(raw_data)
    if df.empty:
        return pd.DataFrame(columns=[
            "source_product_id", "source_name", "title", "brand",
            "category", "price",
        ])

    df = df.rename(columns={
        "id": "source_product_id",
        "title": "title",
        "price": "price",
        "category": "category",
    })
    if source_name == "fakestore":
        df["brand"] = "Generic"

    df["title"] = df["title"].astype(str).str.strip().str.lower()
    df["title"] = df["title"].apply(lambda value: re.sub(r"[^a-z0-9\s]", "", value))
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df["brand"] = df.get("brand", "Unknown").fillna("Unknown")
    df["source_name"] = source_name
    return df[["source_product_id", "source_name", "title", "brand", "category", "price"]]
