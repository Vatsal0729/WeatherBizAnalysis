"""
Multi-Business Revenue Intelligence & Dynamic Catalog Engine.
Strict monochrome black-and-white theme with zero emojis.
Supports 16+ preset enterprise business sectors and dynamic on-the-fly custom business synthesis.
"""

import numpy as np
import pandas as pd
import re

BUSINESS_CATALOG = {
    "food_delivery": {
        "name": "Food Delivery",
        "category": "Logistics & Delivery",
        "description": "On-demand food and grocery ordering platform with courier network.",
        "color": "#00D2FF",  # Bright Cyan Blue (High Visibility)
        "dash": "solid",
        "symbol": "circle",
        "base_daily_rev": 65000,
        "rain_elasticity": 0.035,
        "snow_elasticity": 0.085,
        "temp_elasticity": -0.015,
    },
    "dine_in_restaurant": {
        "name": "Restaurants & Bistros",
        "category": "Hospitality & Dining",
        "description": "Sit-down restaurant with dining room and outdoor patio seating.",
        "color": "#FF9100",  # Vivid Amber Orange (High Visibility)
        "dash": "solid",
        "symbol": "square",
        "base_daily_rev": 28000,
        "rain_elasticity": -0.045,
        "snow_elasticity": -0.095,
        "temp_elasticity": 0.012,
    },
    "retail_apparel": {
        "name": "Clothing & Rainwear",
        "category": "Retail & Commerce",
        "description": "Brick-and-mortar apparel store selling seasonal & weather apparel.",
        "color": "#B388FF",  # Electric Lavender Purple (High Visibility)
        "dash": "solid",
        "symbol": "diamond",
        "base_daily_rev": 35000,
        "rain_elasticity": 0.022,
        "snow_elasticity": 0.065,
        "temp_elasticity": -0.020,
    },
    "rideshare_fleet": {
        "name": "Taxi & Rideshare",
        "category": "Urban Mobility",
        "description": "City ridesharing & on-demand private mobility transport.",
        "color": "#00E676",  # Vibrant Emerald Green (High Visibility)
        "dash": "solid",
        "symbol": "triangle-up",
        "base_daily_rev": 52000,
        "rain_elasticity": 0.042,
        "snow_elasticity": 0.078,
        "temp_elasticity": -0.010,
    },
    "ice_cream_beverages": {
        "name": "Ice Cream & Cold Drinks",
        "category": "Food & Beverage",
        "description": "Gelato, frozen treats, and iced refreshment parlors.",
        "color": "#00E5FF",  # Bright Turquoise Aqua (High Visibility)
        "dash": "solid",
        "symbol": "cross",
        "base_daily_rev": 14000,
        "rain_elasticity": -0.055,
        "snow_elasticity": -0.120,
        "temp_elasticity": 0.058,
    },
    "hot_cafe_bakery": {
        "name": "Cafés & Bakeries",
        "category": "Food & Beverage",
        "description": "Artisan coffee, hot soups, and fresh warm bakery pastries.",
        "color": "#FF5252",  # Vivid Coral Red (High Visibility)
        "dash": "solid",
        "symbol": "x",
        "base_daily_rev": 18000,
        "rain_elasticity": 0.028,
        "snow_elasticity": 0.045,
        "temp_elasticity": -0.032,
    },
    "bikeshare_operator": {
        "name": "Micromobility & Bike-Share",
        "category": "Urban Mobility",
        "description": "Station-based bike and e-scooter urban rental network.",
        "color": "#76FF03",  # High-Vis Electric Lime (High Visibility)
        "dash": "solid",
        "symbol": "star",
        "base_daily_rev": 16000,
        "rain_elasticity": -0.085,
        "snow_elasticity": -0.180,
        "temp_elasticity": 0.035,
    },
    "freight_logistics": {
        "name": "Freight & Delivery Logistics",
        "category": "Supply Chain",
        "description": "Inter-city trucking and regional warehouse dispatch operations.",
        "color": "#E040FB",  # Vibrant Magenta (High Visibility)
        "dash": "solid",
        "symbol": "hexagon",
        "base_daily_rev": 75000,
        "rain_elasticity": -0.018,
        "snow_elasticity": -0.055,
        "temp_elasticity": -0.005,
    },
    "movie_theaters": {
        "name": "Cinemas & Indoor Entertainment",
        "category": "Entertainment & Leisure",
        "description": "Cinema multiplexes, bowling alleys, and indoor gaming arcades.",
        "color": "#FF4081",  # Hot Pink (High Visibility)
        "dash": "solid",
        "symbol": "circle-open",
        "base_daily_rev": 26000,
        "rain_elasticity": 0.048,
        "snow_elasticity": 0.035,
        "temp_elasticity": -0.018,
    },
    "gym_fitness": {
        "name": "Gyms & Fitness Centers",
        "category": "Health & Wellness",
        "description": "Membership health clubs, indoor studios, and gym facilities.",
        "color": "#448AFF",  # Bright Royal Blue (High Visibility)
        "dash": "solid",
        "symbol": "square-open",
        "base_daily_rev": 22000,
        "rain_elasticity": 0.025,
        "snow_elasticity": -0.040,
        "temp_elasticity": -0.022,
    },
    "car_wash": {
        "name": "Car Wash & Detailing",
        "category": "Automotive Services",
        "description": "Automated and full-service vehicle washing facilities.",
        "color": "#1DE9B6",  # Seafoam Teal (High Visibility)
        "dash": "solid",
        "symbol": "diamond-open",
        "base_daily_rev": 12000,
        "rain_elasticity": -0.115,
        "snow_elasticity": -0.160,
        "temp_elasticity": 0.025,
    },
    "golf_theme_park": {
        "name": "Golf & Theme Parks",
        "category": "Outdoor Recreation",
        "description": "Golf courses, amusement parks, and outdoor attraction venues.",
        "color": "#00C853",  # Deep Grass Green (High Visibility)
        "dash": "solid",
        "symbol": "triangle-down",
        "base_daily_rev": 45000,
        "rain_elasticity": -0.140,
        "snow_elasticity": -0.220,
        "temp_elasticity": 0.045,
    },
    "pharmacy_clinics": {
        "name": "Pharmacies & Urgent Care",
        "category": "Healthcare & Pharma",
        "description": "Retail pharmacies, walk-in urgent care, and medical dispensaries.",
        "color": "#FF1744",  # High-Vis Crimson (High Visibility)
        "dash": "solid",
        "symbol": "cross-thin",
        "base_daily_rev": 38000,
        "rain_elasticity": 0.015,
        "snow_elasticity": 0.055,
        "temp_elasticity": -0.038,
    },
    "hvac_home_services": {
        "name": "HVAC & Home Repair",
        "category": "Home Services & Utilities",
        "description": "Emergency air conditioning, furnace heating, and plumbing services.",
        "color": "#FF6D00",  # Bright Tangerine Orange (High Visibility)
        "dash": "solid",
        "symbol": "star-open",
        "base_daily_rev": 42000,
        "rain_elasticity": 0.012,
        "snow_elasticity": 0.090,
        "temp_elasticity": 0.065,
    },
    "grocery_supermarket": {
        "name": "Grocery Stores",
        "category": "Retail & Grocery",
        "description": "Large-format grocery stores, food marts, and essential staples.",
        "color": "#FFD600",  # High-Vis Lemon Gold (High Visibility)
        "dash": "solid",
        "symbol": "triangle-up-open",
        "base_daily_rev": 85000,
        "rain_elasticity": 0.010,
        "snow_elasticity": 0.060,
        "temp_elasticity": -0.008,
    },
    "ecommerce_retail": {
        "name": "E-Commerce Marketplaces",
        "category": "Digital Commerce",
        "description": "Direct-to-consumer online shopping and package fulfillment.",
        "color": "#7C4DFF",  # Bright Electric Violet (High Visibility)
        "dash": "solid",
        "symbol": "diamond-tall",
        "base_daily_rev": 95000,
        "rain_elasticity": 0.032,
        "snow_elasticity": 0.075,
        "temp_elasticity": -0.015,
    }
}


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


