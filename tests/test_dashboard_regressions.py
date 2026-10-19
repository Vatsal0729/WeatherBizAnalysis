from pathlib import Path
import json
import numpy as np
import pandas as pd
import pytest
import src.historical_dashboard as history
from website.server import app

@pytest.mark.parametrize('body', [[], {'city':'INVALID'}, {'city':[]}, {'inspected_day_idx':'0'}, {'inspected_day_idx':True}, {'selected_keys':None}, {'selected_keys':[{}]}, {'horizon':{}}, {'sim_dow':7}, {'sim_rain':float('nan')}])
def test_api_rejects_invalid_input(body):
    with app.test_client() as client:
        response = client.post('/api/portfolio-data', json=body)
        assert response.status_code == 400
        assert response.get_json()['error']

def test_observed_weather_is_preserved_and_missing_values_are_flagged(tmp_path,monkeypatch):
    monkeypatch.setattr(history,'DATA',tmp_path)
    times = pd.date_range('2025-01-01',periods=48,freq='h')
    pd.DataFrame({'local_time':times,'air_temp_deg_c':[5]*24+[10]*24,'precip_accumulation_mm':[1]*24+[2]*24,'snow_depth_delta_cm':0,'sustained_wind_kmh':8}).to_parquet(tmp_path/'nyc_weather_hourly.parquet')
    result = history.weather_for(pd.to_datetime(['2025-01-02','2025-01-01','2025-02-01']),'nyc_taxi')
    assert result.rain.iloc[:2].tolist() == [48,24]
    assert result.weather_estimated.tolist() == [False,False,True]
    assert np.isfinite(result.rain.iloc[2])
    assert history.weather_for(times[:1],'online_retail').weather_estimated.all()

def test_ranges_use_calendar_cutoff_not_observation_count():
    frame = pd.DataFrame({'date':pd.to_datetime(['2023-01-01','2026-08-25','2026-08-31'])})
    result = history.slice_history(frame,'Last 7 Calendar Days')
    assert len(result) == 2
    assert history.slice_history(frame,'Full Available History').equals(frame)

def test_city_does_not_relocate_historical_weather():
    first = history.build_portfolio('nyc_taxi','NYC','Full Available History')
    second = history.build_portfolio('nyc_taxi','ORD','Full Available History')
    assert first['chart_7d'] == second['chart_7d']
    assert second['source_location'] == 'New York City'
    assert second['scenario_city'] == 'ORD'

@pytest.mark.parametrize('key',['online_retail','chipotle_sec'])
def test_estimated_comparators_are_numeric_and_labelled(key):
    data = history.build_portfolio(key,'NYC','Full Available History')
    assert np.isfinite(data['metrics']['total_week_impact'])
    assert np.isfinite(data['metrics']['total_week_base'])
    assert all(np.isfinite(x) for x in data['chart_7d']['rainfall'])
    assert all(np.isfinite(x) for x in data['chart_7d']['businesses'][0]['baseline'])
    assert data['impact_model']['estimated']
    assert 'not a measured weather effect' in data['impact_model']['description']
    json.dumps(data,allow_nan=False)


def test_fitted_effect_comes_from_data_not_fixed_multipliers():
    dates = pd.date_range('2025-01-01',periods=180)
    rng = np.random.default_rng(42)
    rain = rng.choice([0.,1.,5.,10.],len(dates))
    frame = pd.DataFrame({'date':dates,'rain':rain,'snow':0.,'temperature':rng.normal(15,3,len(dates)), 'wind':rng.uniform(5,20,len(dates))})
    frame['revenue'] = 1000 + 25*rain + dates.dayofweek*10 + np.arange(len(dates))*2
    baseline, impact, model = history.fit_association(frame)
    assert model['available']
    assert model['rain_coefficient'] == pytest.approx(25,abs=0.01)
    assert np.allclose(impact,25*rain)
    assert np.allclose(frame.revenue-baseline,impact)
    frame.revenue = frame.revenue-50*rain
    _,other,model = history.fit_association(frame)
    assert model['rain_coefficient'] == pytest.approx(-25,abs=0.01)
    assert (other[rain>0]<0).all()

