"""Tests for source aggregation and safe period replacement."""
import io
import zipfile
import pandas as pd
from src.refresh_data import taxi_frame, bike_frame, sec_frame

def test_taxi_rejects_out_of_month_timestamps():
    raw = pd.DataFrame({'tpep_pickup_datetime':['2025-01-01','2024-12-31'], 'fare_amount':[10,999], 'tip_amount':[2,999], 'total_amount':[15,999]})
    result = taxi_frame(raw,'2025-01')
    assert result.trip_count.sum() == 1
    assert result.total_revenue.sum() == 15

def test_bike_combines_all_archive_parts(tmp_path):
    path = tmp_path/'rides.zip'
    with zipfile.ZipFile(path,'w') as z:
        for part in ['a.csv','b.csv']:
            z.writestr(part,'started_at,ended_at,member_casual\n2025-01-01 10:00,2025-01-01 10:10,member\n')
    result = bike_frame(path,'2025-01')
    assert result.total_rides.sum() == 2
    assert result.avg_duration_min.iloc[0] == 10

def test_sec_uses_period_year_and_excludes_ytd():
    common = {'form':'10-Q','filed':'2025-08-01','accn':'abc','val':100}
    records = [dict(common,start='2024-07-01',end='2024-09-30'),dict(common,start='2024-01-01',end='2024-09-30',val=999)]
    result = sec_frame({'facts':{'us-gaap':{'Revenues':{'units':{'USD':records}}}}})
    assert result.quarter_label.tolist() == ['2024-Q3']
    assert result.revenue_usd.tolist() == [100]

def test_publish_replaces_month_preserves_history(tmp_path, monkeypatch):
    import src.refresh_data as refresh
    monkeypatch.setattr(refresh,'DATA',tmp_path)
    pd.DataFrame({'hour':pd.to_datetime(['2024-12-01','2025-01-01']),'trip_count':[7,999]}).to_parquet(tmp_path/'taxi.parquet')
    new = pd.DataFrame({'hour':pd.to_datetime(['2025-01-01']),'trip_count':[10]})
    refresh.publish(new,'taxi.parquet','hour',['https://example.org'],['test'],'2025-01')
    refresh.publish(new,'taxi.parquet','hour',['https://example.org'],['test'],'2025-01')
    assert pd.read_parquet(tmp_path/'taxi.parquet').trip_count.tolist() == [7,10]
    before = (tmp_path/'taxi.parquet').read_bytes()
    import pytest
    with pytest.raises(ValueError):
        refresh.publish(new.iloc[:0],'taxi.parquet','hour',[],[],'2025-01')
    assert (tmp_path/'taxi.parquet').read_bytes() == before