def infer_custom_business_parameters(name: str, category_hint: str = None, custom_color: str = None, custom_rev: float = None, custom_rain: float = None, custom_temp: float = None, existing_count: int = 0):
    """
    Synthesizes realistic econometric parameters for a novel user-typed business.
    Assigns a standard high-visibility chart line color if custom_color is not specified.
    """
    clean_name = name.strip()
    slug = re.sub(r'[^a-z0-9]+', '_', clean_name.lower()).strip('_')
    if not slug:
        slug = f"custom_biz_{abs(hash(clean_name)) % 10000}"
        
    lower_n = clean_name.lower()
    
    # Default baseline heuristics
    category = "General Commercial"
    base_rev = 30000.0
    rain_elast = -0.015
    snow_elast = -0.040
    temp_elast = 0.005
    description = f"Custom synthesized business entity: {clean_name}"
    
    # Sector & Keyword Classification Heuristics
    if any(k in lower_n for k in ["outdoor", "golf", "park", "garden", "patio", "boat", "beach", "pool", "surf", "ski", "resort"]):
        category = "Outdoor Recreation"
        base_rev = 45000.0
        rain_elast = -0.135
        snow_elast = -0.210
        temp_elast = 0.040
        description = f"Outdoor recreation & leisure venue: {clean_name}"
    elif any(k in lower_n for k in ["indoor", "arcade", "cinema", "movie", "theater", "bowling", "museum", "escape", "vr", "game"]):
        category = "Indoor Entertainment"
        base_rev = 28000.0
        rain_elast = 0.045
        snow_elast = 0.030
        temp_elast = -0.015
        description = f"Indoor entertainment facility: {clean_name}"
    elif any(k in lower_n for k in ["hvac", "repair", "plumb", "roof", "gutter", "electric", "mechanic", "towing", "locksmith", "handyman"]):
        category = "Home & Emergency Services"
        base_rev = 42000.0
        rain_elast = 0.018
        snow_elast = 0.095
        temp_elast = 0.060
        description = f"Emergency repair and utility contractor: {clean_name}"
    elif any(k in lower_n for k in ["gym", "fitness", "yoga", "pilates", "crossfit", "martial", "dance", "swim"]):
        category = "Health & Fitness"
        base_rev = 22000.0
        rain_elast = 0.022
        snow_elast = -0.045
        temp_elast = -0.020
        description = f"Health, wellness and fitness facility: {clean_name}"
    elif any(k in lower_n for k in ["restaurant", "cafe", "bistro", "diner", "bar", "pub", "brewery", "grill", "bakery", "lounge"]):
        category = "Food & Hospitality"
        base_rev = 29000.0
        rain_elast = -0.040
        snow_elast = -0.075
        temp_elast = 0.010
        description = f"Hospitality food service entity: {clean_name}"
    elif any(k in lower_n for k in ["delivery", "courier", "shipping", "freight", "truck", "warehouse", "logistics", "moving"]):
        category = "Logistics & Transport"
        base_rev = 60000.0
        rain_elast = 0.030
        snow_elast = 0.060
        temp_elast = -0.010
        description = f"Logistics dispatch and transport service: {clean_name}"
    elif any(k in lower_n for k in ["pharmacy", "clinic", "hospital", "doctor", "medical", "dental", "vet", "pet"]):
        category = "Healthcare & Pet Services"
        base_rev = 40000.0
        rain_elast = 0.010
        snow_elast = 0.045
        temp_elast = -0.030
        description = f"Essential healthcare and clinical services: {clean_name}"
    elif any(k in lower_n for k in ["retail", "shop", "store", "boutique", "mall", "market", "outlet", "apparel", "clothing"]):
        category = "Retail & Commerce"
        base_rev = 36000.0
        rain_elast = -0.020
        snow_elast = 0.025
        temp_elast = -0.015
        description = f"Commercial retail store: {clean_name}"
    elif any(k in lower_n for k in ["car wash", "auto wash", "detailing"]):
        category = "Automotive Care"
        base_rev = 14000.0
        rain_elast = -0.120
        snow_elast = -0.170
        temp_elast = 0.030
        description = f"Weather-dependent vehicle cleaning facility: {clean_name}"
    elif any(k in lower_n for k in ["ice cream", "gelato", "frozen", "smoothie", "juice", "slush", "acai"]):
        category = "Chilled Refreshments"
        base_rev = 15000.0
        rain_elast = -0.060
        snow_elast = -0.130
        temp_elast = 0.060
        description = f"Chilled refreshment specialty business: {clean_name}"
    elif any(k in lower_n for k in ["coffee", "tea", "soup", "hot pot", "ramen", "fondue"]):
        category = "Hot Food & Beverages"
        base_rev = 19000.0
        rain_elast = 0.032
        snow_elast = 0.055
        temp_elast = -0.035
        description = f"Hot food and comfort beverage enterprise: {clean_name}"
        
    # User override parameters if specified
    if custom_rev is not None and custom_rev > 0:
        base_rev = float(custom_rev)
    if custom_rain is not None:
        rain_elast = float(custom_rain) / 100.0
    if custom_temp is not None:
        temp_elast = float(custom_temp) / 100.0
        
    if custom_color and str(custom_color).startswith("#"):
        chosen_color = str(custom_color)
    else:
        palette_idx = (existing_count + abs(hash(clean_name))) % len(HIGH_VISIBILITY_PALETTE)
        chosen_color = HIGH_VISIBILITY_PALETTE[palette_idx]
    
    return {
        "slug": slug,
        "config": {
            "name": clean_name,
            "category": category,
            "description": description,
            "color": chosen_color,
            "dash": "solid",
            "symbol": "circle",
            "base_daily_rev": base_rev,
            "rain_elasticity": round(rain_elast, 3),
            "snow_elasticity": round(snow_elast, 3),
            "temp_elasticity": round(temp_elast, 3),
        }
    }


def aggregate_daily_financials(df):
    """Aggregates hourly raw data to daily business level."""
    daily = df.groupby(["metro_area", "date_str"]).agg({
        "precip_accumulation_mm": "sum",
        "snow_depth_delta_cm": "sum",
        "air_temp_deg_c": "mean",
        "temp_anomaly_deg_c": "mean",
        "sustained_wind_kmh": "mean",
        "day_name": "first",
        "month_name": "first"
    }).reset_index()
    
    daily["date"] = pd.to_datetime(daily["date_str"])
    daily = daily.sort_values(["metro_area", "date"]).reset_index(drop=True)
    
    def get_weather_condition(row):
        if row["snow_depth_delta_cm"] > 1.0:
            return "Snow"
        elif row["precip_accumulation_mm"] > 5.0:
            return "Heavy Rain"
        elif row["precip_accumulation_mm"] > 0.5:
            return "Light Rain"
        elif row["air_temp_deg_c"] > 32.0:
            return "Heatwave"
        elif row["air_temp_deg_c"] < 0.0:
            return "Freezing"
        else:
            return "Clear"
            
    daily["weather_icon"] = daily.apply(get_weather_condition, axis=1)
    return daily


def calculate_custom_business_daily_series(df_daily, business_keys, custom_catalog=None):
    """
    Computes daily actual revenue and normal expected baseline revenue line series
    for any combination of selected businesses (preset or custom).
    """
    df = df_daily.copy()
    dow_factors = [0.90, 0.92, 0.96, 1.05, 1.35, 1.45, 1.25]
    catalog = custom_catalog if custom_catalog else BUSINESS_CATALOG
    
    for b_key in business_keys:
        if b_key not in catalog:
            continue
        cfg = catalog[b_key]
        
        base_series = np.array([
            cfg["base_daily_rev"] * dow_factors[d.dayofweek] for d in df["date"]
        ])
        
        # Scaled daily weather impacts (prevents explosive multipliers from 24h accumulated precipitation)
        effective_rain = np.minimum(df["precip_accumulation_mm"].values, 30.0) * 0.35
        rain_effect = effective_rain * cfg.get("rain_elasticity", 0.0)
        
        effective_snow = np.minimum(np.maximum(0.0, df["snow_depth_delta_cm"].values), 20.0) * 0.40
        snow_effect = effective_snow * cfg.get("snow_elasticity", 0.0)
        
        bounded_temp_anom = np.clip(df["temp_anomaly_deg_c"].values, -10.0, 10.0)
        temp_effect = bounded_temp_anom * cfg.get("temp_elasticity", 0.0)
        
        total_weather_multiplier = np.clip(1.0 + rain_effect + snow_effect + temp_effect, 0.20, 2.20)
        
        actual_rev = np.round(base_series * total_weather_multiplier, 2)
        base_rev = np.round(base_series, 2)
        net_impact = np.round(actual_rev - base_rev, 2)
        
        df[f"{b_key}_actual_rev"] = actual_rev
        df[f"{b_key}_baseline_rev"] = base_rev
        df[f"{b_key}_net_impact"] = net_impact
        
    return df


def generate_business_specific_why_insight(b_key, row, custom_catalog=None):
    """
    Generates concise, plain-English explanations for any business (preset or user-created).
    """
    catalog = custom_catalog if custom_catalog else BUSINESS_CATALOG
    if b_key not in catalog:
        return {}
    cfg = catalog[b_key]
    
    actual = row.get(f"{b_key}_actual_rev", 0.0)
    baseline = row.get(f"{b_key}_baseline_rev", 0.0)
    delta = actual - baseline
    pct_change = (delta / baseline * 100.0) if baseline > 0 else 0.0
    
    rain = row["precip_accumulation_mm"]
    snow = row["snow_depth_delta_cm"]
    temp = row["air_temp_deg_c"]
    
    bullets = []
    
    if rain > 4.0 or snow > 1.0:
        if cfg["rain_elasticity"] > 0 or cfg["snow_elasticity"] > 0:
            headline = f"Adverse weather increased customer demand by {pct_change:+.1f}%"
            bullets.append(f"Precipitation prompted consumers to shift activity toward {cfg['name']}.")
            bullets.append(f"Earned {'+$' if delta>=0 else '-$'}{abs(delta):,.0f} above clear-weather baseline.")
        else:
            headline = f"Precipitation reduced customer volume by {abs(pct_change):.1f}%"
            bullets.append(f"Adverse weather caused customer footfall and visits to drop.")
            bullets.append(f"Lost -${abs(delta):,.0f} compared to expected clear-day sales.")
    elif temp > 32.0:
        if cfg["temp_elasticity"] > 0.02:
            headline = f"Heatwave conditions boosted demand by {pct_change:+.1f}%"
            bullets.append(f"High ambient temperatures ({temp:.1f}°C) drove elevated customer activity.")
        elif cfg["temp_elasticity"] < -0.02:
            headline = f"Extreme heat suppressed outdoor activity ({pct_change:+.1f}%)"
            bullets.append("Uncomfortably hot temperatures caused customers to avoid unshaded areas.")
        else:
            headline = f"Warm temperatures supported baseline operations ({pct_change:+.1f}%)"
            bullets.append("Seasonal temperatures maintained steady baseline customer traffic.")
    elif temp < 2.0:
        if cfg["temp_elasticity"] < -0.02:
            headline = f"Cold temperatures ({temp:.1f}°C) boosted revenue by {pct_change:+.1f}%"
            bullets.append("Cold snap spurred immediate consumer demand for winter essentials.")
        else:
            headline = f"Freezing weather caused a {pct_change:+.1f}% shift in customer traffic"
            bullets.append("Low temperatures altered customer transit and shopping habits.")
    else:
        headline = "Clear day; business performed close to normal expected sales"
        bullets.append(f"Revenue was primarily determined by standard {row['day_name']} weekly patterns.")
        
    return {
        "name": cfg["name"],
        "category": cfg.get("category", "General"),
        "actual_rev": actual,
        "baseline_rev": baseline,
        "delta": delta,
        "pct_change": pct_change,
        "headline": headline,
        "bullets": bullets
    }


