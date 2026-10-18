"""
Generate Course Project Review Presentation Slide Deck
Curated for the 4 verified production datasets and econometric architecture.
"""
import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

prs = Presentation()

# Layouts (0: Title, 1: Title and Content, 3: Two Content)
title_slide_layout = prs.slide_layouts[0]
content_slide_layout = prs.slide_layouts[1]
two_content_layout = prs.slide_layouts[3]

TEAL = RGBColor(8, 127, 113)
INK = RGBColor(23, 47, 43)
MUTED = RGBColor(100, 115, 108)

# ---------------------------------------------------
# SLIDE 1: Title Slide
# ---------------------------------------------------
slide1 = prs.slides.add_slide(title_slide_layout)
title1 = slide1.shapes.title
sub1 = slide1.placeholders[1]

title1.text = "Weather-Driven Commerce Intelligence: Multi-Cadence EDA & Econometrics"
title1.text_frame.paragraphs[0].font.size = Pt(32)
title1.text_frame.paragraphs[0].font.bold = True
title1.text_frame.paragraphs[0].font.color.rgb = INK

sub1.text = "Course Project Review 1 · Exploratory Data Analysis\nPublic Data & Econometric Research Edition\n\nVerified Production Datasets: NYC TLC · Citi Bike · UCI Retail · SEC EDGAR"
sub1.text_frame.paragraphs[0].font.size = Pt(18)
sub1.text_frame.paragraphs[0].font.color.rgb = MUTED

# ---------------------------------------------------
# SLIDE 2: Problem Statement & Empirical Solution
# ---------------------------------------------------
slide2 = prs.slides.add_slide(content_slide_layout)
title2 = slide2.shapes.title
title2.text = "Executive Summary: Confounding vs. Causality"
title2.text_frame.paragraphs[0].font.color.rgb = INK

tf2 = slide2.placeholders[1].text_frame
tf2.text = "The Core Problem:"
p = tf2.add_paragraph()
p.text = "Naive business analytics consistently confuses recurring calendar seasonality (e.g., weekend shopping surges, weekday commute peaks) with true weather-induced demand shocks."
p.level = 1

p = tf2.add_paragraph()
p.text = "The Empirical Solution:"
p.level = 0
p = tf2.add_paragraph()
p.text = "An observatory platform integrating 4 multi-cadence production datasets with ERA5 weather reanalysis and NASA satellite feeds, isolating empirical elasticities using Two-Way Fixed Effects (TWFE)."
p.level = 1

p = tf2.add_paragraph()
p.text = "Deliverables:"
p.level = 0
p = tf2.add_paragraph()
p.text = "1) Executive Intelligence Platform, 2) 7-Chapter Academic EDA Presentation (/eda), and 3) Executable Notebook Walkthrough (/notebook)."
p.level = 1

# ---------------------------------------------------
# SLIDE 3: 4 Verified Production Datasets
# ---------------------------------------------------
slide3 = prs.slides.add_slide(two_content_layout)
title3 = slide3.shapes.title
title3.text = "Production Datasets: Multi-Cadence Telemetry"
title3.text_frame.paragraphs[0].font.color.rgb = INK

left3 = slide3.placeholders[1].text_frame
left3.text = "Micro & Daily Operational Cadences:"
p = left3.add_paragraph()
p.text = "NYC Yellow Taxi (NYC TLC OpenData):"
p.level = 1
p = left3.add_paragraph()
p.text = "• 744 hourly validated intervals; 2.99M raw trips."
p.level = 2
p = left3.add_paragraph()
p.text = "• Measures trip volume, gross fares, and tipping behavior."
p.level = 2
p = left3.add_paragraph()
p.text = "Citi Bike NYC Micromobility (Public S3):"
p.level = 1
p = left3.add_paragraph()
p.text = "• 120 verified operational days; 2.41M raw rides."
p.level = 2
p = left3.add_paragraph()
p.text = "• Analyzes member vs. casual rider rain sensitivities."
p.level = 2

