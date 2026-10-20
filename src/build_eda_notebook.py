"""Build the executable real-data EDA notebook used by the web walkthrough."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "notebooks" / "weather_impact_analysis.ipynb"


def md(text):
    return {"cell_type":"markdown","metadata":{},"source":[line+"\n" for line in text.strip().splitlines()]}


def code(title, explanation, math, source):
    return {"cell_type":"code","execution_count":None,"outputs":[],
            "metadata":{"show_in_presentation":True,"presentation_title":title,
                        "presentation_explanation":explanation,"presentation_math":math},
            "source":[line+"\n" for line in source.strip().splitlines()]}


CELLS = [
    md("""
# Weather × Commerce: Evidence-First Exploratory Data Analysis

Four **separate case studies** use a common EDA workflow. Their locations, cadences and value definitions differ, so coefficients are not ranked as though they came from one experiment. Historical EDA uses observed weather only. Estimated revenue, proxy weather and scenarios are labelled and excluded from unsupported causal claims.
"""),
    code("Define scope before comparison", "Build a scorecard that makes geography, cadence, coverage and estimated values explicit.", "Comparability is a design condition, not a statistical result.", """
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from IPython.display import display

ROOT = Path.cwd()
if not (ROOT / 'data').exists(): ROOT = ROOT.parent
from src.real_eda_engine import (build_dataset_scorecards, get_matched_series_data,
    compute_quality_evidence, compute_missingness_matrix, compute_eda_statistics,
    compute_correlation_and_math, compute_advanced_association)
scorecards = pd.DataFrame(build_dataset_scorecards())
display(scorecards)
assert scorecards['key'].nunique() == 4
"""),
    code("Load observed case-study data", "Load the same source-specific frame used by the academic presentation; no presentation weather is fabricated here.", "Observed-weather rate = matched observed weather rows / business rows.", """
series_key = 'nyc_taxi'
d = get_matched_series_data(series_key)
display(d.head())
print({'rows':len(d), 'start':d.date.min(), 'end':d.date.max()})
assert not d['weather_estimated'].any()
"""),
    code("Audit missingness and duplicates", "Measure missing values, duplicate rows and duplicate timestamps before analysis.", "Missing % = missing observations / all observations × 100.", """
quality = compute_quality_evidence(d)
quality_table = pd.DataFrame(quality['rows'])
display(quality_table[['feature','dtype','n','missing','missing_pct','missing_mechanism']])
print({'duplicate_rows':quality['duplicate_rows'], 'duplicate_dates':quality['duplicate_dates']})
"""),
    code("Flag unusual values two ways", "Compare Tukey IQR flags with Isolation Forest; retain plausible extremes for sensitivity analysis.", "IQR fences = Q1 − 1.5·IQR and Q3 + 1.5·IQR; Isolation Forest isolates short random-tree paths.", """
display(quality_table[['feature','invalid_negative','iqr_flags','isolation_flags']])
assert (quality_table['iqr_flags'] >= 0).all()
"""),
    code("Evaluate skewness transformations", "Compare raw and log1p skewness without overwriting the measured columns.", "log1p(x) = ln(1+x), defined at x=0.", """
display(quality_table[['feature','raw_skew','log1p_skew']])
"""),
    code("Describe distributions", "Calculate center, dispersion, skewness, kurtosis and IQR flags.", "s² = Σ(xᵢ−x̄)²/(n−1); IQR = Q3−Q1.", """
stats = pd.DataFrame(compute_eda_statistics(d))
display(stats)
"""),
    code("Compare Pearson and Spearman", "Use Pearson for linear association and Spearman for monotonic association with tied ranks.", "r = Sxy/√(Sxx·Syy); ρ = Pearson correlation of average ranks.", """
corr, columns, association = compute_correlation_and_math(d)
display(corr)
display(pd.DataFrame(association['associations']))
"""),
    code("Reproduce Pearson and OLS mathematics", "Calculate centered sums, covariance, slope, intercept and R² from the same paired rows.", "Sxy=Σ(xᵢ−x̄)(yᵢ−ȳ); b₁=Sxy/Sxx; b₀=ȳ−b₁x̄; R²=r².", """
worked = association['rain']
result = worked
display(pd.Series({k:worked[k] for k in ['n','xmean','ymean','sxx','syy','sxy','covariance','pearson','spearman','slope','intercept','r2']}).to_frame('value'))
paired = d[['rain_mm','count']].dropna()
assert np.isclose(worked['pearson'], paired.rain_mm.corr(paired['count']))
"""),
    code("Inspect time patterns and gaps", "Plot observed activity against actual time so the multi-year taxi gap remains visibly broken.", "Δtᵢ = dateᵢ − dateᵢ₋₁; gaps are descriptive missing periods, not zeros.", """
ordered = d.sort_values('date').copy()
ordered['gap_days'] = ordered.date.diff().dt.total_seconds().div(86400)
print(ordered.nlargest(5, 'gap_days')[['date','gap_days']].to_string(index=False))
ax = ordered.set_index('date')['count'].plot(figsize=(12,3), style='o', ms=2, linestyle='None')
ax.set_title('Observed activity points; no line is drawn across missing periods')
display(ax.figure)
plt.close(ax.figure)
"""),
    code("Diagnose the controlled association model", "Check uncertainty, residual dependence, heteroscedasticity, collinearity and time-split error.", "OLS: y=Xβ+ε; HC3 CI; DW≈2 suggests weak first-order residual autocorrelation.", """
diagnostics = compute_advanced_association(d)
display(pd.Series(diagnostics).drop(labels=['vif','sensitivity','lagged'], errors='ignore').to_frame('value'))
if diagnostics['available']:
    display(pd.DataFrame(diagnostics['vif']))
"""),
    code("Test sensitivity and lags", "Recalculate associations without the top 1% of rain, on wet days only, and at short weather lags.", "ρₖ = corr(rank(rainₜ₋ₖ), rank(activityₜ)).", """
if diagnostics['available']:
    display(pd.DataFrame(diagnostics['sensitivity']))
    display(pd.DataFrame(diagnostics['lagged']))
else:
    print(diagnostics['reason'])
"""),
    code("State bounded conclusions", "Report what is observed, what is estimated, and what cannot be inferred.", "Association ≠ causation; cross-case coefficient rankings are invalid without a shared design.", """
conclusions = {
 'observed': 'Descriptive distributions, time patterns and matched-weather associations.',
 'estimated': 'Citi Bike fare revenue and executive scenario outputs; excluded from unsupported causal claims.',
 'not_identified': 'Individual behaviour changes or universal weather effects across cases.'}
display(pd.Series(conclusions).to_frame('claim boundary'))
""")
]


def build():
    notebook = {"cells":CELLS,"metadata":{"kernelspec":{"display_name":"Python 3","language":"python","name":"python3"},
                "language_info":{"name":"python","version":"3"}},"nbformat":4,"nbformat_minor":5}
    OUTPUT.write_text(json.dumps(notebook, indent=1), encoding="utf-8")
    return OUTPUT


if __name__ == "__main__":
    print(build())