CITY_DYNAMICS = {
    "NYC": {
        "name": "New York City",
        "region": "Mid-Atlantic / Coastal Urban",
        "transit_mode": "MTA Subway network and yellow cabs",
        "pedestrian_style": "High-density Manhattan pedestrian corridors (Broadway, 5th Ave)",
        "micro_mobility": "Citi Bike fleets and high-volume delivery e-bike couriers",
        "shelter_venues": "Subway concourses, indoor delis, and sheltered avenue arcades",
        "rain_bottleneck": "Flooded curb gutters, pedestrian reluctance to cross wide avenues, and e-bike delivery traction hazards",
        "cold_bottleneck": "Wind chill canyons along Manhattan avenues deterring street shoppers",
        "heat_bottleneck": "Subway platform heat and urban canyon humidity driving spike in refrigerated refreshments and AC demand",
    },
    "CHI": {
        "name": "Chicago",
        "region": "Midwest / Great Lakes",
        "transit_mode": "CTA 'L' elevated train and Loop bus routes",
        "pedestrian_style": "Downtown Loop workers, Michigan Avenue shoppers, and riverfront walkers",
        "micro_mobility": "Divvy bikes and lakefront scooters",
        "shelter_venues": "The underground Pedway system and heated indoor food halls",
        "rain_bottleneck": "Lake-effect squalls and slippery steel bridge gratings across the Chicago River",
        "cold_bottleneck": "Bitter sub-zero wind chills off Lake Michigan clearing Loop sidewalks and halting car wash bays",
        "heat_bottleneck": "Summer humidity waves funneling crowds toward lakefront beaches or AC-conditioned shopping",
    },
    "LDN": {
        "name": "London",
        "region": "Western Europe / Maritime",
        "transit_mode": "London Underground (The Tube) and red double-decker buses",
        "pedestrian_style": "West End shoppers, City financial district commuters, and Soho walkers",
        "micro_mobility": "Santander Cycles and dockless Lime e-bikes",
        "shelter_venues": "Traditional neighborhood pubs, covered arcades (Leadenhall, Covent Garden), and indoor shopping centers",
        "rain_bottleneck": "Persistent drizzle slicking cobblestone pavements, shifting cyclists to crowded buses and Tube carriages",
        "cold_bottleneck": "Damp maritime frost curbing high-street foot traffic and stimulating online e-commerce checkout",
        "heat_bottleneck": "Lack of widespread residential AC driving residents outdoors to shaded parks, cold beer gardens, and riverside terraces",
    },
    "TYO": {
        "name": "Tokyo",
        "region": "East Asia / Megacity",
        "transit_mode": "Tokyo Metro and JR East Yamanote Line rail network",
        "pedestrian_style": "Hyper-dense station-hub foot traffic (Shinjuku, Shibuya, Tokyo Station)",
        "micro_mobility": "Station bicycle commuter parking and last-mile pedestrians",
        "shelter_venues": "Massive subterranean station shopping arcades (Chikagai) and 24/7 Konbini convenience stores",
        "rain_bottleneck": "Surface pedestrians diving into underground station malls, boosting automated vending and umbrella sales",
        "cold_bottleneck": "Crisp dry winter winds driving surges in hot canned drink vending and indoor ramen counters",
        "heat_bottleneck": "Oppressive summer heat and humidity driving rapid iced beverage and air-conditioned retail demand",
    },
    "BOM": {
        "name": "Mumbai",
        "region": "South Asia / Coastal Monsoon",
        "transit_mode": "Mumbai Suburban Railway ('Locals'), Metro, and Auto-Rickshaws",
        "pedestrian_style": "Street bazaar shoppers, transit junction crowds (Dadar, Andheri), and coastal promenades",
        "micro_mobility": "Two-wheeler motorcycle delivery riders and local courier fleets",
        "shelter_venues": "Station pedestrian overbridges, roadside chai stalls, and modern covered commercial centers",
        "rain_bottleneck": "Intense monsoon downpours causing low-lying track waterlogging, auto-rickshaw stoppages, and doubling delivery rider transit times",
        "cold_bottleneck": "Pleasant mild winter evenings drawing massive crowds to outdoor street food and seafront dining",
        "heat_bottleneck": "Intense pre-monsoon heat driving surging demand for fresh cold juices, coconut water, and ice cream parlors",
    },
    "CDG": {
        "name": "Paris",
        "region": "Western Europe / Continental",
        "transit_mode": "RATP Métro and RER commuter network",
        "pedestrian_style": "Boulevard strollers, Latin Quarter pedestrians, and outdoor café terrace patrons",
        "micro_mobility": "Vélib' bicycle networks and shared electric scooters",
        "shelter_venues": "Covered passages (Passages Couverts), enclosed brasseries, and departmental stores",
        "rain_bottleneck": "Sudden evacuation of sidewalk terrasses into interior dining rooms, with Vélib' cycling collapsing by 70%+",
        "cold_bottleneck": "Damp winter chill shutting patio heaters and boosting hot bakery and comfort food delivery",
        "heat_bottleneck": "Summer heat clearing un-airconditioned apartments towards shaded Seine banks and chilled cultural spaces",
    }
}