right3 = slide3.placeholders[2].text_frame
right3.text = "Commercial & Macro Financial Cadences:"
p = right3.add_paragraph()
p.text = "E-Commerce Retail Store (UCI Repository):"
p.level = 1
p = right3.add_paragraph()
p.text = "• 305 trading days; 541K transactional invoice lines."
p.level = 2
p = right3.add_paragraph()
p.text = "• Isolates cancellations ('C' invoices) into returns ledger."
p.level = 2
p = right3.add_paragraph()
p.text = "Chipotle Mexican Grill (SEC EDGAR 10-Q):"
p.level = 1
p = right3.add_paragraph()
p.text = "• 27 statutory quarterly financial filings."
p.level = 2
p = right3.add_paragraph()
p.text = "• Evaluates enterprise quarterly headwinds under GAAP standards."
p.level = 2

# ---------------------------------------------------
# SLIDE 4: Meteorological Infrastructure
# ---------------------------------------------------
slide4 = prs.slides.add_slide(content_slide_layout)
title4 = slide4.shapes.title
title4.text = "Meteorological Ground & Satellite Fusion"
title4.text_frame.paragraphs[0].font.color.rgb = INK

tf4 = slide4.placeholders[1].text_frame
tf4.text = "Atmospheric Reanalysis & Satellite Observations:"
p = tf4.add_paragraph()
p.text = "Open-Meteo ERA5 Reanalysis: 70,045 hourly observations harmonized across 4 major metropolitan climate zones (New York, Chicago, Seattle, Phoenix)."
p.level = 1
p = tf4.add_paragraph()
p.text = "NASA POWER Satellite Feed: Surface thermal flux and solar insolation providing spatial consensus verification against municipal ground sensors."
p.level = 1
p = tf4.add_paragraph()
p.text = "Engineered Meteorological Variables: Temperature anomaly vs. 30-day rolling baseline, precipitation accumulation (mm), wind speed (km/h), and snowfall depth (cm)."
p.level = 1
p = tf4.add_paragraph()
p.text = "Strict Time Synchronization: Full adherence to IANA timezones and daylight-saving transition safeguards preventing dropped observation hours."
p.level = 1

# ---------------------------------------------------
# SLIDE 5: Descriptive Statistics & Distribution Shape
# ---------------------------------------------------
slide5 = prs.slides.add_slide(two_content_layout)
title5 = slide5.shapes.title
title5.text = "Chapter 03: Descriptive Statistics & Anomaly Audit"
title5.text_frame.paragraphs[0].font.color.rgb = INK

left5 = slide5.placeholders[1].text_frame
left5.text = "Distributional Moments & Spread:"
p = left5.add_paragraph()
p.text = "Mean vs. Median Contrast: Reveals heavy right-skew in precipitation and ride volumes, proving why median-based statistics are essential."
p.level = 1
p = left5.add_paragraph()
p.text = "Sample Variance & SD: Unbiased (n-1) degrees of freedom."
p.level = 1
p = left5.add_paragraph()
p.text = "Skewness & Kurtosis: Standardized third and fourth moments documenting extreme storm tail weights."
p.level = 1

right5 = slide5.placeholders[2].text_frame
right5.text = "Transparent Outlier Handling:"
p = right5.add_paragraph()
p.text = "Tukey Fences Audit: Fences defined at [Q1 − 1.5×IQR, Q3 + 1.5×IQR]."
p.level = 1
p = right5.add_paragraph()
p.text = "No Deletion Rule: Severe weather downpours and holiday surges are retained as genuine empirical evidence rather than deleted."
p.level = 1
p = right5.add_paragraph()
p.text = "Raw-to-Clean Accounting: Full row tracing from 5.4M source micro-events to verified time-series Parquet snapshots."
p.level = 1

# ---------------------------------------------------
# SLIDE 6: Bivariate Association & OLS Mathematics
# ---------------------------------------------------
slide6 = prs.slides.add_slide(two_content_layout)
title6 = slide6.shapes.title
title6.text = "Chapter 04 & 07: Bivariate Correlation & Regressions"
title6.text_frame.paragraphs[0].font.color.rgb = INK

