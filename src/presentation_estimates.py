"""Presentation estimates. Never write inferred values into source datasets."""
import numpy as np
import pandas as pd

def fill_weather(observed, dates, key, hourly=False):
    dates = pd.DatetimeIndex(pd.to_datetime(dates))
    # Deterministic seasonal scenario: stable across refreshes and filter choices.
    ordinal = np.array([d.toordinal() for d in dates],dtype=float)
    phase = 2*np.pi*(dates.dayofyear.to_numpy()-80)/365.25
    seasonal_temp = (11.5 if key == 'online_retail' else 13.0) + (8.5 if key == 'online_retail' else 13.5)*np.sin(phase)
    uniform = np.mod(np.sin(ordinal*12.9898+78.233)*43758.5453,1)
    wet = uniform > 0.62
    rain = np.where(wet, -np.log(np.maximum(1-uniform,0.001))*3.2,0)
    snow = np.where(seasonal_temp<1,rain*0.7,0)
    wind = 10+10*np.mod(np.sin(ordinal*4.17)*517.9,1)
    if hourly:
        seasonal_temp += 3*np.sin(2*np.pi*(dates.hour.to_numpy()-8)/24)
        rain, snow = rain/24, snow/24
    if key == 'chipotle_sec':
        # Representative quarterly climate scenario, not company-wide observations.
        starts = dates.to_period('Q').start_time
        ends = dates.to_period('Q').end_time.normalize()
        days = np.array((ends-starts).days+1,dtype=float)
        rain = (2.3+0.6*np.sin(phase))*days
        seasonal_temp = 13+11*np.sin(phase-0.6)
        snow = np.maximum(0,3-seasonal_temp)*1.3
        wind = np.full(len(dates),15.)
    fallback = pd.DataFrame({'temperature':seasonal_temp,'rain':rain,'snow':snow,'wind':wind})
    result = observed.reset_index(drop=True).copy()
    fields = ['temperature','rain','snow','wind']
    result['weather_estimated'] = result[fields].isna().any(axis=1)
    for field in fields:
        result[field] = result[field].fillna(fallback[field])
    return result

def baseline_estimate(frame):
    """Trailing median comparator; deviation is not attributed to weather."""
    revenue = frame.revenue.astype(float)
    previous = revenue.shift(1).rolling(7,min_periods=1).median()
    previous = previous.fillna(revenue.expanding().median()).clip(lower=0.01)
    return previous, revenue-previous