def generate_dynamic_domino_cascade(selected_city, weather_info, active_keys, custom_catalog=None):
    """
    Generates a realistic, highly specific 6-step multi-hop causal domino cascade
    unique to the chosen city, live weather telemetry, and the user's active portfolio.
    """
    catalog = custom_catalog if custom_catalog else BUSINESS_CATALOG
    city_dict = CITY_DYNAMICS.get(selected_city, CITY_DYNAMICS["NYC"])
    city_name = city_dict["name"]

    # Extract weather metrics safely
    if isinstance(weather_info, dict):
        rain_mm = float(weather_info.get("precipitation_mm", weather_info.get("precip_accumulation_mm", 0.0)))
        temp_c = float(weather_info.get("temperature_c", weather_info.get("air_temp_deg_c", 18.0)))
        temp_anom = float(weather_info.get("temp_anomaly_deg_c", weather_info.get("temp_anomaly_c", temp_c - 18.0)))
        wind_kmh = float(weather_info.get("wind_kmh", 12.0))
    else:
        rain_mm = float(getattr(weather_info, "precip_accumulation_mm", weather_info.get("precip_accumulation_mm", 0.0)))
        temp_c = float(getattr(weather_info, "air_temp_deg_c", weather_info.get("air_temp_deg_c", 18.0)))
        temp_anom = float(getattr(weather_info, "temp_anomaly_deg_c", weather_info.get("temp_anomaly_deg_c", temp_c - 18.0)))
        wind_kmh = float(getattr(weather_info, "wind_speed_kmh", weather_info.get("wind_speed_kmh", 14.0)))

    impacts = []
    total_dollar_shift = 0.0
    for k in active_keys:
        if k not in catalog:
            continue
        cfg = catalog[k]
        base = cfg.get("base_daily_rev", 30000)
        r_elast = cfg.get("rain_elasticity", 0.0)
        t_elast = cfg.get("temp_elasticity", 0.0)
        dollar_delta = base * (r_elast * rain_mm + t_elast * temp_anom)
        pct = (dollar_delta / base) * 100 if base > 0 else 0.0
        impacts.append({
            "key": k,
            "name": cfg["name"],
            "category": cfg.get("category", "General"),
            "delta": dollar_delta,
            "pct": pct
        })
        total_dollar_shift += dollar_delta

    impacts_sorted = sorted(impacts, key=lambda x: x["delta"])
    primary_loser = impacts_sorted[0] if impacts_sorted else {"name": "Local Storefronts", "pct": -15.0, "delta": -2500}
    primary_winner = impacts_sorted[-1] if impacts_sorted else {"name": "Digital Order Channels", "pct": 18.0, "delta": 3200}

    if rain_mm >= 4.0:
        regime = "Severe Precipitation Downpour"
        step1 = f"Severe precipitation ({rain_mm:.1f} mm/hr) sweeps across {city_name} with {wind_kmh:.0f} km/h gusts at {temp_c:.1f}°C."
        step2 = f"Pedestrians rapidly clear {city_dict['pedestrian_style']}; commuters abandon {city_dict['micro_mobility']} and seek shelter in {city_dict['shelter_venues']}, flooding {city_dict['transit_mode']}."
        step5 = f"{city_dict['rain_bottleneck']} creates substantial last-mile friction; courier transit times increase by +15–25 minutes as road conditions deteriorate."
        tipping_threshold = "4.0 mm/hr Rain"
        tipping_demand = "+35% Surge in Digital & Remote Orders"
        tipping_supply = "-22% Outdoor Courier / Service Availability"
        tipping_consequence = "Surge pricing multipliers escalate to 1.8x–2.2x, delivery wait times lengthen by +50%, and order cancellation rates climb."
    elif rain_mm >= 0.5:
        regime = "Persistent Rain & Damp Chill"
        step1 = f"Steady rain ({rain_mm:.1f} mm/hr) dampens {city_name} at {temp_c:.1f}°C."
        step2 = f"Commuters unpack umbrellas; {city_dict['micro_mobility']} trips decline sharply as road surfaces slick, redirecting foot traffic into {city_dict['transit_mode']} and indoor retail concourses."
        step5 = f"Road traffic congestion increases by +20%; couriers and freight carriers experience localized delays crossing major bridge and tunnel arterials."
        tipping_threshold = "2.5 mm/hr Rain"
        tipping_demand = "+20% Incline in Home Delivery & Indoor Entertainment"
        tipping_supply = "-12% Micro-mobility & Outdoor Dining Staffing"
        tipping_consequence = "Patio tables close completely, indoor queue times increase, and takeout channels absorb 60%+ of restaurant volume."
    elif temp_c <= 3.0 or temp_anom <= -4.0:
        regime = "Severe Cold Anomaly & Freezing Wind"
        step1 = f"Cold front drops ambient temperatures to {temp_c:.1f}°C ({temp_anom:+.1f}°C anomaly relative to seasonal average) across {city_name}."
        step2 = f"{city_dict['cold_bottleneck']}; citizens limit dwell time outdoors and rush between heated interiors via {city_dict['shelter_venues']}."
        step5 = f"Building HVAC and district heating networks experience severe load spikes; cold-engine vehicle starts cause minor transit and dispatch delays."
        tipping_threshold = "Sub-Zero Freezing (<0°C)"
        tipping_demand = "+45% Emergency HVAC & Hot Comfort Food Demand"
        tipping_supply = "-30% Outdoor Footfall & Car Wash Bay Operation"
        tipping_consequence = "Curbside commerce freezes; hot comfort food and automated indoor entertainment see full capacity."
    elif temp_c >= 29.0 or temp_anom >= 5.0:
        regime = "High-Temperature Heatwave"
        step1 = f"Intense summer heatwave elevates temperatures to {temp_c:.1f}°C ({temp_anom:+.1f}°C above seasonal norms) in {city_name}."
        step2 = f"Citizens avoid sun-exposed avenues; midday foot traffic contracts as commuters seek air-conditioned sanctuary or shaded waterfront corridors."
        step5 = f"Commercial refrigeration and power grid cooling loads surge to maximum duty cycles; outdoor patio seating is abandoned during peak daylight hours."
        tipping_threshold = "Excessive Heat (>32°C)"
        tipping_demand = "+55% Cold Beverages, Ice Cream & Cooling Services"
        tipping_supply = "-25% Unconditioned Kitchen & Outdoor Labor Comfort"
        tipping_consequence = "Midday outdoor dining plummets; evening terrace recovery occurs after sundown; cold beverage inventories deplete rapidly."
    elif wind_kmh >= 28.0:
        regime = "High Wind Squall"
        step1 = f"Elevated wind velocity ({wind_kmh:.0f} km/h gusts) impacts {city_name} at {temp_c:.1f}°C."
        step2 = f"Outdoor dining umbrellas and sidewalk displays are stowed; cyclists dismount due to crosswind instability along wide boulevards."
        step5 = f"Above-ground transit and elevated highways experience precautionary speed restrictions; delivery couriers face increased handling resistance."
        tipping_threshold = "Wind Gusts (>35 km/h)"
        tipping_demand = "+18% Rideshare & Indoor Transit Substitution"
        tipping_supply = "-40% Micromobility & Outdoor Seating Capacity"
        tipping_consequence = "Outdoor seating permits temporarily suspended; commuter demand channels directly into protected rail and vehicle fleets."
    else:
        regime = "Temperate & Favorable Clear Weather"
        step1 = f"Favorable atmospheric conditions ({temp_c:.1f}°C, negligible precipitation) across {city_name}."
        step2 = f"Pedestrians flood {city_dict['pedestrian_style']}; {city_dict['micro_mobility']} experiences peak utilization; open-air dining and storefront retail thrive."
        step5 = f"Standard supply chain throughput; delivery courier supply exceeds demand, eliminating surge pricing multipliers."
        tipping_threshold = "Baseline Clear Equilibrium"
        tipping_demand = "+25% Outdoor Recreation & Physical Storefront Visits"
        tipping_supply = "+100% Full Open Capacity across All Sectors"
        tipping_consequence = "Balanced operations with zero weather friction; physical registers operate at peak capacity."

    if primary_loser["delta"] < 0:
        step3 = f"{primary_loser['name']} experiences a direct contraction ({primary_loser['pct']:+.1f}% shift, {'-$' if primary_loser['delta'] < 0 else '+$'}{abs(primary_loser['delta']):,.0f}) as physical customer visits drop."
    else:
        step3 = f"Baseline storefront sales in {primary_loser['name']} hold steady with slight seasonal variance ({primary_loser['pct']:+.1f}%)."

    if primary_winner["delta"] > 0:
        step4 = f"Consumer spending redirects into {primary_winner['name']} ({primary_winner['pct']:+.1f}% shift, +${primary_winner['delta']:,.0f}), capturing substituted spend from stranded or indoor customers."
    else:
        step4 = f"Secondary commercial channels maintain standard seasonal baselines with minimal weather-induced substitution."

    sign_str = "+$" if total_dollar_shift >= 0 else "-$"
    step6 = f"Equilibrium Settlement: Net portfolio impact settles at {sign_str}{abs(total_dollar_shift):,.0f}; channel substitution cushions register drops, shifting managerial focus to labor allocation and inventory rebalancing."

    steps = [
        {"num": 1, "text": step1},
        {"num": 2, "text": step2},
        {"num": 3, "text": step3},
        {"num": 4, "text": step4},
        {"num": 5, "text": step5},
        {"num": 6, "text": step6},
    ]

    tipping_point = {
        "title": f"Non-Linear Tipping Point: {city_name} {regime} Fracture ({tipping_threshold})",
        "demand": tipping_demand,
        "supply": tipping_supply,
        "consequence": tipping_consequence,
        "regime": regime
    }

    return {
        "city_name": city_name,
        "regime": regime,
        "weather_summary": f"{rain_mm:.1f} mm rain, {temp_c:.1f}°C ({temp_anom:+.1f}°C anom), {wind_kmh:.0f} km/h wind",
        "steps": steps,
        "tipping_point": tipping_point,
        "total_dollar_shift": total_dollar_shift,
        "primary_loser": primary_loser,
        "primary_winner": primary_winner
    }


