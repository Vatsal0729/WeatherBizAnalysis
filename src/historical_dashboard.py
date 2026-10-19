"""Date-aligned historical dashboard data; scenario engines remain separate."""
from pathlib import Path
import re
import numpy as np
import pandas as pd
import statsmodels.api as sm
from src.presentation_estimates import fill_weather, baseline_estimate
from src.real_data_manager import load_real_dataset, REAL_BUSINESS_CATALOG

DATA = Path(__file__).resolve().parents[1] / 'data' / 'real'
SCOPE = {'nyc_taxi':'New York City', 'citibike_nyc':'New York City',
         'online_retail':'UK online retailer (historical UCI snapshot)',
         'chipotle_sec':'Chipotle consolidated company revenue'}

def values(series):
    return [None if pd.isna(v) or not np.isfinite(float(v)) else round(float(v), 2) for v in series]

def observed_weather_for(dates, key, hourly=False):
    """Exact local timestamps/dates only; unmatched observations stay missing."""
    dates = pd.DatetimeIndex(pd.to_datetime(dates))
    result = pd.DataFrame(index=dates, columns=['temperature','rain','snow','wind'],dtype=float)
    if key == 'online_retail':
        path = DATA/'retail_weather_daily.parquet'
        if path.exists() and not hourly:
            proxy = pd.read_parquet(path).set_index('date')
            proxy.index = pd.to_datetime(proxy.index)
            return proxy[['temperature','rain','snow','wind']].reindex(dates).reset_index(drop=True)
        return result.reset_index(drop=True)
    path = DATA/'nyc_weather_hourly.parquet'
    if key not in ('nyc_taxi','citibike_nyc') or not path.exists():
        return result.reset_index(drop=True)
    weather = pd.read_parquet(path).rename(columns={'air_temp_deg_c':'temperature','precip_accumulation_mm':'rain','snow_depth_delta_cm':'snow','sustained_wind_kmh':'wind'})
    weather.index = pd.to_datetime(weather.local_time)
    weather = weather[['temperature','rain','snow','wind']].groupby(level=0).mean()
    if not hourly:
        # Require a complete local day; missing hours never become zero rain.
        counts = weather.resample('D').count()
        weather = weather.resample('D').agg({'temperature':'mean','rain':lambda s:s.sum(min_count=1),'snow':lambda s:s.sum(min_count=1),'wind':'mean'})
        weather = weather.where(counts >= 24)
    return weather.reindex(dates).reset_index(drop=True)

def weather_for(dates, key, hourly=False):
    observed = observed_weather_for(dates, key, hourly)
    return fill_weather(observed, dates, key, hourly)


def fit_association(frame):
    """In-sample precipitation association, never presented as causal attribution."""
    message = 'Estimated baseline comparison; no causal attribution.'
    baseline = pd.Series(np.nan,index=frame.index)
    impact = baseline.copy()
    matched = frame.dropna(subset=['revenue','rain','temperature','snow','wind']).copy()
    if len(matched) < 40 or (matched.rain.eq(0).sum() < 5) or (matched.rain.gt(0).sum() < 5):
        return baseline, impact, {'available':False,'description':message,'n':len(matched)}
    if 'weather_estimated' in matched:
        matched = matched.loc[~matched.weather_estimated]
    if len(matched) < 40:
        return baseline, impact, {'available':False,'description':message,'n':len(matched)}
    dates = pd.to_datetime(matched.date)
    x = matched[['rain','temperature','wind']].astype(float).copy()
    if matched.snow.nunique() > 1:
        x['snow'] = matched.snow
    x['trend'] = (dates-dates.min()).dt.days.astype(float)
    calendar = pd.DataFrame({'weekday':dates.dt.dayofweek.astype(str),'month':dates.dt.month.astype(str)},index=matched.index)
    x = sm.add_constant(pd.concat([x,pd.get_dummies(calendar,drop_first=True,dtype=float)],axis=1),has_constant='add')
    if len(x) < 3*x.shape[1] or np.linalg.matrix_rank(x.to_numpy()) < x.shape[1]:
        return baseline, impact, {'available':False,'description':message,'n':len(matched)}
    model = sm.OLS(matched.revenue.astype(float),x).fit(cov_type='HC3')
    clear = x.copy()
    clear['rain'] = 0.0
    if 'snow' in clear:
        clear['snow'] = 0.0
    delta = model.predict(x)-model.predict(clear)
    counterfactual = matched.revenue-delta
    usable = np.isfinite(delta) & np.isfinite(counterfactual) & counterfactual.gt(0)
    impact.loc[matched.index[usable]] = delta.loc[usable]
    baseline.loc[matched.index[usable]] = counterfactual.loc[usable]
    ci = model.conf_int().loc['rain'].tolist()
    return baseline,impact,{'available':True,'description':'Fitted precipitation association; in-sample estimate, not a measured causal effect. Controls: weekday, month, time trend, temperature and wind. Other factors held fixed.', 'n':len(matched),'rain_coefficient':float(model.params['rain']),'rain_pvalue':float(model.pvalues['rain']),'rain_ci95':ci,'r_squared':float(model.rsquared)}

