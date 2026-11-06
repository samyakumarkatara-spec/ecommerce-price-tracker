from src.ingestion.processing.processor import clean_and_normalize


def test_fake_store_normalization():
    data = [{
        "id": 1,
        "title": "  Test! Product  ",
        "price": "12.50",
        "category": "electronics",
    }]

    result = clean_and_normalize(data, "fakestore")

    assert result.loc[0, "source_product_id"] == 1
    assert result.loc[0, "source_name"] == "fakestore"
    assert result.loc[0, "title"] == "test product"
    assert result.loc[0, "price"] == 12.50
    assert result.loc[0, "brand"] == "Generic"


def test_invalid_price_is_numeric_nan():
    data = [{"id": 2, "title": "Invalid", "price": "unknown", "category": "other", "brand": "Test"}]

    result = clean_and_normalize(data, "dummyjson")

    assert result["price"].isna().iloc[0]
