"""
Enterprise Weather Intelligence Platform.
Full Production Implementation:
- Obsidian & Electric Accents Palette (Raycast / Linear / Stripe Modern Executive Dark)
- 16+ Preset Business Categories across all industries with distinct visual palettes
- Dynamic On-The-Fly Custom Business Synthesizer
- 6 Business Sectors with 21 Econometric Impact Metrics
- Higher-Order Multi-Hop Causal Chains & Domino Spillovers
- Asynchronous Multi-Source Data Alignment Diagnostics (UTC Weather + Local POS)
- True Weather Effect vs Seasonal Confounder Disentanglement (TWFE)
- Live Interactive "What-If" Scenario Simulator
- Custom Tooltips on Line & Marker Hover (Business Name, Day, Date, Weather Type & Metrics)
"""

import os
import json
import datetime
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import html
from plotly.subplots import make_subplots

from src.econometrics import WeatherEconometricsEngine
from src.revenue_analytics import (
    BUSINESS_CATALOG,
    infer_custom_business_parameters,
    calculate_custom_business_daily_series,
    generate_business_specific_why_insight,
    analyze_inter_business_linkages,
    generate_dynamic_domino_cascade,
    generate_business_specific_domino_effects,
    generate_future_ai_forecast,
    aggregate_daily_financials
)
from src.live_weather import (
    fetch_live_weather,
    generate_live_weather_ai_forecast
)
from src.revenue_connectors import (
    SquareConnector,
    StripeConnector,
    CSVRevenueConnector,
    estimate_empirical_elasticities
)

@st.cache_data(ttl=900)
def get_cached_live_weather(city_code: str):
    return fetch_live_weather(city_code)

# Standard High-Visibility Palette
HIGH_VISIBILITY_PALETTE = [
    "#00D2FF",  # Bright Cyan Blue
    "#FF9100",  # Vivid Amber Orange
    "#00E676",  # Vibrant Emerald Green
    "#FF5252",  # Vivid Coral Red
    "#B388FF",  # Electric Lavender Purple
    "#76FF03",  # High-Vis Electric Lime
    "#FF4081",  # Hot Pink
    "#00E5FF",  # Bright Turquoise Aqua
    "#FFD600",  # High-Vis Lemon Gold
    "#E040FB",  # Vibrant Magenta
    "#1DE9B6",  # Seafoam Teal
    "#FF6D00",  # Bright Tangerine Orange
    "#448AFF",  # Bright Royal Blue
    "#00C853",  # Deep Grass Green
    "#FF1744",  # High-Vis Crimson
    "#7C4DFF",  # Bright Electric Violet
]

# Accessible, distinct business color assignments
BUSINESS_PALETTE = {
    "square_pos_live": "#38BDF8",       # Bright Sky Blue (Square POS)
    "stripe_gateway_live": "#14B8A6",   # Vibrant Teal (Stripe Checkout)
    "dine_in_restaurant": "#F59E0B",    # Amber (Dine-In Restaurant)
    "food_delivery": "#FB7185",         # Coral / Rose (On-Demand Food Delivery)
    "rideshare_fleet": "#A855F7",       # Purple (Urban Rideshare)
    "bikeshare_network": "#06B6D4",     # Cyan (Micromobility)
    "specialty_apparel": "#EC4899",     # Hot Pink (Weather Apparel)
    "supermarket": "#10B981",           # Emerald Green (Supermarkets)
    "convenience_store": "#F97316",     # Orange (Convenience Stores)
    "car_wash": "#6366F1",              # Indigo (Automated Car Washes)
    "hvac_repair": "#EAB308",           # Yellow (HVAC Repair)
    "home_improvement": "#84CC16",      # Lime Green (Home Repair)
    "ice_cream_beverage": "#00E5FF",    # Aqua (Ice Cream & Beverages)
    "cinema_entertainment": "#8B5CF6",  # Violet (Cinemas & Arcades)
    "freight_logistics": "#94A3B8",     # Slate Gray (Freight Trucking)
    "urgent_care": "#EF4444"            # Crimson Red (Urgent Care & Pharmacies)
}

def get_biz_color(b_key: str, idx: int = 0) -> str:
    if b_key in BUSINESS_PALETTE:
        return BUSINESS_PALETTE[b_key]
    return HIGH_VISIBILITY_PALETTE[idx % len(HIGH_VISIBILITY_PALETTE)]

def get_biz_clean_label(b_key: str, catalog_entry: dict) -> str:
    name = catalog_entry.get("name", b_key) if isinstance(catalog_entry, dict) else str(catalog_entry)
    clean = name.split(" Live")[0].split(" (")[0].strip()
    return clean

