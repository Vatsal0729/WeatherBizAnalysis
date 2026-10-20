"""
Real EDA Engine: Descriptive, Bivariate, and Econometric Statistics
Computed dynamically across the 4 verified production datasets and weather telemetry.
"""
import os
import json
import numpy as np
import pandas as pd
from functools import lru_cache
from src.historical_dashboard import observed_weather_for
from sklearn.ensemble import IsolationForest
from statsmodels.stats.diagnostic import het_breuschpagan
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.stats.stattools import durbin_watson
import statsmodels.api as sm

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REAL_DATA_DIR = os.path.join(BASE_DIR, "data", "real")
PROCESSED_DATA_DIR = os.path.join(BASE_DIR, "data", "processed")

SERIES_METADATA = {
    "nyc_taxi": {
        "name": "NYC Yellow Taxi (Hourly Hail Volume)",
        "unit": "trips/hour",
        "cadence": "hourly",
        "file": os.path.join(REAL_DATA_DIR, "nyc_taxi_hourly.parquet"),
        "count_col": "trip_count",
        "revenue_col": "total_revenue",
        "city": "New York City",
        "date_col": "hour",
        "time_grain": "hourly"
        ,"geography": "New York City", "value_status": "Reported TLC fares and trips",
        "coverage_note": "January 2023 and August 2026 snapshots; the intervening gap is not continuous coverage."
    },
    "citibike_nyc": {
        "name": "Citi Bike NYC (Daily Micromobility Rides)",
        "unit": "rides/day",
        "cadence": "daily",
        "file": os.path.join(REAL_DATA_DIR, "citibike_daily.parquet"),
        "count_col": "total_rides",
        "revenue_col": "estimated_revenue_usd",
        "city": "New York City",
        "date_col": "date",
        "time_grain": "daily"
        ,"geography": "New York City", "value_status": "Rides observed; revenue estimated from assumed fares",
        "coverage_note": "Daily snapshot; estimated revenue is not operator-reported revenue."
    },
    "online_retail": {
        "name": "E-Commerce Retail (Daily Order Volume)",
        "unit": "orders/day",
        "cadence": "daily",
        "file": os.path.join(REAL_DATA_DIR, "online_retail_daily.parquet"),
        "count_col": "order_count",
        "revenue_col": "daily_revenue",
        "city": "London, UK (regional proxy)",
        "date_col": "date",
        "time_grain": "daily"
        ,"geography": "United Kingdom", "value_status": "Reported transactions aggregated daily",
        "coverage_note": "London weather is a regional proxy, not a verified store location."
    },
    "chipotle_sec": {
        "name": "Chipotle Mexican Grill (SEC 10-Q Revenue)",
        "unit": "USD millions/quarter",
        "cadence": "quarterly",
        "file": os.path.join(REAL_DATA_DIR, "sec_quarterly_restaurants.parquet"),
        "count_col": "revenue_usd",
        "revenue_col": "revenue_usd",
        "city": "New York City",
        "date_col": "end",
        "time_grain": "quarterly"
        ,"geography": "Company-wide United States", "value_status": "Reported SEC quarterly revenue",
        "coverage_note": "No defensible company-wide matched weather; weather-effect inference is disabled."
    }
}

SEASONS = {
    "all": "All seasons",
    "winter": "Winter (Dec - Feb)",
    "spring": "Spring (Mar - May)",
    "summer": "Summer (Jun - Aug)",
    "autumn": "Autumn (Sep - Nov)"
}

def get_season(month: int) -> str:
    if month in (12, 1, 2):
        return "winter"
    elif month in (3, 4, 5):
        return "spring"
    elif month in (6, 7, 8):
        return "summer"
    return "autumn"

