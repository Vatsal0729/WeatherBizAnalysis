import os
import pandas as pd
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REAL_DATA_DIR = os.path.join(BASE_DIR, "data", "real")

REAL_BUSINESS_CATALOG = {
    "nyc_taxi": {
        "key": "nyc_taxi",
        "name": "NYC Yellow Taxi & Rideshare Fleet",
        "clean_name": "NYC Yellow Taxi & Rideshare",
        "cadence": "hourly",
        "cadence_label": "Hourly & Daily Operations",
        "category": "Urban Mobility",
        "source": "NYC TLC Official Trip Records (OpenData)",
        "color": "#00E676",  # High-Vis Emerald Green
        "symbol": "circle",
        "base_daily_rev": 138000.0,
        "base_hourly_rev": 5750.0,
        "rain_elasticity": 0.042,
        "snow_elasticity": -0.075,
        "temp_elasticity": -0.012,
        "metric_name": "Gross Trip Fares ($ USD)",
        "unit": "USD",
        "summary": "Real-time municipal taxi hail trip records tracking hourly passenger fares, congestion surcharges, and driver tipping patterns during rain events.",
        "data_file": os.path.join(REAL_DATA_DIR, "nyc_taxi_hourly.parquet")
    },
    "citibike_nyc": {
        "key": "citibike_nyc",
        "name": "Citi Bike NYC Micromobility",
        "clean_name": "Citi Bike NYC Micromobility",
        "cadence": "daily",
        "cadence_label": "Daily Ride Volume & Fares",
        "category": "Micromobility",
        "source": "Citi Bike System Records (NYC S3)",
        "color": "#38BDF8",  # Electric Cyan
        "symbol": "diamond",
        "base_daily_rev": 6200.0,
        "base_hourly_rev": 260.0,
        "rain_elasticity": -0.085,
        "snow_elasticity": -0.160,
        "temp_elasticity": 0.035,
        "metric_name": "Daily Ride Revenue ($)",
        "unit": "USD",
        "summary": "Public urban bike-share station checkouts showing sharp demand drop during precipitation and peak ridership during mild 20°C–24°C temperatures.",
        "data_file": os.path.join(REAL_DATA_DIR, "citibike_daily.parquet")
    },
    "online_retail": {
        "key": "online_retail",
        "name": "E-Commerce & Online Retail Store",
        "clean_name": "E-Commerce & Online Retail Store",
        "cadence": "daily",
        "cadence_label": "Daily Commercial Orders",
        "category": "Commercial Retail",
        "source": "UCI Machine Learning Repository",
        "color": "#B388FF",  # Lavender Purple
        "symbol": "square",
        "base_daily_rev": 46500.0,
        "base_hourly_rev": 1940.0,
        "rain_elasticity": 0.024,
        "snow_elasticity": 0.055,
        "temp_elasticity": -0.018,
        "metric_name": "Invoice Revenue ($)",
        "unit": "USD",
        "summary": "Transaction-level digital invoices and merchandise orders showing indoor spending acceleration on wet and cold weekdays.",
        "data_file": os.path.join(REAL_DATA_DIR, "online_retail_daily.parquet")
    },
    "chipotle_sec": {
        "key": "chipotle_sec",
        "name": "Chipotle Mexican Grill (SEC 10-Q)",
        "clean_name": "Chipotle Mexican Grill (SEC 10-Q)",
        "cadence": "quarterly",
        "cadence_label": "Quarterly Financial Statements",
        "category": "Public Fast-Casual Chain",
        "source": "U.S. SEC EDGAR 10-Q Filings",
        "color": "#F59E0B",  # Amber Gold
        "symbol": "star",
        "base_daily_rev": 31500000.0,
        "base_hourly_rev": 1312500.0,
        "rain_elasticity": -0.015,
        "snow_elasticity": -0.045,
        "temp_elasticity": 0.008,
        "metric_name": "Quarterly Net Revenue ($)",
        "unit": "USD",
        "summary": "Official SEC 10-Q quarterly reports showing macroeconomic weather headwinds and seasonal winter foot traffic variations across multi-billion dollar corporate filings.",
        "data_file": os.path.join(REAL_DATA_DIR, "sec_quarterly_restaurants.parquet")
    }
}

# Cache for loaded real datasets
_LOADED_DATA = {}

def get_real_catalog():
    """Returns the metadata catalog for the 4 real-world businesses."""
    return REAL_BUSINESS_CATALOG

def load_real_dataset(b_key: str) -> pd.DataFrame:
    """Loads and caches the cleaned real dataset for the requested business."""
    if b_key in _LOADED_DATA:
        return _LOADED_DATA[b_key]
    
    cfg = REAL_BUSINESS_CATALOG.get(b_key)
    if not cfg:
        return pd.DataFrame()
    
    file_path = cfg["data_file"]
    if not os.path.exists(file_path):
        return pd.DataFrame()
        
    df = pd.read_parquet(file_path)
    _LOADED_DATA[b_key] = df
    return df