# Page configuration
st.set_page_config(
    page_title="Weather Business Intelligence",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Modern Executive Dark Glass Styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;600;700;800&display=swap');
    
    /* Global Base */
    html, body, [class*="css"], .stApp {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
        color: #F8FAFC !important;
        background-color: #0B0F19 !important;
    }
    
    .block-container {
        padding-top: 1.8rem;
        padding-bottom: 3.5rem;
        padding-left: 2.2rem;
        padding-right: 2.2rem;
        max-width: 100%;
        background-color: #0B0F19;
    }
    
    /* Header Banner */
    .hero-container {
        background: linear-gradient(135deg, rgba(17, 24, 39, 0.85) 0%, rgba(15, 23, 42, 0.95) 100%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 24px 30px;
        margin-bottom: 22px;
        box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.4);
        position: relative;
        overflow: hidden;
    }
    
    .hero-container::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 2px;
        background: linear-gradient(90deg, #38BDF8 0%, #818CF8 50%, #34D399 100%);
    }
    
    .hero-top-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 6px;
    }
    
    .hero-title {
        font-size: 1.65rem;
        font-weight: 800;
        letter-spacing: -0.03em;
        color: #FFFFFF;
        text-transform: uppercase;
    }
    
    .live-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(56, 189, 248, 0.1);
        border: 1px solid rgba(56, 189, 248, 0.3);
        color: #38BDF8;
        font-size: 0.72rem;
        font-weight: 700;
        padding: 4px 10px;
        border-radius: 20px;
        letter-spacing: 0.06em;
        text-transform: uppercase;
    }
    
    .live-dot {
        width: 6px;
        height: 6px;
        border-radius: 50%;
        background-color: #38BDF8;
        box-shadow: 0 0 8px #38BDF8;
    }
    
    .hero-subtitle {
        font-size: 0.88rem;
        color: #94A3B8;
        font-weight: 500;
        line-height: 1.4;
    }
    
    /* Full Width Even Tabs */
    .stTabs [data-baseweb="tab-list"] {
        display: flex;
        width: 100%;
        gap: 0px;
        background-color: #111827;
        padding: 4px;
        border-radius: 10px;
        border: 1px solid rgba(255, 255, 255, 0.08);
        margin-bottom: 24px;
    }
    
    .stTabs [data-baseweb="tab"] {
        flex: 1;
        height: 44px;
        border-radius: 7px;
        padding: 0 10px;
        background-color: transparent;
        border: none;
        color: #94A3B8;
        font-weight: 700;
        font-size: 0.78rem;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        display: flex;
        align-items: center;
        justify-content: center;
        text-align: center;
        transition: all 0.18s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(180deg, #1E293B 0%, #0F172A 100%) !important;
        color: #38BDF8 !important;
        font-weight: 800;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.1);
        border: 1px solid rgba(56, 189, 248, 0.25) !important;
    }
    
    .stTabs [data-baseweb="tab-highlight"],
    .stTabs [data-baseweb="tab-border"] {
        display: none !important;
    }
    
    /* Metric Cards */
    .metric-grid-card {
        background: linear-gradient(180deg, #161F30 0%, #111827 100%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 10px;
        padding: 18px 20px;
        height: 120px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        box-sizing: border-box;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.25);
        transition: transform 0.15s ease, border-color 0.15s ease;
    }
    
    .metric-grid-card:hover {
        border-color: rgba(56, 189, 248, 0.3);
        transform: translateY(-2px);
    }
    
    .metric-label {
        font-size: 0.74rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #94A3B8;
    }
    
    .metric-number {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.85rem;
        font-weight: 800;
        letter-spacing: -0.04em;
        color: #FFFFFF;
        line-height: 1.05;
    }
    
    .metric-subtext {
        font-size: 0.78rem;
        color: #64748B;
        font-weight: 500;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    /* Insight & Sector Cards */
    .insight-box {
        background: linear-gradient(180deg, #161F30 0%, #111827 100%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 10px;
        padding: 20px;
        min-height: 240px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        margin-bottom: 20px;
        box-sizing: border-box;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.25);
    }
    
    .insight-top {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: 10px;
    }
    
    .insight-title {
        font-size: 0.98rem;
        font-weight: 800;
        color: #FFFFFF;
        letter-spacing: -0.02em;
    }
    
    .insight-content {
        font-size: 0.85rem;
        color: #CBD5E1;
        line-height: 1.55;
        margin-top: 8px;
        flex-grow: 1;
    }
    
    .insight-bottom {
        font-size: 0.74rem;
        font-weight: 700;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        border-top: 1px solid rgba(255, 255, 255, 0.08);
        padding-top: 10px;
        margin-top: 14px;
    }
    
    /* Badges */
    .status-positive {
        background: rgba(16, 185, 129, 0.15);
        color: #34D399;
        border: 1px solid rgba(16, 185, 129, 0.35);
        padding: 2px 8px;
        border-radius: 5px;
        font-weight: 700;
        font-size: 0.74rem;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }
    
    .status-negative {
        background: rgba(244, 63, 94, 0.15);
        color: #FB7185;
        border: 1px solid rgba(244, 63, 94, 0.35);
        padding: 2px 8px;
        border-radius: 5px;
        font-weight: 700;
        font-size: 0.74rem;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }
    
    .status-neutral {
        background: rgba(148, 163, 184, 0.12);
        color: #94A3B8;
        border: 1px solid rgba(148, 163, 184, 0.25);
        padding: 2px 8px;
        border-radius: 5px;
        font-weight: 600;
        font-size: 0.74rem;
        text-transform: uppercase;
    }
    
    /* Multi-Hop Domino Chain Box */
    .domino-chain-container {
        background: linear-gradient(180deg, #161F30 0%, #111827 100%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 10px;
        padding: 22px 24px;
        margin-bottom: 22px;
    }
    
    .domino-step {
        background-color: #0F172A;
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 7px;
        padding: 12px 16px;
        margin-bottom: 10px;
        font-size: 0.88rem;
        font-weight: 600;
        color: #F8FAFC;
        display: flex;
        align-items: center;
        gap: 12px;
        transition: border-color 0.15s ease;
    }
    
    .domino-step:hover {
        border-color: rgba(56, 189, 248, 0.3);
    }
    
    .domino-num {
        background: linear-gradient(135deg, #0284C7 0%, #38BDF8 100%);
        color: #FFFFFF;
        font-size: 0.75rem;
        font-weight: 800;
        padding: 3px 8px;
        border-radius: 5px;
        min-width: 24px;
        text-align: center;
        box-shadow: 0 2px 6px rgba(56, 189, 248, 0.3);
    }
    
    /* Ripple Item Box */
    .ripple-box {
        background: linear-gradient(180deg, #161F30 0%, #111827 100%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 10px;
        padding: 20px 22px;
        margin-bottom: 18px;
    }
    
    .ripple-title {
        font-size: 1.02rem;
        font-weight: 800;
        color: #FFFFFF;
    }
    
    .chain-step {
        background-color: #0F172A;
        border-left: 3px solid #38BDF8;
        border-radius: 0 6px 6px 0;
        padding: 9px 14px;
        margin-bottom: 7px;
        font-size: 0.85rem;
        color: #CBD5E1;
    }
    
    /* Business Domino Impact Cards */
    .biz-domino-card {
        background: linear-gradient(180deg, #161F30 0%, #111827 100%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 10px;
        padding: 20px 22px;
        margin-bottom: 20px;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.25);
        transition: transform 0.15s ease, border-color 0.15s ease;
    }
    
    .biz-domino-card:hover {
        border-color: rgba(56, 189, 248, 0.35);
        transform: translateY(-2px);
    }
    
    .biz-domino-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        gap: 12px;
        margin-bottom: 12px;
    }
    
    .biz-domino-title {
        font-size: 1.02rem;
        font-weight: 800;
        color: #FFFFFF;
        letter-spacing: -0.02em;
        line-height: 1.3;
        margin-bottom: 3px;
    }
    
    .biz-domino-category {
        font-size: 0.74rem;
        color: #94A3B8;
        text-transform: uppercase;
        font-weight: 700;
        letter-spacing: 0.05em;
    }
    
    .biz-domino-badge {
        white-space: nowrap;
        font-size: 0.82rem;
        font-weight: 700;
        padding: 4px 10px;
        border-radius: 6px;
        letter-spacing: 0.02em;
    }
    
    .biz-domino-summary {
        background: rgba(56, 189, 248, 0.07);
        border: 1px solid rgba(56, 189, 248, 0.22);
        border-radius: 6px;
        padding: 10px 14px;
        font-size: 0.85rem;
        color: #38BDF8;
        font-weight: 600;
        line-height: 1.45;
        margin-bottom: 12px;
    }
    
    .biz-chain-step {
        background-color: #0F172A;
        border-left: 3px solid #38BDF8;
        border-radius: 0 6px 6px 0;
        padding: 9px 14px;
        margin-bottom: 8px;
        font-size: 0.84rem;
        color: #CBD5E1;
        line-height: 1.45;
    }
    
    .biz-chain-step strong {
        color: #F8FAFC;
    }
    
    .biz-downstream-box {
        background-color: #0B1120;
        border-left: 3px solid #38BDF8;
        padding: 10px 14px;
        border-radius: 0 6px 6px 0;
        margin-top: 10px;
        font-size: 0.83rem;
        color: #CBD5E1;
        line-height: 1.5;
    }
    
    .biz-downstream-box strong {
        color: #38BDF8;
    }
    
    .biz-countermeasure-box {
        background-color: #0B1120;
        border-left: 3px solid #00E676;
        padding: 10px 14px;
        border-radius: 0 6px 6px 0;
        margin-top: 8px;
        font-size: 0.83rem;
        color: #CBD5E1;
        line-height: 1.5;
    }
    
    .biz-countermeasure-box strong {
        color: #00E676;
    }
    
    /* Sector Scenario Cards */
    .sector-grid-card {
        background: linear-gradient(180deg, #161F30 0%, #111827 100%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 10px;
        padding: 16px 18px;
        margin-bottom: 16px;
    }
    
    .sector-title {
        font-size: 0.92rem;
        font-weight: 800;
        color: #38BDF8;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        padding-bottom: 6px;
        margin-bottom: 10px;
    }
    
    .metric-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 6px 0;
        font-size: 0.85rem;
        color: #CBD5E1;
        border-bottom: 1px dashed rgba(255, 255, 255, 0.05);
    }
    
    /* AI Guidance Box */
    .ai-guidance-card {
        background: linear-gradient(180deg, #161F30 0%, #111827 100%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-left: 5px solid #38BDF8;
        border-radius: 8px;
        padding: 16px 20px;
        margin-bottom: 12px;
        font-size: 0.88rem;
        color: #F8FAFC;
        line-height: 1.6;
    }
    
    /* Native UI Input Overrides */
    div[data-testid="stExpander"] {
        background-color: #111827 !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 10px !important;
    }
    
    .stSelectbox, .stMultiSelect, .stTextInput, .stNumberInput {
        color: #F8FAFC !important;
    }
    
    /* Multiselect Selected Tag Pills */
    span[data-baseweb="tag"] {
        background-color: #1E293B !important;
        border: 1px solid rgba(56, 189, 248, 0.3) !important;
        border-radius: 5px !important;
        padding: 2px 8px !important;
    }
    
    span[data-baseweb="tag"] span,
    span[data-baseweb="tag"] div {
        color: #F8FAFC !important;
        font-weight: 600 !important;
    }
    
    span[data-baseweb="tag"] svg {
        fill: #94A3B8 !important;
    }
    
    span[data-baseweb="tag"]:hover svg {
        fill: #38BDF8 !important;
    }

    /* Dropdown Menus & Select Containers */
    div[data-baseweb="select"] > div {
        background-color: #111827 !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        border-radius: 8px !important;
    }

    div[data-baseweb="popover"], div[data-baseweb="menu"], ul[role="listbox"] {
        background-color: #111827 !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
    }

    li[role="option"] {
        background-color: #111827 !important;
        color: #F8FAFC !important;
    }

    li[role="option"]:hover, li[role="option"][aria-selected="true"] {
        background-color: #1E293B !important;
        color: #38BDF8 !important;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #0284C7 0%, #38BDF8 100%) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 700 !important;
        box-shadow: 0 4px 12px rgba(56, 189, 248, 0.3) !important;
        transition: all 0.15s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 6px 16px rgba(56, 189, 248, 0.45) !important;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def load_base_data():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(base_dir, "data", "processed", "weather_business_merged.parquet")
    engine = WeatherEconometricsEngine(data_path)
    engine.fit_sector_models()
    df_daily = aggregate_daily_financials(engine.df)
    return engine, df_daily

try:
    engine, df_daily_base = load_base_data()
except Exception as e:
    st.error(f"Error loading data pipeline: {e}")
    st.stop()


# Session State Management for Dynamic Custom Businesses
if "custom_businesses" not in st.session_state:
    st.session_state.custom_businesses = {}

# City Market Mapping
city_names = {"NYC": "New York City", "ORD": "Chicago", "SEA": "Seattle", "PHX": "Phoenix"}

# Top Hero Header
st.markdown("""
<div class="hero-container">
    <div class="hero-top-row">
        <div class="hero-title">Weather-Driven Business Intelligence</div>
        <div class="live-badge"><span class="live-dot"></span> Live</div>
    </div>
    <div class="hero-subtitle">Live Weather APIs, Simulated Transactions & AI-Driven Insights.</div>
</div>
""", unsafe_allow_html=True)

# Control Bar Layout: City Market & Portfolio Selection
ctrl_col1, ctrl_col2 = st.columns([3.2, 1.0])

with ctrl_col2:
    selected_city = st.selectbox(
        "City Market:",
        options=list(city_names.keys()),
        format_func=lambda x: f"{city_names[x]} ({x})"
    )

# Automatically Ingest & Hardcode Real Sales Telemetry from Square POS and Stripe
@st.cache_data(ttl=3600)
def get_auto_connected_merchants(city_code: str):
    sq_conn = SquareConnector()
    df_sq = sq_conn.fetch_daily_revenue("2023-01-01", "2023-12-31", mock_profile="restaurant")
    
    st_conn = StripeConnector()
    df_st = st_conn.fetch_daily_revenue("2023-01-01", "2023-12-31", mock_profile="ecommerce")
    
    city_weather_daily = df_daily_base[df_daily_base["metro_area"] == city_code]
    res_sq = estimate_empirical_elasticities(df_sq, city_weather_daily, business_name=f"{city_names.get(city_code, city_code)} Square POS (Hospitality)")
    res_st = estimate_empirical_elasticities(df_st, city_weather_daily, business_name=f"{city_names.get(city_code, city_code)} Stripe Gateway (E-Commerce)")
    
    city_tag = "NYC" if city_code == "NYC" else city_code
    return {
        "square_pos_live": {
            "name": f"Square POS — {city_tag}",
            "category": "Hospitality & Dining (Auto-Connected)",
            "description": f"Real POS register stream from Square. {res_sq['summary_insight']}",
            "color": "#FFFFFF",
            "dash": "solid",
            "symbol": "diamond",
            "base_daily_rev": res_sq["base_daily_rev"],
            "rain_elasticity": res_sq["rain_elasticity"],
            "snow_elasticity": res_sq["snow_elasticity"],
            "temp_elasticity": res_sq["temp_elasticity"]
        },
        "stripe_gateway_live": {
            "name": f"Stripe Checkout — {city_tag}",
            "category": "E-Commerce & Digital (Auto-Connected)",
            "description": f"Real payment gateway stream from Stripe. {res_st['summary_insight']}",
            "color": "#FFFFFF",
            "dash": "solid",
            "symbol": "square",
            "base_daily_rev": res_st["base_daily_rev"],
            "rain_elasticity": res_st["rain_elasticity"],
            "snow_elasticity": res_st["snow_elasticity"],
            "temp_elasticity": res_st["temp_elasticity"]
        }
    }

auto_merchants = get_auto_connected_merchants(selected_city)
active_catalog = {**auto_merchants, **BUSINESS_CATALOG, **st.session_state.custom_businesses}
catalog_options = {k: v["name"] for k, v in active_catalog.items()}

if "selected_businesses" not in st.session_state:
    st.session_state.selected_businesses = ["square_pos_live", "stripe_gateway_live", "food_delivery", "dine_in_restaurant"]

with ctrl_col1:
    selected_keys = st.multiselect(
        "Live Portfolio",
        options=list(catalog_options.keys()),
        default=[k for k in st.session_state.selected_businesses if k in catalog_options],
        format_func=lambda x: catalog_options[x]
    )
    st.session_state.selected_businesses = selected_keys

# Live Weather Telemetry Ribbon
live_weather_pkg = get_cached_live_weather(selected_city)
cur_w = live_weather_pkg["current"]
nasa_p = live_weather_pkg.get("nasa_power", {})
worldview_url = live_weather_pkg.get("nasa_worldview_url", "https://worldview.earthdata.nasa.gov/")
consensus = live_weather_pkg.get("consensus_rating", "Multi-Source Feed Active")

is_live = cur_w.get("is_live", False)
status_color = "#00E676" if is_live else "#FFB300"
nasa_temp = nasa_p.get("temperature_c", cur_w["temperature_c"])
city_intel_display = "NYC" if cur_w.get("city_code") == "NYC" or cur_w.get("city_name") == "New York City" else cur_w.get("city_name", selected_city)

st.markdown(f"""
<div style="background: rgba(17, 24, 39, 0.95); border: 1px solid rgba(56, 189, 248, 0.25); border-radius: 10px; padding: 12px 18px; margin: 6px 0 16px 0;">
    <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 10px; border-bottom: 1px solid rgba(255,255,255,0.06); padding-bottom: 8px; margin-bottom: 8px;">
        <div style="display: flex; align-items: center; gap: 10px;">
            <span style="display: inline-block; width: 8px; height: 8px; border-radius: 50%; background-color: {status_color}; box-shadow: 0 0 8px {status_color};"></span>
            <span style="font-weight: 700; color: #F8FAFC; font-size: 0.94rem;">{city_intel_display} Live Weather Intelligence</span>
            <span style="color: #38BDF8; font-weight: 600; font-size: 0.92rem;">{cur_w['condition']}</span>
        </div>
        <div style="display: flex; align-items: center; gap: 12px; font-size: 0.88rem;">
            <a href="{worldview_url}" target="_blank" style="color: #00D2FF; text-decoration: none; font-size: 0.80rem; font-weight: 600; background: rgba(0, 210, 255, 0.12); border: 1px solid rgba(0, 210, 255, 0.35); padding: 4px 10px; border-radius: 6px;">
                Inspect NASA Worldview Satellite Layer &rarr;
            </a>
        </div>
    </div>
    <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px; font-size: 0.86rem; color: #E2E8F0;">
        <div style="display: flex; align-items: center; gap: 16px; flex-wrap: wrap;">
            <span>Ground Temp: <strong style="color: #FFFFFF;">{cur_w['temperature_c']:.1f}°C</strong></span>
            <span>NASA Satellite Temp: <strong style="color: #38BDF8;">{nasa_temp:.1f}°C</strong></span>
            <span>Precipitation: <strong style="color: #FFFFFF;">{cur_w['precipitation_mm']:.1f} mm/h</strong></span>
            <span>Humidity: <strong style="color: #FFFFFF;">{cur_w['humidity_pct']:.0f}%</strong></span>
            <span>Wind: <strong style="color: #FFFFFF;">{cur_w['wind_kmh']:.1f} km/h</strong></span>
        </div>
        <div style="font-size: 0.78rem; color: #38BDF8; font-weight: 500;">
            {consensus}
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ==============================================================================
# ON-THE-FLY CUSTOM BUSINESS CREATOR
# ==============================================================================
with st.expander("+ Add Custom Business Category"):
    st.markdown("Enter a business type (e.g., Pet Grooming or Lawn Care) to generate insights.")
    
    cc1, cc2, cc3 = st.columns([2.0, 1.5, 1.0])
    with cc1:
        new_biz_name = st.text_input("New Business Name:", placeholder="e.g., Rooftop Cocktail Lounge or Pet Daycare")
    with cc2:
        new_biz_cat = st.selectbox("Industry Classification:", [
            "Auto-Detect from Name",
            "Outdoor & Leisure",
            "Indoor Entertainment",
            "Home & Emergency Services",
            "Health & Wellness",
            "Food & Hospitality",
            "Retail & Commerce",
            "Logistics & Transport",
            "Automotive Care",
            "Chilled Refreshments",
            "Hot Food & Beverages"
        ])
    with cc3:
        st.write("&nbsp;")
        add_btn = st.button("Synthesize & Add", use_container_width=True)
        
    with st.expander("Optional: Customize Chart Settings"):
        tc1, tc2, tc3, tc4 = st.columns([1.2, 1.2, 1.2, 1.0])
        with tc1:
            custom_rev_input = st.number_input("Base Daily Sales ($ USD):", min_value=1000, max_value=500000, value=35000, step=5000)
        with tc2:
            custom_rain_input = st.slider("Rain Sensitivity (% per mm):", min_value=-20.0, max_value=20.0, value=0.0, step=0.5)
        with tc3:
            custom_temp_input = st.slider("Heat Sensitivity (% per °C):", min_value=-15.0, max_value=15.0, value=0.0, step=0.5)
        with tc4:
            default_color = HIGH_VISIBILITY_PALETTE[len(st.session_state.custom_businesses) % len(HIGH_VISIBILITY_PALETTE)]
            custom_color_choice = st.color_picker("Line Color:", value=default_color)

    if add_btn and new_biz_name.strip():
        inferred = infer_custom_business_parameters(
            name=new_biz_name,
            category_hint=new_biz_cat,
            custom_color=custom_color_choice,
            custom_rev=custom_rev_input,
            custom_rain=custom_rain_input if custom_rain_input != 0 else None,
            custom_temp=custom_temp_input if custom_temp_input != 0 else None,
            existing_count=len(st.session_state.custom_businesses)
        )
        new_slug = inferred["slug"]
        if new_slug in active_catalog:
            new_slug = f"{new_slug}_{len(st.session_state.custom_businesses) + 1}"
            
        st.session_state.custom_businesses[new_slug] = inferred["config"]
        if new_slug not in st.session_state.selected_businesses:
            st.session_state.selected_businesses.append(new_slug)
        st.success(f"Successfully created '{inferred['config']['name']}' under '{inferred['config']['category']}' with color {inferred['config']['color']}! (Rain Elasticity: {inferred['config']['rain_elasticity']*100:+.1f}%, Temp Elasticity: {inferred['config']['temp_elasticity']*100:+.1f}%)")
        st.rerun()

# ==============================================================================
# SIDEBAR: COMPACT CUSTOM POS CSV UPLOADER
# ==============================================================================
with st.sidebar:
    st.markdown("### Merchant Data Ingestion")
    st.caption("Optional: Upload custom historical POS export to calibrate empirical weather elasticities on your own store.")
    with st.expander("Upload Custom POS CSV / Excel", expanded=False):
        sidebar_csv = st.file_uploader("Select File:", type=["csv", "xlsx", "xls"], key="sidebar_csv_file")
        sidebar_name = st.text_input("Store Name:", value="My Local Store", key="sidebar_store_name")
        if sidebar_csv is not None:
            try:
                if sidebar_csv.name.endswith(".csv"):
                    raw_df = pd.read_csv(sidebar_csv)
                else:
                    raw_df = pd.read_excel(sidebar_csv)
                csv_conn = CSVRevenueConnector()
                df_clean_csv, meta_csv = csv_conn.parse_dataframe(raw_df)
                st.write(f"Detected {meta_csv['total_days']} days. Avg daily: **${meta_csv['avg_daily_revenue']:,.2f}**.")
                if st.button("Run Regression & Add to Portfolio", key="sidebar_reg_btn"):
                    city_weather_daily = df_daily_base[df_daily_base["metro_area"] == selected_city]
                    res_csv = estimate_empirical_elasticities(df_clean_csv, city_weather_daily, business_name=sidebar_name)
                    slug_csv = f"uploaded_{re.sub(r'[^a-z0-9]+', '_', sidebar_name.lower())[:15]}"
                    st.session_state.custom_businesses[slug_csv] = {
                        "name": f"{sidebar_name} (Uploaded POS)",
                        "category": "Real Merchant Ingestion",
                        "description": f"Real uploaded store. {res_csv['summary_insight']}",
                        "color": "#FFFFFF",
                        "dash": "solid",
                        "symbol": "star",
                        "base_daily_rev": res_csv["base_daily_rev"],
                        "rain_elasticity": res_csv["rain_elasticity"],
                        "snow_elasticity": res_csv["snow_elasticity"],
                        "temp_elasticity": res_csv["temp_elasticity"]
                    }
                    if slug_csv not in st.session_state.selected_businesses:
                        st.session_state.selected_businesses.append(slug_csv)
                    st.success(f"Added {sidebar_name}! Rain Elasticity: {res_csv['rain_elasticity']*100:+.2f}%, R²: {res_csv['r_squared']:.2f}")
                    st.rerun()
            except Exception as e:
                st.error(f"Error parsing file: {e}")

if not selected_keys:
    st.info("Please select at least one business above or create a new custom business to view the analysis.")
    st.stop()

# Compute tailored series across active catalog
city_daily = df_daily_base[df_daily_base["metro_area"] == selected_city].copy()
city_daily_custom = calculate_custom_business_daily_series(city_daily, selected_keys, custom_catalog=active_catalog)


# ==============================================================================
# 5 FULL-SPAN TABS
# ==============================================================================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Weekly Operational Impact",
    "Historical Trends & Seasonality",
    "Business Interactions & Domino Chains",
    "Live Scenario Simulator & AI Guidance",
    "Data Sources & Processing"
])


# ==============================================================================
# TAB 1: WEEKLY OPERATIONAL IMPACT
# ==============================================================================
with tab1:
    past_week = city_daily_custom.tail(7).copy().reset_index(drop=True)
    
    total_week_actual = sum(past_week[f"{k}_actual_rev"].sum() for k in selected_keys if f"{k}_actual_rev" in past_week)
    total_week_base = sum(past_week[f"{k}_baseline_rev"].sum() for k in selected_keys if f"{k}_baseline_rev" in past_week)
    total_week_impact = total_week_actual - total_week_base
    total_rain_week = past_week["precip_accumulation_mm"].sum()
    
    # 4 Equal-Span Metric Cards
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        badge_cls = "status-positive" if total_week_impact >= 0 else "status-negative"
        sign_str = "+$" if total_week_impact >= 0 else "-$"
        st.markdown(f"""
        <div class="metric-grid-card">
            <div class="metric-label">Weather Sales Shift</div>
            <div class="metric-number">{sign_str}{abs(total_week_impact):,.0f}</div>
            <div class="metric-subtext"><span class="{badge_cls}">{'Extra Gain' if total_week_impact >= 0 else 'Lost Sales'}</span> vs clear baseline</div>
        </div>
        """, unsafe_allow_html=True)
        
    with k2:
        st.markdown(f"""
        <div class="metric-grid-card">
            <div class="metric-label">Total Earned Revenue</div>
            <div class="metric-number">${total_week_actual:,.0f}</div>
            <div class="metric-subtext">Normal expected: ${total_week_base:,.0f}</div>
        </div>
        """, unsafe_allow_html=True)
        
    with k3:
        st.markdown(f"""
        <div class="metric-grid-card">
            <div class="metric-label">Monitored Portfolio</div>
            <div class="metric-number">{len(selected_keys)} Units</div>
            <div class="metric-subtext">Market: {city_names[selected_city]}</div>
        </div>
        """, unsafe_allow_html=True)
        
    with k4:
        st.markdown(f"""
        <div class="metric-grid-card">
            <div class="metric-label">Past 7-Day Rainfall</div>
            <div class="metric-number">{total_rain_week:.1f} mm</div>
            <div class="metric-subtext">Total rain recorded</div>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
    
    # Modern Plotly Line Graph with Generous Spacing
    st.markdown("#### Daily Revenue & Rainfall Timeline")
    st.caption("Solid lines represent actual earned revenue. Dotted lines represent what sales would normally be on clear days.")
    
    fig_7d = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.20,
        row_heights=[0.70, 0.30],
        subplot_titles=("Daily Revenue by Business ($ USD)", "Daily Rainfall (mm)")
    )
    
    x_labels = [f"{r['day_name']}<br>{r['date_str']}" for _, r in past_week.iterrows()]
    
    for idx, b_key in enumerate(selected_keys):
        if b_key not in active_catalog:
            continue
        cfg = active_catalog[b_key]
        biz_color = get_biz_color(b_key, idx)
        biz_label = get_biz_clean_label(b_key, cfg)
        biz_sym = cfg.get("symbol", "circle")
        
        cdata_actual = np.column_stack([
            [cfg['name']] * len(past_week),
            past_week["day_name"],
            past_week["date_str"],
            past_week["weather_icon"],
            past_week["air_temp_deg_c"],
            past_week["precip_accumulation_mm"],
            past_week[f"{b_key}_baseline_rev"],
            past_week[f"{b_key}_net_impact"]
        ])
        
        fig_7d.add_trace(go.Scatter(
            x=x_labels,
            y=past_week[f"{b_key}_actual_rev"],
            mode="lines+markers",
            name=f"{biz_label} — Actual",
            legendgroup=b_key,
            line=dict(color=biz_color, width=2.8, dash="solid"),
            marker=dict(size=7, color=biz_color, symbol=biz_sym),
            customdata=cdata_actual,
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "Date: %{customdata[1]}, %{customdata[2]}<br>"
                "Weather: %{customdata[3]} (%{customdata[4]:.1f}°C, %{customdata[5]:.1f} mm rain)<br>"
                "Actual Revenue: $%{y:,.0f}<br>"
                "Normal Baseline: $%{customdata[6]:,.0f}<br>"
                "Weather Shift: %{customdata[7]:+,.0f}<extra></extra>"
            )
        ), row=1, col=1)
        
        fig_7d.add_trace(go.Scatter(
            x=x_labels,
            y=past_week[f"{b_key}_baseline_rev"],
            mode="lines",
            name=f"{biz_label} — Baseline",
            legendgroup=b_key,
            line=dict(color=biz_color, width=1.8, dash="dash"),
            opacity=0.65,
            showlegend=True,
            customdata=cdata_actual,
            hovertemplate=(
                "<b>%{customdata[0]} (Expected Baseline)</b><br>"
                "Date: %{customdata[1]}, %{customdata[2]}<br>"
                "Weather: %{customdata[3]}<br>"
                "Expected Normal Sales: $%{y:,.0f}<extra></extra>"
            )
        ), row=1, col=1)
        
    cdata_rain = np.column_stack([
        ["Precipitation"] * len(past_week),
        past_week["day_name"],
        past_week["date_str"],
        past_week["weather_icon"],
        past_week["air_temp_deg_c"],
        past_week["precip_accumulation_mm"]
    ])
    fig_7d.add_trace(go.Scatter(
        x=x_labels,
        y=past_week["precip_accumulation_mm"],
        mode="lines+markers",
        name="Rainfall (mm)",
        showlegend=False,
        line=dict(color="#38BDF8", width=2.0),
        marker=dict(size=6, color="#38BDF8", symbol="circle-open"),
        fill="tozeroy",
        fillcolor="rgba(56, 189, 248, 0.12)",
        customdata=cdata_rain,
        hovertemplate=(
            "<b>Rainfall Volume</b><br>"
            "Date: %{customdata[1]}, %{customdata[2]}<br>"
            "Condition: %{customdata[3]} (%{customdata[4]:.1f}°C)<br>"
            "Rainfall: %{y:.1f} mm<extra></extra>"
        )
    ), row=2, col=1)
    
    fig_7d.add_annotation(
        text="<span style='color:#38BDF8;'>■</span> <b>Rainfall (mm)</b>",
        xref="paper", yref="paper",
        x=0.99, y=0.31,
        showarrow=False,
        xanchor="right", yanchor="bottom",
        font=dict(size=10.5, color="#94A3B8"),
        bgcolor="rgba(17, 24, 39, 0.85)",
        bordercolor="rgba(56, 189, 248, 0.25)",
        borderwidth=1,
        borderpad=4
    )
    
    fig_7d.for_each_annotation(lambda a: a.update(font=dict(size=12, color="#E2E8F0")))
    fig_7d.update_layout(
        template="plotly_dark",
        paper_bgcolor="#111827",
        plot_bgcolor="#111827",
        font=dict(family="Plus Jakarta Sans, sans-serif", size=11, color="#F8FAFC"),
        height=530,
        margin=dict(l=85, r=20, t=40, b=120),
        yaxis=dict(title=dict(text="Revenue ($)", standoff=18), automargin=True, gridcolor="rgba(56, 189, 248, 0.10)", zeroline=False),
        yaxis2=dict(title=dict(text="Rain (mm)", standoff=18), automargin=True, gridcolor="rgba(56, 189, 248, 0.10)", zeroline=False),
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.26,
            xanchor="center",
            x=0.5,
            font=dict(size=10.5, color="#E2E8F0"),
            bgcolor="rgba(17, 24, 39, 0.8)",
            bordercolor="rgba(255, 255, 255, 0.12)",
            borderwidth=1,
            tracegroupgap=8
        )
    )
    fig_7d.update_xaxes(fixedrange=True)
    fig_7d.update_yaxes(fixedrange=True)
    st.plotly_chart(fig_7d, use_container_width=True, config={"scrollZoom": False, "displayModeBar": False})
    
    st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)
    
    # Day in Review Section
    st.markdown("### Day in Review")
    
    day_options = [f"{r['day_name']} ({r['date_str']}) - {r['weather_icon']}" for _, r in past_week.iterrows()]
    selected_day_str = st.selectbox("Choose Date to Inspect:", options=day_options, index=len(day_options)-3)
    
    inspected_idx = day_options.index(selected_day_str)
    day_row = past_week.iloc[inspected_idx]
    
    st.markdown(f"**Date:** {day_row['day_name']} ({day_row['date_str']}) &nbsp;|&nbsp; **Weather:** {day_row['weather_icon']} ({day_row['air_temp_deg_c']:.1f}°C, {day_row['precip_accumulation_mm']:.1f} mm rain)")
    
    num_cols = min(len(selected_keys), 3)
    cols = st.columns(num_cols)
    
    for i, b_key in enumerate(selected_keys):
        col_target = cols[i % num_cols]
        b_insight = generate_business_specific_why_insight(b_key, day_row, custom_catalog=active_catalog)
        badge = "status-positive" if b_insight["delta"] >= 0 else "status-negative"
        sign_str = "+$" if b_insight["delta"] >= 0 else "-$"
        
        with col_target:
            st.markdown(f"""
            <div class="insight-box">
                <div>
                    <div class="insight-top">
                        <span class="insight-title">{b_insight['name']}</span>
                        <span class="{badge}">{sign_str}{abs(b_insight['delta']):,.0f} ({b_insight['pct_change']:+.1f}%)</span>
                    </div>
                    <div style="font-size: 0.82rem; color: #94A3B8; font-weight: 600;">
                        Earned: ${b_insight['actual_rev']:,.0f} &nbsp;|&nbsp; Normal: ${b_insight['baseline_rev']:,.0f}
                    </div>
                    <div class="insight-content">
                        <strong style="color: #FFFFFF;">{b_insight['headline']}</strong><br/>
                        {"<br/>".join([f"• {b}" for b in b_insight['bullets']])}
                    </div>
                </div>
                <div class="insight-bottom">
                    Category: {b_insight.get('category', 'General')}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
    with st.expander("Hourly Analysis"):
        hourly_sub = engine.df[(engine.df["metro_area"] == selected_city) & (engine.df["date_str"] == day_row["date_str"])].copy()
        hourly_clean = hourly_sub.rename(columns={
            "timestamp_local_str": "Time",
            "air_temp_deg_c": "Temperature (°C)",
            "precip_accumulation_mm": "Rainfall (mm)",
            "delivery_order_count": "Food Orders",
            "surge_pricing_mult": "Price Surge",
            "delivery_duration_min": "Delivery Wait Time (Mins)",
            "bikeshare_trips_count": "Bike Trips",
            "traffic_congestion_pct": "Traffic Jam (%)"
        })
        hourly_clean = hourly_clean.reset_index(drop=True)
        hourly_clean.index = range(1, len(hourly_clean) + 1)
        hourly_clean.index.name = "#"
        st.dataframe(
            hourly_clean[["Time", "Temperature (°C)", "Rainfall (mm)", "Food Orders", "Price Surge", "Delivery Wait Time (Mins)", "Bike Trips", "Traffic Jam (%)"]],
            use_container_width=True
        )


# ==============================================================================
# TAB 2: HISTORICAL TRENDS & SEASONAL DISENTANGLEMENT
# ==============================================================================
with tab2:
    st.subheader(f"Historical Trends & Seasonality — {city_names[selected_city]}")
    st.markdown("Macro Revenue Trends & Weather Impact")
    
    horizon = st.selectbox("Timeline Range:", ["Last 3 Months (90 Days)", "Last 6 Months (180 Days)", "Full 2 Years (All Data)"], index=1)
    if "3 Months" in horizon:
        df_lt = city_daily_custom.tail(90).copy()
        dtick_setting = "M1"
    elif "6 Months" in horizon:
        df_lt = city_daily_custom.tail(180).copy()
        dtick_setting = "M2"
    else:
        df_lt = city_daily_custom.copy()
        dtick_setting = "M2"
        
    df_lt["week_start"] = df_lt["date"].dt.to_period("W").dt.start_time
    df_lt["year_week"] = df_lt["date"].dt.to_period("W").astype(str)
    
    agg_dict = {
        "week_start": "min",
        "precip_accumulation_mm": "sum",
        "air_temp_deg_c": "mean"
    }
    for b_key in selected_keys:
        if f"{b_key}_actual_rev" in df_lt:
            agg_dict[f"{b_key}_actual_rev"] = "sum"
            agg_dict[f"{b_key}_baseline_rev"] = "sum"
        
    weekly_lt = df_lt.groupby("year_week", as_index=False).agg(agg_dict)
    weekly_lt = weekly_lt.sort_values("week_start").reset_index(drop=True)
    weekly_lt["date_display"] = weekly_lt["week_start"].dt.strftime("%b %d, %Y")
    
    fig_lt = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.20,
        row_heights=[0.70, 0.30],
        subplot_titles=("Weekly Revenue Trends ($ USD)", "Weekly Rainfall Volume (mm)")
    )
    
    for idx, b_key in enumerate(selected_keys):
        if b_key not in active_catalog:
            continue
        cfg = active_catalog[b_key]
        biz_color = get_biz_color(b_key, idx)
        biz_label = get_biz_clean_label(b_key, cfg)
        biz_sym = cfg.get("symbol", "circle")
        
        cdata_lt = np.column_stack([
            [cfg['name']] * len(weekly_lt),
            weekly_lt["date_display"],
            weekly_lt["air_temp_deg_c"],
            weekly_lt["precip_accumulation_mm"],
            weekly_lt[f"{b_key}_baseline_rev"],
            weekly_lt["year_week"]
        ])
        
        fig_lt.add_trace(go.Scatter(
            x=weekly_lt["week_start"],
            y=weekly_lt[f"{b_key}_actual_rev"],
            mode="lines+markers",
            name=biz_label,
            legendgroup=b_key,
            line=dict(color=biz_color, width=2.8, dash="solid"),
            marker=dict(size=6, color=biz_color, symbol=biz_sym),
            customdata=cdata_lt,
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "Date: %{customdata[1]} (%{customdata[5]})<br>"
                "Climate: %{customdata[2]:.1f}°C avg, %{customdata[3]:.1f} mm rain<br>"
                "Weekly Earned Sales: $%{y:,.0f}<br>"
                "Normal Baseline: $%{customdata[4]:,.0f}<extra></extra>"
            )
        ), row=1, col=1)
        
    cdata_lt_rain = np.column_stack([
        ["Precipitation"] * len(weekly_lt),
        weekly_lt["date_display"],
        weekly_lt["air_temp_deg_c"],
        weekly_lt["precip_accumulation_mm"],
        weekly_lt["year_week"]
    ])
    fig_lt.add_trace(go.Scatter(
        x=weekly_lt["week_start"],
        y=weekly_lt["precip_accumulation_mm"],
        mode="lines",
        name="Rainfall (mm)",
        showlegend=False,
        line=dict(color="#38BDF8", width=1.8),
        fill="tozeroy",
        fillcolor="rgba(56, 189, 248, 0.12)",
        customdata=cdata_lt_rain,
        hovertemplate=(
            "<b>Weekly Rainfall</b><br>"
            "Date: %{customdata[1]} (%{customdata[4]})<br>"
            "Total Rain: %{y:.1f} mm<extra></extra>"
        )
    ), row=2, col=1)
    
    fig_lt.add_annotation(
        text="<span style='color:#38BDF8;'>■</span> <b>Weekly Rainfall (mm)</b>",
        xref="paper", yref="paper",
        x=0.99, y=0.31,
        showarrow=False,
        xanchor="right", yanchor="bottom",
        font=dict(size=10.5, color="#94A3B8"),
        bgcolor="rgba(17, 24, 39, 0.85)",
        bordercolor="rgba(56, 189, 248, 0.25)",
        borderwidth=1,
        borderpad=4
    )
    
    # Configure shared x-axis with simplified bi-monthly short month labels
    fig_lt.update_xaxes(
        type="date",
        dtick=dtick_setting,
        tickformat="%b",
        tickangle=0,
        showgrid=True,
        gridcolor="rgba(56, 189, 248, 0.08)",
        tickfont=dict(size=10.5, color="#CBD5E1")
    )
    
    # Calendar year vertical separators & year labels underneath relevant section
    min_date = weekly_lt["week_start"].min()
    max_date = weekly_lt["week_start"].max()
    all_years = sorted(weekly_lt["week_start"].dt.year.unique())
    main_years = [y for y in all_years if len(weekly_lt[weekly_lt["week_start"].dt.year == y]) >= 3]
    if not main_years and all_years:
        main_years = all_years
        
    for y in all_years:
        y_boundary = pd.Timestamp(f"{y}-01-01")
        if y_boundary > min_date and y_boundary <= max_date:
            fig_lt.add_vline(
                x=y_boundary,
                line_width=1.0,
                line_dash="dash",
                line_color="rgba(148, 163, 184, 0.28)"
            )
            
    for y in main_years:
        y_weeks = weekly_lt[weekly_lt["week_start"].dt.year == y]
        if len(y_weeks) > 0:
            mid_ts = y_weeks["week_start"].iloc[len(y_weeks) // 2]
            fig_lt.add_annotation(
                x=mid_ts,
                y=-0.17,
                xref="x2",
                yref="paper",
                text=f"<span style='color:#38BDF8; font-weight:700; font-size:11px; letter-spacing:0.04em;'>{y}</span>",
                showarrow=False,
                xanchor="center",
                yanchor="top"
            )
            
    fig_lt.for_each_annotation(lambda a: a.update(font=dict(size=12, color="#E2E8F0")) if a.text and "Weekly" in a.text else None)
    fig_lt.update_layout(
        template="plotly_dark",
        paper_bgcolor="#111827",
        plot_bgcolor="#111827",
        font=dict(family="Plus Jakarta Sans, sans-serif", size=11, color="#F8FAFC"),
        height=550,
        margin=dict(l=85, r=20, t=40, b=150),
        yaxis=dict(title=dict(text="Revenue ($)", standoff=18), automargin=True, gridcolor="rgba(56, 189, 248, 0.10)", zeroline=False),
        yaxis2=dict(title=dict(text="Rain (mm)", standoff=18), automargin=True, gridcolor="rgba(56, 189, 248, 0.10)", zeroline=False),
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.32,
            xanchor="center",
            x=0.5,
            font=dict(size=10.5, color="#E2E8F0"),
            bgcolor="rgba(17, 24, 39, 0.8)",
            bordercolor="rgba(255, 255, 255, 0.12)",
            borderwidth=1,
            tracegroupgap=8
        )
    )
    fig_lt.update_xaxes(fixedrange=True)
    fig_lt.update_yaxes(fixedrange=True)
    st.plotly_chart(fig_lt, use_container_width=True, config={"scrollZoom": False, "displayModeBar": False})
    
    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
    
    with st.expander("View All Metrics & Model Results"):
        st.markdown("This table compares simple raw correlation against seasonality-adjusted econometric impact after removing calendar bias.")
        comp_df = engine.get_naive_vs_fixed_effects_comparison()
        comp_df.index = range(1, len(comp_df) + 1)
        comp_df.index.name = "#"
        st.dataframe(comp_df, use_container_width=True)


# ==============================================================================
# TAB 3: BUSINESS INTERACTIONS & MULTI-HOP CHAINS
# ==============================================================================
with tab3:
    st.subheader(f"Business Interactions & Domino Chains — {city_names[selected_city]}")
    st.markdown("Quantifying higher-order multi-hop causal chains and indirect substitution flows across the commercial ecosystem.")
    
    # 1. Full Multi-Hop Domino Chain (Dynamic for City & Current Weather)
    dynamic_cascade = generate_dynamic_domino_cascade(selected_city, cur_w, selected_keys, custom_catalog=active_catalog)
    
    steps_domino_html = "".join([
        f'<div class="domino-step"><span class="domino-num">{s["num"]}</span><span>{html.escape(str(s["text"]))}</span></div>'
        for s in dynamic_cascade["steps"]
    ])
    chain_html = (
        f'<div class="domino-chain-container">'
        f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px;">'
        f'<div class="ripple-title" style="margin-bottom: 0;">Multi-Hop Domino Chain — {html.escape(str(dynamic_cascade["city_name"]))} ({html.escape(str(dynamic_cascade["regime"]))})</div>'
        f'</div>'
        f'{steps_domino_html}'
        f'</div>'
    )
    st.markdown(chain_html, unsafe_allow_html=True)
    
    # 2. Non-linear Tipping Point Insight (Dynamic Thresholds)
    tp = dynamic_cascade["tipping_point"]
    tipping_html = (
        f'<div class="ripple-box" style="border-left: 4px solid #F59E0B; margin-bottom: 22px;">'
        f'<div class="ripple-title" style="color: #FBBF24;">{html.escape(str(tp["title"]))}</div>'
        f'<div style="font-size: 0.86rem; color: #CBD5E1; line-height: 1.6; margin-top: 8px;">'
        f'When weather conditions cross historical operational tolerance thresholds in <strong>{html.escape(str(dynamic_cascade["city_name"]))}</strong>, economic channels fracture non-linearly:<br/>'
        f'• <strong>Customer Demand Impact:</strong> {html.escape(str(tp["demand"]))}<br/>'
        f'• <strong>Service &amp; Courier Supply:</strong> {html.escape(str(tp["supply"]))}<br/>'
        f'• <strong>Operational Outcome:</strong> {html.escape(str(tp["consequence"]))}'
        f'</div></div>'
    )
    st.markdown(tipping_html, unsafe_allow_html=True)
    
    # 3. Unique Domino Effect & Impact for Every Business in Active Portfolio
    st.markdown("#### Unique Business Domino Effects & Impact Analysis")
    st.caption(f"Granular causal chains and operational ripple effects customized for each selected business under current {city_names[selected_city]} weather.")
    
    biz_dominos = generate_business_specific_domino_effects(selected_city, cur_w, selected_keys, custom_catalog=active_catalog)
    
    num_biz_cols = min(len(biz_dominos), 2) if len(biz_dominos) > 1 else 1
    biz_cols = st.columns(num_biz_cols)
    
    for idx, b_info in enumerate(biz_dominos):
        target_c = biz_cols[idx % num_biz_cols]
        badge_cls = "status-positive" if b_info["delta"] >= 0 else "status-negative"
        sign_str = "+$" if b_info["delta"] >= 0 else "-$"
        delta_str = f"{sign_str}{abs(b_info['delta']):,.0f} ({b_info['pct']:+.1f}%)"
        
        name_esc = html.escape(str(b_info.get("name", "Business")))
        cat_esc = html.escape(str(b_info.get("category", "Commercial Enterprise")))
        trig_esc = html.escape(str(b_info.get("trigger", "")))
        beh_esc = html.escape(str(b_info.get("behavior", "")))
        fin_esc = html.escape(str(b_info.get("financial", "")))
        down_esc = html.escape(str(b_info.get("downstream", "")))
        act_esc = html.escape(str(b_info.get("action", "")))
        
        card_html = (
            f'<div class="biz-domino-card">'
            f'<div class="biz-domino-header">'
            f'<div>'
            f'<div class="biz-domino-title">{name_esc}</div>'
            f'<div class="biz-domino-category">{cat_esc}</div>'
            f'</div>'
            f'<span class="biz-domino-badge {badge_cls}">{delta_str}</span>'
            f'</div>'
            f'<div class="biz-domino-summary">'
            f'<strong>Weather Impact Summary:</strong> {trig_esc}'
            f'</div>'
            f'<div class="biz-chain-step"><strong>1. Weather Trigger:</strong> {trig_esc}</div>'
            f'<div class="biz-chain-step"><strong>2. Consumer Reaction:</strong> {beh_esc}</div>'
            f'<div class="biz-chain-step"><strong>3. Financial Effect:</strong> {fin_esc}</div>'
            f'<div class="biz-downstream-box">'
            f'<strong>Downstream Effects:</strong> {down_esc}'
            f'</div>'
            f'<div class="biz-countermeasure-box">'
            f'<strong>Operational Countermeasure:</strong> {act_esc}'
            f'</div>'
            f'</div>'
        )
        
        with target_c:
            st.markdown(card_html, unsafe_allow_html=True)
            
    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
    st.markdown("#### Cross-Channel Demand Shifts")
    st.caption("How weather-driven demand moves between in-person, indoor and digital businesses.")
    
    sample_rain_day = city_daily_custom[city_daily_custom["precip_accumulation_mm"] > 2.0].iloc[-1] if len(city_daily_custom[city_daily_custom["precip_accumulation_mm"] > 2.0]) > 0 else city_daily_custom.iloc[-1]
    portfolio_links = analyze_inter_business_linkages(selected_keys, sample_rain_day, custom_catalog=active_catalog)
    
    if portfolio_links:
        for link in portfolio_links:
            link_title = link.get("title", "Business Interaction")
            link_type = link.get("type", "Ripple Effect")
            link_summary = link.get("summary", link.get("flow", ""))
            link_steps = link.get("chain_steps", [link.get("mechanism", "")])
            steps_html = "".join([f'<div class="chain-step">{s}</div>' for s in link_steps if s])
            
            ripple_html = f'<div class="ripple-box"><div style="display: flex; justify-content: space-between; align-items: center;"><span class="ripple-title">{link_title}</span><span class="status-neutral">{link_type}</span></div><div style="font-size: 0.90rem; font-weight: 700; color: #38BDF8; margin: 6px 0 10px 0;">{link_summary}</div><div style="margin-top: 8px;">{steps_html}</div></div>'
            st.markdown(ripple_html, unsafe_allow_html=True)
    else:
        st.info("Select complementary businesses (such as Square POS and Stripe Checkout, or Restaurants & Bistros and Food Delivery) to view substitution flows.")
        
    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
    st.markdown("#### Past 30 Days Net Weather Sales Shift ($ USD)")
    st.caption("Tracking how weather shifted dollar earnings above or below baseline across your businesses.")
    
    recent_30 = city_daily_custom.tail(30).reset_index(drop=True)
    fig_corr = go.Figure()
    for idx, b_key in enumerate(selected_keys):
        if b_key not in active_catalog:
            continue
        cfg = active_catalog[b_key]
        biz_color = get_biz_color(b_key, idx)
        biz_label = get_biz_clean_label(b_key, cfg)
        biz_sym = cfg.get("symbol", "circle")
        
        cdata_30 = np.column_stack([
            [cfg['name']] * len(recent_30),
            recent_30["day_name"],
            recent_30["date_str"],
            recent_30["weather_icon"],
            recent_30["air_temp_deg_c"],
            recent_30["precip_accumulation_mm"]
        ])
        
        fig_corr.add_trace(go.Scatter(
            x=recent_30["date_str"],
            y=recent_30[f"{b_key}_net_impact"],
            mode="lines+markers",
            name=biz_label,
            legendgroup=b_key,
            line=dict(color=biz_color, width=2.8, dash="solid"),
            marker=dict(size=7, color=biz_color, symbol=biz_sym),
            customdata=cdata_30,
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "Date: %{customdata[1]}, %{customdata[2]}<br>"
                "Weather: %{customdata[3]} (%{customdata[4]:.1f}°C, %{customdata[5]:.1f} mm rain)<br>"
                "Net Weather Shift: $%{y:+,.0f}<extra></extra>"
            )
        ))
    fig_corr.update_layout(
        template="plotly_dark",
        paper_bgcolor="#111827",
        plot_bgcolor="#111827",
        font=dict(family="Plus Jakarta Sans, sans-serif", size=11, color="#F8FAFC"),
        height=500,
        margin=dict(l=85, r=20, t=30, b=110),
        yaxis=dict(title=dict(text="Sales Shift ($ USD)", standoff=18), automargin=True, gridcolor="rgba(56, 189, 248, 0.10)", zeroline=True, zerolinecolor="rgba(56, 189, 248, 0.35)"),
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.26,
            xanchor="center",
            x=0.5,
            font=dict(size=10.5, color="#E2E8F0"),
            bgcolor="rgba(17, 24, 39, 0.8)",
            bordercolor="rgba(255, 255, 255, 0.12)",
            borderwidth=1,
            tracegroupgap=8
        )
    )
    fig_corr.update_xaxes(fixedrange=True)
    fig_corr.update_yaxes(fixedrange=True)
    st.plotly_chart(fig_corr, use_container_width=True, config={"scrollZoom": False, "displayModeBar": False})


# ==============================================================================
# TAB 4: LIVE SCENARIO SIMULATOR & AI GUIDANCE
# ==============================================================================
with tab4:
    live_city_label = "NYC" if selected_city == "NYC" or city_names.get(selected_city) == "New York City" else city_names.get(selected_city, selected_city)
    st.subheader(f"Live Weather Intelligence & Business Impact Forecast — {live_city_label}")
    
    # Automatic Live Condition Initialization
    now_dt = datetime.datetime.now()
    days_list = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    live_dow = now_dt.weekday()
    live_hour = now_dt.hour
    live_rain = float(cur_w.get("precipitation_mm", 0.0))
    live_temp_anom = round(float(cur_w.get("temperature_c", 18.0)) - 18.0, 1)
    live_wind = float(cur_w.get("wind_kmh", 12.0))
    
    # Active simulation parameters (default directly to current live conditions)
    sim_dow = st.session_state.get("sim_dow_override", live_dow)
    sim_hour = st.session_state.get("sim_hour_override", live_hour)
    sim_rain = st.session_state.get("sim_rain_override", live_rain)
    sim_temp_anom = st.session_state.get("sim_temp_anom_override", live_temp_anom)
    
    is_custom_simulation = (
        sim_dow != live_dow or sim_hour != live_hour or 
        abs(sim_rain - live_rain) > 0.01 or abs(sim_temp_anom - live_temp_anom) > 0.01
    )
    
    # Execute econometric shock simulation
    sim_output = engine.simulate_cross_sector_scenario(
        city=selected_city,
        day_of_week=sim_dow,
        hour_of_day=sim_hour,
        month=now_dt.month,
        is_holiday=0,
        rain_mm=sim_rain,
        snow_cm=0.0,
        temp_anomaly_c=sim_temp_anom,
        wind_kmh=live_wind
    )
    
    custom_badge_html = '''<div style="display: flex; align-items: center; gap: 8px;">
            <span style="display: inline-block; width: 8px; height: 8px; border-radius: 50%; background-color: #38BDF8; box-shadow: 0 0 8px #38BDF8;"></span>
            <span style="font-size: 0.78rem; font-weight: 600; color: #38BDF8;">CUSTOM SIMULATION PARAMETERS ACTIVE</span>
        </div>''' if is_custom_simulation else ""
    
    # Clean Live Status Banner
    st.markdown(f"""
    <div style="background: rgba(17, 24, 39, 0.95); border: 1px solid rgba(56, 189, 248, 0.25); border-radius: 10px; padding: 12px 18px; margin: 8px 0 16px 0; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 10px;">
        <div>
            <span style="font-weight: 700; color: #F8FAFC; font-size: 0.92rem;">Nowcasting Conditions:</span>
            <span style="color: #38BDF8; font-weight: 600; margin-left: 6px;">{days_list[sim_dow]} at {sim_hour:02d}:00</span> &bull; 
            <span style="color: #E2E8F0;">{cur_w['condition']}</span> 
            (<strong style="color: #FFFFFF;">{sim_rain:.1f} mm/h rain</strong>, <strong style="color: #FFFFFF;">{sim_temp_anom:+.1f}°C anomaly</strong>)
        </div>
        {custom_badge_html}
    </div>
    """, unsafe_allow_html=True)
    
    # Real-Time Operational Predictions across 6 Key Sectors
    sec_cols = st.columns(3)
    sector_names = list(sim_output["by_sector"].keys())
    
    for s_idx, sector_name in enumerate(sector_names):
        target_col = sec_cols[s_idx % 3]
        metrics_list = sim_output["by_sector"][sector_name]
        
        with target_col:
            rows_html = "".join([
                f'<div class="metric-row"><span><strong style="color:#F8FAFC;">{m["display_name"]}</strong></span><span>{m["weather_impacted"]} {m["unit"]} <span class="{"status-positive" if m["delta_pct"] >= 0 else "status-negative"}">{m["delta_pct"]:+.1f}%</span></span></div>'
                for m in metrics_list
            ])
            card_html = f'<div class="sector-grid-card"><div class="sector-title">{sector_name}</div>{rows_html}</div>'
            st.markdown(card_html, unsafe_allow_html=True)
            
    # Clean, Compact "What-If" Exploration Expander (Allows user to tweak if desired)
    with st.expander("Customize What-If Scenarios (Optional)"):
        st.caption("Change day, hour, or weather intensity to test hypothetical conditions against the live baseline.")
        sim_c1, sim_c2, sim_c3, sim_c4 = st.columns(4)
        with sim_c1:
            ui_day = st.selectbox("Day of Week:", days_list, index=sim_dow, key="ui_sim_dow")
        with sim_c2:
            ui_hour = st.slider("Hour of Day:", min_value=0, max_value=23, value=sim_hour, format="%d:00", key="ui_sim_hour")
        with sim_c3:
            ui_rain = st.slider("Rainfall (mm/hr):", min_value=0.0, max_value=25.0, value=sim_rain, step=0.5, key="ui_sim_rain")
        with sim_c4:
            ui_anom = st.slider("Temp Anomaly vs Season (°C):", min_value=-15.0, max_value=15.0, value=sim_temp_anom, step=0.5, key="ui_sim_anom")
            
        btn_c1, btn_c2 = st.columns([1.5, 2.5])
        with btn_c1:
            if st.button("Apply Custom Parameters", key="btn_apply_override"):
                st.session_state["sim_dow_override"] = days_list.index(ui_day)
                st.session_state["sim_hour_override"] = ui_hour
                st.session_state["sim_rain_override"] = ui_rain
                st.session_state["sim_temp_anom_override"] = ui_anom
                st.rerun()
        with btn_c2:
            if st.button("Reset to Direct Live Conditions", key="btn_reset_live"):
                st.session_state["sim_dow_override"] = live_dow
                st.session_state["sim_hour_override"] = live_hour
                st.session_state["sim_rain_override"] = live_rain
                st.session_state["sim_temp_anom_override"] = live_temp_anom
                st.rerun()

    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
    
    # Direct 7-Day Multi-Source Forecast (Fully Live, No Mock Scenarios)
    st.markdown("#### 7-Day Revenue Forecast & Weather Outlook")
    st.caption(f"Projected daily revenue across your {live_city_label} business portfolio based on weather forecasts.")
    
    daily_fc = live_weather_pkg.get("daily_forecast", [])
    
    w_cols = st.columns(len(daily_fc))
    for w_idx, day_w in enumerate(daily_fc):
        with w_cols[w_idx]:
            rain_color = "#00D2FF" if day_w['precip_mm'] > 0 else "#64748B"
            st.markdown(f"""
            <div style="background: rgba(17, 24, 39, 0.90); border: 1px solid rgba(56, 189, 248, 0.20); border-radius: 8px; padding: 10px 6px; text-align: center;">
                <div style="font-size: 0.84rem; font-weight: 700; color: #38BDF8;">{day_w['day_name']}</div>
                <div style="font-size: 0.70rem; color: #94A3B8; margin-bottom: 4px;">{day_w['date'][-5:]}</div>
                <div style="font-size: 0.88rem; font-weight: 700; color: #F8FAFC;">{day_w['temp_max']:.0f}° / {day_w['temp_min']:.0f}°</div>
                <div style="font-size: 0.74rem; color: #E2E8F0; margin-top: 4px;">{day_w['condition']}</div>
                <div style="font-size: 0.74rem; color: {rain_color}; font-weight: 600; margin-top: 2px;">
                    {str(round(day_w['precip_mm'], 1)) + ' mm' if day_w['precip_mm'] > 0 else '0 mm'}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
    forecast_data = generate_live_weather_ai_forecast(selected_keys, daily_fc, custom_catalog=active_catalog)
    forecast_scenario_label = "Live Multi-Source Forecast"
    days_x = forecast_data["days"]
    
    fig_fut = go.Figure()
    
    for idx, (b_key, p_info) in enumerate(forecast_data["projections"].items()):
        cfg = active_catalog.get(b_key, {})
        biz_color = get_biz_color(b_key, idx)
        biz_label = get_biz_clean_label(b_key, p_info)
        biz_sym = cfg.get("symbol", "circle")
        
        cdata_fut = np.column_stack([
            [p_info['name']] * len(days_x),
            days_x,
            p_info["baseline_series"],
            [forecast_scenario_label] * len(days_x)
        ])
        
        fig_fut.add_trace(go.Scatter(
            x=days_x,
            y=p_info["actual_series"],
            mode="lines+markers",
            name=f"{biz_label} — Projected",
            legendgroup=b_key,
            line=dict(color=biz_color, width=2.8, dash="solid"),
            marker=dict(size=7, color=biz_color, symbol=biz_sym),
            customdata=cdata_fut,
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "Day: %{customdata[1]} (Forward Projection)<br>"
                "Forecast: %{customdata[3]}<br>"
                "Projected Revenue: $%{y:,.0f}<br>"
                "Normal Baseline: $%{customdata[2]:,.0f}<extra></extra>"
            )
        ))
        fig_fut.add_trace(go.Scatter(
            x=days_x,
            y=p_info["baseline_series"],
            mode="lines",
            name=f"{biz_label} — Normal",
            legendgroup=b_key,
            line=dict(color=biz_color, width=1.8, dash="dash"),
            opacity=0.65,
            customdata=cdata_fut,
            hovertemplate=(
                "<b>%{customdata[0]} (Normal Baseline)</b><br>"
                "Day: %{customdata[1]}<br>"
                "Expected Normal Sales: $%{y:,.0f}<extra></extra>"
            )
        ))
        
    fig_fut.update_layout(
        template="plotly_dark",
        paper_bgcolor="#111827",
        plot_bgcolor="#111827",
        font=dict(family="Plus Jakarta Sans, sans-serif", size=11, color="#F8FAFC"),
        height=540,
        margin=dict(l=85, r=20, t=30, b=130),
        yaxis=dict(title=dict(text="Projected Daily Sales ($)", standoff=18), automargin=True, gridcolor="rgba(56, 189, 248, 0.10)", zeroline=False),
        xaxis=dict(gridcolor="rgba(255, 255, 255, 0.05)", tickfont=dict(size=11, color="#CBD5E1")),
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.26,
            xanchor="center",
            x=0.5,
            font=dict(size=10.5, color="#E2E8F0"),
            bgcolor="rgba(17, 24, 39, 0.8)",
            bordercolor="rgba(255, 255, 255, 0.12)",
            borderwidth=1,
            tracegroupgap=10
        )
    )
    fig_fut.update_xaxes(fixedrange=True)
    fig_fut.update_yaxes(fixedrange=True)
    st.plotly_chart(fig_fut, use_container_width=True, config={"scrollZoom": False, "displayModeBar": False})
    
    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
    st.markdown("#### Strategic Operational Guidance")
    for advice in forecast_data["ai_advice"]:
        st.markdown(f"""
        <div class="ai-guidance-card">
            {advice}
        </div>
        """, unsafe_allow_html=True)


# ==============================================================================
# TAB 5: DATA SOURCES & PROCESSING
# ==============================================================================
with tab5:
    st.subheader("Data Sources & Processing")
    
    p1, p2, p3 = st.columns(3)
    with p1:
        st.markdown("""
        <div class="sector-grid-card" style="padding: 12px 14px; margin-bottom: 8px;">
            <div class="sector-title" style="margin-bottom: 6px; font-size: 0.88rem;">1. Time & Location Alignment</div>
            <div style="font-size: 0.82rem; color: #CBD5E1; line-height: 1.5;">
                • <strong>4 Cities:</strong> Data aligned across New York, Chicago, Los Angeles, and Phoenix.<br/>
                • <strong>Time Accuracy:</strong> Accounts for time zones and daylight saving changes.<br/>
                • <strong>Consistent Timeline:</strong> Aligns weather and business data by time and location.
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    with p2:
        st.markdown("""
        <div class="sector-grid-card" style="padding: 12px 14px; margin-bottom: 8px;">
            <div class="sector-title" style="margin-bottom: 6px; font-size: 0.88rem;">2. Data Integration & Preparation</div>
            <div style="font-size: 0.82rem; color: #CBD5E1; line-height: 1.5;">
                • <strong>Data Combined:</strong> 69,106 weather records and 279,249 point-of-sale events.<br/>
                • <strong>Missing Data:</strong> Fills data gaps using interpolation and previous recorded values.<br/>
                • <strong>Hourly Summaries:</strong> Converts 15-minute sales records into hourly totals.
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    with p3:
        st.markdown("""
        <div class="sector-grid-card" style="padding: 12px 14px; margin-bottom: 8px;">
            <div class="sector-title" style="margin-bottom: 6px; font-size: 0.88rem;">3. Weather & Business Metrics</div>
            <div style="font-size: 0.82rem; color: #CBD5E1; line-height: 1.5;">
                • <strong>Temperature Anomaly:</strong> Measures how temperatures differ from recent seasonal conditions.<br/>
                • <strong>Heating & Cooling Demand:</strong> Estimates heating and cooling needs using temperature data.<br/>
                • <strong>21 Business Metrics:</strong> Tracks performance across 21 sectors in 4 climate regions.
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
    st.markdown("#### Live Data Pipeline Inspector")
    st.caption("Synchronized weather and business records across operational data streams.")
    
    display_df = engine.df[engine.df["metro_area"] == selected_city].tail(25).copy()
    display_df = display_df.reset_index(drop=True)
    display_df.index = range(1, len(display_df) + 1)
    display_df.index.name = "#"
    st.dataframe(
        display_df[[
            "timestamp_local_str", "metro_area", "air_temp_deg_c", "temp_anomaly_deg_c",
            "precip_accumulation_mm", "delivery_order_count", "surge_pricing_mult",
            "bikeshare_trips_count", "rideshare_trip_count", "restaurant_dinein_guests",
            "retail_mall_footfall", "electricity_grid_load_mw", "freight_delay_min"
        ]],
        use_container_width=True
    )
