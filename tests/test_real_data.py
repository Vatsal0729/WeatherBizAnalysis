import os
import sys
import pytest
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.real_data_manager import REAL_BUSINESS_CATALOG, get_real_catalog, load_real_dataset

def test_real_catalog_contents():
    cat = get_real_catalog()
    assert "nyc_taxi" in cat
    assert "citibike_nyc" in cat
    assert "online_retail" in cat
    assert "chipotle_sec" in cat

def test_nyc_taxi_dataset():
    df = load_real_dataset("nyc_taxi")
    assert not df.empty
    assert "hour" in df.columns
    assert "trip_count" in df.columns
    assert "total_revenue" in df.columns
    assert len(df) >= 700

def test_citibike_dataset():
    df = load_real_dataset("citibike_nyc")
    assert not df.empty
    assert "date" in df.columns
    assert "total_rides" in df.columns
    assert "estimated_revenue_usd" in df.columns
    assert len(df) >= 100

def test_online_retail_dataset():
    df = load_real_dataset("online_retail")
    assert not df.empty
    assert "date" in df.columns
    assert "daily_revenue" in df.columns
    assert "order_count" in df.columns
    assert len(df) >= 300

def test_chipotle_sec_dataset():
    df = load_real_dataset("chipotle_sec")
    assert not df.empty
    assert "end" in df.columns
    assert "quarter_label" in df.columns
    assert "revenue_usd" in df.columns
    assert len(df) >= 20
