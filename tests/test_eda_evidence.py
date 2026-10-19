import json
from pathlib import Path

import numpy as np
import pytest

from src.real_eda_engine import (
    build_dataset_scorecards,
    compute_advanced_association,
    compute_missingness_matrix,
    compute_quality_evidence,
    get_matched_series_data,
)
from website.server import app


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as test_client:
        yield test_client


def test_scorecards_expose_comparability_limits():
    cards = build_dataset_scorecards()
    assert len(cards) == 4
    assert all(c["geography"] and c["cadence"] and c["coverage_note"] for c in cards)
    assert any("estimated" in c["value_status"].lower() for c in cards)


def test_academic_eda_never_fills_missing_weather():
    chipotle = get_matched_series_data("chipotle_sec")
    assert chipotle["rain_mm"].isna().all()
    assert not chipotle["weather_estimated"].any()


def test_quality_evidence_flags_without_mutating_rows():
    taxi = get_matched_series_data("nyc_taxi")
    before = taxi.copy(deep=True)
    report = compute_quality_evidence(taxi)
    assert len(report["rows"]) >= 5
    assert report["policy"].startswith("Flag")
    assert taxi.equals(before)


def test_missingness_matrix_is_percentage_bounded():
    matrix = compute_missingness_matrix(get_matched_series_data("online_retail"))
    assert matrix["rows"]
    assert all(0 <= row[col] <= 100 for row in matrix["rows"] for col in matrix["columns"])


def test_model_diagnostics_are_explicit_when_available_or_unavailable():
    result = compute_advanced_association(get_matched_series_data("nyc_taxi"))
    assert "available" in result and "n" in result
    if result["available"]:
        assert np.isfinite(result["rain_coef"])
        assert len(result["rain_ci"]) == 2
        assert result["test_n"] > 0
    else:
        assert result["reason"]


def test_notebook_is_the_walkthrough_source_of_truth(client):
    path = ROOT / "notebooks" / "weather_impact_analysis.ipynb"
    notebook = json.loads(path.read_text(encoding="utf-8"))
    stage_count = sum(c.get("metadata", {}).get("show_in_presentation", False) for c in notebook["cells"])
    response = client.get("/notebook")
    assert response.status_code == 200
    assert stage_count == 12
    assert response.data.count(b'class="section notebook-stage"') == stage_count
    assert b"Download executable .ipynb" in response.data


def test_eda_page_displays_evidence_sections(client):
    response = client.get("/eda?series=nyc_taxi")
    assert response.status_code == 200
    for phrase in [b"Dataset comparability scorecard", b"Missingness by chronological period",
                   b"Isolation Forest", b"MODEL DIAGNOSTICS", b"Evidence mode"]:
        assert phrase.lower() in response.data.lower()