def slice_history(frame,horizon,quarterly=False):
    horizon = horizon.lower()
    if 'full' in horizon or 'all' in horizon:
        return frame.copy()
    latest = frame.date.max()
    if 'latest available month' in horizon:
        return frame.loc[frame.date.dt.to_period('M').eq(latest.to_period('M'))].copy()
    if quarterly:
        n = 4 if ('1 year' in horizon or '4 quarter' in horizon) else 8
        return frame.tail(n).copy()
    found = re.search(r'(180|90|30|14|7)(?: calendar)? days',horizon)
    days = int(found.group(1)) if found else None
    if days is None:
        days = 180
    return frame.loc[frame.date >= latest-pd.Timedelta(days=days-1)].copy()


def build_portfolio(key,city,horizon,index=None):
    cfg = REAL_BUSINESS_CATALOG[key]
    raw = load_real_dataset(key).copy()
    if raw.empty:
        raise ValueError('Business dataset is empty or missing')
    if key == 'nyc_taxi':
        raw['date'] = pd.to_datetime(raw.hour).dt.normalize()
        frame = raw.groupby('date',as_index=False).agg(revenue=('total_revenue','sum'),count=('trip_count','sum'))
    else:
        date_col, revenue_col, count_col = {
            'citibike_nyc':('date','estimated_revenue_usd','total_rides'),
            'online_retail':('date','daily_revenue','order_count'),
            'chipotle_sec':('end','revenue_usd','revenue_usd')}[key]
        frame = pd.DataFrame({'date':pd.to_datetime(raw[date_col]),'revenue':raw[revenue_col],'count':raw[count_col]})
    frame = frame.sort_values('date').drop_duplicates('date').reset_index(drop=True)
    weather = weather_for(frame.date,key)
    frame = pd.concat([frame,weather],axis=1)
    frame['baseline'],frame['impact'],model = fit_association(frame)
    if key == 'online_retail':
        frame['baseline'] = np.nan
        frame['impact'] = np.nan
        model = {'available':False,'description':'Historical London weather is a regional proxy for the UK retailer, not its verified premises or customer weather. A store-level weather effect is not estimated from this proxy.','n':int(frame.rain.notna().sum())}
    estimate, deviation = baseline_estimate(frame)
    missing_baseline = frame.baseline.isna()
    frame.loc[missing_baseline,'baseline'] = estimate[missing_baseline]
    frame.loc[missing_baseline,'impact'] = deviation[missing_baseline]
    if not model['available']:
        model = {'available':True,'estimated':True,'description':'Estimated trailing-median revenue baseline. The displayed shift is actual revenue minus that comparator, not a measured weather effect. Weather gaps use a labelled seasonal scenario.','n':len(frame)}
    elif missing_baseline.any():
        model['description'] += ' Some comparator values use trailing-median estimates.'
    quarterly = cfg['cadence'] == 'quarterly'
    recent = frame.tail(8 if quarterly else 7).reset_index(drop=True)
    index = len(recent)-1 if index is None or index >= len(recent) else index
    chosen = recent.iloc[index]
    selected_history = slice_history(frame,horizon,quarterly).reset_index(drop=True)
    history = selected_history.copy()
    range_breaks = []
    labels = lambda ds: [f'{d.year}-Q{d.quarter}' if quarterly else d.strftime('%a') for d in ds]
    icon = lambda row: ('Estimated ' if row.weather_estimated else '') + ('Rain' if row.rain>0 else 'Dry')
    identity = {'key':key,'name':cfg['name'],'clean_label':cfg['clean_name'],'color':cfg['color'],'symbol':cfg['symbol'],'currency':'GBP' if key == 'online_retail' else 'USD'}
    chart = {'currency':identity['currency'],'dates':recent.date.dt.strftime('%Y-%m-%d').tolist(),'days':labels(recent.date),'x_labels':[d.strftime('%b %d, %Y') if not quarterly else f'{d.year}-Q{d.quarter}' for d in recent.date], 'icons':[icon(r) for _,r in recent.iterrows()], 'rainfall':values(recent.rain),'temperatures':values(recent.temperature),'businesses':[{**identity,'actual':values(recent.revenue),'baseline':values(recent.baseline),'net_impact':values(recent.impact)}]}
    number = lambda v: None if pd.isna(v) else round(float(v),2)
    actual = float(chosen.revenue) if quarterly else float(recent.revenue.sum())
    complete = recent.impact.notna().all()
    total_impact = number(chosen.impact) if quarterly else (number(recent.impact.sum()) if complete else None)
    total_base = number(chosen.baseline) if quarterly else (number(recent.baseline.sum()) if complete else None)
    insight = {**identity,'b_name':cfg['name'],'delta':number(chosen.impact),'actual_rev':number(chosen.revenue),'baseline_rev':number(chosen.baseline),'pct_change':number(chosen.impact/chosen.baseline*100) if pd.notna(chosen.baseline) else None,'headline':f'{cfg["clean_name"]}: {chosen.date:%Y-%m-%d}', 'bullets':[f'Historical source: {SCOPE[key]}.',f'Revenue: {chosen.revenue:,.2f} ({"estimated fares" if key=="citibike_nyc" else "reported dataset value"}).',model['description']], 'category':cfg['category']}
    records = []
    if key == 'nyc_taxi':
        detail = raw.loc[raw.date.eq(chosen.date)].sort_values('hour')
        detail_weather = weather_for(detail.hour,key,hourly=True)
        for i,(_,r) in enumerate(detail.iterrows()):
            w = detail_weather.iloc[i]
            records.append({'num':i+1,'time':r.hour.strftime('%H:%M'),'temp':number(w.temperature),'rain':number(w.rain),'food_orders':f'{int(r.trip_count):,} Trips','price_surge':f'${r.avg_fare:.2f} Avg','wait_time':f'${r.total_revenue:,.0f}','bike_trips':int(r.trip_count),'traffic_jam':'NYC TLC'})
    else:
        raw_dates = pd.to_datetime(raw['end' if quarterly else 'date'])
        for i,(_,r) in enumerate(recent.iterrows()):
            records.append({'num':i+1,'time':f'{r.date:%Y-%m-%d}','temp':number(r.temperature),'rain':number(r.rain),'food_orders':f'{r["count"]:,.0f}' if not quarterly else f'${r.revenue:,.0f}','price_surge':'SEC filing' if quarterly else 'Historical observation','wait_time':'â€”','bike_trips':'â€”','traffic_jam':f'${r.revenue:,.0f}'})
            source = raw.loc[raw_dates.eq(r.date)].iloc[-1]
            if key == 'citibike_nyc':
                records[-1].update(food_orders=f'{int(source.total_rides):,} Rides', price_surge=f'{int(source.member_rides):,} Mem',wait_time=f'{source.avg_duration_min:.1f} min',bike_trips=int(source.total_rides))
            elif key == 'online_retail':
                records[-1].update(food_orders=f'{int(source.order_count):,} Orders',price_surge=f'{int(source.items_sold):,} Items',wait_time=f'{source.avg_order_value:.2f} AOV',bike_trips=int(source.order_count))
    if model.get('rain_ci95'):
        lo, hi = model['rain_ci95']
        model['description'] += f" Rain coefficient: {model['rain_coefficient']:,.2f} revenue units/mm (95% CI {lo:,.2f} to {hi:,.2f}; p={model['rain_pvalue']:.3g}; n={model['n']})."
        if lo <= 0 <= hi:
            model['description'] += ' The interval includes zero; the direction of the effect is uncertain.'
        insight['bullets'][-1] = model['description']
    weather_label = 'London, UK regional proxy (Open-Meteo historical reanalysis)' if key == 'online_retail' else ('New York City historical reanalysis' if key in ('nyc_taxi','citibike_nyc') else 'Estimated representative quarterly climate scenario')
    weather_dates = pd.date_range(selected_history.date.min(), selected_history.date.max(),freq='D') if not quarterly else selected_history.date
    calendar_weather = weather_for(weather_dates,key)
    scope = f'Historical data: {SCOPE[key]}. Live scenario city: {city}; changing it does not relocate this dataset. Weather: {weather_label}. Revenue points are joined across all dates for presentation; connecting segments are visual estimates, not additional sales observations. Missing weather uses estimated seasonal values.'
    diagnostics = []
    if not model.get('estimated'):
        baseline_mean = frame.revenue.mean()
        diagnostics = [{'num':1,'metric':cfg['clean_name'],'baseline':f'{baseline_mean:,.2f} revenue units/day','raw_temp_corr':number(frame.revenue.corr(frame.temperature)), 'adj_temp_impact':'Control variable','raw_rain_corr':number(frame.revenue.corr(frame.rain)),'adj_rain_impact':f"{model['rain_coefficient']:+,.2f} revenue units/mm",'r2':f"{model['r_squared']:.3f} (in-sample)",'reliability':f"p={model['rain_pvalue']:.3g}; 95% CI {model['rain_ci95'][0]:,.2f} to {model['rain_ci95'][1]:,.2f}"}]
    if model.get('estimated'):
        diagnostics = [{'num':1,'metric':cfg['clean_name']+' (estimated comparison)','baseline':f'{frame.baseline.mean():,.2f}','raw_temp_corr':number(frame.revenue.corr(frame.temperature)) or 0.0,'adj_temp_impact':'Seasonal scenario','raw_rain_corr':number(frame.revenue.corr(frame.rain)) or 0.0,'adj_rain_impact':'Baseline deviation','r2':'Descriptive comparison','reliability':'Estimated; no inferential significance claimed'}]
    return {'cadence':cfg['cadence'],'cadence_label':cfg['cadence_label'],'is_real':True,'primary_key':key,'business_name':cfg['clean_name'],'currency':identity['currency'],'source_location':SCOPE[key],'scenario_city':city,'scope_notice':scope,'impact_model':model,'estimation':{'weather_rows':int(frame.weather_estimated.sum()),'baseline_rows':int(missing_baseline.sum())},'coverage':{'first':str(frame.date.min().date()),'last':str(frame.date.max().date()),'observations':len(frame),'selected_observations':len(selected_history)},'metrics':{'total_week_actual':actual,'total_week_base':total_base,'total_week_impact':total_impact,'total_rain_week':number(recent.rain.sum()) if recent.rain.notna().all() else None,'portfolio_count':1},'chart_7d':chart,'day_in_review':{'inspected_idx':index,'date_str':chosen.date.strftime('%Y-%m-%d'),'day_name':labels([chosen.date])[0],'weather_icon':icon(chosen),'temperature':number(chosen.temperature),'rain':number(chosen.rain),'insights':[insight],'hourly_table':records},'historical_timeline':{'range_breaks':range_breaks,'currency':identity['currency'],'weather_label':weather_label,'weather_dates':pd.DatetimeIndex(weather_dates).strftime('%Y-%m-%d').tolist(),'weather_rainfall':values(calendar_weather.rain),'dates':history.date.dt.strftime('%Y-%m-%d').tolist(),'display_dates':history.date.dt.strftime('%b %d, %Y').tolist(),'rainfall':values(history.rain),'temperatures':values(history.temperature),'businesses':[{**identity,'actual':values(history.revenue),'baseline':values(history.baseline)}]},'econometrics_table':diagnostics}