def load_weather_reference():
    parquet_path = os.path.join(REAL_DATA_DIR, "nyc_weather_hourly.parquet")
    if not os.path.exists(parquet_path):
        parquet_path = os.path.join(PROCESSED_DATA_DIR, "weather_business_merged.parquet")
    if not os.path.exists(parquet_path):
        return pd.DataFrame()
    df = pd.read_parquet(parquet_path)
    return df

def get_matched_series_data(series_key: str = "nyc_taxi") -> pd.DataFrame:
    meta = SERIES_METADATA.get(series_key, SERIES_METADATA["nyc_taxi"])
    if not os.path.exists(meta["file"]):
        return pd.DataFrame()
    
    biz_df = pd.read_parquet(meta["file"])
    # EDA uses observed weather only. Presentation estimates remain in the separate
    # executive scenario layer and never enter descriptive or inferential statistics.
    biz_df['date'] = pd.to_datetime(biz_df[meta['date_col']])
    biz_df['count'] = biz_df[meta['count_col']]
    if series_key == 'chipotle_sec':
        biz_df['count'] = biz_df['count'] / 1e6
    biz_df['revenue'] = biz_df[meta['revenue_col']]
    weather = observed_weather_for(biz_df['date'], series_key, hourly=series_key == 'nyc_taxi')
    merged = biz_df.reset_index(drop=True).copy()
    merged['weather_estimated'] = False
    for target, source in [('rain_mm','rain'),('temperature_c','temperature'),('wind_kmh','wind'),('snow_cm','snow')]:
        merged[target] = weather[source].to_numpy()

    merged["season"] = merged["date"].dt.month.map(get_season)
    merged["weekday"] = merged["date"].dt.dayofweek
    merged["day_type"] = np.where(merged["weekday"] < 5, "weekday", "weekend")
    merged["year"] = merged["date"].dt.year.astype(str)
    
    return merged.sort_values("date")


def build_dataset_scorecards():
    """Comparable metadata without pretending the four case studies share a design."""
    cards = []
    for key, meta in SERIES_METADATA.items():
        d = get_matched_series_data(key)
        observed_weather = int(d[["rain_mm", "temperature_c", "wind_kmh"]].notna().all(axis=1).sum()) if len(d) else 0
        date_min = d["date"].min() if len(d) else None
        date_max = d["date"].max() if len(d) else None
        cards.append({
            "key": key, "name": meta["name"], "geography": meta["geography"],
            "cadence": meta["cadence"], "unit": meta["unit"], "n": len(d),
            "start": str(date_min.date()) if date_min is not None else "Unavailable",
            "end": str(date_max.date()) if date_max is not None else "Unavailable",
            "weather_n": observed_weather, "weather_pct": (100 * observed_weather / len(d)) if len(d) else 0,
            "value_status": meta["value_status"], "coverage_note": meta["coverage_note"]
        })
    return cards


def compute_quality_evidence(d: pd.DataFrame):
    """Dataset-level cleaning evidence; flags observations but never silently deletes them."""
    numeric = [c for c in ["count", "revenue", "rain_mm", "temperature_c", "snow_cm", "wind_kmh"] if c in d]
    duplicate_rows = int(d.duplicated().sum())
    duplicate_dates = int(d.duplicated("date").sum()) if "date" in d else 0
    rows = []
    for col in numeric:
        x = pd.to_numeric(d[col], errors="coerce")
        q1, q3 = x.quantile([.25, .75]) if x.notna().any() else (np.nan, np.nan)
        iqr = q3 - q1
        iqr_mask = ((x < q1 - 1.5 * iqr) | (x > q3 + 1.5 * iqr)) if pd.notna(iqr) else pd.Series(False, index=x.index)
        valid = x.dropna()
        isolation_n = 0
        if len(valid) >= 20 and valid.nunique() >= 3:
            pred = IsolationForest(contamination=0.05, random_state=42).fit_predict(valid.to_numpy().reshape(-1, 1))
            isolation_n = int((pred == -1).sum())
        raw_skew = float(valid.skew()) if len(valid) >= 3 else np.nan
        nonnegative = valid.clip(lower=0)
        log_skew = float(np.log1p(nonnegative).skew()) if len(nonnegative) >= 3 else np.nan
        rows.append({
            "feature": col, "dtype": str(d[col].dtype), "n": int(valid.size),
            "missing": int(x.isna().sum()), "missing_pct": float(100*x.isna().mean()),
            "missing_mechanism": ("Structural / not applicable" if x.isna().all() else
                                  "Likely MAR: weather availability depends on source/date" if col in {"rain_mm","temperature_c","snow_cm","wind_kmh"} and x.isna().any() else
                                  "No missing values observed"),
            "invalid_negative": int((x < 0).sum()) if col in {"count","revenue","rain_mm","snow_cm","wind_kmh"} else 0,
            "iqr_flags": int(iqr_mask.sum()), "isolation_flags": isolation_n,
            "raw_skew": raw_skew, "log1p_skew": log_skew,
        })
    return {"rows": rows, "duplicate_rows": duplicate_rows, "duplicate_dates": duplicate_dates,
            "policy": "Flag, investigate, and retain plausible extremes; do not impute business outcomes."}


