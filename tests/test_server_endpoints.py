import os
import sys
import pytest
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from website.server import app

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

def test_initial_state(client):
    res = client.get("/api/initial-state?city=NYC")
    assert res.status_code == 200
    data = res.get_json()
    assert "catalog" in data
    assert "weather" in data
    assert data["city"] == "NYC"
    keys = [item["key"] for item in data["catalog"]]
    assert len(keys) == 4
    assert set(keys) == {"nyc_taxi", "citibike_nyc", "online_retail", "chipotle_sec"}

def test_portfolio_nyc_taxi(client):
    res = client.post("/api/portfolio-data", json={"city": "NYC", "selected_keys": ["nyc_taxi"]})
    assert res.status_code == 200
    data = res.get_json()
    assert data["cadence"] == "hourly"
    assert "metrics" in data
    assert len(data["chart_7d"]["businesses"]) == 1
    assert data["chart_7d"]["businesses"][0]["key"] == "nyc_taxi"
    assert len(data["day_in_review"]["insights"]) >= 1
    assert "bullets" in data["day_in_review"]["insights"][0]

def test_portfolio_citibike(client):
    res = client.post("/api/portfolio-data", json={"city": "NYC", "selected_keys": ["citibike_nyc"]})
    assert res.status_code == 200
    data = res.get_json()
    assert data["cadence"] == "daily"
    assert len(data["chart_7d"]["businesses"]) == 1
    assert data["chart_7d"]["businesses"][0]["key"] == "citibike_nyc"
    assert "bullets" in data["day_in_review"]["insights"][0]

def test_portfolio_online_retail(client):
    res = client.post("/api/portfolio-data", json={"city": "NYC", "selected_keys": ["online_retail"]})
    assert res.status_code == 200
    data = res.get_json()
    assert data["cadence"] == "daily"
    assert len(data["chart_7d"]["businesses"]) == 1
    assert data["chart_7d"]["businesses"][0]["key"] == "online_retail"
    assert "bullets" in data["day_in_review"]["insights"][0]

def test_portfolio_chipotle_sec(client):
    res = client.post("/api/portfolio-data", json={"city": "NYC", "selected_keys": ["chipotle_sec"]})
    assert res.status_code == 200
    data = res.get_json()
    assert data["cadence"] == "quarterly"
    assert len(data["chart_7d"]["businesses"]) == 1
    assert data["chart_7d"]["businesses"][0]["key"] == "chipotle_sec"
    assert "bullets" in data["day_in_review"]["insights"][0]
    assert data["metrics"]["total_week_actual"] > 1e9

def test_domino_and_nowcast(client):
    res_dom = client.post("/api/domino-data", json={"city": "NYC", "selected_keys": ["nyc_taxi"]})
    assert res_dom.status_code == 200
    data_dom = res_dom.get_json()
    assert "cascade" in data_dom
    assert "biz_dominos" in data_dom

    res_now = client.post("/api/nowcast", json={"city": "NYC", "selected_keys": ["nyc_taxi"]})
    assert res_now.status_code == 200
    data_now = res_now.get_json()
    assert "sector_predictions" in data_now
    assert "strategic_advice" in data_now
    assert len(data_now["sector_predictions"]) == 4
    assert "NYC Yellow Taxi & Rideshare Fleet" in data_now["sector_predictions"]
    assert "Citi Bike NYC Micromobility" in data_now["sector_predictions"]
    assert "E-Commerce & Online Retail Store" in data_now["sector_predictions"]
    assert "Chipotle Mexican Grill (SEC 10-Q)" in data_now["sector_predictions"]

def test_eda_presentation_and_audit(client):
    # Test EDA audit endpoint
    res_audit = client.get("/api/eda-audit")
    assert res_audit.status_code == 200
    data_audit = res_audit.get_json()
    assert "rows" in data_audit
    assert len(data_audit["rows"]) == 5

    # Test EDA page for each of the 4 production series
    for series in ["nyc_taxi", "citibike_nyc", "online_retail", "chipotle_sec"]:
        res_eda = client.get(f"/eda?series={series}")
        assert res_eda.status_code == 200
        assert b"Academic EDA Presentation" in res_eda.data
        assert b"Understand the unit of observation" in res_eda.data

def test_notebook_walkthrough(client):
    res_nb = client.get("/notebook")
    assert res_nb.status_code == 200
    assert b"Notebook Walkthrough" in res_nb.data
    assert b"Load verified production Parquet datasets" in res_nb.data