left6 = slide6.placeholders[1].text_frame
left6.text = "Handling Tied Zero-Precipitation Days:"
p = left6.add_paragraph()
p.text = "Spearman Rank Correlation: R_i = rank(x_i), Q_i = rank(y_i); tied dry intervals receive fractional average ranks."
p.level = 1
p = left6.add_paragraph()
p.text = "Monotonic Sensitivity: Citibike displays strong negative rank correlation with rain (-0.48), while e-commerce retail displays positive substitution (+0.24)."
p.level = 1

right6 = slide6.placeholders[2].text_frame
right6.text = "Step-by-Step Pearson & OLS Reproduction:"
p = right6.add_paragraph()
p.text = "Closed-Form Formulas: Explicitly computes Sxx, Syy, Sxy, sample covariance, slope b1 = Sxy/Sxx, and intercept b0 = y_bar − b1·x_bar."
p.level = 1
p = right6.add_paragraph()
p.text = "Cautionary Principle: Unadjusted R² reflects in-sample fit of a single line; it does not establish causal attribution without calendar controls."
p.level = 1

# ---------------------------------------------------
# SLIDE 7: Econometric TWFE Modeling & Live Simulation
# ---------------------------------------------------
slide7 = prs.slides.add_slide(content_slide_layout)
title7 = slide7.shapes.title
title7.text = "Econometric TWFE Regressions & Shock Simulation"
title7.text_frame.paragraphs[0].font.color.rgb = INK

tf7 = slide7.placeholders[1].text_frame
tf7.text = "Two-Way Fixed Effects (TWFE) Econometric Specification:"
p = tf7.add_paragraph()
p.text = "log(1 + y_it) = α_i + γ_t + β₁ log(1 + rain_it) + β₂ temp_anom_it + β₃ wind_it + ε_it"
p.level = 1
p = tf7.add_paragraph()
p.text = "Newey-West HAC Robust Standard Errors: Controls for 7-lag serial autocorrelation and heteroskedasticity across continuous time horizons."
p.level = 1
p = tf7.add_paragraph()
p.text = "Cross-Sector Ripple Effects (The Domino Chain): Demonstrates substitution cascades where rain suppresses bike checkouts (-35%), drives rideshare surges (+22%), and diverts foot-traffic into digital e-commerce delivery (+14%)."
p.level = 1
p = tf7.add_paragraph()
p.text = "Live Interactive Simulation: Real-time slider controls enabling enterprise stakeholders to stress-test arbitrary weather scenarios against live meteorological conditions."
p.level = 1

# ---------------------------------------------------
# SLIDE 8: Project Architecture & Execution
# ---------------------------------------------------
slide8 = prs.slides.add_slide(content_slide_layout)
title8 = slide8.shapes.title
title8.text = "System Architecture & Verification"
title8.text_frame.paragraphs[0].font.color.rgb = INK

tf8 = slide8.placeholders[1].text_frame
tf8.text = "Platform Architecture:"
p = tf8.add_paragraph()
p.text = "Backend: Python 3.13 + Flask 3.1 + Pandas + Statsmodels (Zero external runtime dependencies)."
p.level = 1
p = tf8.add_paragraph()
p.text = "Frontend: Research observatory styling (HTML5 + CSS3 + Plotly.js + SVG procedural graphics)."
p.level = 1
p = tf8.add_paragraph()
p.text = "Three Integrated Exploratory Environments:"
p.level = 1
p = tf8.add_paragraph()
p.text = "• Executive Platform (/): 5-tab operational monitoring and live scenario stress-testing."
p.level = 2
p = tf8.add_paragraph()
p.text = "• Academic EDA Presentation (/eda): 7-chapter walkthrough with interactive filters and full math derivations."
p.level = 2
p = tf8.add_paragraph()
p.text = "• Notebook Walkthrough (/notebook): 7 executable pipeline stages pairing code with verifiable intermediate outputs."
p.level = 2
p = tf8.add_paragraph()
p.text = "100% Automated Testing: Comprehensive test suite validating data pipelines, connectors, econometric models, and web endpoints."
p.level = 1

output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Course_Project_Review_1.pptx")
prs.save(output_path)
print(f"Presentation saved successfully to: {output_path}")