def compute_missingness_matrix(d: pd.DataFrame):
    cols = [c for c in ["count","revenue","rain_mm","temperature_c","snow_cm","wind_kmh"] if c in d]
    if d.empty:
        return {"columns": cols, "rows": []}
    ordered = d.sort_values("date")
    chunk_count = min(12, len(ordered))
    bounds = np.linspace(0, len(ordered), chunk_count + 1, dtype=int)
    chunks = [ordered.iloc[bounds[i]:bounds[i+1]] for i in range(chunk_count)]
    rows = []
    for i, chunk in enumerate(chunks, 1):
        row = {"label": f"Period {i}"}
        for c in cols:
            row[c] = float(100 * chunk[c].isna().mean())
        rows.append(row)
    return {"columns": cols, "rows": rows}


def compute_advanced_association(d: pd.DataFrame):
    """Diagnostics and time-split validation for observed weather only."""
    pair = d[["date","count","rain_mm","temperature_c","wind_kmh"]].dropna().sort_values("date").copy()
    result = {"available": False, "n": len(pair), "reason": "At least 40 matched observations are required."}
    if len(pair) < 40 or pair["rain_mm"].nunique() < 2:
        return result
    dates = pd.to_datetime(pair["date"])
    x = pair[["rain_mm","temperature_c","wind_kmh"]].astype(float).copy()
    x["trend"] = (dates - dates.min()).dt.total_seconds() / 86400
    calendar = pd.DataFrame({"weekday":dates.dt.dayofweek.astype(str), "month":dates.dt.month.astype(str)}, index=pair.index)
    x = pd.concat([x, pd.get_dummies(calendar, drop_first=True, dtype=float)], axis=1)
    x = sm.add_constant(x, has_constant="add")
    if np.linalg.matrix_rank(x.to_numpy()) < x.shape[1] or len(x) < 3*x.shape[1]:
        result["reason"] = "The selected subset is too small or collinear for the controlled model."
        return result
    split = max(int(len(pair)*.8), x.shape[1] + 2)
    if split >= len(pair):
        return result
    model = sm.OLS(pair["count"].astype(float), x).fit(cov_type="HC3")
    # Least-squares prediction tolerates a category absent from the chronological
    # training window without pretending its coefficient is uniquely identified.
    beta, *_ = np.linalg.lstsq(x.iloc[:split].to_numpy(), pair["count"].iloc[:split].astype(float).to_numpy(), rcond=None)
    pred = pd.Series(x.iloc[split:].to_numpy() @ beta, index=x.index[split:])
    actual = pair["count"].iloc[split:]
    mae = float(np.mean(np.abs(actual-pred)))
    baseline = float(np.mean(np.abs(actual-pair["count"].iloc[:split].median())))
    bp = het_breuschpagan(model.resid, model.model.exog)
    vif_rows = []
    for i, col in enumerate(x.columns):
        if col == "const": continue
        try: vif_rows.append({"feature":col,"vif":float(variance_inflation_factor(x.to_numpy(),i))})
        except Exception: pass
    pearson = float(pair["rain_mm"].corr(pair["count"], method="pearson"))
    spearman = float(pair["rain_mm"].corr(pair["count"], method="spearman"))
    sensitivity = []
    for label, subset in [("All observed",pair),("Without top 1% rain",pair[pair.rain_mm <= pair.rain_mm.quantile(.99)]),("Wet days only",pair[pair.rain_mm > 0])]:
        sensitivity.append({"label":label,"n":len(subset),"pearson":float(subset.rain_mm.corr(subset["count"])) if len(subset)>=3 and subset.rain_mm.nunique()>1 else np.nan,"spearman":float(subset.rain_mm.corr(subset["count"],method="spearman")) if len(subset)>=3 and subset.rain_mm.nunique()>1 else np.nan})
    lagged = []
    for lag in range(0,4):
        shifted = pair["rain_mm"].shift(lag)
        lagged.append({"lag":lag,"n":int((shifted.notna() & pair["count"].notna()).sum()),"correlation":float(shifted.corr(pair["count"],method="spearman"))})
    return {"available":True,"n":len(pair),"pearson":pearson,"spearman":spearman,
            "rain_coef":float(model.params["rain_mm"]),"rain_pvalue":float(model.pvalues["rain_mm"]),
            "rain_ci":model.conf_int().loc["rain_mm"].astype(float).tolist(),"r_squared":float(model.rsquared),
            "durbin_watson":float(durbin_watson(model.resid)),"breusch_pagan_pvalue":float(bp[1]),
            "test_n":len(actual),"test_mae":mae,"baseline_mae":baseline,"vif":sorted(vif_rows,key=lambda z:z["vif"],reverse=True)[:6],
            "sensitivity":sensitivity,"lagged":lagged,"reason":""}

