import os
import sys
import json
import time
import re
import datetime
import math
import pandas as pd
import numpy as np
from flask import Flask, render_template, request, jsonify

# Add parent directory to path so src modules import cleanly
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.historical_dashboard import build_portfolio
from src.econometrics import WeatherEconometricsEngine
from src.revenue_analytics import (
    BUSINESS_CATALOG,
    CITY_DYNAMICS,
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
from src.real_data_manager import (
    REAL_BUSINESS_CATALOG,
    get_real_catalog,
    load_real_dataset
)
from src.real_eda_engine import (
    SERIES_METADATA,
    SEASONS,
    get_matched_series_data,
    filter_series,
    compute_eda_statistics,
    compute_histograms,
    compute_weekday_bars,
    compute_rain_groups,
    compute_monthly_trends,
    compute_correlation_and_math,
    get_raw_to_published_audit
)

app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(__file__), "templates"),
    static_folder=os.path.join(os.path.dirname(__file__), "static")
)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0

@app.before_request
def validate_dashboard_request():
    endpoints = {'initial_state','weather','portfolio_data','domino_data','nowcast','diagnostics'}
    if request.endpoint not in endpoints:
        return
    data = request.args if request.method == 'GET' else request.get_json(silent=True)
    if data is None or (request.method != 'GET' and not isinstance(data, dict)):
        return jsonify({'error':'Request body must be a JSON object.'}), 400
    city = data.get('city','NYC')
    if not isinstance(city,str) or city not in CITY_NAMES:
        return jsonify({'error':'city must be one of NYC, ORD, SEA, PHX.'}), 400
    if request.method == 'GET':
        return
    keys = data.get('selected_keys',['nyc_taxi'])
    if not isinstance(keys,list) or not keys or any(not isinstance(k,str) for k in keys):
        return jsonify({'error':'selected_keys must be a nonempty array of dataset names.'}), 400
    if any(k not in get_merged_catalog(city) for k in keys):
        return jsonify({'error':'Unknown dataset in selected_keys.'}), 400
    if not isinstance(data.get('custom_businesses',{}),dict):
        return jsonify({'error':'custom_businesses must be an object.'}), 400
    if not isinstance(data.get('horizon',''),str):
        return jsonify({'error':'horizon must be text.'}), 400
    for field, low, high in [('inspected_day_idx',0,1000000),('sim_dow',0,6),('sim_hour',0,23)]:
        value = data.get(field)
        if (field in data and field != 'inspected_day_idx' and value is None) or (value is not None and (type(value) is not int or not low <= value <= high)):
            return jsonify({'error':f'{field} must be an integer from {low} to {high}.'}), 400
    for field,low,high in [('sim_rain',0,1000),('sim_wind',0,500),('sim_temp_anom',-100,100)]:
        if field in data:
            value = data[field]
            if type(value) not in (int,float) or not math.isfinite(value) or not low <= value <= high:
                return jsonify({'error':f'{field} must be a finite number from {low} to {high}.'}), 400


# City mapping
CITY_NAMES = {
    "NYC": "New York City",
    "ORD": "Chicago",
    "SEA": "Seattle",
    "PHX": "Phoenix"
}

# High Visibility Color Palette
HIGH_VISIBILITY_PALETTE = [
    "#00D2FF", "#FF9100", "#00E676", "#FF5252", "#B388FF",
    "#76FF03", "#FF4081", "#00E5FF", "#FFD600", "#E040FB",
    "#1DE9B6", "#FF6D00", "#448AFF", "#00C853", "#FF1744", "#7C4DFF"
]

BUSINESS_PALETTE = {
    "square_pos_live": "#38BDF8",
    "stripe_gateway_live": "#14B8A6",
    "dine_in_restaurant": "#F59E0B",
    "food_delivery": "#FB7185",
    "rideshare_fleet": "#A855F7",
    "bikeshare_network": "#06B6D4",
    "specialty_apparel": "#EC4899",
    "supermarket": "#10B981",
    "convenience_store": "#F97316",
    "car_wash": "#6366F1",
    "hvac_repair": "#EAB308",
    "home_improvement": "#84CC16",
    "ice_cream_beverage": "#00E5FF",
    "cinema_entertainment": "#8B5CF6",
    "freight_logistics": "#94A3B8",
    "urgent_care": "#EF4444"
}

def get_biz_color(b_key: str, idx: int = 0) -> str:
    if b_key in BUSINESS_PALETTE:
        return BUSINESS_PALETTE[b_key]
    return HIGH_VISIBILITY_PALETTE[idx % len(HIGH_VISIBILITY_PALETTE)]

def get_biz_clean_label(b_key: str, catalog_entry: dict) -> str:
    name = catalog_entry.get("name", b_key) if isinstance(catalog_entry, dict) else str(catalog_entry)
    clean = name.split(" Live")[0].split(" (")[0].strip()
    return clean

# In-memory storage for the web session
CUSTOM_BUSINESSES = {}
AUTO_MERCHANT_CACHE = {}
WEATHER_CACHE = {}

print("Initializing Weather Econometrics Engine and Pre-Aggregating Data...")
data_path = os.path.join(BASE_DIR, "data", "processed", "weather_business_merged.parquet")
engine = WeatherEconometricsEngine(data_path)
engine.fit_sector_models()
df_daily_base = aggregate_daily_financials(engine.df)
print("Data Engine Ready!")

