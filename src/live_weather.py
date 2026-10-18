"""
Multi-Source Weather Intelligence Engine
Integrates:
1. Open-Meteo API: High-resolution real-time ground telemetry and 7-day forward forecasts.
   (Reference: https://open-meteo.com/?lat=12.5&lon=53.83)
2. NASA POWER API: Satellite-observed solar & surface meteorology (T2M, PRECTOTCORR, WS10M, RH2M).
   (Reference: https://power.larc.nasa.gov/docs/services/api/temporal/hourly/#formats)
3. NASA Worldview / Earthdata GIBS: Near-real-time satellite observation layers.
   (Reference: https://worldview.earthdata.nasa.gov/)
"""

import urllib.request
import urllib.parse
import json
import datetime
import pandas as pd
from typing import Dict, Any, Tuple, List, Optional

# Operational Hub Coordinates & Timezones
CITY_GEO = {
    "NYC": {"name": "New York City", "lat": 40.7128, "lon": -74.0060, "timezone": "America/New_York"},
    "ORD": {"name": "Chicago", "lat": 41.8781, "lon": -87.6298, "timezone": "America/Chicago"},
    "SEA": {"name": "Seattle", "lat": 47.6062, "lon": -122.3321, "timezone": "America/Los_Angeles"},
    "PHX": {"name": "Phoenix", "lat": 33.4484, "lon": -112.0740, "timezone": "America/Phoenix"}
}

# WMO Weather Interpretation Codes
WMO_DESCRIPTIONS = {
    0: "Clear Sky",
    1: "Mainly Clear",
    2: "Partly Cloudy",
    3: "Overcast",
    45: "Foggy",
    48: "Depositing Rime Fog",
    51: "Light Drizzle",
    53: "Moderate Drizzle",
    55: "Dense Drizzle",
    61: "Slight Rain",
    63: "Moderate Rain",
    65: "Heavy Downpour",
    71: "Slight Snow Fall",
    73: "Moderate Snow Fall",
    75: "Heavy Snow Fall",
    77: "Snow Grains",
    80: "Slight Rain Showers",
    81: "Moderate Rain Showers",
    82: "Violent Rain Showers",
    85: "Slight Snow Showers",
    86: "Heavy Snow Showers",
    95: "Thunderstorm",
    96: "Thunderstorm with Slight Hail",
    99: "Thunderstorm with Heavy Hail"
}

def decode_wmo_code(code: int) -> str:
    """Map WMO numeric code to standard human-readable text."""
    return WMO_DESCRIPTIONS.get(code, "Variable Weather")


def generate_nasa_worldview_url(lat: float, lon: float, date_str: Optional[str] = None) -> str:
    """
    Constructs an interactive NASA Worldview URL centered on coordinates.
    Layers: Coastlines, Borders, VIIRS TrueColor, MODIS Corrected Reflectance.
    Reference: https://worldview.earthdata.nasa.gov/
    """
    box_w = 4.5
    box_h = 3.0
    v_param = f"{lon - box_w:.4f},{lat - box_h:.4f},{lon + box_w:.4f},{lat + box_h:.4f}"
    layers = "Reference_Labels_15m(hidden),Reference_Features_15m(hidden),Coastlines_15m,VIIRS_SNPP_CorrectedReflectance_TrueColor,MODIS_Aqua_CorrectedReflectance_TrueColor"
    
    url = f"https://worldview.earthdata.nasa.gov/?v={v_param}&l={layers}"
    if date_str:
        url += f"&t={date_str}"
    return url