def filter_series(df: pd.DataFrame, year: str = "all", season: str = "all", day_type: str = "all") -> pd.DataFrame:
    filtered = df.copy()
    if year != "all":
        filtered = filtered[filtered["year"] == str(year)]
    if season != "all":
        filtered = filtered[filtered["season"] == season]
    if day_type != "all":
        filtered = filtered[filtered["day_type"] == day_type]
    return filtered

def compute_eda_statistics(d: pd.DataFrame, columns=None):
    if columns is None:
        columns = ["count", "rain_mm", "temperature_c", "snow_cm", "wind_kmh"]
    
    stats = []
    for col in columns:
        if col not in d.columns:
            continue
        x = d[col].dropna()
        if len(x) == 0:
            continue
        q1, q3 = x.quantile([0.25, 0.75])
        iqr = q3 - q1
        mean = float(x.mean())
        median = float(x.median())
        std = float(x.std()) if len(x) > 1 else 0.0
        skew = float(x.skew()) if len(x) > 2 else 0.0
        kurt = float(x.kurt()) if len(x) > 3 else 0.0
        flagged = int(((x < q1 - 1.5 * iqr) | (x > q3 + 1.5 * iqr)).sum())
        
        stats.append({
            "feature": col,
            "n": len(x),
            "missing": int(d[col].isna().sum()),
            "mean": mean,
            "median": median,
            "std": std,
            "iqr": iqr,
            "skew": skew,
            "kurtosis": kurt,
            "flagged": flagged
        })
    return stats

def compute_histograms(d: pd.DataFrame, columns=None):
    if columns is None:
        columns = ["count", "rain_mm"]
    histograms = []
    for col in columns:
        if col not in d.columns:
            continue
        valid = d[col].dropna()
        if len(valid) == 0:
            continue
        counts, edges = np.histogram(valid, bins=12)
        max_c = max(int(counts.max()), 1)
        bars = [
            {
                "label": f"{edges[i]:,.1f}–{edges[i+1]:,.1f}",
                "value": int(n),
                "width": float(n / max_c * 580)
            }
            for i, n in enumerate(counts)
        ]
        histograms.append({"name": col, "bars": bars})
    return histograms