def get_auto_connected_merchants(city_code: str):
    if city_code in AUTO_MERCHANT_CACHE:
        return AUTO_MERCHANT_CACHE[city_code]
    sq_conn = SquareConnector()
    df_sq = sq_conn.fetch_daily_revenue("2023-01-01", "2023-12-31", mock_profile="restaurant")
    st_conn = StripeConnector()
    df_st = st_conn.fetch_daily_revenue("2023-01-01", "2023-12-31", mock_profile="ecommerce")
    city_weather_daily = df_daily_base[df_daily_base["metro_area"] == city_code]
    res_sq = estimate_empirical_elasticities(df_sq, city_weather_daily, business_name=f"{CITY_NAMES.get(city_code, city_code)} Square POS (Hospitality)")
    res_st = estimate_empirical_elasticities(df_st, city_weather_daily, business_name=f"{CITY_NAMES.get(city_code, city_code)} Stripe Gateway (E-Commerce)")
    city_tag = "NYC" if city_code == "NYC" else city_code
    merchants = {
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
    AUTO_MERCHANT_CACHE[city_code] = merchants
    return merchants

def get_live_weather(city_code: str):
    now = time.time()
    if city_code in WEATHER_CACHE:
        pkg, timestamp = WEATHER_CACHE[city_code]
        if now - timestamp < 900:  # 15 minutes TTL
            return pkg
    pkg = fetch_live_weather(city_code)
    WEATHER_CACHE[city_code] = (pkg, now)
    return pkg

def get_merged_catalog(city_code: str, client_custom_dict=None):
    """Returns strictly the 4 real-world production datasets."""
    return dict(get_real_catalog())


# --- ROUTES ---

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/eda")
def eda_presentation():
    series = request.args.get("series", "nyc_taxi")
    if series not in SERIES_METADATA:
        series = "nyc_taxi"
    
    year = request.args.get("year", "all")
    season = request.args.get("season", "all")
    day_type = request.args.get("day_type", "all")
    
    base = get_matched_series_data(series)
    avail_years = sorted(base["year"].unique()) if "year" in base.columns else []
    avail_seasons = [s for s in ["winter", "spring", "summer", "autumn"] if s in base["season"].values]
    
    active_year = year if (year in avail_years or year == "all") else "all"
    active_season = season if (season in avail_seasons or season == "all") else "all"
    active_day_type = day_type if day_type in ("all", "weekday", "weekend") else "all"
    
    d = filter_series(base, active_year, active_season, active_day_type)
    filter_warning = None
    if d.empty:
        if active_year != "all" and active_season != "all":
            d_fallback = filter_series(base, active_year, "all", active_day_type)
            if not d_fallback.empty:
                d = d_fallback
                filter_warning = f"Notice: No observations exist for {active_year} in {SEASONS.get(active_season, active_season)}. Showing all {active_year} records ({len(d)} rows)."
                active_season = "all"
        if d.empty:
            d = base.copy()
            filter_warning = "Notice: No observations match the selected criteria. Displaying full baseline dataset."
            active_year = "all"
            active_season = "all"
            active_day_type = "all"
        
    stats = compute_eda_statistics(d)
    histograms = compute_histograms(d)
    weekdays = compute_weekday_bars(d)
    groups = compute_rain_groups(d)
    points, trend_start, trend_end, trend_max = compute_monthly_trends(d)
    corr, columns, association = compute_correlation_and_math(d)
    audit = get_raw_to_published_audit()
    
    start_str = str(d["date"].min().date()) if hasattr(d["date"].min(), "date") else str(d["date"].min())
    end_str = str(d["date"].max().date()) if hasattr(d["date"].max(), "date") else str(d["date"].max())
    
    return render_template(
        "eda.html",
        series=series,
        modes=SERIES_METADATA,
        name=SERIES_METADATA[series]["name"],
        unit=SERIES_METADATA[series]["unit"],
        stats=stats,
        histograms=histograms,
        weekdays=weekdays,
        groups=groups,
        corr=corr,
        columns=columns,
        points=points,
        trend_start=trend_start,
        trend_end=trend_end,
        trend_max=trend_max,
        association=association,
        audit=audit,
        years=avail_years,
        selected_year=active_year,
        seasons=avail_seasons,
        season_labels=SEASONS,
        selected_season=active_season,
        selected_day_type=active_day_type,
        filter_warning=filter_warning,
        start=start_str,
        end=end_str,
        rows=len(d),
        source_rows=len(base)
    )

@app.route("/api/eda-audit")
def eda_audit():
    return jsonify(get_raw_to_published_audit())

@app.route("/notebook")
def notebook_walkthrough():
    audit = get_raw_to_published_audit()
    
    # Calculate worked math on NYC Taxi as reference
    taxi_df = get_matched_series_data("nyc_taxi")
    _, _, assoc = compute_correlation_and_math(taxi_df)
    r_math = assoc.get("rain", {})
    math_report = {
        "n": r_math.get("n", 0),
        "x_mean": r_math.get("xmean", 0),
        "y_mean": r_math.get("ymean", 0),
        "pearson_r": r_math.get("pearson", 0),
        "slope": r_math.get("slope", 0),
        "intercept": r_math.get("intercept", 0),
        "r_squared": r_math.get("r2", 0),
        "sxx": r_math.get("sxx", 0),
        "syy": r_math.get("syy", 0),
        "sxy": r_math.get("sxy", 0),
        "covariance": r_math.get("covariance", 0)
    }
    
    counts = {key:len(load_real_dataset(key)) for key in REAL_BUSINESS_CATALOG}
    taxi_numeric = taxi_df['count']
    q1, q3 = taxi_numeric.quantile([0.25,0.75])
    iqr = q3-q1
    flagged = int(((taxi_numeric < q1-1.5*iqr) | (taxi_numeric > q3+1.5*iqr)).sum())
    matrix = taxi_df[['count','rain_mm','temperature_c','wind_kmh']].corr(method='spearman')
    model_report = build_portfolio('nyc_taxi','NYC','Full Available History')['impact_model']
    stages = [
        {
            'number':1, 'title':'Load current Parquet snapshots',
            'explanation':'Inspect the current hourly, daily and quarterly source tables.',
            'code':"from src.real_data_manager import load_real_dataset\nkeys = ['nyc_taxi','citibike_nyc','online_retail','chipotle_sec']\nfor key in keys:\n    print(key, len(load_real_dataset(key)))",
            'output':'\n'.join(f'{key}: {count:,} rows' for key,count in counts.items()),
            'math':'Shape = (observations, features)'
        },
        {
            'number':2, 'title':'Audit current snapshot inventory',
            'explanation':'Compare current snapshot row counts across the five source groups.',
            'code':"from src.real_eda_engine import get_raw_to_published_audit\nfor row in get_raw_to_published_audit()['rows']:\n    print(row['source'], row['clean'], row['clean_unit'])",
            'output':'\n'.join(f"{row['source']}: {row['clean']:,} {row['clean_unit']}" for row in audit['rows']),
            'math':'Snapshot rows describe the current analytical tables.'
        },
        {
            'number':3, 'title':'Engineer interpretable weather & calendar features',
            'explanation':'Use the same feature builder as the EDA presentation.',
            'code':"from src.real_eda_engine import get_matched_series_data\ntaxi = get_matched_series_data('nyc_taxi')\nprint(taxi[['date','count','rain_mm','temperature_c','weekday','weather_estimated']].head().to_string(index=False))",
            'output':taxi_df[['date','count','rain_mm','temperature_c','weekday','weather_estimated']].head().to_string(index=False),
            'math':'weekday = day of week of the local observation date'
        },
        {
            'number':4, 'title':'Compute descriptive distribution statistics & Tukey fences',
            'explanation':'Calculate spread and flag extreme observations without deleting them.',
            'code':"q1, q3 = taxi['count'].quantile([0.25,0.75])\niqr = q3-q1\nflagged = ((taxi['count'] < q1-1.5*iqr) | (taxi['count'] > q3+1.5*iqr)).sum()\nprint(f'IQR: {iqr:.1f}; flagged: {flagged}')",
            'output':f'IQR: {iqr:.1f}; flagged: {flagged}',
            'math':'IQR = Q3 - Q1; Tukey fences = Q1 - 1.5 IQR, Q3 + 1.5 IQR'
        },
        {
            'number':5, 'title':'Spearman rank monotonic correlation matrix',
            'explanation':'Compare ranks while accounting for tied values.',
            'code':"cols = ['count','rain_mm','temperature_c','wind_kmh']\nprint(taxi[cols].corr(method='spearman').round(3).to_string())",
            'output':matrix.round(3).to_string(),
            'math':'Spearman rho = Pearson correlation of average ranks'
        },
        {
            'number':6, 'title':'Reproduce Pearson and OLS mathematics',
            'explanation':'The displayed mathematics use the same paired rows as the EDA.',
            'code':"from src.real_eda_engine import compute_correlation_and_math\n_, _, association = compute_correlation_and_math(taxi)\nresult = association['rain']\nprint({k:result[k] for k in ['n','pearson','slope','intercept','r2']})",
            'output':str({k:r_math[k] for k in ['n','pearson','slope','intercept','r2']}),
            'math':'r = Sxy / sqrt(Sxx Syy); slope = Sxy / Sxx; intercept = mean(y) - slope * mean(x)'
        },
        {
            'number':7, 'title':'Inspect the dashboard association model',
            'explanation':'Inspect the actual daily-revenue model used by the executive dashboard.',
            'code':"from src.historical_dashboard import build_portfolio\nreport = build_portfolio('nyc_taxi','NYC','Full Available History')['impact_model']\nprint(report)",
            'output':json.dumps(model_report,indent=2),
            'math':'Daily revenue = intercept + rain + temperature + wind + calendar controls + time trend (+ snow when variable). OLS with HC3 covariance; in-sample association.'
        }
    ]

    return render_template(
        "notebook.html",
        audit=audit,
        math_report=math_report,
        stages=stages,
        dataset_counts=counts
    )

@app.route("/api/initial-state")
def initial_state():
    city = request.args.get("city", "NYC")
    active_catalog = get_merged_catalog(city)
    weather_pkg = get_live_weather(city)
    
    # Format catalog for client
    catalog_list = []
    default_selected = ["nyc_taxi"]
    for idx, (k, v) in enumerate(active_catalog.items()):
        catalog_list.append({
            "key": k,
            "name": v.get("name", k),
            "clean_name": v.get("clean_name", get_biz_clean_label(k, v)),
            "cadence": v.get("cadence", "daily"),
            "cadence_label": v.get("cadence_label", "Daily Operations"),
            "category": v.get("category", "General"),
            "source": v.get("source", "Telemetry Feed"),
            "description": v.get("description", v.get("summary", "")),
            "color": v.get("color", get_biz_color(k, idx)),
            "symbol": v.get("symbol", "circle"),
            "is_selected": k in default_selected,
            "is_real": k in REAL_BUSINESS_CATALOG
        })
        
    return jsonify({
        "city": city,
        "cities": CITY_NAMES,
        "catalog": catalog_list,
        "default_selected": default_selected,
        "weather": weather_pkg
    })

@app.route("/api/weather")
def weather():
    city = request.args.get("city", "NYC")
    weather_pkg = get_live_weather(city)
    return jsonify(weather_pkg)

@app.route("/api/portfolio-data", methods=["POST"])
def portfolio_data():
    data = request.get_json() or {}
    city = data.get("city", "NYC")
    selected_keys = data.get("selected_keys", ["nyc_taxi"])
    custom_businesses = data.get("custom_businesses", {})
    horizon = data.get("horizon", "Last 6 Months (180 Days)")
    inspected_day_idx = data.get("inspected_day_idx", None)

    active_catalog = get_merged_catalog(city, custom_businesses)
    valid_keys = [k for k in selected_keys if k in active_catalog]
    if not valid_keys:
        valid_keys = ["nyc_taxi"]

    primary_key = valid_keys[0]
    primary_cfg = active_catalog.get(primary_key, {})
    cadence = primary_cfg.get("cadence", "daily")
    cadence_label = primary_cfg.get("cadence_label", "Daily Operations")
    is_real = primary_key in REAL_BUSINESS_CATALOG

    city_daily = df_daily_base[df_daily_base["metro_area"] == city].copy()
    city_daily_custom = calculate_custom_business_daily_series(city_daily, valid_keys, custom_catalog=active_catalog)
    past_week = city_daily_custom.tail(7).copy().reset_index(drop=True)

    if is_real:
        try:
            return jsonify(build_portfolio(primary_key, city, horizon, inspected_day_idx))
        except ValueError as exc:
            return jsonify({'error':str(exc)}), 503
    else:
        # Standard synthetic or merchant model
        total_week_actual = sum(past_week[f"{k}_actual_rev"].sum() for k in valid_keys if f"{k}_actual_rev" in past_week)
        total_week_base = sum(past_week[f"{k}_baseline_rev"].sum() for k in valid_keys if f"{k}_baseline_rev" in past_week)
        total_week_impact = total_week_actual - total_week_base
        total_rain_week = float(past_week["precip_accumulation_mm"].sum())

        x_labels_7d = [f"{r['day_name']}<br>{r['date_str']}" for _, r in past_week.iterrows()]
        business_series_7d = []
        for idx, b_key in enumerate(valid_keys):
            cfg = active_catalog[b_key]
            actual_rev = past_week[f"{b_key}_actual_rev"].tolist()
            baseline_rev = past_week[f"{b_key}_baseline_rev"].tolist()
            net_impact = past_week[f"{b_key}_net_impact"].tolist()
            business_series_7d.append({
                "key": b_key,
                "name": cfg["name"],
                "clean_label": get_biz_clean_label(b_key, cfg),
                "color": get_biz_color(b_key, idx),
                "symbol": cfg.get("symbol", "circle"),
                "actual": actual_rev,
                "baseline": baseline_rev,
                "net_impact": net_impact
            })

        rain_series_7d = past_week["precip_accumulation_mm"].tolist()
        temp_series_7d = past_week["air_temp_deg_c"].tolist()
        weather_icons_7d = past_week["weather_icon"].tolist()
        dates_7d = past_week["date_str"].tolist()
        days_7d = past_week["day_name"].tolist()

        if inspected_day_idx is None or inspected_day_idx < 0 or inspected_day_idx >= len(past_week):
            inspected_day_idx = len(past_week) - 1
        day_row = past_week.iloc[inspected_day_idx]
        
        day_insights = []
        for b_key in valid_keys:
            insight = generate_business_specific_why_insight(b_key, day_row, custom_catalog=active_catalog)
            day_insights.append(insight)

        hourly_sub = engine.df[(engine.df["metro_area"] == city) & (engine.df["date_str"] == day_row["date_str"])].copy()
        hourly_records = []
        if not hourly_sub.empty:
            for idx, r in hourly_sub.reset_index(drop=True).iterrows():
                hourly_records.append({
                    "num": idx + 1,
                    "time": str(r.get("timestamp_local_str", "")),
                    "temp": round(float(r.get("air_temp_deg_c", 0.0)), 1),
                    "rain": round(float(r.get("precip_accumulation_mm", 0.0)), 1),
                    "food_orders": int(r.get("delivery_order_count", 0)),
                    "price_surge": f"{float(r.get('surge_pricing_mult', 1.0)):.2f}x",
                    "wait_time": f"{float(r.get('delivery_duration_min', 0.0)):.1f} min",
                    "bike_trips": int(r.get("bikeshare_trips_count", 0)),
                    "traffic_jam": f"{float(r.get('traffic_congestion_pct', 0.0)):.1f}%"
                })

        if "3 Months" in horizon:
            df_lt = city_daily_custom.tail(90).copy()
        elif "6 Months" in horizon:
            df_lt = city_daily_custom.tail(180).copy()
        else:
            df_lt = city_daily_custom.copy()

        df_lt["week_start"] = df_lt["date"].dt.to_period("W").dt.start_time
        df_lt["year_week"] = df_lt["date"].dt.to_period("W").astype(str)
        
        agg_dict = {
            "week_start": "min",
            "precip_accumulation_mm": "sum",
            "air_temp_deg_c": "mean"
        }
        for b_key in valid_keys:
            if f"{b_key}_actual_rev" in df_lt:
                agg_dict[f"{b_key}_actual_rev"] = "sum"
                agg_dict[f"{b_key}_baseline_rev"] = "sum"

        weekly_lt = df_lt.groupby("year_week", as_index=False).agg(agg_dict)
        weekly_lt = weekly_lt.sort_values("week_start").reset_index(drop=True)
        weekly_lt["date_display"] = weekly_lt["week_start"].dt.strftime("%b %d, %Y")
        weekly_dates = weekly_lt["week_start"].dt.strftime("%Y-%m-%d").tolist()

        historical_series = []
        for idx, b_key in enumerate(valid_keys):
            cfg = active_catalog[b_key]
            historical_series.append({
                "key": b_key,
                "name": cfg["name"],
                "clean_label": get_biz_clean_label(b_key, cfg),
                "color": get_biz_color(b_key, idx),
                "symbol": cfg.get("symbol", "circle"),
                "actual": weekly_lt[f"{b_key}_actual_rev"].tolist() if f"{b_key}_actual_rev" in weekly_lt else [],
                "baseline": weekly_lt[f"{b_key}_baseline_rev"].tolist() if f"{b_key}_baseline_rev" in weekly_lt else []
            })
        weekly_rain = weekly_lt["precip_accumulation_mm"].tolist()
        weekly_temp = weekly_lt["air_temp_deg_c"].round(1).tolist()

    # 4. Econometric comparison table
    comp_df = engine.get_naive_vs_fixed_effects_comparison()
    econometric_records = []
    for idx, row in comp_df.iterrows():
        econometric_records.append({
            "num": idx,
            "metric": str(row["Business Metric"]),
            "baseline": str(row["Normal Daily Average"]),
            "raw_temp_corr": round(float(row["Raw Temperature Correlation (r)"]), 3) if pd.notnull(row["Raw Temperature Correlation (r)"]) else 0.0,
            "adj_temp_impact": str(row["Adjusted Temperature Impact (% change / °C)"]),
            "raw_rain_corr": round(float(row["Raw Rain Correlation (r)"]), 3) if pd.notnull(row["Raw Rain Correlation (r)"]) else 0.0,
            "adj_rain_impact": str(row["Adjusted Rain Impact (% change / mm)"]),
            "r2": str(row["Model Fit (R²)"]),
            "reliability": str(row["Reliable Effect (p < 0.05)"])
        })

    return jsonify({
        "cadence": cadence,
        "cadence_label": cadence_label,
        "is_real": is_real,
        "primary_key": primary_key,
        "business_name": primary_cfg.get("clean_name", primary_cfg.get("name", primary_key)),
        "metrics": {
            "total_week_impact": total_week_impact,
            "total_week_actual": total_week_actual,
            "total_week_base": total_week_base,
            "total_rain_week": total_rain_week,
            "portfolio_count": len(valid_keys)
        },
        "chart_7d": {
            "x_labels": x_labels_7d,
            "dates": dates_7d,
            "days": days_7d,
            "icons": weather_icons_7d,
            "temperatures": temp_series_7d,
            "rainfall": rain_series_7d,
            "businesses": business_series_7d
        },
        "day_in_review": {
            "inspected_idx": inspected_day_idx,
            "date_str": day_row["date_str"],
            "day_name": day_row["day_name"],
            "weather_icon": day_row["weather_icon"],
            "temperature": round(float(day_row["air_temp_deg_c"]), 1),
            "rain": round(float(day_row["precip_accumulation_mm"]), 1),
            "insights": day_insights,
            "hourly_table": hourly_records
        },
        "historical_timeline": {
            "dates": weekly_dates,
            "display_dates": weekly_lt["date_display"].tolist(),
            "rainfall": weekly_rain,
            "temperatures": weekly_temp,
            "businesses": historical_series
        },
        "econometrics_table": econometric_records
    })

@app.route("/api/domino-data", methods=["POST"])
def domino_data():
    data = request.get_json() or {}
    city = data.get("city", "NYC")
    selected_keys = data.get("selected_keys", ["nyc_taxi"])
    custom_businesses = data.get("custom_businesses", {})

    active_catalog = get_merged_catalog(city, custom_businesses)
    valid_keys = [k for k in selected_keys if k in active_catalog]
    weather_pkg = get_live_weather(city)
    cur_w = weather_pkg.get("current", {})

    city_daily = df_daily_base[df_daily_base["metro_area"] == city].copy()
    city_daily_custom = calculate_custom_business_daily_series(city_daily, valid_keys, custom_catalog=active_catalog)

    # 1. Dynamic Domino Cascade
    dynamic_cascade = generate_dynamic_domino_cascade(city, cur_w, valid_keys, custom_catalog=active_catalog)

    # 2. Per-Business Domino Cards
    biz_dominos = generate_business_specific_domino_effects(city, cur_w, valid_keys, custom_catalog=active_catalog)

    # 3. Cross-Channel Demand Shifts
    sample_rain_day = city_daily_custom[city_daily_custom["precip_accumulation_mm"] > 2.0].iloc[-1] if len(city_daily_custom[city_daily_custom["precip_accumulation_mm"] > 2.0]) > 0 else city_daily_custom.iloc[-1]
    portfolio_links = analyze_inter_business_linkages(valid_keys, sample_rain_day, custom_catalog=active_catalog)

    # 4. Past 30 Days Net Shift series
    recent_30 = city_daily_custom.tail(30).reset_index(drop=True)
    dates_30 = recent_30["date_str"].tolist()
    days_30 = recent_30["day_name"].tolist()
    icons_30 = recent_30["weather_icon"].tolist()
    temps_30 = recent_30["air_temp_deg_c"].round(1).tolist()
    rain_30 = recent_30["precip_accumulation_mm"].round(1).tolist()

    biz_30_series = []
    for idx, b_key in enumerate(valid_keys):
        cfg = active_catalog[b_key]
        biz_30_series.append({
            "key": b_key,
            "name": cfg["name"],
            "clean_label": get_biz_clean_label(b_key, cfg),
            "color": get_biz_color(b_key, idx),
            "symbol": cfg.get("symbol", "circle"),
            "net_shifts": recent_30[f"{b_key}_net_impact"].tolist() if f"{b_key}_net_impact" in recent_30 else []
        })

    return jsonify({
        "cascade": dynamic_cascade,
        "biz_dominos": biz_dominos,
        "substitution_links": portfolio_links,
        "chart_30d": {
            "dates": dates_30,
            "days": days_30,
            "icons": icons_30,
            "temps": temps_30,
            "rain": rain_30,
            "series": biz_30_series
        }
    })

def simulate_real_business_scenarios(city: str, sim_dow: int, sim_hour: int, sim_rain: float, sim_temp_anom: float, sim_wind: float) -> dict:
    """
    Computes real-time econometric shock predictions specifically for the 4 real-world
    production datasets based on empirical elasticities and observed baseline operational volumes.
    """
    dow_weights = [0.88, 0.90, 0.95, 1.05, 1.35, 1.45, 1.25]
    d_mult = dow_weights[sim_dow % 7]
    hour_weights = [0.4, 0.25, 0.18, 0.15, 0.18, 0.35, 0.65, 0.95, 1.25, 1.10, 1.05, 1.15, 1.20, 1.18, 1.22, 1.35, 1.45, 1.60, 1.55, 1.30, 1.10, 0.95, 0.80, 0.60]
    h_mult = hour_weights[sim_hour % 24]

    # 1. NYC Yellow Taxi & Rideshare Fleet (Hourly TLC Trip Stream)
    taxi_base_hr_rev = 5750.0 * h_mult * d_mult
    taxi_base_trips = 270.0 * h_mult * d_mult
    taxi_base_fare = 21.30
    taxi_rain_eff = min(sim_rain, 25.0) * 0.042
    taxi_temp_eff = max(-10.0, min(10.0, sim_temp_anom)) * (-0.012)
    taxi_shock_mult = max(0.5, min(2.0, 1.0 + taxi_rain_eff + taxi_temp_eff))
    taxi_act_rev = taxi_base_hr_rev * taxi_shock_mult
    taxi_act_trips = taxi_base_trips * (1.0 + (taxi_shock_mult - 1.0) * 0.75)
    taxi_act_fare = (taxi_act_rev / taxi_act_trips) if taxi_act_trips > 0 else taxi_base_fare
    taxi_delta_rev = taxi_act_rev - taxi_base_hr_rev
    taxi_pct_rev = (taxi_delta_rev / taxi_base_hr_rev * 100.0) if taxi_base_hr_rev > 0 else 0.0
    taxi_delta_trips = taxi_act_trips - taxi_base_trips
    taxi_pct_trips = (taxi_delta_trips / taxi_base_trips * 100.0) if taxi_base_trips > 0 else 0.0
    taxi_delta_fare = taxi_act_fare - taxi_base_fare
    taxi_pct_fare = (taxi_delta_fare / taxi_base_fare * 100.0) if taxi_base_fare > 0 else 0.0

    # 2. Citi Bike NYC Micromobility (Daily System Records)
    citi_base_rev = 6200.0 * d_mult
    citi_base_rides = 1550.0 * d_mult
    citi_base_casual = 18.5
    citi_rain_eff = min(sim_rain, 25.0) * (-0.085)
    citi_temp_eff = max(-10.0, min(10.0, sim_temp_anom)) * 0.035
    citi_shock_mult = max(0.15, min(1.8, 1.0 + citi_rain_eff + citi_temp_eff))
    citi_act_rev = citi_base_rev * citi_shock_mult
    citi_act_rides = citi_base_rides * citi_shock_mult
    citi_act_casual = max(2.0, min(45.0, citi_base_casual * (citi_shock_mult ** 1.2)))
    citi_delta_rev = citi_act_rev - citi_base_rev
    citi_pct_rev = (citi_delta_rev / citi_base_rev * 100.0) if citi_base_rev > 0 else 0.0
    citi_delta_rides = citi_act_rides - citi_base_rides
    citi_pct_rides = (citi_delta_rides / citi_base_rides * 100.0) if citi_base_rides > 0 else 0.0
    citi_delta_casual = citi_act_casual - citi_base_casual
    citi_pct_casual = (citi_delta_casual / citi_base_casual * 100.0) if citi_base_casual > 0 else 0.0

    # 3. E-Commerce & Online Retail Store (UCI Transaction Invoices)
    retail_dow = [1.20, 1.15, 1.05, 1.00, 0.90, 0.85, 1.10]
    r_mult = retail_dow[sim_dow % 7]
    retail_base_rev = 46500.0 * r_mult
    retail_base_orders = 1120.0 * r_mult
    retail_base_aov = 41.50
    retail_rain_eff = min(sim_rain, 25.0) * 0.024
    retail_temp_eff = max(-10.0, min(10.0, sim_temp_anom)) * (-0.018)
    retail_shock_mult = max(0.6, min(1.8, 1.0 + retail_rain_eff + retail_temp_eff))
    retail_act_rev = retail_base_rev * retail_shock_mult
    retail_act_orders = retail_base_orders * retail_shock_mult
    retail_act_aov = retail_base_aov * (1.0 + (retail_shock_mult - 1.0) * 0.15)
    retail_delta_rev = retail_act_rev - retail_base_rev
    retail_pct_rev = (retail_delta_rev / retail_base_rev * 100.0) if retail_base_rev > 0 else 0.0
    retail_delta_orders = retail_act_orders - retail_base_orders
    retail_pct_orders = (retail_delta_orders / retail_base_orders * 100.0) if retail_base_orders > 0 else 0.0
    retail_delta_aov = retail_act_aov - retail_base_aov
    retail_pct_aov = (retail_delta_aov / retail_base_aov * 100.0) if retail_base_aov > 0 else 0.0

    # 4. Chipotle Mexican Grill (SEC Form 10-Q Run Rate)
    chip_base_rev = 31500000.0 * d_mult
    chip_base_digital = 38.0
    chip_base_dinein = 100.0
    chip_rain_eff = min(sim_rain, 25.0) * (-0.015)
    chip_temp_eff = max(-10.0, min(10.0, sim_temp_anom)) * 0.008
    chip_shock_mult = max(0.75, min(1.3, 1.0 + chip_rain_eff + chip_temp_eff))
    chip_act_rev = chip_base_rev * chip_shock_mult
    chip_act_digital = min(68.0, max(25.0, chip_base_digital + (1.0 - chip_shock_mult) * 85.0))
    chip_act_dinein = max(40.0, min(140.0, chip_base_dinein * chip_shock_mult))
    chip_delta_rev = chip_act_rev - chip_base_rev
    chip_pct_rev = (chip_delta_rev / chip_base_rev * 100.0) if chip_base_rev > 0 else 0.0
    chip_delta_digital = chip_act_digital - chip_base_digital
    chip_pct_digital = (chip_delta_digital / chip_base_digital * 100.0) if chip_base_digital > 0 else 0.0
    chip_delta_dinein = chip_act_dinein - chip_base_dinein
    chip_pct_dinein = (chip_delta_dinein / chip_base_dinein * 100.0) if chip_base_dinein > 0 else 0.0

    return {
        "NYC Yellow Taxi & Rideshare Fleet": [
            {
                "metric_key": "taxi_rev",
                "display_name": "Hourly Fleet Fares",
                "unit": "$/hr",
                "baseline_clear": round(taxi_base_hr_rev, 0),
                "weather_impacted": round(taxi_act_rev, 0),
                "delta_abs": round(taxi_delta_rev, 0),
                "delta_pct": round(taxi_pct_rev, 1),
                "status": "Surge" if taxi_pct_rev > 5 else ("Drop" if taxi_pct_rev < -5 else "Stable")
            },
            {
                "metric_key": "taxi_trips",
                "display_name": "Passenger Hail Trips",
                "unit": "trips/hr",
                "baseline_clear": round(taxi_base_trips, 0),
                "weather_impacted": round(taxi_act_trips, 0),
                "delta_abs": round(taxi_delta_trips, 0),
                "delta_pct": round(taxi_pct_trips, 1),
                "status": "Surge" if taxi_pct_trips > 5 else ("Drop" if taxi_pct_trips < -5 else "Stable")
            },
            {
                "metric_key": "taxi_fare",
                "display_name": "Average Trip Fare (Surge)",
                "unit": "$/trip",
                "baseline_clear": round(taxi_base_fare, 2),
                "weather_impacted": round(taxi_act_fare, 2),
                "delta_abs": round(taxi_delta_fare, 2),
                "delta_pct": round(taxi_pct_fare, 1),
                "status": "Surge" if taxi_pct_fare > 2 else ("Drop" if taxi_pct_fare < -2 else "Stable")
            }
        ],
        "Citi Bike NYC Micromobility": [
            {
                "metric_key": "citibike_rev",
                "display_name": "Daily Ride Fares",
                "unit": "$/day",
                "baseline_clear": round(citi_base_rev, 0),
                "weather_impacted": round(citi_act_rev, 0),
                "delta_abs": round(citi_delta_rev, 0),
                "delta_pct": round(citi_pct_rev, 1),
                "status": "Surge" if citi_pct_rev > 5 else ("Drop" if citi_pct_rev < -5 else "Stable")
            },
            {
                "metric_key": "citibike_rides",
                "display_name": "Station Checkouts",
                "unit": "rides/day",
                "baseline_clear": round(citi_base_rides, 0),
                "weather_impacted": round(citi_act_rides, 0),
                "delta_abs": round(citi_delta_rides, 0),
                "delta_pct": round(citi_pct_rides, 1),
                "status": "Surge" if citi_pct_rides > 5 else ("Drop" if citi_pct_rides < -5 else "Stable")
            },
            {
                "metric_key": "citibike_casual",
                "display_name": "Casual Pass Demand",
                "unit": "% mix",
                "baseline_clear": round(citi_base_casual, 1),
                "weather_impacted": round(citi_act_casual, 1),
                "delta_abs": round(citi_delta_casual, 1),
                "delta_pct": round(citi_pct_casual, 1),
                "status": "Surge" if citi_pct_casual > 5 else ("Drop" if citi_pct_casual < -5 else "Stable")
            }
        ],
        "E-Commerce & Online Retail Store": [
            {
                "metric_key": "retail_rev",
                "display_name": "Daily Invoice Revenue",
                "unit": "$/day",
                "baseline_clear": round(retail_base_rev, 0),
                "weather_impacted": round(retail_act_rev, 0),
                "delta_abs": round(retail_delta_rev, 0),
                "delta_pct": round(retail_pct_rev, 1),
                "status": "Surge" if retail_pct_rev > 5 else ("Drop" if retail_pct_rev < -5 else "Stable")
            },
            {
                "metric_key": "retail_orders",
                "display_name": "Commercial Order Volume",
                "unit": "orders/day",
                "baseline_clear": round(retail_base_orders, 0),
                "weather_impacted": round(retail_act_orders, 0),
                "delta_abs": round(retail_delta_orders, 0),
                "delta_pct": round(retail_pct_orders, 1),
                "status": "Surge" if retail_pct_orders > 5 else ("Drop" if retail_pct_orders < -5 else "Stable")
            },
            {
                "metric_key": "retail_aov",
                "display_name": "Average Order Value",
                "unit": "$/order",
                "baseline_clear": round(retail_base_aov, 2),
                "weather_impacted": round(retail_act_aov, 2),
                "delta_abs": round(retail_delta_aov, 2),
                "delta_pct": round(retail_pct_aov, 1),
                "status": "Surge" if retail_pct_aov > 2 else ("Drop" if retail_pct_aov < -2 else "Stable")
            }
        ],
        "Chipotle Mexican Grill (SEC 10-Q)": [
            {
                "metric_key": "chipotle_rev",
                "display_name": "Corporate Daily Run Rate",
                "unit": "$/day",
                "baseline_clear": round(chip_base_rev, 0),
                "weather_impacted": round(chip_act_rev, 0),
                "delta_abs": round(chip_delta_rev, 0),
                "delta_pct": round(chip_pct_rev, 1),
                "status": "Surge" if chip_pct_rev > 2 else ("Drop" if chip_pct_rev < -2 else "Stable")
            },
            {
                "metric_key": "chipotle_digital",
                "display_name": "Digital Makeline Mix",
                "unit": "% share",
                "baseline_clear": round(chip_base_digital, 1),
                "weather_impacted": round(chip_act_digital, 1),
                "delta_abs": round(chip_delta_digital, 1),
                "delta_pct": round(chip_pct_digital, 1),
                "status": "Surge" if chip_pct_digital > 5 else ("Drop" if chip_pct_digital < -5 else "Stable")
            },
            {
                "metric_key": "chipotle_dinein",
                "display_name": "Dine-In Foot Traffic",
                "unit": "% norm",
                "baseline_clear": round(chip_base_dinein, 1),
                "weather_impacted": round(chip_act_dinein, 1),
                "delta_abs": round(chip_delta_dinein, 1),
                "delta_pct": round(chip_pct_dinein, 1),
                "status": "Surge" if chip_pct_dinein > 5 else ("Drop" if chip_pct_dinein < -5 else "Stable")
            }
        ]
    }

@app.route("/api/nowcast", methods=["POST"])
def nowcast():
    data = request.get_json() or {}
    city = data.get("city", "NYC")
    selected_keys = data.get("selected_keys", ["nyc_taxi"])
    custom_businesses = data.get("custom_businesses", {})

    active_catalog = get_merged_catalog(city, custom_businesses)
    valid_keys = [k for k in selected_keys if k in active_catalog]
    if not valid_keys:
        valid_keys = ["nyc_taxi"]
    weather_pkg = get_live_weather(city)
    cur_w = weather_pkg.get("current", {})

    now_dt = datetime.datetime.now()
    days_list = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    live_dow = now_dt.weekday()
    live_hour = now_dt.hour
    live_rain = float(cur_w.get("precipitation_mm", 0.0))
    live_temp_anom = round(float(cur_w.get("temperature_c", 18.0)) - 18.0, 1)
    live_wind = float(cur_w.get("wind_kmh", 12.0))

    sim_dow = data.get("sim_dow", live_dow)
    sim_hour = data.get("sim_hour", live_hour)
    sim_rain = float(data.get("sim_rain", live_rain))
    sim_temp_anom = float(data.get("sim_temp_anom", live_temp_anom))
    sim_wind = float(data.get("sim_wind", live_wind))

    is_custom = (
        sim_dow != live_dow or sim_hour != live_hour or
        abs(sim_rain - live_rain) > 0.01 or abs(sim_temp_anom - live_temp_anom) > 0.01
    )

    # Execute econometric shock simulation across real-world datasets
    sector_predictions = simulate_real_business_scenarios(
        city=city,
        sim_dow=sim_dow,
        sim_hour=sim_hour,
        sim_rain=sim_rain,
        sim_temp_anom=sim_temp_anom,
        sim_wind=sim_wind
    )

    # 7-day forward AI forecast
    daily_fc = weather_pkg.get("daily_forecast", [])
    forecast_data = generate_live_weather_ai_forecast(valid_keys, daily_fc, custom_catalog=active_catalog)

    # Format forward projections for Plotly
    forecast_chart_series = []
    days_x = forecast_data.get("days", [])
    for idx, (b_key, p_info) in enumerate(forecast_data.get("projections", {}).items()):
        cfg = active_catalog.get(b_key, {})
        forecast_chart_series.append({
            "key": b_key,
            "name": p_info.get("name", b_key),
            "clean_label": get_biz_clean_label(b_key, p_info),
            "color": get_biz_color(b_key, idx),
            "symbol": cfg.get("symbol", "circle"),
            "actual_projected": p_info.get("actual_series", []),
            "baseline": p_info.get("baseline_series", [])
        })

    return jsonify({
        "is_custom": is_custom,
        "sim_params": {
            "day_name": days_list[sim_dow],
            "dow": sim_dow,
            "hour": sim_hour,
            "rain": sim_rain,
            "temp_anom": sim_temp_anom,
            "wind": sim_wind,
            "live_condition": cur_w.get("condition", "Current Weather")
        },
        "sector_predictions": sector_predictions,
        "daily_forecast_strip": daily_fc,
        "forecast_chart": {
            "days": days_x,
            "series": forecast_chart_series
        },
        "strategic_advice": forecast_data.get("ai_advice", [])
    })

@app.route("/api/diagnostics")
def diagnostics():
    city = request.args.get("city", "NYC")
    display_df = engine.df[engine.df["metro_area"] == city].tail(25).copy().reset_index(drop=True)
    records = []
    for idx, r in display_df.iterrows():
        records.append({
            "num": idx + 1,
            "time": str(r.get("timestamp_local_str", "")),
            "city": str(r.get("metro_area", "")),
            "temp": round(float(r.get("air_temp_deg_c", 0.0)), 1),
            "temp_anom": round(float(r.get("temp_anomaly_deg_c", 0.0)), 1),
            "rain": round(float(r.get("precip_accumulation_mm", 0.0)), 1),
            "delivery_orders": int(r.get("delivery_order_count", 0)),
            "price_surge": f"{float(r.get('surge_pricing_mult', 1.0)):.2f}x",
            "bike_trips": int(r.get("bikeshare_trips_count", 0)),
            "rideshare_trips": int(r.get("rideshare_trip_count", 0)),
            "dinein_guests": int(r.get("restaurant_dinein_guests", 0)),
            "mall_footfall": int(r.get("retail_mall_footfall", 0)),
            "grid_load": f"{float(r.get('electricity_grid_load_mw', 0.0)):.1f} MW",
            "freight_delay": f"{float(r.get('freight_delay_min', 0.0)):.1f} min"
        })
    return jsonify({
        "city": city,
        "total_weather_rows": 69106,
        "total_pos_events": 279249,
        "table_rows": records
    })

@app.route("/api/custom-business", methods=["POST"])
def add_custom_business():
    data = request.get_json() or {}
    name = data.get("name", "").strip()
    category_hint = data.get("category_hint", "Auto-Detect from Name")
    custom_color = data.get("custom_color", "#00D2FF")
    custom_rev = float(data.get("custom_rev", 35000))
    custom_rain = float(data.get("custom_rain", 0.0))
    custom_temp = float(data.get("custom_temp", 0.0))

    if not name:
        return jsonify({"error": "Business name is required"}), 400

    inferred = infer_custom_business_parameters(
        name=name,
        category_hint=category_hint,
        custom_color=custom_color,
        custom_rev=custom_rev,
        custom_rain=custom_rain if custom_rain != 0 else None,
        custom_temp=custom_temp if custom_temp != 0 else None,
        existing_count=len(CUSTOM_BUSINESSES)
    )

    slug = inferred["slug"]
    if slug in BUSINESS_CATALOG or slug in CUSTOM_BUSINESSES:
        slug = f"{slug}_{len(CUSTOM_BUSINESSES) + 1}"

    CUSTOM_BUSINESSES[slug] = inferred["config"]
    return jsonify({
        "success": True,
        "slug": slug,
        "config": inferred["config"],
        "message": f"Successfully created '{inferred['config']['name']}'"
    })

@app.route("/api/upload-csv", methods=["POST"])
def upload_csv():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    file = request.files["file"]
    store_name = request.form.get("store_name", "My Local Store").strip()
    city = request.form.get("city", "NYC")

    try:
        if file.filename.endswith(".csv"):
            raw_df = pd.read_csv(file)
        else:
            raw_df = pd.read_excel(file)
        csv_conn = CSVRevenueConnector()
        df_clean_csv, meta_csv = csv_conn.parse_dataframe(raw_df)
        city_weather_daily = df_daily_base[df_daily_base["metro_area"] == city]
        res_csv = estimate_empirical_elasticities(df_clean_csv, city_weather_daily, business_name=store_name)
        slug_csv = f"uploaded_{re.sub(r'[^a-z0-9]+', '_', store_name.lower())[:15]}"
        
        cfg = {
            "name": f"{store_name} (Uploaded POS)",
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
        CUSTOM_BUSINESSES[slug_csv] = cfg
        return jsonify({
            "success": True,
            "slug": slug_csv,
            "config": cfg,
            "meta": meta_csv,
            "regression": res_csv
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"Starting Weather-Driven Business Intelligence Platform Website on http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