def test_retail_proxy_has_daily_rain_even_without_sales(monkeypatch,tmp_path):
    retail = pd.DataFrame({'date':pd.to_datetime(['2011-09-11','2011-09-13']),'daily_revenue':[100,200],'order_count':[1,2],'items_sold':[2,3],'avg_order_value':[100,100]})
    weather = pd.DataFrame({'date':pd.date_range('2011-09-11',periods=3),'temperature':[12,13,14],'rain':[0,4,2],'snow':[0,0,0],'wind':[10,11,12]})
    weather.to_parquet(tmp_path/'retail_weather_daily.parquet')
    monkeypatch.setattr(history,'DATA',tmp_path)
    monkeypatch.setattr(history,'load_real_dataset',lambda key:retail)
    result = history.build_portfolio('online_retail','NYC','Full Available History')
    timeline = result['historical_timeline']
    assert timeline['weather_rainfall'] == [0,4,2]
    assert timeline['weather_dates'] == ['2011-09-11','2011-09-12','2011-09-13']
    assert [v for v in timeline['businesses'][0]['actual'] if v is not None] == [100,200]
    assert 'regional proxy' in timeline['weather_label']
    assert result['currency'] == 'GBP'
    assert np.isfinite(result['metrics']['total_week_impact'])

@pytest.mark.parametrize('key',['nyc_taxi','citibike_nyc','online_retail','chipotle_sec'])
def test_all_timelines_are_continuous_numeric_and_sources_unchanged(key):
    import hashlib
    path = Path(history.REAL_BUSINESS_CATALOG[key]['data_file'])
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    result = history.build_portfolio(key,'NYC','Full Available History')
    timeline = result['historical_timeline']
    assert timeline['range_breaks'] == []
    assert all(np.isfinite(x) for x in timeline['businesses'][0]['actual'])
    assert all(np.isfinite(x) for x in timeline['businesses'][0]['baseline'])
    assert all(np.isfinite(x) for x in timeline['weather_rainfall'])
    assert 'visual estimates' in result['scope_notice']
    assert hashlib.sha256(path.read_bytes()).hexdigest() == before

def test_weather_estimates_are_stable_across_date_filters(monkeypatch,tmp_path):
    monkeypatch.setattr(history,'DATA',tmp_path)
    dates = pd.date_range('2022-01-01',periods=10)
    full = history.weather_for(dates,'nyc_taxi')
    subset = history.weather_for(dates[3:6],'nyc_taxi')
    assert np.allclose(full.iloc[3:6].temperature, subset.temperature)
    assert np.allclose(full.iloc[3:6].rain, subset.rain)
    assert full.weather_estimated.all()

def test_notebook_examples_execute_against_current_data():
    import io
    from contextlib import redirect_stdout
    from flask import template_rendered
    from src.real_data_manager import load_real_dataset
    contexts = []
    def capture(sender, template, context, **extra):
        if template.name == 'notebook.html':
            contexts.append(context)
    template_rendered.connect(capture,app)
    try:
        with app.test_client() as client:
            response = client.get('/notebook')
        assert response.status_code == 200
    finally:
        template_rendered.disconnect(capture,app)
    context = contexts[-1]
    namespace = {}
    with redirect_stdout(io.StringIO()):
        for stage in context['stages']:
            exec(compile(stage['code'],f"stage-{stage['number']}",'exec'),namespace)
    assert context['dataset_counts']['nyc_taxi'] == len(load_real_dataset('nyc_taxi'))
    assert namespace['result']['pearson'] == pytest.approx(context['math_report']['pearson_r'])
    assert namespace['report']['n'] > 0
    assert 'HC3' in context['stages'][-1]['math']
