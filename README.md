# 🗺️ Food Equity Dashboard

An interactive, county-level food insecurity visualization dashboard built for the **Chicago Education Advocacy Cooperative (ChiEAC)**. The dashboard maps food insecurity metrics across all 3,144 U.S. counties, enabling drill-down exploration from national to state to county level with real-time data served from AWS.

🔗 **Live Dashboard**: [https://d2ckhwdq814t8q.cloudfront.net](https://d2ckhwdq814t8q.cloudfront.net)

---

## 📌 Project Overview

Food insecurity is one of the most persistent socioeconomic challenges in the United States. This project builds a full data pipeline — from raw Census and Feeding America datasets to a publicly accessible interactive map — allowing policymakers, researchers, and advocates to understand where food insecurity is most severe and what factors drive it.

The dashboard visualizes:
- **Annual Budget Shortfall** — total dollar gap to meet food needs
- **Food Insecurity Rate** — modeled proportion of food-insecure population
- **Poverty Rate** — county-level poverty prevalence
- **Unemployment Rate** — BLS annual average
- **Disability Rate** — a key risk factor per Feeding America's 2025 model
- **Homeownership Rate** — inverse proxy for economic stability
- **Food Insecure Population** — total count of affected individuals

---

## 🏗️ Project Architecture

```
Raw Data Sources
      │
      ▼
Phase 1: Data Collection (Census ACS, BLS, Feeding America, CPI)
      │
      ▼
Phase 2: Data Cleaning & Feature Engineering (Python / Jupyter)
      │
      ▼
Phase 3: Statistical Modeling (Multivariate Regression, Calibration)
      │
      ▼
Phase 4: Financial Calculation (CPI Inflation Adjustment, Shortfall Formula)
      │
      ▼
Phase 5: AWS Deployment
         ├── S3 (Data Lake)
         ├── Lambda (Data API)
         ├── API Gateway (REST Endpoint)
         └── CloudFront + S3 (Frontend Hosting)
```

---

## 📁 Repository Structure

```
Food_Equity_Dashboard/
│
├── README.md
├── Data.xlsx                          # Consolidated gold-layer dataset
├── Data_cleaning.ipynb                # Full data pipeline notebook
├── Data_cleaning.py                   # Exported Python script
├── cpi_config.json                    # Regional CPI multipliers (2023 → 2026)
├── manifest.json                      # AWS S3 QuickSight manifest (legacy)
│
├── Data/                              # Raw source datasets
│   ├── average_meal_prices.csv        # Feeding America localized meal costs
│   ├── CPI_Dec.csv                    # Consumer Price Index by region
│   ├── Disability_rate.csv            # ACS disability prevalence by county
│   ├── Homeownership_rate.csv         # ACS homeownership rate by county
│   ├── laucntycur14.zip               # BLS Local Area Unemployment Statistics
│   ├── MMG2025_Data_ToShare.zip       # Feeding America Map the Meal Gap 2025
│   ├── population.csv                 # Census county population estimates
│   ├── Poverty_rate.csv               # ACS poverty rate by county
│   ├── Unemployment_rate.xlsx         # BLS unemployment (processed)
│   └── Data Notes.docx                # Source documentation and field descriptions
│
├── References/
│   └── Map_the_Meal_Gap_2025_Technical_Brief.pdf   # Feeding America methodology
│
├── Dashboard/
│   └── food_equity_map.html           # Standalone interactive dashboard (D3.js)
│
└── AWS/
    └── lambda_function.py             # AWS Lambda handler (S3 → JSON API)
```

---

## 🔬 Methodology

### Statistical Model

The food insecurity rate for each county is estimated using a multivariate linear regression model derived from **Feeding America's Map the Meal Gap 2025 Technical Brief** (Gundersen et al.), based on state-level CPS data from 2009–2023:

```
FI_rate = α + β₁(Unemployment) + β₂(Poverty) + β₃(Disability)
            + β₄(Homeownership) + β₅(Median Income) + μ_year + υ_state
```

**Coefficients applied at county level:**

| Variable | Coefficient | Source |
|---|---|---|
| Unemployment Rate | 0.460 | MMG 2025 Technical Brief, Table A1 |
| Poverty Rate | 0.332 | MMG 2025 Technical Brief, Table A1 |
| Disability Rate | 0.198 | MMG 2025 Technical Brief, Table A1 |
| Homeownership Rate | -0.071 | MMG 2025 Technical Brief, Table A1 |

State-level calibration offsets are applied to align predicted rates with USDA ground-truth food insecurity estimates.

### Annual Budget Shortfall Formula

Derived directly from Feeding America's methodology:

```
Shortfall = Food_Insecure_Population × 52 weeks × (7/12) months × Adjusted_Meal_Cost
```

Where `Adjusted_Meal_Cost` = 2023 localized meal cost × regional CPI multiplier (projected to 2026).

### Inflation Adjustment

Regional CPI multipliers are applied to localize and project 2023 meal cost data to 2026 dollars, using Bureau of Labor Statistics CPI-U series segmented into four Census regions: Midwest (MW), Northeast (NE), South (S), and West (W).

---

## 📊 Data Sources

| Dataset | Source | Description |
|---|---|---|
| Food Insecurity Rates | [Feeding America MMG 2025](https://www.feedingamerica.org/research/map-the-meal-gap) | County-level food insecurity estimates |
| Poverty Rate | U.S. Census Bureau ACS (Table B14006) | 5-year estimates |
| Unemployment Rate | Bureau of Labor Statistics (LAUS) | Annual average, county-level |
| Disability Rate | U.S. Census Bureau ACS (Table S1810) | Disability prevalence |
| Homeownership Rate | U.S. Census Bureau ACS (Table DP04) | Owner-occupied housing |
| Population | U.S. Census Bureau ACS (Table DP05) | Total county population |
| Meal Costs | Feeding America / NielsenIQ | Localized cost-of-food index |
| CPI Adjustment | Bureau of Labor Statistics (CPI-U) | Regional inflation multipliers |

---

## ☁️ AWS Infrastructure

```
User Browser
    │
    ▼
CloudFront (HTTPS CDN)
    │
    ├──► S3 Bucket (food_equity_map.html — static website)
    │
    └──► API Gateway (GET /prod/data)
              │
              ▼
         Lambda Function
              │
              ▼
         S3 Data Lake (adjusted_final_data.csv)
```

**Services used:**
- **S3** — Static website hosting + data lake storage
- **Lambda** — Python serverless function (boto3, CSV → JSON)
- **API Gateway** — HTTP API with CORS configured
- **CloudFront** — HTTPS delivery with WAF protection (Free plan)

---

## 🖥️ Dashboard Features

- **USA Overview Map** — all 50 states colored by selected metric using a square-root color scale (blue → green → yellow → red)
- **Click-to-Drill** — click any state to zoom in and render county-level choropleth
- **ESC to Return** — keyboard shortcut to return to national view
- **State Search** — type any state name or abbreviation to jump directly
- **Metric Switcher** — toggle between 7 socioeconomic indicators
- **Live Tooltips** — hover over any state or county for detailed stats
- **Auto-Updating Data** — Lambda refreshes from S3 monthly; dashboard always reflects latest data

---

## 🚀 Running Locally

The dashboard is a single self-contained HTML file — no server or build step required.

```bash
git clone https://github.com/NithinRachakonda/Food_Equity_Dashboard.git
cd Food_Equity_Dashboard/Dashboard
open food_equity_map.html   # macOS
# or double-click the file in Windows Explorer
```

The file fetches data from the live AWS API on load. An internet connection is required.

---

## 🔧 Reproducing the Data Pipeline

```bash
# 1. Install dependencies
pip install pandas numpy scikit-learn openpyxl boto3 jupyter

# 2. Place raw datasets in the Data/ folder

# 3. Run the cleaning and modeling pipeline
jupyter notebook Data_cleaning.ipynb

# 4. Output: Data.xlsx (gold layer, ready for S3 upload)
```

---

## 📐 Key Design Decisions

- **Square-root color scale** — used instead of linear to spread mid-range values visually, preventing most counties from appearing uniformly low-risk
- **Pre-projected TopoJSON** — `us-atlas@3` uses Albers USA pre-projection; `d3.geoIdentity()` is used instead of `d3.geoAlbersUsa()` to avoid double-projection artifacts
- **State dimming on drill-down** — surrounding states fade to near-black when viewing county detail, reducing visual noise
- **Serverless API** — Lambda + API Gateway avoids always-on server costs; ~$0/month at portfolio traffic levels

---

## 📚 References

- Gundersen, C. et al. (2025). *Map the Meal Gap 2025 Technical Brief*. Feeding America.
- Rabbitt, M.P. et al. (2024). *Household Food Security in the United States in 2023* (ERR-337). USDA ERS.
- U.S. Census Bureau. *American Community Survey 5-Year Estimates*.
- Bureau of Labor Statistics. *Local Area Unemployment Statistics (LAUS)*.
- NielsenIQ. *Cost-of-Food Index via Feeding America*.

---

## 👤 Author

**Nithin Rachakonda**
- GitHub: [@NithinRachakonda](https://github.com/NithinRachakonda)

---

## 🤝 Built For

**ChiEAC — Chicago Education Advocacy Cooperative**
[chieac.org](https://chieac.org)

---

*Data as of February 2026. Food insecurity estimates follow Feeding America's Map the Meal Gap 2025 methodology.*