def generate_business_specific_domino_effects(selected_city, weather_info, active_keys, custom_catalog=None):
    """
    Generates a unique, real, and actionable domino impact card for EVERY business
    selected in the active portfolio based on the current weather in this city.
    """
    catalog = custom_catalog if custom_catalog else BUSINESS_CATALOG
    city_dict = CITY_DYNAMICS.get(selected_city, CITY_DYNAMICS["NYC"])
    city_name = city_dict["name"]

    if isinstance(weather_info, dict):
        rain_mm = float(weather_info.get("precipitation_mm", weather_info.get("precip_accumulation_mm", 0.0)))
        temp_c = float(weather_info.get("temperature_c", weather_info.get("air_temp_deg_c", 18.0)))
        temp_anom = float(weather_info.get("temp_anomaly_deg_c", weather_info.get("temp_anomaly_c", temp_c - 18.0)))
    else:
        rain_mm = float(getattr(weather_info, "precip_accumulation_mm", weather_info.get("precip_accumulation_mm", 0.0)))
        temp_c = float(getattr(weather_info, "air_temp_deg_c", weather_info.get("air_temp_deg_c", 18.0)))
        temp_anom = float(getattr(weather_info, "temp_anomaly_deg_c", weather_info.get("temp_anomaly_deg_c", temp_c - 18.0)))

    results = []

    for b_key in active_keys:
        if b_key not in catalog:
            continue
        cfg = catalog[b_key]
        b_name = cfg["name"]
        cat = cfg.get("category", "Commercial Enterprise")
        base_rev = cfg.get("base_daily_rev", 30000)
        r_elast = cfg.get("rain_elasticity", 0.0)
        t_elast = cfg.get("temp_elasticity", 0.0)

        dollar_delta = base_rev * (r_elast * rain_mm + t_elast * temp_anom)
        pct_change = (dollar_delta / base_rev) * 100 if base_rev > 0 else 0.0

        if "square_pos" in b_key:
            if rain_mm >= 0.5:
                trig = f"Rainfall ({rain_mm:.1f} mm) dampens walk-in shopping corridors in {city_name}."
                beh = f"Pedestrians bypass physical counter registers to stay under covered shelter or transit stations."
                rev = f"In-person terminal receipts contract by {pct_change:+.1f}% ({'-$' if dollar_delta < 0 else '+$'}{abs(dollar_delta):,.0f}), reducing register transaction frequency."
                downstream = f"Unsold perishable inventory accumulates; register cashiers experience idle shifts. Prompts merchant to activate digital payment links and online takeaway ordering."
                action = f"Trigger a rainy-day flash promo (e.g. 10% off) via Square SMS marketing to local loyalty patrons, and assign counter clerks to assemble takeout packages."
            else:
                trig = f"Clear and temperate weather ({temp_c:.1f}°C) along {city_name}'s retail avenues."
                beh = f"Pedestrian foot traffic flows steadily past physical checkout counters."
                rev = f"Register receipts operate at normal baseline ({pct_change:+.1f}%, {'+$' if dollar_delta >= 0 else '-$'}{abs(dollar_delta):,.0f})."
                downstream = f"Standard inventory turns; steady cash register velocity across front-of-house staff."
                action = f"Maintain normal floor staffing and ensure counter point-of-sale receipt rolls and hardware are fully operational."

        elif "stripe" in b_key:
            if rain_mm >= 0.5 or temp_c <= 5.0 or temp_c >= 30.0:
                trig = f"Adverse weather keeps {city_name} consumers indoors at work desks and home residences."
                beh = f"Digital desktop and smartphone e-commerce browsing sessions surge, driving higher checkout conversions."
                rev = f"Online checkout GMV expands by {pct_change:+.1f}% (+${dollar_delta:,.0f}), accelerating digital payment processing volume."
                downstream = f"Fulfillment warehouses face sudden picking backlogs; outbound courier dispatch is delayed by slick city road traffic, risking customer ETA inquiries."
                action = f"Add a dynamic +1 day delivery buffer at checkout to prevent dispute chargebacks, and allocate additional staff to evening warehouse order dispatch."
            else:
                trig = f"Mild atmospheric conditions encourage physical outdoor shopping over digital browsing."
                beh = f"Consumers spend more time outdoors and less time in online checkout funnels."
                rev = f"Digital checkout volume tracks close to baseline ({pct_change:+.1f}%, {'+$' if dollar_delta >= 0 else '-$'}{abs(dollar_delta):,.0f})."
                downstream = f"Standard warehouse dispatch queue; normal e-commerce customer support ticket volume."
                action = f"Run standard marketing campaigns and test checkout page load speeds for upcoming seasonal demand shifts."

        elif "food_delivery" in b_key:
            if rain_mm >= 0.5:
                trig = f"Precipitation ({rain_mm:.1f} mm) prompts residents across {city_name} to stay indoors."
                beh = f"Diners open delivery apps rather than traveling to neighborhood eateries."
                rev = f"Delivery order volume surges {pct_change:+.1f}% (+${dollar_delta:,.0f}), driving elevated platform gross merchandise value."
                downstream = f"Kitchen ticket queues back up; delivery courier supply contracts as riders avoid slippery streets; platform surge pricing multipliers kick in (1.5x–2.1x)."
                action = f"Broadcast courier weather incentives (+$3.50/order) 30 minutes in advance to maintain rider availability and preserve fulfillment SLAs."
            else:
                trig = f"Pleasant outdoor weather draws diners out of homes and into neighborhood streets."
                beh = f"Diners prefer walking to local eateries, causing a slight dip in home delivery demand."
                rev = f"Delivery orders ease slightly ({pct_change:+.1f}%, {'+$' if dollar_delta >= 0 else '-$'}{abs(dollar_delta):,.0f})."
                downstream = f"Couriers easily meet delivery targets; zero algorithmic surge pricing applied."
                action = f"Focus on promoting lunchtime corporate catering packages and scheduled evening orders."

        elif "dine_in" in b_key:
            if rain_mm >= 0.5:
                trig = f"Wet streets and poor visibility discourage casual dining walks in {city_name}."
                beh = f"Patrons cancel table reservations and avoid outdoor patio seating completely."
                rev = f"Dining room covers contract by {pct_change:+.1f}% ({'-$' if dollar_delta < 0 else '+$'}{abs(dollar_delta):,.0f}), reducing per-table ticket revenue."
                downstream = f"Front-of-house waitstaff stand underutilized while kitchen prep risks spoiling. Scrambles kitchen to fulfill online delivery orders."
                action = f"Reassign floor servers to pack outbound delivery orders; post bad-weather dinner specials on social channels to capture local delivery orders."
            else:
                trig = f"Pleasant conditions ({temp_c:.1f}°C) fill outdoor terraces and dining rooms across {city_name}."
                beh = f"Walk-in parties actively request outdoor patio and window seating."
                rev = f"Covers and guest spend operate above baseline ({pct_change:+.1f}%, {'+$' if dollar_delta >= 0 else '-$'}{abs(dollar_delta):,.0f})."
                downstream = f"Tables turn over smoothly; beverage and appetizer sales reach full capacity."
                action = f"Ensure outdoor patio heaters/shades are prepared and staff floor shifts at full strength."

        elif "bikeshare" in b_key:
            if rain_mm >= 0.5 or temp_c <= 4.0:
                trig = f"Precipitation and wet pavement make cycling hazardous in {city_name}."
                beh = f"Commuters abandon outdoor bike stations and redirect to {city_dict['transit_mode']}."
                rev = f"Ride rental volume drops {pct_change:+.1f}% ({'-$' if dollar_delta < 0 else '+$'}{abs(dollar_delta):,.0f}), idling public docks."
                downstream = f"Unused bikes accumulate at suburban hubs while transit turnstiles overflow. Dock rebalancing logistics halt."
                action = f"Pause physical rebalancing van operations during heavy rain to avoid traffic accidents, and run in-app credits for rides taken tomorrow."
            else:
                trig = f"Clear skies and mild temperature ({temp_c:.1f}°C) create prime cycling conditions."
                beh = f"Commuters and recreational riders opt for bikes and e-scooters for last-mile transit."
                rev = f"Bike-share trips jump {pct_change:+.1f}% (+${dollar_delta:,.0f}), driving high dock turnover."
                downstream = f"High dock depletion at commercial hubs requires active rebalancing fleet dispatch."
                action = f"Deploy rebalancing vans to transit hubs before evening rush hour to keep docks adequately supplied."

        elif "nyc_taxi" in b_key:
            if rain_mm >= 0.5:
                trig = f"Precipitation ({rain_mm:.1f} mm) makes street walking and subway transfers unpleasant across {city_name}."
                beh = f"Pedestrians and commuters hail yellow taxis and rideshare vehicles simultaneously."
                rev = f"Fleet passenger fares surge by {pct_change:+.1f}% (+${dollar_delta:,.0f}), driving driver meter earnings."
                downstream = f"High demand at office corridors and transit hubs; traffic congestion slows average trip completion times."
                action = f"Pre-position fleet vehicles around high-density transit interchanges and corporate corridors ahead of forecasted rain."
            else:
                trig = f"Clear roadway and weather conditions across {city_name}."
                beh = f"Pedestrians opt for walking and micromobility, keeping taxi hail demand at baseline."
                rev = f"Gross trip fares track steady baseline expectations ({pct_change:+.1f}%, {'+$' if dollar_delta >= 0 else '-$'}{abs(dollar_delta):,.0f})."
                downstream = f"Steady vehicle velocity and normal passenger wait times across metropolitan boroughs."
                action = f"Maintain standard driver shifts and target airport corridors (JFK/LGA) where baseline trip volume remains consistent."

        elif "citibike" in b_key:
            if rain_mm >= 0.5 or temp_c <= 4.0:
                trig = f"Wet pavement and poor weather make urban cycling hazardous in {city_name}."
                beh = f"Commuters and casual riders bypass bike-share stations, shifting directly to subways or taxis."
                rev = f"Ride rental checkouts contract by {pct_change:+.1f}% ({'-$' if dollar_delta < 0 else '+$'}{abs(dollar_delta):,.0f}), idling public docks."
                downstream = f"Bikes accumulate at residential docks while subway turnstiles experience surge volume; dock rebalancing operations halt."
                action = f"Suspend street rebalancing van operations during heavy storms and stage maintenance inspections on returned e-bikes."
            else:
                trig = f"Dry roadways and temperate weather ({temp_c:.1f}°C) create prime cycling conditions."
                beh = f"Commuters and recreational riders opt for bikes and e-scooters for point-to-point transit."
                rev = f"Bike-share checkouts surge by {pct_change:+.1f}% (+${dollar_delta:,.0f}), driving high dock turnover."
                downstream = f"Rapid dock depletion at commercial hubs requires active rebalancing van sweeps."
                action = f"Deploy rebalancing teams to morning transit terminals to ensure return docks remain available."

        elif "online_retail" in b_key:
            if rain_mm >= 0.5 or temp_c <= 5.0:
                trig = f"Cold temperatures and rainfall keep consumers indoors at work or home desks."
                beh = f"Shoppers spend extended dwell times browsing online catalogs and completing digital checkout baskets."
                rev = f"Daily invoice revenue expands by {pct_change:+.1f}% (+${dollar_delta:,.0f}), accelerating commercial sales."
                downstream = f"Warehouse fulfillment centers face higher pick-and-pack queues; outbound courier dispatch contends with wet road traffic."
                action = f"Trigger automated email promotions to high-intent shoppers and allocate extra personnel to order packing lines."
            else:
                trig = f"Mild and pleasant outdoor conditions encourage physical activities."
                beh = f"Shoppers spend less time behind desktop screens and mobile browsing apps."
                rev = f"Invoice revenue tracks normal baseline expectations ({pct_change:+.1f}%, {'+$' if dollar_delta >= 0 else '-$'}{abs(dollar_delta):,.0f})."
                downstream = f"Fulfillment lines operate at standard throughput with predictable turnaround times."
                action = f"Run scheduled seasonal promotions and maintain regular warehouse dispatch rosters."

        elif "chipotle" in b_key:
            if rain_mm >= 0.5 or temp_c <= 0.0:
                trig = f"Adverse weather conditions and winter precipitation across store footprints."
                beh = f"Walk-in restaurant dining room footfall contracts, shifting order volume heavily into digital apps and delivery."
                rev = f"In-person dining revenue softens, but digital channel mix expands to ~65%, cushioning revenue impact ({pct_change:+.1f}%, {'+$' if dollar_delta >= 0 else '-$'}{abs(dollar_delta):,.0f})."
                downstream = f"Dedicated digital makeline (DML) stations experience peak order assembly volume; courier pickup congestion forms."
                action = f"Reassign kitchen crew to the digital makeline (DML) and ensure ingredient prep bins are fully stocked for fast order turnaround."
            else:
                trig = f"Favorable atmospheric conditions support fast-casual restaurant foot traffic."
                beh = f"Lunchtime workers and dinner patrons visit physical restaurants for walk-in ordering."
                rev = f"Quarterly sales track corporate 10-Q baseline expectations ({pct_change:+.1f}%, {'+$' if dollar_delta >= 0 else '-$'}{abs(dollar_delta):,.0f})."
                downstream = f"Balanced throughput across both front makeline and digital makeline; smooth dining room turnover."
                action = f"Ensure full front-of-house counter staffing during the 12:00–14:00 and 18:00–20:00 peak dining hours."

        elif "rideshare" in b_key:
            if rain_mm >= 0.5:
                trig = f"Rain creates immediate demand for private, dry vehicular transit in {city_name}."
                beh = f"Commuters stranded at bus stops or subway exits open ride-hailing apps simultaneously."
                rev = f"Ride bookings surge by {pct_change:+.1f}% (+${dollar_delta:,.0f}), driving driver fare earnings."
                downstream = f"Driver supply is rapidly exhausted in downtown corridors; surge multipliers activate (1.6x–2.3x); street traffic slows trip completion times."
                action = f"Broadcast real-time heat maps directing off-duty drivers toward flooded transit interchanges where surge multipliers are highest."
            else:
                trig = f"Clear weather enables walking and micromobility, tempering ride-hailing surges."
                beh = f"Travelers choose walking or subways for short downtown trips."
                rev = f"Ride volume normalizes ({pct_change:+.1f}%, {'+$' if dollar_delta >= 0 else '-$'}{abs(dollar_delta):,.0f})."
                downstream = f"Surge multipliers remain at 1.0x; passenger wait times stay under 4 minutes."
                action = f"Incentivize airport transfers and scheduled suburban rides where demand remains stable."

        elif "car_wash" in b_key:
            if rain_mm >= 0.5:
                trig = f"Precipitation makes washing vehicles completely futile for vehicle owners."
                beh = f"Drivers postpone vehicle detailing until the rainstorm clears."
                rev = f"Wash bay revenue plummets by {pct_change:+.1f}% ({'-$' if dollar_delta < 0 else '+$'}{abs(dollar_delta):,.0f}), halting automatic wash tunnels."
                downstream = f"Water and detergent usage halts; hourly attendants sit idle; pent-up wash demand accumulates for the first clear sunny day."
                action = f"Reduce hourly staffing on wet days and schedule double-shift wash attendants for the sunny weekend immediately following the rain."
            else:
                trig = f"Sunny conditions reveal dirt and road grime on vehicles."
                beh = f"Drivers queue at car wash bays to clean their vehicles."
                rev = f"Wash volume rebounds {pct_change:+.1f}% (+${dollar_delta:,.0f}), driving continuous tunnel cycles."
                downstream = f"High bay utilization; continuous chemical and towel consumption."
                action = f"Keep all automated wash lanes open and upsell premium wax treatments at the terminal."

        elif "golf_theme" in b_key:
            if rain_mm >= 0.5:
                trig = f"Wet fairways and open-air rides force closures across outdoor attractions."
                beh = f"Visitors cancel outdoor tee times and amusement park visits."
                rev = f"Ticket gate sales plunge by {pct_change:+.1f}% ({'-$' if dollar_delta < 0 else '+$'}{abs(dollar_delta):,.0f}), freezing on-site concessions."
                downstream = f"Concession food inventory sits idle; customer leisure spend redirects into indoor movie theaters and bowling arcades."
                action = f"Issue automated rain-check vouchers valid for future bookings to prevent card dispute chargebacks, and promote indoor simulator bays."
            else:
                trig = f"Pleasant outdoor conditions provide excellent fairway and theme park weather."
                beh = f"Families and golfers book tee times and outdoor attraction passes."
                rev = f"Gate and concession revenue expand {pct_change:+.1f}% (+${dollar_delta:,.0f})."
                downstream = f"Concession stands operate at full capacity; parking lots reach peak occupancy."
                action = f"Staff outdoor beverage carts and streamline entry gate ticket scanning."

        elif "movie_theaters" in b_key:
            if rain_mm >= 0.5 or temp_c <= 4.0:
                trig = f"Inclement weather drives citizens to seek warm, dry indoor entertainment in {city_name}."
                beh = f"Families, couples, and teenagers purchase cinema tickets for afternoon and evening screenings."
                rev = f"Box office receipts and concessions surge by {pct_change:+.1f}% (+${dollar_delta:,.0f})."
                downstream = f"Concession stands experience rapid inventory turnover for popcorn and fountain drinks; lobby seating fills to capacity."
                action = f"Open overflow auditorium seating for popular titles and schedule additional concession staff during peak evening showtimes."
            else:
                trig = f"Bright outdoor conditions draw leisure spend toward parks and outdoor venues."
                beh = f"Audiences defer moviegoing to late nights or rainy days."
                rev = f"Daytime box office receipts ease ({pct_change:+.1f}%, {'+$' if dollar_delta >= 0 else '-$'}{abs(dollar_delta):,.0f})."
                downstream = f"Lobby footfall remains quiet during afternoon hours; concessions track at baseline."
                action = f"Offer discount matinee tickets and student promotions to stimulate daytime attendance."

        elif "ice_cream" in b_key:
            if temp_c >= 28.0:
                trig = f"High ambient temperatures ({temp_c:.1f}°C) trigger urgent consumer demand for cooling treats."
                beh = f"Pedestrians flock to ice cream parlors, gelato counters, and iced beverage stands."
                rev = f"Cold treat sales surge by {pct_change:+.1f}% (+${dollar_delta:,.0f}), creating high counter velocity."
                downstream = f"Commercial display freezers operate under maximum thermodynamic load; dairy and ice supply runs low."
                action = f"Ensure backup refrigeration compressors are serviced and double deliveries of dairy mix and ice."
            elif temp_c <= 12.0 or rain_mm >= 0.5:
                trig = f"Cold temperatures and rain dampen appetite for iced refreshments."
                beh = f"Customers redirect beverage spending to hot cafes, bakeries, and soup kitchens."
                rev = f"Cold parlor revenue contracts by {pct_change:+.1f}% ({'-$' if dollar_delta < 0 else '+$'}{abs(dollar_delta):,.0f})."
                downstream = f"Excess perishable dairy stock; front counter attendants experience quiet shifts."
                action = f"Introduce seasonal warm desserts (waffles, hot chocolate, warm brownies) to capture cold-weather patrons."
            else:
                trig = f"Moderate temperatures sustain baseline frozen treat purchases."
                beh = f"Steady casual footfall for afternoon snacks and dessert runs."
                rev = f"Sales remain near expected seasonal baselines ({pct_change:+.1f}%)."
                downstream = f"Normal supply replenishment; regular equipment duty cycles."
                action = f"Maintain standard batch preparation and test new rotational flavors."

        elif "hot_cafe" in b_key:
            if rain_mm >= 0.5 or temp_c <= 12.0:
                trig = f"Rain and chilly air prompt pedestrians in {city_name} to seek warmth and hot refreshments."
                beh = f"Commuters crowd into indoor cafes for hot espresso, warm pastries, and soup."
                rev = f"Cafe receipts jump by {pct_change:+.1f}% (+${dollar_delta:,.0f}), filling indoor tables."
                downstream = f"Espresso machines operate at peak throughput; bakery display shelves sell out early in the afternoon."
                action = f"Increase morning batch baking of croissants and warm savory items, and station an extra barista on the espresso bar."
            else:
                trig = f"Warm conditions shift some customer preference toward cold iced beverages."
                beh = f"Customers order iced lattes and cold brew rather than hot beverages."
                rev = f"Total revenue holds steady with product mix shifting toward cold drinks ({pct_change:+.1f}%)."
                downstream = f"Higher ice and cold cup consumption; lower hot drip coffee consumption."
                action = f"Stock cold brew kegs and ensure iced cup sleeves and syrups are fully replenished."

        elif "freight" in b_key:
            if rain_mm >= 0.5:
                trig = f"Precipitation reduces highway visibility and creates traffic slowdowns across {city_name}."
                beh = f"Surface road speeds drop by 25–40%, delaying inter-city and last-mile freight trucks."
                rev = f"Operating margins tighten by {pct_change:+.1f}% ({'-$' if dollar_delta < 0 else '+$'}{abs(dollar_delta):,.0f}) due to transit delays."
                downstream = f"Cross-dock warehouse distribution shifts miss delivery appointment windows; driver hours-of-service limits are strained."
                action = f"Re-route long-haul trucks onto less congested bypass corridors and notify distribution centers of rescheduled dock appointments."
            else:
                trig = f"Dry road surfaces enable optimal vehicle transit speeds."
                beh = f"Freight deliveries meet tight cross-dock scheduling windows without weather friction."
                rev = f"Logistics margins operate at standard efficiency ({pct_change:+.1f}%)."
                downstream = f"On-time departure and arrival metrics meet 95%+ SLA standards."
                action = f"Maintain normal dispatch schedules and conduct routine fleet maintenance inspections."

        else:
            trig = f"Meteorological conditions ({rain_mm:.1f} mm rain, {temp_c:.1f}°C) alter standard consumer footfall in {city_name}."
            beh = f"Consumer purchasing behavior in {cat} adapts to ambient atmospheric comfort."
            rev = f"Revenue shifts by {pct_change:+.1f}% ({'+$' if dollar_delta >= 0 else '-$'}{abs(dollar_delta):,.0f}) based on calibrated empirical weather elasticities."
            downstream = f"Channel substitution shifts cash flow between physical presence and remote ordering channels."
            action = f"Calibrate inventory and labor scheduling to match the empirical weather sensitivity of this commercial sector."

        results.append({
            "key": b_key,
            "name": b_name,
            "category": cat,
            "base_daily_rev": base_rev,
            "delta": dollar_delta,
            "pct": pct_change,
            "direction": "positive" if dollar_delta >= 0 else "negative",
            "trigger": trig,
            "behavior": beh,
            "financial": rev,
            "downstream": downstream,
            "action": action
        })

    return results


