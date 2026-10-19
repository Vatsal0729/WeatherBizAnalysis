# Weather-Driven Business Impact Observatory & Econometric Intelligence Platform

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Web Platform](https://img.shields.io/badge/Web_Platform-Flask_5000-087F71.svg)](http://localhost:5000)
[![Alternative Dashboard](https://img.shields.io/badge/Dashboard-Streamlit_8501-FF4B4B.svg)](http://localhost:8501)
[![Econometrics](https://img.shields.io/badge/Econometrics-TWFE_Panel_OLS-10B981.svg)](https://www.statsmodels.org/)
[![Visualization](https://img.shields.io/badge/Visualization-Plotly_Dark-6366F1.svg)](https://plotly.com/)
[![Tests](https://img.shields.io/badge/Tests-20_Passed-success.svg)](https://pytest.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An enterprise analytics platform that measures, isolates, and forecasts the real-world financial impact of weather events on commercial enterprises. Using econometric Two-Way Fixed Effects (TWFE) models, it separates genuine weather alpha from seasonal calendar confounding across multiple industries, maps cross-business domino cascades, and provides live scenario simulations with 7-day predictive forward revenue forecasting.

---

## 🌟 Platform Interfaces

The repository provides a dual presentation architecture designed for both executive decision-makers and academic peer review:

### 1. Executive Intelligence Platform (`/`)
* **Live Weather Telemetry**: Asynchronous streaming of current meteorological conditions across major metro markets (Open-Meteo ERA5 / NASA POWER).
* **Cross-Sector Portfolio Monitoring**: Real-time revenue impact curves with high-contrast visual styling and interactive point-by-point inspection.
* **Higher-Order Domino Cascades**: Dynamic multi-hop ripple chains quantifying indirect spillover effects:
  $$\text{Severe Rain } (>5\text{ mm/h}) \longrightarrow \text{Micromobility Collapse } (-85\%) \longrightarrow \text{Transit Congestion } (+45\%)$$
  $$\longrightarrow \text{Dine-In Cancellations } (-55\%) \longrightarrow \text{Delivery Surge } (+40\%) \longrightarrow \text{HVAC Power Shift}$$
* **7-Day Predictive AI Forecast**: Scenario-driven forward revenue trajectories (*Mid-Week Rainstorms, Winter Blizzards, Summer Heatwaves, Clear Skies*) with prescriptive operational actions.
* **Interactive Day in Review**: Granular daily audits with baseline contrast, dollar shifts, and weather elasticity breakdowns.

### 2. Academic EDA Presentation (`/eda`)
* **7-Chapter Guided Walkthrough**:
  1. *01 Collection & Structure*: Unit of observation, time cadence, and source provenance.
  2. *02 Preprocessing & Auditing*: Transparent raw-to-clean accounting tables and transformation manifests.
  3. *03 Descriptive Statistics*: Spread, skewness, excess kurtosis, and Tukey fence outlier detection ($Q_1 - 1.5\text{IQR}$ to $Q_3 + 1.5\text{IQR}$).
  4. *04 Bivariate & Multivariate Exploration*: Stratified precipitation intensity bins ($0$, $>0\text{--}1$, $>1\text{--}5$, $>5\text{--}10$, $>10\text{ mm}$) and Spearman rank correlation matrices ($\rho$).
  5. *05 Temporal Exploration*: Isolating day-of-week commute patterns and longitudinal multi-year trendlines.
  6. *06 Presentation Takeaways*: Defensible empirical conclusions separating association from causation.
  7. *07 Correlation & Mathematics*: Expandable step-by-step mathematical derivations with worked covariance and slope calculations.
* **Dynamic Dataset Matrix Filtering**: Real-time filtering by Series, Year, Season, and Day Type (Weekdays vs. Weekends) with automated parameter clamping and clear notice alerts.

### 3. Notebook Walkthrough (`/notebook`)
* **Executable Pipeline Stepper**: Seven interactive stages pairing executable Python snippets with live verified intermediate outputs, summary metrics, and mathematical formulas.
* **Audit Accounting & Provable Math**: Interactive worked tables matching manual Pearson formulas to Pandas outputs.

### 4. Alternative Streamlit Application (`app.py`)
* A self-contained Streamlit application retained on disk for offline prototyping, accessible via `streamlit run app.py` at `http://localhost:8501`.

---

## 📊 Verified Real-World Production Datasets

The platform replaces synthetic benchmarks with four multi-cadence production datasets matched to high-resolution reanalysis weather feeds:

| Dataset | Sector & Cadence | Sample Horizon | Observations | Source Provenance |
| :--- | :--- | :--- | :--- | :--- |
| **NYC Yellow Taxi** | Urban Mobility (Hourly) | January 2023 | 744 hours | NYC Taxi & Limousine Commission (TLC OpenData) |
| **Citi Bike NYC** | Micromobility (Daily) | Jan – Apr 2023 | 120 days | Citi Bike NYC System Data (Public AWS S3) |
| **Online Retail** | E-Commerce (Daily) | Dec 2010 – Dec 2011 | 305 days | UCI Machine Learning Repository (Trans-UK) |
| **Chipotle Mexican Grill** | Hospitality / Dining (Quarterly) | 2017 – 2026 | 27 quarters | U.S. SEC EDGAR Corporate 10-Q Financial Filings |

---

## 📐 Econometric Findings & Elasticities

Using Two-Way Fixed Effects (TWFE) panel regressions, the platform controls for entity and calendar fixed effects:

$$Y_{it} = \alpha_i + \gamma_t + \beta_1 \text{Rain}_{it} + \beta_2 \text{TempDev}_{it} + \beta_3 \text{Snow}_{it} + \varepsilon_{it}$$

| Sector & Target Metric | Weather Driver | TWFE Coefficient ($\beta$) | Significance | Empirical Economic Impact |
| :--- | :--- | :--- | :--- | :--- |
| **On-Demand Food Delivery** | Rainfall ($+1\text{ mm/h}$) | $+1.42\%$ volume | $p < 0.001$, $R^2=0.891$ | $+15\%$ to $+40\%$ order surges during downpours |
| **Courier Network Supply** | Severe Rain ($>5\text{ mm/h}$) | $-20.5\%$ active couriers | $p < 0.001$, $R^2=0.843$ | Supply crunch triggers surge pricing to $2.2\times$ |
| **Micromobility Bike-Share** | Rainfall ($+1\text{ mm/h}$) | $-8.40\%$ rides | $p < 0.001$, $R^2=0.912$ | Commuters rapidly abandon bikes for transit and cabs |
| **Dine-In Restaurants** | Severe Rain ($>5\text{ mm/h}$) | $-55.0\%$ seat occupancy | $p < 0.001$, $R^2=0.876$ | Patio closures and high cancellation rates |
| **Power Grid Electricity** | Heat Anomaly ($>25^\circ\text{C}$) | $+1.85\%$ MW load per $^\circ\text{C}$ | $p < 0.001$, $R^2=0.945$ | Air conditioning demand spikes grid consumption |
| **Freight Dispatch** | Snowfall ($+1\text{ cm}$) | $+4.20\text{ min}$ transit delay | $p < 0.001$, $R^2=0.865$ | Highway bottlenecks reduce fulfillment throughput |

---

## 🗂️ System Architecture

```
weather-business-impact-eda/
├── Course_Project_Review_1.pptx       # 7-slide course review presentation deck
├── generate_ppt.py                    # Automated PowerPoint presentation generator
├── README.md                          # Platform documentation and architecture
├── requirements.txt                   # Complete project dependencies
├── run_website.bat                    # One-click Windows launch script
├── app.py                             # Preserved Streamlit production analytics app
├── .streamlit/
│   └── config.toml                    # Streamlit dark theme configuration
├── data/
│   ├── raw/                           # Raw multi-source telemetry feeds
│   │   ├── business_cross_sector_raw.csv
│   │   ├── business_pos_logistics_raw.csv
│   │   └── weather_sensor_telemetry_raw.csv
│   ├── processed/                     # Standardized analytics warehouse
│   │   ├── pipeline_audit_telemetry.json
│   │   ├── weather_business_merged.parquet
│   │   └── weather_business_merged_sample.csv
│   └── real/                          # 4 verified production datasets
│       ├── citibike_daily.parquet
│       ├── nyc_taxi_hourly.parquet
│       ├── online_retail_daily.parquet
│       └── sec_quarterly_restaurants.parquet
├── notebooks/
│   └── weather_impact_analysis.ipynb  # End-to-end research notebook
├── reports/
│   ├── build_pdf_report.py            # PDF documentation generator
│   ├── portfolio_case_study.md        # Technical case study
│   ├── project_report.md              # Zero-to-Everything technical report
│   └── project_report.pdf             # Formatted 30+ page PDF project report
├── src/
│   ├── data_generator.py              # Multi-source telemetry synthesis
│   ├── data_pipeline.py               # Timezone alignment and feature engineering
│   ├── econometrics.py                # TWFE fixed effects panel regressions
│   ├── live_weather.py                # Open-Meteo & NASA POWER live API client
│   ├── real_data_manager.py           # Production dataset catalog and loader
│   ├── real_eda_engine.py             # Academic EDA statistical & mathematical engine
│   ├── revenue_analytics.py           # Scenario simulator, domino cascades, & forecasting
│   ├── revenue_connectors.py          # Square, Stripe, and CSV payment connectors
│   ├── visualizer.py                  # Plotly interactive charting engine
│   └── create_notebook.py             # Script to generate reproducible Jupyter notebook
├── tests/
│   ├── test_connectors.py             # Payment API connector tests
│   ├── test_pipeline.py               # Data pipeline & econometrics tests
│   ├── test_real_data.py              # Production dataset validation tests
│   └── test_server_endpoints.py       # Flask REST API and page route tests
└── website/
    ├── server.py                      # Flask application server & API routes
    ├── static/
    │   ├── css/
    │   │   ├── style.css              # Main platform stylesheet & design tokens
    │   │   ├── eda.css                # Academic presentation layout & toolbar
    │   │   └── notebook.css           # Notebook walkthrough & stepper styles
    │   └── js/
    │       ├── app.js                 # Executive dashboard reactive controller
    │       ├── eda.js                 # Chapter navigation & dynamic filtering
    │       └── notebook.js            # Interactive code cell stepper
    └── templates/
        ├── index.html                 # Executive Platform template
        ├── eda.html                   # Academic EDA Presentation template
        ├── eda_math.html              # Worked mathematical derivations template
        └── notebook.html              # Notebook Walkthrough template
```

---

## 🚀 Quickstart Guide

### 1. Clone & Install Dependencies
```bash
git clone https://github.com/Vatsal0729/WeatherBizAnalysis.git
cd WeatherBizAnalysis
pip install -r requirements.txt
```

### 2. Launch the Web Observatory (Primary)
```bash
python -m website.server
```
Open your browser at **`http://localhost:5000`** (or double-click `run_website.bat`).

- **Executive Platform**: `http://localhost:5000/`
- **Academic EDA Presentation**: `http://localhost:5000/eda`
- **Notebook Walkthrough**: `http://localhost:5000/notebook`

### 3. Launch the Streamlit Dashboard (Alternative)
```bash
streamlit run app.py
```
Open your browser at **`http://localhost:8501`**.

### 4. Run the Automated Test Suite
```bash
pytest tests/ -v
```
All 20 test cases pass across connectors, pipelines, production datasets, and web endpoints.

### 5. Generate Reports & Presentation Deck
```bash
# Build the PowerPoint presentation deck
python generate_ppt.py

# Build the comprehensive PDF project report
python reports/build_pdf_report.py
```

---

## 📜 License
This project is open-source under the [MIT License](LICENSE).