def compute_weekday_bars(d: pd.DataFrame):
    if "weekday" not in d.columns:
        return []
    weekdays = d.groupby("weekday")["count"].agg(["mean", "size"])
    max_mean = max(float(weekdays["mean"].max()), 1.0) if len(weekdays) > 0 else 1.0
    labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    bars = []
    for i in range(7):
        if i in weekdays.index:
            r = weekdays.loc[i]
            val = float(r["mean"])
            cnt = int(r["size"])
        else:
            val = 0.0
            cnt = 0
        bars.append({
            "label": labels[i],
            "value": val,
            "n": cnt,
            "width": float(val / max_mean * 580)
        })
    return bars

def compute_rain_groups(d: pd.DataFrame):
    if "rain_mm" not in d.columns or "count" not in d.columns:
        return []
    bins = [-0.001, 0, 1, 5, 10, float("inf")]
    labels = ["Dry: 0", ">0–1", ">1–5", ">5–10", ">10"]
    d_copy = d.copy()
    d_copy["rain_group"] = pd.cut(d_copy["rain_mm"], bins, labels=labels)
    g = d_copy.groupby("rain_group", observed=False)["count"].agg(["size", "mean", "median"]).reset_index()
    records = g[g["size"] > 0].to_dict("records")
    for r in records:
        r["size"] = int(r["size"])
        r["mean"] = float(r["mean"])
        r["median"] = float(r["median"])
    return records

def compute_monthly_trends(d: pd.DataFrame):
    if "date" not in d.columns or "count" not in d.columns:
        return "", "", "", 100.0
    period_s = d["date"].dt.to_period("M")
    trends = d.groupby(period_s)["count"].mean()
    if len(trends) == 0:
        return "", "", "", 100.0
    max_v = max(float(trends.max()), 1.0)
    n_points = max(len(trends) - 1, 1)
    points = " ".join(
        f"{60 + i * 620 / n_points:.1f},{220 - v / max_v * 180:.1f}"
        for i, v in enumerate(trends)
    )
    start_label = str(trends.index.min())
    end_label = str(trends.index.max())
    return points, start_label, end_label, max_v