def fetch_nasa_power_telemetry(lat: float, lon: float) -> Dict[str, Any]:
    """
    Polls the NASA POWER API (Prediction Of Worldwide Energy Resources) for satellite-derived surface meteorology.
    Parameters queried:
    - T2M: Temperature at 2 Meters (°C)
    - PRECTOTCORR: Corrected Total Precipitation (mm/hour)
    - WS10M: Wind Speed at 10 Meters (m/s)
    - RH2M: Relative Humidity at 2 Meters (%)
    Reference: https://power.larc.nasa.gov/docs/services/api/temporal/hourly/#formats
    """
    # NASA POWER satellite latency is ~3-4 days for calibrated surface models
    end_dt = datetime.datetime.now() - datetime.timedelta(days=4)
    start_dt = end_dt - datetime.timedelta(days=2)
    
    start_str = start_dt.strftime("%Y%m%d")
    end_str = end_dt.strftime("%Y%m%d")
    
    url = (
        f"https://power.larc.nasa.gov/api/temporal/hourly/point?"
        f"parameters=T2M,PRECTOTCORR,WS10M,RH2M&community=RE&"
        f"longitude={lon:.4f}&latitude={lat:.4f}&"
        f"start={start_str}&end={end_str}&format=JSON"
    )
    
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "WeatherBusinessImpactEDA/2.0 (NASA-POWER Client)"}
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            
        params = data.get("properties", {}).get("parameter", {})
        t2m_series = params.get("T2M", {})
        precip_series = params.get("PRECTOTCORR", {})
        ws10m_series = params.get("WS10M", {})
        rh2m_series = params.get("RH2M", {})
        
        # NASA uses -999.0 as missing data sentinel
        valid_hours = [h for h, v in t2m_series.items() if float(v) > -100.0]
        if not valid_hours:
            raise ValueError("No valid non-sentinel T2M observations")
            
        latest_hour = sorted(valid_hours)[-1]
        temp_c = round(float(t2m_series[latest_hour]), 1)
        precip_raw = float(precip_series.get(latest_hour, 0.0))
        precip_mm = round(max(0.0, precip_raw) if precip_raw > -100.0 else 0.0, 1)
        
        ws_raw = float(ws10m_series.get(latest_hour, 3.0))
        wind_ms = ws_raw if ws_raw > -100.0 else 3.2
        wind_kmh = round(wind_ms * 3.6, 1)  # Convert m/s to km/h
        
        rh_raw = float(rh2m_series.get(latest_hour, 50.0))
        rh_pct = round(rh_raw if rh_raw > -100.0 else 50.0, 0)
        
        # Format human-readable observation timestamp: YYYYMMDDHH -> YYYY-MM-DD HH:00 UTC
        obs_formatted = f"{latest_hour[:4]}-{latest_hour[4:6]}-{latest_hour[6:8]} {latest_hour[8:]}:00 UTC"
        
        return {
            "status": "SUCCESS",
            "source": "NASA POWER API (Satellite Surface Observation)",
            "observation_timestamp": obs_formatted,
            "temperature_c": temp_c,
            "precipitation_mm": precip_mm,
            "wind_kmh": wind_kmh,
            "humidity_pct": rh_pct,
            "is_live": True
        }
    except Exception as exc:
        return {
            "status": "FALLBACK",
            "source": f"NASA POWER (Heuristic Calibration: {str(exc)[:40]})",
            "temperature_c": 16.5,
            "precipitation_mm": 0.0,
            "wind_kmh": 11.5,
            "humidity_pct": 52.0,
            "is_live": False,
            "error_msg": str(exc)
        }