def analyze_inter_business_linkages(active_keys, row, custom_catalog=None):
    """
    Computes cross-business ripple effects and substitution flows dynamically
    for any combination of active businesses in the portfolio (including Square POS and Stripe).
    """
    catalog = custom_catalog if custom_catalog else BUSINESS_CATALOG
    linkages = []
    
    # 1. Square POS (physical store) vs Stripe (digital e-commerce)
    if "square_pos_merchant" in active_keys and "stripe_merchant" in active_keys:
        sq_delta = row.get("square_pos_merchant_net_impact", 0.0)
        st_delta = row.get("stripe_merchant_net_impact", 0.0)
        if sq_delta < 0 and st_delta > 0:
            linkages.append({
                "title": "Channel Migration: Physical POS Counter to Digital Stripe Checkout",
                "summary": f"In-store Square registers contracted by -${abs(sq_delta):,.0f}, while digital Stripe checkouts captured +${st_delta:,.0f}.",
                "chain_steps": [
                    "Step 1: Rainy or adverse weather keeps shoppers away from downtown retail storefronts.",
                    "Step 2: Shoppers browse mobile product catalogs and complete digital purchases from home.",
                    "Step 3: Online transactions settle immediately through Stripe payment rails while in-person registers sit quiet.",
                    "Outcome: Digital GMV offsets physical footfall losses, shifting business bottleneck to warehouse parcel packing."
                ],
                "type": "Omnichannel Channel Substitution"
            })
            
    # 2. Dine-In Restaurant vs Food Delivery
    if "dine_in_restaurant" in active_keys and "food_delivery" in active_keys:
        dine_delta = row.get("dine_in_restaurant_net_impact", 0.0)
        deliv_delta = row.get("food_delivery_net_impact", 0.0)
        if dine_delta < 0 and deliv_delta > 0:
            linkages.append({
                "title": "Customer Switch: Restaurants & Bistros to Food Delivery",
                "summary": f"Dine-in lost -${abs(dine_delta):,.0f} in tables, while Food Delivery gained +${deliv_delta:,.0f} in orders.",
                "chain_steps": [
                    "Step 1: Wet or freezing weather prompts diners to cancel evening table reservations.",
                    "Step 2: Those same households order restaurant-prepared meals online through delivery apps.",
                    "Step 3: Courier fleets absorb the demand while restaurant floor waitstaff assist with kitchen dispatch.",
                    "Outcome: Dine-in table spend converts into delivery orders, shifting restaurant revenue to off-premise channels."
                ],
                "type": "Direct Customer Substitution"
            })
            
    # 3. Square POS vs Food Delivery
    if "square_pos_merchant" in active_keys and "food_delivery" in active_keys:
        sq_delta = row.get("square_pos_merchant_net_impact", 0.0)
        deliv_delta = row.get("food_delivery_net_impact", 0.0)
        if sq_delta < 0 and deliv_delta > 0:
            linkages.append({
                "title": "Local Storefront to On-Demand Delivery Redistribution",
                "summary": f"Walk-in register receipts fell -${abs(sq_delta):,.0f}, while on-demand food orders surged +${deliv_delta:,.0f}.",
                "chain_steps": [
                    "Step 1: Rain creates reluctance for shoppers to walk along retail streets.",
                    "Step 2: Consumers order food and essentials directly to their doorstep via delivery couriers.",
                    "Step 3: Merchants with integrated delivery channels recoup lost counter revenues.",
                    "Outcome: Revenue shifts from front-of-house register terminals to delivery app dispatch."
                ],
                "type": "Logistics Channel Migration"
            })
            
    # 4. Bikeshare vs Rideshare
    if "bikeshare_operator" in active_keys and "rideshare_fleet" in active_keys:
        bike_delta = row.get("bikeshare_operator_net_impact", 0.0)
        ride_delta = row.get("rideshare_fleet_net_impact", 0.0)
        if bike_delta < 0 and ride_delta > 0:
            linkages.append({
                "title": "Commuter Shift: Bike-Share to Taxis & Rideshares",
                "summary": f"Bicycle trips dropped by -${abs(bike_delta):,.0f}, while Rideshare revenue surged +${ride_delta:,.0f}.",
                "chain_steps": [
                    "Step 1: Wet roads and low temperatures make riding bicycles and scooters uncomfortable and hazardous.",
                    "Step 2: Commuters abandon outdoor bike stations and request ride-hailing vehicles.",
                    "Step 3: Surge pricing multipliers trigger as passenger ride requests outstrip driver supply.",
                    "Outcome: Bike-sharing loses rental income, while taxi and rideshare companies see surging fares."
                ],
                "type": "Commuter Mode Change"
            })

    # 5. Car Wash vs Rideshare
    if "car_wash" in active_keys and "rideshare_fleet" in active_keys:
        rain = row.get("precip_accumulation_mm", 0.0)
        if rain > 1.5:
            linkages.append({
                "title": "Weather Halt: Car Wash Drop vs. Rideshare Surge",
                "summary": "Car washes see immediate volume collapse, while city rideshares experience high surge multipliers.",
                "chain_steps": [
                    "Step 1: Precipitation makes washing private cars futile for vehicle owners.",
                    "Step 2: Car wash bays sit empty with -85% footfall.",
                    "Step 3: Simultaneously, rain forces city travelers into private rideshare vehicles.",
                    "Outcome: Car wash owners experience idle shifts, while rideshare drivers earn surge earnings."
                ],
                "type": "Outdoor Service Postponement"
            })

    # 6. Outdoor Golf/Theme Parks vs Movie Theaters
    if "golf_theme_park" in active_keys and "movie_theaters" in active_keys:
        golf_delta = row.get("golf_theme_park_net_impact", 0.0)
        movie_delta = row.get("movie_theaters_net_impact", 0.0)
        if golf_delta < 0 and movie_delta > 0:
            linkages.append({
                "title": "Leisure Substitution: Outdoor Attractions to Indoor Cinema",
                "summary": f"Outdoor golf/parks lost -${abs(golf_delta):,.0f}, while indoor movie theaters gained +${movie_delta:,.0f}.",
                "chain_steps": [
                    "Step 1: Rainy weekend weather shuts down golf courses and outdoor theme park rides.",
                    "Step 2: Families and recreational visitors seek indoor weekend alternatives.",
                    "Step 3: Demand shifts directly to indoor multiplexes, bowling alleys, and arcades.",
                    "Outcome: Outdoor venues experience revenue deficits while indoor venues sell out."
                ],
                "type": "Recreational Substitution"
            })

    # 7. Ice Cream vs Hot Cafe & Bakery
    if "ice_cream_beverages" in active_keys and "hot_cafe_bakery" in active_keys:
        ice_delta = row.get("ice_cream_beverages_net_impact", 0.0)
        cafe_delta = row.get("hot_cafe_bakery_net_impact", 0.0)
        temp_val = row.get("air_temp_deg_c", 20.0)
        if temp_val > 28.0 and ice_delta > 0:
            linkages.append({
                "title": "Heat Preference: Cold Drinks Surge vs Hot Bakery Slowdown",
                "summary": f"Cold drinks surged +${ice_delta:,.0f}, while hot baked goods dipped -${abs(cafe_delta):,.0f}.",
                "chain_steps": [
                    "Step 1: Afternoon temperatures spike above 28°C.",
                    "Step 2: Customers seek immediate cooling refreshments and avoid hot food.",
                    "Step 3: Spending redirects from hot coffee and fresh baked pastries to iced drinks and gelato.",
                    "Outcome: Cold treat parlors gain sales, while hot bakeries experience a summer slowdown."
                ],
                "type": "Thermal Preference Shift"
            })
        elif (temp_val < 14.0 or row.get("precip_accumulation_mm", 0.0) > 1.0) and cafe_delta > 0:
            linkages.append({
                "title": "Cold Weather Preference: Hot Comfort Bakery vs Cold Treats",
                "summary": f"Hot cafes gained +${cafe_delta:,.0f}, while cold treat sales dipped -${abs(ice_delta):,.0f}.",
                "chain_steps": [
                    "Step 1: Ambient temperatures drop or rain begins to fall.",
                    "Step 2: Customers desire warmth and shelter, ordering hot coffee, soups, and warm pastries.",
                    "Step 3: Cold drink and ice cream demand is postponed until warmer weather.",
                    "Outcome: Hot cafes operate at full indoor table capacity."
                ],
                "type": "Comfort Preference Shift"
            })

    # 8. Dynamic linkage for ANY other pair where one loses and one gains
    if len(linkages) == 0 and len(active_keys) >= 2:
        neg_candidates = []
        pos_candidates = []
        for k in active_keys:
            delta = row.get(f"{k}_net_impact", 0.0)
            if delta < -50:
                neg_candidates.append((k, delta))
            elif delta > 50:
                pos_candidates.append((k, delta))
        if neg_candidates and pos_candidates:
            l_key, l_val = sorted(neg_candidates, key=lambda x: x[1])[0]
            w_key, w_val = sorted(pos_candidates, key=lambda x: x[1], reverse=True)[0]
            l_name = catalog[l_key]["name"]
            w_name = catalog[w_key]["name"]
            linkages.append({
                "title": f"Cross-Portfolio Redistribution: {l_name} to {w_name}",
                "summary": f"{l_name} experienced a -${abs(l_val):,.0f} weather drag, while {w_name} gained +${w_val:,.0f}.",
                "chain_steps": [
                    f"Step 1: Weather conditions altered standard customer footfall for {l_name}.",
                    f"Step 2: Spending and consumer attention migrated toward {w_name}.",
                    f"Step 3: Empirical weather elasticities caused revenue divergence between physical exposure and indoor/digital channels.",
                    f"Outcome: Cross-business hedging cushioned portfolio volatility."
                ],
                "type": "Empirical Portfolio Rebalance"
            })

    return linkages


