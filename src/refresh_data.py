"""Refresh official business data. Run python -m src.refresh_data --help."""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import tempfile
from datetime import datetime, timezone
import urllib.request
import zipfile
import xml.etree.ElementTree as ET
from urllib.parse import quote
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data' / 'real'

def download(url, destination, agent='WeatherBizAnalysis/1.0'):
    request = urllib.request.Request(url, headers={'User-Agent': agent})
    if url.endswith('.zip'):
        head = urllib.request.Request(url, headers={'User-Agent': agent}, method='HEAD')
        with urllib.request.urlopen(head, timeout=60) as response:
            size = int(response.headers['Content-Length'])
        # Bounded range requests avoid buffering an entire large archive at gateways.
        step = 8 * 1024 * 1024
        with open(destination, 'wb') as out:
            for offset in range(0,size,step):
                end = min(offset+step,size)-1
                req = urllib.request.Request(url,headers={'User-Agent':agent,'Range':f'bytes={offset}-{end}'})
                with urllib.request.urlopen(req,timeout=120) as response:
                    if response.status != 206 or response.headers.get('Content-Range') != f'bytes {offset}-{end}/{size}':
                        raise ValueError('Archive server did not honor requested byte range')
                    block = response.read()
                if len(block) != end-offset+1:
                    raise ValueError('Incomplete archive byte range')
                out.write(block)
                if offset // step % 10 == 0:
                    print(f'Archive download: {min(end+1,size)*100//size}%',flush=True)
    else:
        with urllib.request.urlopen(request, timeout=120) as response, open(destination, 'wb') as out:
            shutil.copyfileobj(response, out)
    with open(destination, 'rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def taxi_frame(frame, month):
    dates = pd.to_datetime(frame.tpep_pickup_datetime, errors='coerce')
    frame = frame.loc[dates.dt.to_period('M').astype(str).eq(month)].copy()
    frame['hour'] = dates.loc[frame.index].dt.floor('h')
    result = frame.groupby('hour').agg(trip_count=('total_amount','size'), fare_revenue=('fare_amount','sum'), tip_revenue=('tip_amount','sum'), total_revenue=('total_amount','sum'), avg_fare=('fare_amount','mean')).reset_index()
    return result

def bike_frame(archive, month):
    pieces = []
    with zipfile.ZipFile(archive) as z:
        for name in z.namelist():
            if not name.endswith('.csv') or '__MACOSX' in name:
                continue
            with z.open(name) as stream:
                for chunk in pd.read_csv(stream, chunksize=150000, usecols=['started_at','ended_at','member_casual']):
                    start = pd.to_datetime(chunk.started_at, errors='coerce')
                    duration = (pd.to_datetime(chunk.ended_at, errors='coerce') - start).dt.total_seconds() / 60
                    valid = start.dt.to_period('M').astype(str).eq(month) & duration.ge(0)
                    part = pd.DataFrame({'date':start[valid].dt.normalize(), 'member':chunk.loc[valid,'member_casual'].eq('member').astype(int), 'duration':duration[valid]})
                    pieces.append(part.groupby('date').agg(total_rides=('member','size'),member_rides=('member','sum'),duration_sum=('duration','sum')))
    if not pieces:
        raise ValueError('No ride CSV records found')
    result = pd.concat(pieces).groupby(level=0).sum().reset_index()
    result['casual_rides'] = result.total_rides - result.member_rides
    result['avg_duration_min'] = result.duration_sum / result.total_rides
    # Explicit illustrative fare assumption, NOT reported revenue.
    result['estimated_revenue_usd'] = result.member_rides * 3.5 + result.casual_rides * 6.5
    return result.drop(columns='duration_sum')

def sec_frame(payload):
    facts = payload['facts']['us-gaap']
    rows = []
    for priority, tag in enumerate(['RevenueFromContractWithCustomerExcludingAssessedTax','Revenues','SalesRevenueNet']):
        for fact in facts.get(tag, {}).get('units', {}).get('USD', []):
            if fact.get('form') not in ('10-Q','10-K','10-Q/A','10-K/A') or 'start' not in fact:
                continue
            start, end = pd.Timestamp(fact['start']), pd.Timestamp(fact['end'])
            if not 70 <= (end-start).days <= 105:
                continue  # Never treat YTD or annual revenue as quarterly revenue.
            rows.append({'start':start,'end':end,'revenue_usd':fact['val'],'filed':fact['filed'],'accession':fact['accn'],'priority':priority})
    if not rows:
        raise ValueError('No standalone quarterly revenue facts returned')
    result = pd.DataFrame(rows).sort_values(['end','priority','filed'], ascending=[True,False,True]).drop_duplicates('end',keep='last')
    result['fy'] = result.end.dt.year
    result['fp'] = 'Q' + result.end.dt.quarter.astype(str)
    result['quarter_label'] = result.fy.astype(str) + '-' + result.fp
    result['company_name'], result['ticker'] = 'Chipotle Mexican Grill', 'CMG'
    return result.drop(columns='priority').reset_index(drop=True)

def publish(frame, filename, key, urls, hashes, month=None):
    if frame.empty:
        raise ValueError('Refusing to publish an empty dataset')
    if not frame.select_dtypes('number').apply(lambda x: x.notna().all()).all():
        raise ValueError('Missing numeric values in refreshed data')
    DATA.mkdir(parents=True, exist_ok=True)
    target = DATA / filename
    combined = frame
    if month and target.exists():
        old = pd.read_parquet(target)
        keep = ~pd.to_datetime(old[key]).dt.to_period('M').astype(str).eq(month)
        combined = pd.concat([old.loc[keep], frame], ignore_index=True)
    combined = combined.sort_values(key).drop_duplicates(key,keep='last')
    if target.exists():
        shutil.copy2(target, target.with_suffix('.parquet.bak'))
    with tempfile.NamedTemporaryFile(dir=DATA, suffix='.parquet', delete=False) as handle:
        stage = Path(handle.name)
    try:
        combined.to_parquet(stage,index=False)
        os.replace(stage,target)
    finally:
        stage.unlink(missing_ok=True)
    manifest_path = DATA / 'refresh_manifest.json'
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    entry = manifest.setdefault(filename, {'periods':{}})
    entry.update(updated_at=datetime.now(timezone.utc).isoformat(), rows=len(combined), first=str(combined[key].min()), last=str(combined[key].max()))
    entry['periods'][month or 'quarterly'] = {'urls':urls,'sha256':hashes,'downloaded_at':entry['updated_at']}
    stage_json = manifest_path.with_suffix('.json.tmp')
    stage_json.write_text(json.dumps(manifest,indent=2))
    os.replace(stage_json,manifest_path)
    print(f'Updated {filename}: {len(combined)} rows', flush=True)

def refresh_weather(tmp):
    dates = []
    for filename, key in [('nyc_taxi_hourly.parquet','hour'),('citibike_daily.parquet','date')]:
        path = DATA/filename
        if path.exists():
            dates.extend(pd.to_datetime(pd.read_parquet(path)[key]).tolist())
    if not dates:
        raise ValueError('Import NYC business data first')
    start, end = min(dates).date(), max(dates).date()
    url = f'https://archive-api.open-meteo.com/v1/archive?latitude=40.7128&longitude=-74.0060&start_date={start}&end_date={end}&hourly=temperature_2m,precipitation,wind_speed_10m,snowfall&timezone=America%2FNew_York'
    path = tmp/'weather.json'
    digest = download(url,path)
    hourly = json.loads(path.read_text())['hourly']
    frame = pd.DataFrame({'local_time':pd.to_datetime(hourly['time']),'air_temp_deg_c':hourly['temperature_2m'],'precip_accumulation_mm':hourly['precipitation'],'sustained_wind_kmh':hourly['wind_speed_10m'],'snow_depth_delta_cm':hourly['snowfall']})
    frame['region_name'] = 'New York City'
    frame['date_str'] = frame.local_time.dt.strftime('%Y-%m-%d')
    # UTC field retained for consumers; local_time is used for NYC business joins.
    frame['timestamp_utc'] = frame.local_time.dt.tz_localize('America/New_York', ambiguous=False, nonexistent='shift_forward').dt.tz_convert('UTC')
    publish(frame,'nyc_weather_hourly.parquet','local_time',[url],[digest])


def refresh_retail_weather(tmp):
    """London regional proxy: UCI identifies the retailer only as UK-based."""
    retail = pd.read_parquet(DATA/'online_retail_daily.parquet')
    dates = pd.to_datetime(retail['date'])
    start, end = dates.min().date(), dates.max().date()
    url = f'https://archive-api.open-meteo.com/v1/archive?latitude=51.5074&longitude=-0.1278&start_date={start}&end_date={end}&daily=temperature_2m_mean,precipitation_sum,snowfall_sum,wind_speed_10m_mean&timezone=Europe%2FLondon'
    path = tmp/'retail-weather.json'
    digest = download(url,path)
    daily = json.loads(path.read_text())['daily']
    frame = pd.DataFrame({'date':pd.to_datetime(daily['time']),'temperature':daily['temperature_2m_mean'],'rain':daily['precipitation_sum'],'snow':daily['snowfall_sum'],'wind':daily['wind_speed_10m_mean']})
    frame['weather_location'] = 'London, UK (regional proxy)'
    frame['latitude'], frame['longitude'] = 51.5074, -0.1278
    publish(frame,'retail_weather_daily.parquet','date',[url],[digest])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', choices=['all','taxi','citibike','sec','weather','retail-weather'], default='all')
    parser.add_argument('--month', help='Specific YYYY-MM month; default latest published month for each monthly source')
    args = parser.parse_args()
    if args.month:
        pd.Period(args.month, freq='M')
        if not re.fullmatch(r'\d{4}-\d{2}',args.month):
            parser.error('Use YYYY-MM')
    failed = False
    cache = ROOT / 'work'
    cache.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='weather-refresh-', dir=cache) as tmp:
        tmp = Path(tmp)
        for source in (['taxi','citibike','weather','retail-weather','sec'] if args.source == 'all' else [args.source]):
            try:
                if source == 'retail-weather':
                    refresh_retail_weather(tmp)
                    continue
                if source == 'weather':
                    refresh_weather(tmp)
                    continue
                if source == 'sec':
                    agent = os.environ.get('SEC_USER_AGENT','')
                    if '@' not in agent:
                        raise ValueError('Set SEC_USER_AGENT to your real name/organization and contact email before SEC downloads')
                    url = 'https://data.sec.gov/api/xbrl/companyfacts/CIK0001058090.json'
                    path = tmp/'sec.json'
                    digest = download(url,path,agent)
                    publish(sec_frame(json.loads(path.read_text())), 'sec_quarterly_restaurants.parquet','end',[url],[digest])
                    continue
                if args.month:
                    month = args.month
                elif source == 'taxi':
                    path = tmp/'index.html'
                    download('https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page',path)
                    month = max(re.findall(r'yellow_tripdata_(\d{4}-\d{2})\.parquet',path.read_text()))
                else:
                    months = []
                    token = ''
                    while True:
                        path = tmp/'index.xml'
                        url = 'https://s3.amazonaws.com/tripdata?list-type=2' + ('&continuation-token='+quote(token,safe='') if token else '')
                        download(url,path)
                        tree = ET.fromstring(path.read_text())
                        ns = {'s':'http://s3.amazonaws.com/doc/2006-03-01/'}
                        months.extend(m.group(1) for node in tree.findall('s:Contents/s:Key',ns) if (m := re.fullmatch(r'(\d{6})-citibike-tripdata(?:\.csv)?\.zip',node.text or '')))
                        token = tree.findtext('s:NextContinuationToken',default='',namespaces=ns)
                        if not token:
                            break
                    latest = max(months)
                    month = latest[:4]+'-'+latest[4:]
                filename, key = ('nyc_taxi_hourly.parquet','hour') if source == 'taxi' else ('citibike_daily.parquet','date')
                manifest_path = DATA/'refresh_manifest.json'
                manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
                if not args.month and month in manifest.get(filename,{}).get('periods',{}):
                    print(f'{source}: latest published month {month} already imported',flush=True)
                    continue
                if source == 'taxi':
                    url = f'https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_{month}.parquet'
                    path = tmp/'taxi.parquet'
                    digest = download(url,path)
                    frame = taxi_frame(pd.read_parquet(path,columns=['tpep_pickup_datetime','fare_amount','tip_amount','total_amount']),month)
                else:
                    url = f'https://s3.amazonaws.com/tripdata/{month.replace("-","")}-citibike-tripdata.zip'
                    path = tmp/'bike.zip'
                    digest = download(url,path)
                    frame = bike_frame(path,month)
                publish(frame,filename,key,[url],[digest],month)
            except Exception as exc:
                print(f'{source}: FAILED: {exc}',flush=True)
                failed = True
    return int(failed)

if __name__ == '__main__':
    raise SystemExit(main())