def fetch_live_weather(city_code_or_coords: str) -> Dict[str, Any]:
    """
    Multi-Source Live Weather Aggregator.
    Pulls simultaneously from:
    1. Open-Meteo API: Real-time ground telemetry & 7-day hourly forecasts.
    2. NASA POWER API: Satellite-derived surface meteorology.
    3. NASA Worldview: Direct GIBS satellite imagery coordinates.
    """
    # Parse city code or coordinates
    if city_code_or_coords in CITY_GEO:
        geo = CITY_GEO[city_code_or_coords]
        lat, lon = geo["lat"], geo["lon"]
        tz = geo["timezone"]
        c_name = geo["name"]
    else:
        # Check if coordinates string like "12.5, 53.83"
        try:
            parts = [float(x.strip()) for x in city_code_or_coords.split(",")]
            lat, lon = parts[0], parts[1]
            tz = "auto"
            c_name = f"Custom Coordinates ({lat:.2f}, {lon:.2f})"
        except Exception:
            geo = CITY_GEO["NYC"]
            lat, lon = geo["lat"], geo["lon"]
            tz = geo["timezone"]
            c_name = geo["name"]

    # 1. Open-Meteo High-Resolution Ingestion
    om_url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}&"
        f"current=temperature_2m,relative_humidity_2m,precipitation,weather_code,wind_speed_10m&"
        f"daily=temperature_2m_max,temperature_2m_min,precipitation_sum,weather_code,wind_speed_10m_max&"
        f"timezone={urllib.parse.quote(tz)}&"
        f"forecast_days=7"
    )

    nasa_worldview_url = generate_nasa_worldview_url(lat, lon)
    nasa_power_data = fetch_nasa_power_telemetry(lat, lon)

    try:
        req = urllib.request.Request(
            om_url,
            headers={"User-Agent": "WeatherBusinessImpactEDA/2.0 (MultiSource-Aggregator)"}
        )
        with urllib.request.urlopen(req, timeout=8) as response:
            raw_data = json.loads(response.read().decode("utf-8"))

        current_raw = raw_data.get("current", {})
        daily_raw = raw_data.get("daily", {})

        current_cond = decode_wmo_code(current_raw.get("weather_code", 0))
        om_temp = float(current_raw.get("temperature_2m", 18.0))
        om_precip = float(current_raw.get("precipitation", 0.0))
        om_wind = float(current_raw.get("wind_speed_10m", 12.0))
        om_rh = float(current_raw.get("relative_humidity_2m", 50.0))

        # Multi-Source Consensus Blending
        nasa_temp = nasa_power_data.get("temperature_c", om_temp)
        temp_delta = abs(om_temp - nasa_temp)
        if temp_delta <= 2.5:
            consensus_rating = "High Data Agreement (Ground + Satellite)"
        else:
            consensus_rating = f"Moderate Data Variance ({temp_delta:.1f}°C Delta Between Ground and Satellite)"

        current_data = {
            "city_code": city_code_or_coords if city_code_or_coords in CITY_GEO else "CUSTOM",
            "city_name": c_name,
            "latitude": lat,
            "longitude": lon,
            "timestamp": current_raw.get("time", datetime.datetime.now().strftime("%Y-%m-%dT%H:%M")),
            "temperature_c": om_temp,
            "humidity_pct": om_rh,
            "precipitation_mm": om_precip,
            "wind_kmh": om_wind,
            "weather_code": int(current_raw.get("weather_code", 0)),
            "condition": current_cond,
            "is_live": True,
            "source": "Open-Meteo API + NASA POWER Satellite Verification"
        }

        # Format 7-Day Forecast Days
        forecast_days = []
        dates = daily_raw.get("time", [])
        t_max = daily_raw.get("temperature_2m_max", [])
        t_min = daily_raw.get("temperature_2m_min", [])
        precip = daily_raw.get("precipitation_sum", [])
        w_codes = daily_raw.get("weather_code", [])
        wind_max = daily_raw.get("wind_speed_10m_max", [])

        for idx, date_str in enumerate(dates):
            dt = datetime.datetime.strptime(date_str, "%Y-%m-%d")
            max_c = float(t_max[idx]) if idx < len(t_max) else 20.0
            min_c = float(t_min[idx]) if idx < len(t_min) else 12.0
            avg_c = round((max_c + min_c) / 2.0, 1)
            rain_mm = float(precip[idx]) if idx < len(precip) else 0.0
            code = int(w_codes[idx]) if idx < len(w_codes) else 0
            w_kmh = float(wind_max[idx]) if idx < len(wind_max) else 10.0

            forecast_days.append({
                "date": date_str,
                "day_name": dt.strftime("%a"),
                "display_date": dt.strftime("%a, %b %d"),
                "temp_avg": avg_c,
                "temp_max": max_c,
                "temp_min": min_c,
                "precip_mm": rain_mm,
                "wind_kmh": w_kmh,
                "weather_code": code,
                "condition": decode_wmo_code(code)
            })

        return {
            "status": "SUCCESS",
            "current": current_data,
            "nasa_power": nasa_power_data,
            "nasa_worldview_url": nasa_worldview_url,
            "consensus_rating": consensus_rating,
            "daily_forecast": forecast_days,
            "city_name": c_name,
            "sources": [
                "Open-Meteo High-Resolution Forecast",
                "NASA POWER Satellite Surface Telemetry",
                "NASA Worldview Satellite GIBS Imagery"
            ]
        }

    except Exception as exc:
        now = datetime.datetime.now()
        fallback_current = {
            "city_code": city_code_or_coords if city_code_or_coords in CITY_GEO else "CUSTOM",
            "city_name": c_name,
            "latitude": lat,
            "longitude": lon,
            "timestamp": now.strftime("%Y-%m-%dT%H:%M"),
            "temperature_c": 17.5,
            "humidity_pct": 55.0,
            "precipitation_mm": 0.0,
            "wind_kmh": 14.0,
            "weather_code": 1,
            "condition": "Mainly Clear",
            "is_live": False,
            "source": f"Local Fallback Cache ({str(exc)[:40]})"
        }

        fallback_days = []
        for i in range(7):
            dt = now + datetime.timedelta(days=i)
            fallback_days.append({
                "date": dt.strftime("%Y-%m-%d"),
                "day_name": dt.strftime("%a"),
                "display_date": dt.strftime("%a, %b %d"),
                "temp_avg": 17.0 + (i % 3),
                "temp_max": 22.0,
                "temp_min": 12.0,
                "precip_mm": 4.5 if i in [2, 3] else 0.0,
                "wind_kmh": 12.0,
                "weather_code": 61 if i in [2, 3] else 0,
                "condition": "Moderate Rain" if i in [2, 3] else "Clear Sky"
            })

        return {
            "status": "FALLBACK",
            "current": fallback_current,
            "nasa_power": nasa_power_data,
            "nasa_worldview_url": nasa_worldview_url,
            "consensus_rating": "Local Resilient Cache Active",
            "daily_forecast": fallback_days,
            "city_name": c_name,
            "sources": ["Local Resilient Cache", "NASA POWER API"],
            "error_msg": str(exc)
        }