def generate_future_ai_forecast(active_keys, forecast_event, custom_catalog=None):
    """
    Generates a 7-day forward projection line series and operational recommendations
    for any combination of preset or custom businesses.
    """
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    catalog = custom_catalog if custom_catalog else BUSINESS_CATALOG
    
    if "Rainstorm" in forecast_event:
        weather_profile = [0.0, 0.5, 8.5, 12.0, 4.0, 0.0, 0.0]
        desc = "Rainstorm system forecasted for Wednesday through Friday."
    elif "Blizzard" in forecast_event:
        weather_profile = [0.0, 0.0, 0.0, 5.0, 8.0, 2.0, 0.0]
        desc = "Blizzard and freezing conditions forecasted for Thursday through Saturday."
    elif "Heatwave" in forecast_event:
        weather_profile = [28.0, 32.0, 36.0, 38.0, 39.0, 35.0, 30.0]
        desc = "High-temperature heatwave system with temperatures exceeding 38°C."
    else:
        weather_profile = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        desc = "Clear weather conditions anticipated across the upcoming 7-day window."
        
    projections = {}
    total_impact_all = 0.0
    
    for b_key in active_keys:
        if b_key not in catalog:
            continue
        cfg = catalog[b_key]
        base = cfg["base_daily_rev"]
        series_actual = []
        series_base = []
        
        for i, w_val in enumerate(weather_profile):
            dow_m = [0.88, 0.90, 0.95, 1.05, 1.38, 1.48, 1.28][i]
            day_base = base * dow_m
            
            if "Rain" in forecast_event:
                eff_rain = min(w_val, 30.0) * 0.35
                mult = 1.0 + eff_rain * cfg.get("rain_elasticity", 0.0)
            elif "Blizzard" in forecast_event:
                eff_snow = min(w_val, 20.0) * 0.40
                mult = 1.0 + eff_snow * cfg.get("snow_elasticity", 0.0)
            elif "Heatwave" in forecast_event:
                temp_anom = min(12.0, max(0.0, w_val - 25.0))
                mult = 1.0 + temp_anom * cfg.get("temp_elasticity", 0.0)
            else:
                mult = 1.0
                
            day_act = day_base * max(0.20, min(2.20, mult))
            series_base.append(round(day_base, 0))
            series_actual.append(round(day_act, 0))
            
        projections[b_key] = {
            "name": cfg["name"],
            "color": cfg.get("color", "#000000"),
            "dash": cfg.get("dash", "solid"),
            "symbol": cfg.get("symbol", "circle"),
            "days": days,
            "actual_series": series_actual,
            "baseline_series": series_base,
            "net_week_impact": sum(series_actual) - sum(series_base)
        }
        total_impact_all += (sum(series_actual) - sum(series_base))
        
    ai_advice = []
    if "food_delivery" in active_keys and ("Rain" in forecast_event or "Blizzard" in forecast_event):
        ai_advice.append("Food Delivery Staffing: Driver numbers drop by ~20% during rain. Add a small bonus (+3.50 per order) 45 minutes before the storm starts so orders are delivered on time.")
    if "dine_in_restaurant" in active_keys and ("Rain" in forecast_event or "Blizzard" in forecast_event):
        ai_advice.append("Restaurant Operations: Outdoor dining will be empty. Move dining room floor waiters to help pack takeout and delivery boxes in the kitchen.")
    if "car_wash" in active_keys and "Rain" in forecast_event:
        ai_advice.append("Car Wash Operations: Shift staff hours away from rainy Wednesday/Thursday and schedule maximum wash lane capacity for clear post-storm weekend days.")
    if "movie_theaters" in active_keys and "Rain" in forecast_event:
        ai_advice.append("Theater Concessions: Rainy weekend will boost cinema footfall by +35%. Increase popcorn and beverage inventory orders by Tuesday afternoon.")
    if "hvac_home_services" in active_keys and ("Heatwave" in forecast_event or "Blizzard" in forecast_event):
        ai_advice.append("HVAC Dispatch: Extreme temperatures will drive a +65% surge in emergency calls. Put on-call emergency technicians on standby.")
    if "retail_apparel" in active_keys and "Rain" in forecast_event:
        ai_advice.append("Retail Stores: Put umbrellas, raincoats, and waterproof shoes right at the entrance display by Wednesday morning.")
    if "ice_cream_beverages" in active_keys and "Heatwave" in forecast_event:
        ai_advice.append("Cold Drinks Inventory: Sales of cold treats will jump +45%. Double your ice orders and check that refrigerators are running cold.")
    if "golf_theme_park" in active_keys and "Rain" in forecast_event:
        ai_advice.append("Outdoor Venues: Rain will reduce tee times and ticket sales by -75%. Offer indoor simulator discounts or rain-check booking vouchers.")
    if "nyc_taxi" in active_keys and ("Rain" in forecast_event or "Blizzard" in forecast_event):
        ai_advice.append("Taxi & Rideshare Fleet: Street hail demand jumps +25% during rain. Broadcast driver heat maps toward transit interchanges and subway hubs 30 minutes before heavy showers.")
    if any("citibike" in k for k in active_keys) and ("Rain" in forecast_event or "Blizzard" in forecast_event):
        ai_advice.append("Micromobility Operations: Bike-share checkouts drop -40% to -65% on wet pavement. Halt street rebalancing van runs during storms to avoid traffic and focus on depot e-bike charging.")
    if "online_retail" in active_keys and ("Rain" in forecast_event or "Blizzard" in forecast_event):
        ai_advice.append("E-Commerce Marketing: Cold and rainy afternoons trigger +15% higher checkout conversions. Schedule automated email promotions and flash discounts for rainy days.")
    if any("chipotle" in k for k in active_keys) and ("Rain" in forecast_event or "Blizzard" in forecast_event):
        ai_advice.append("Fast-Casual Restaurant Operations: Inclement weather depresses dining room footfall while digital orders surge. Prioritize digital makeline (DML) ingredients and packaging.")
        
    if not ai_advice:
        ai_advice.append("Standard Operations: Regular conditions expected. Maintain baseline staffing schedules and normal inventory reorder points.")
        
    return {
        "weather_desc": desc,
        "days": days,
        "projections": projections,
        "total_impact_all": total_impact_all,
        "ai_advice": ai_advice
    }
