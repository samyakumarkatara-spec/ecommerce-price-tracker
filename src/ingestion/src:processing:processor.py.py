
import pandas as pd
import re
from rapidfuzz import fuzz, process

def clean_and_normalize(raw_data: list, source_name: str) -> pd.DataFrame:
    df = pd.DataFrame(raw_data)
    
    # Handle different key names depending on the API source
    if source_name == "fakestore":
        df = df.rename(columns={'id': 'source_product_id', 'title': 'title', 'price': 'price', 'category': 'category'})
        df['brand'] = 'Generic'
    elif source_name == "dummyjson":
        # DummyJSON returns nested lists/dictionaries sometimes, structure accordingly
        df = df.rename(columns={'id': 'source_product_id', 'title': 'title', 'price': 'price', 'category': 'category', 'brand': 'brand'})
    
    # Cleaning text and prices
    df['title'] = df['title'].astype(str).str.strip().str.lower()
    df['title'] = df['title'].apply(lambda x: re.sub(r'[^a-z0-9\s]', '', str(x)))
    df['price'] = pd.to_numeric(df['price'], errors='coerce')
    df['brand'] = df['brand'].fillna('Unknown')
    df['source_name'] = source_name
    
    return df[['source_product_id', 'source_name', 'title', 'brand', 'category', 'price']]

def match_master_product(incoming_title: str, master_titles: list, threshold: int = 85) -> str:
    """Matches incoming product title against existing master catalog titles using fuzzy logic."""
    if not master_titles:
        return incoming_title
    match = process.extractOne(incoming_title, master_titles, scorer=fuzz.token_set_ratio)
    if match and match[1] >= threshold:
        return match[0]
    return incoming_title