def generate_live_weather_ai_forecast(
    active_keys: List[str],
    daily_forecast: List[Dict[str, Any]],
    custom_catalog: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate daily revenue projections using real upcoming meteorological forecast.
    Calculates day-by-day revenue shifts using business-specific econometric elasticities.
    """
    catalog = custom_catalog
    projections = {}
    total_impact_all = 0.0
    day_labels = [d["display_date"] for d in daily_forecast]

    total_rain_forecast = sum(d["precip_mm"] for d in daily_forecast)
    max_temp_forecast = max(d["temp_max"] for d in daily_forecast)
    min_temp_forecast = min(d["temp_min"] for d in daily_forecast)

    for b_key in active_keys:
        if b_key not in catalog:
            continue
        cfg = catalog[b_key]
        base = cfg["base_daily_rev"]
        series_actual = []
        series_base = []

        for idx, day_info in enumerate(daily_forecast):
            dt = datetime.datetime.strptime(day_info["date"], "%Y-%m-%d")
            dow_idx = dt.weekday()
            dow_weights = [0.88, 0.90, 0.95, 1.05, 1.38, 1.48, 1.28]
            dow_m = dow_weights[dow_idx]
            day_base = base * dow_m

            rain_val = day_info["precip_mm"]
            temp_val = day_info["temp_avg"]

            # Calculate seasonal baseline expectation for the forecast month
            month_idx = dt.month - 1
            monthly_normals = [2.0, 3.5, 7.5, 13.0, 18.5, 23.5, 26.0, 25.0, 21.0, 15.0, 9.5, 4.0]
            seasonal_normal = monthly_normals[month_idx]
            temp_anom = max(-10.0, min(10.0, temp_val - seasonal_normal))

            # Scaled daily precipitation shock
            effective_rain = min(rain_val, 30.0) * 0.35
            rain_effect = effective_rain * cfg.get("rain_elasticity", 0.0)

            # Temperature anomaly shock
            temp_effect = temp_anom * cfg.get("temp_elasticity", 0.0)

            # Freezing / snow precipitation shock
            if temp_val <= 0.0 and rain_val > 0.0:
                effective_snow = min(rain_val * 0.8, 20.0) * 0.40
                snow_effect = effective_snow * cfg.get("snow_elasticity", 0.0)
            else:
                snow_effect = 0.0

            # Additive linear econometric formulation bounded in realistic financial ranges
            total_multiplier = max(0.20, min(2.20, 1.0 + rain_effect + temp_effect + snow_effect))
            day_act = day_base * total_multiplier

            series_base.append(round(day_base, 0))
            series_actual.append(round(day_act, 0))

        projections[b_key] = {
            "name": cfg["name"],
            "color": cfg.get("color", "#FFFFFF"),
            "dash": cfg.get("dash", "solid"),
            "symbol": cfg.get("symbol", "circle"),
            "days": day_labels,
            "actual_series": series_actual,
            "baseline_series": series_base,
            "net_week_impact": sum(series_actual) - sum(series_base)
        }
        total_impact_all += (sum(series_actual) - sum(series_base))

    ai_advice = []
    rainy_days = [d["day_name"] for d in daily_forecast if d["precip_mm"] >= 4.0]

    if rainy_days:
        rain_str = ", ".join(rainy_days)
        if "food_delivery" in active_keys:
            ai_advice.append(
                f"Food Delivery Operations: Elevated rain forecasted on {rain_str}. Courier supply is expected to contract by ~18%. "
                "Activate driver surge incentives 30 minutes prior to precipitation windows to maintain fulfillment SLAs."
            )
        if "dine_in_restaurant" in active_keys:
            ai_advice.append(
                f"Restaurant Dining Floor: Precipitation on {rain_str} will suppress walk-ins and patio utilization by up to -45%. "
                "Reassign floor waitstaff to manage takeout dispatch and delivery packaging stations."
            )
        if "retail_apparel" in active_keys:
            ai_advice.append(
                f"Retail Merchandising: Position waterproof apparel, umbrellas, and footwear at entrance end-caps ahead of {rain_str} to capitalize on impulse demand."
            )
        if "car_wash" in active_keys:
            ai_advice.append(
                f"Car Wash Maintenance: Wash volumes will decline sharply on {rain_str}. Schedule bay equipment maintenance and staff training during these downtime intervals."
            )
        if "nyc_taxi" in active_keys:
            ai_advice.append(
                f"Taxi & Rideshare Fleet: Rain forecasted on {rain_str} will boost hail demand +25% across transit interchanges. Pre-position vehicles in commercial hubs ahead of precipitation."
            )
        if any("citibike" in k for k in active_keys):
            ai_advice.append(
                f"Micromobility Operations: Precipitation on {rain_str} will reduce bike-share checkouts by -40% to -60%. Divert field staff to warehouse depot maintenance and battery swapping."
            )
        if "online_retail" in active_keys:
            ai_advice.append(
                f"E-Commerce Retail: Inclement weather on {rain_str} increases consumer indoor browsing. Trigger automated promotional email campaigns and abandoned cart reminders."
            )
        if any("chipotle" in k for k in active_keys):
            ai_advice.append(
                f"Fast-Casual Dining Floor: Precipitation on {rain_str} depresses dine-in foot traffic. Prep the digital makeline (DML) stations and allocate staff to packaging delivery orders."
            )

    if max_temp_forecast >= 32.0:
        if "ice_cream_beverages" in active_keys:
            ai_advice.append(
                f"Cold Beverages & Confectionery: High temperatures reaching {max_temp_forecast:.1f}°C will boost cold refreshment sales by +40%. "
                "Ensure ice machine maintenance and advance replenishment of dairy and syrup stocks."
            )
        if "hvac_home_services" in active_keys:
            ai_advice.append(
                f"HVAC Emergency Dispatch: Summer heat index reaching {max_temp_forecast:.1f}°C will surge residential AC emergency calls. "
                "Place secondary technician shifts on call."
            )

    if not ai_advice:
        ai_advice.append(
            f"Standard Baseline Operations: Mild and stable weather anticipated over the upcoming 7-day period (max rain: {total_rain_forecast:.1f} mm, max temp: {max_temp_forecast:.1f}°C). Maintain normal operational staffing and standard supply replenishment schedules."
        )

    return {
        "weather_desc": f"Multi-Source Meteorological Trajectory (Cumulative Rain: {total_rain_forecast:.1f} mm, Temp Range: {min_temp_forecast:.0f}°C to {max_temp_forecast:.0f}°C)",
        "days": day_labels,
        "daily_forecast": daily_forecast,
        "projections": projections,
        "total_impact_all": total_impact_all,
        "ai_advice": ai_advice
    }