def compute_correlation_and_math(d: pd.DataFrame):
    columns = ["count", "rain_mm", "temperature_c", "snow_cm", "wind_kmh"]
    avail_cols = [c for c in columns if c in d.columns]
    
    corr_df = d[avail_cols].corr(method="spearman")
    
    # Paired rain math
    rain_series = d[["rain_mm", "count"]].dropna()
    n = len(rain_series)
    if n >= 3:
        x = rain_series["rain_mm"].values
        y = rain_series["count"].values
        xmean = float(x.mean())
        ymean = float(y.mean())
        dx = x - xmean
        dy = y - ymean
        sxx = float((dx**2).sum())
        syy = float((dy**2).sum())
        sxy = float((dx * dy).sum())
        cov = sxy / (n - 1)
        sx = np.sqrt(sxx / (n - 1)) if sxx > 0 else 0.0
        sy = np.sqrt(syy / (n - 1)) if syy > 0 else 0.0
        pearson = (sxy / np.sqrt(sxx * syy)) if (sxx > 0 and syy > 0) else 0.0
        spearman = float(pd.Series(x).corr(pd.Series(y), method="spearman"))
        slope = (sxy / sxx) if sxx > 0 else 0.0
        intercept = ymean - slope * xmean
        r2 = pearson**2
        
        # Examples for the 5-row table
        examples = []
        for i in range(min(5, n)):
            examples.append({
                "date": str(d.loc[rain_series.index[i], "date"].date()),
                "x": float(x[i]),
                "y": float(y[i]),
                "dx": float(dx[i]),
                "dy": float(dy[i]),
                "product": float(dx[i] * dy[i])
            })
            
        # Scatter points for SVG
        xmax = max(float(x.max()), 1.0)
        ymax = max(float(y.max()), 1.0)
        ymin = max(0.0, float(y.min()))
        y_range = max(ymax - ymin, 1.0)
        
        scatter = []
        for i in range(min(120, n)):
            px = 70 + (x[i] / xmax) * 610
            py = 260 - ((y[i] - ymin) / y_range) * 200
            scatter.append({
                "x": round(px, 1),
                "y": round(py, 1),
                "label": f"{x[i]:.1f} mm rain · {y[i]:,.0f} counts"
            })
            
        fit_y1 = 260 - ((intercept + slope * 0 - ymin) / y_range) * 200
        fit_y2 = 260 - ((intercept + slope * xmax - ymin) / y_range) * 200
        
        rain_math = {
            "available": True,
            "n": n,
            "xmean": xmean,
            "ymean": ymean,
            "sxx": sxx,
            "syy": syy,
            "sxy": sxy,
            "covariance": cov,
            "sx": sx,
            "sy": sy,
            "pearson": pearson,
            "spearman": spearman,
            "slope": slope,
            "intercept": intercept,
            "r2": r2,
            "xmin": 0.0,
            "xmax": round(xmax, 1),
            "examples": examples
        }
        line_meta = {
            "low": ymin,
            "high": ymax,
            "y1": round(fit_y1, 1),
            "y2": round(fit_y2, 1)
        }
    else:
        rain_math = {"available": False}
        scatter = []
        line_meta = {"low": 0, "high": 100, "y1": 260, "y2": 260}

    # Summary table across features
    assocs = []
    for col in ["rain_mm", "temperature_c", "wind_kmh", "snow_cm"]:
        if col in d.columns:
            pair = d[[col, "count"]].dropna()
            if len(pair) >= 3 and pair[col].std() > 0:
                p_r = float(pair[col].corr(pair["count"], method="pearson"))
                s_r = float(pair[col].corr(pair["count"], method="spearman"))
                assocs.append({
                    "feature": col,
                    "n": len(pair),
                    "available": True,
                    "pearson": p_r,
                    "spearman": s_r,
                    "r2": p_r**2
                })
            else:
                assocs.append({"feature": col, "n": len(pair), "available": False})

    association = {
        "associations": assocs,
        "rain": rain_math,
        "scatter": scatter,
        "line": line_meta
    }
    return corr_df, avail_cols, association

def get_raw_to_published_audit():
    """Current analytical inventory, computed from files rather than fixed counts."""
    from src.real_data_manager import load_real_dataset, REAL_BUSINESS_CATALOG
    rows = []
    for key, cfg in REAL_BUSINESS_CATALOG.items():
        count = len(load_real_dataset(key))
        rows.append({'source':cfg['source'],'raw':count,'raw_unit':'snapshot rows','clean':count,'clean_unit':cfg['cadence']+' observations','excluded':0,'action':'Current snapshot inventory; transaction-level exclusion counts are outside this view.'})
    weather_count = 0
    for name in ['nyc_weather_hourly.parquet','retail_weather_daily.parquet']:
        path = os.path.join(REAL_DATA_DIR,name)
        if os.path.exists(path):
            weather_count += len(pd.read_parquet(path))
    rows.append({'source':'Historical weather snapshots','raw':weather_count,'raw_unit':'snapshot rows','clean':weather_count,'clean_unit':'hourly/daily records','excluded':0,'action':'Downloaded historical weather; modelled estimates are constructed in the presentation layer.'})
    return {'rows':rows,'note':'Counts describe current local snapshots. No transaction-level exclusion audit is claimed by this inventory.'}
