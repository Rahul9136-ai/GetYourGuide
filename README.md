# GetYourGuide — Demand Forecasting & Capacity Planning

A multi-tenant FastAPI app that forecasts daily demand for any number of
**Lines of Business (LOBs)** and turns those forecasts into a **workforce
capacity plan**. It ships with a clean GetYourGuide-branded dashboard.

## Features

**Forecasting**
- Trains and compares **18 methods per LOB** — 4 classical statistical baselines
  (Naive, Seasonal Naive, Moving Average, Drift) + 14 ML regressors
  (Linear/Ridge/Lasso/ElasticNet, KNN, Decision Tree, Random Forest, Extra Trees,
  Gradient Boosting, HistGradientBoosting, AdaBoost, Bagging, SVR, MLP).
- Backtests each on a hold-out window, scores MAE / RMSE / MAPE / R² / accuracy,
  and keeps the best model per LOB (the full scoreboard is exposed).
- Recursive multi-step forecast (default **3 months**, up to 365 days).
- **Summary & trend** tab: explains whether a forecast is inflated or deflated
  vs recent demand, the running trend, and the drivers behind it.

**Capacity planning** (`/ui/capacity.html`)
- Converts the forecast into **required FTE** using WFM assumptions: AHT,
  shrinkage, max occupancy, hours per FTE.
- **Erlang C** sizing for the busiest interval against a service-level target.
- **Daily / Weekly / Monthly** granularity toggle.
- **Download CSV** of the forecast and the capacity plan.

**Platform**
- Dynamic LOBs — upload a CSV to add/retrain, delete to scale down.
- Multi-tenant with `X-API-Key` auth (tenant derived from the key; admin keys
  for cross-tenant management).

## Quick start (Windows)

```powershell
# 1. create a venv and install deps
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

# 2. run it (generates synthetic data + trains models on first run)
./run_local.ps1        # or double-click run_local.bat
```

Then open <http://127.0.0.1:8000/>. The dashboard pre-fills the dev key
`dev-key-default`.

Or run the server directly:

```powershell
uvicorn forecast_api:app --reload
```

## API

| Endpoint | Purpose |
|----------|---------|
| `GET /metrics` | Per-LOB algorithm scoreboard |
| `GET /forecast?horizon=&lob=` | Forecast values |
| `GET /history/{lob}` | Recent actuals |
| `GET /summary?lob=&horizon=` | Forecast explanation (trend, inflate/deflate) |
| `GET /capacity?lob=&horizon=&aht_sec=&shrinkage=&...` | Capacity plan |
| `POST /lobs` (CSV) / `DELETE /lobs/{lob}` | Scale LOBs up/down |
| `GET /tenants`, `DELETE /tenants/{id}` | Admin (admin key) |

All data endpoints require an `X-API-Key` header.

## Configuration

Copy `config/api_keys.example.json` to `config/api_keys.json` and set real keys,
or use the `LOB_API_KEYS` / `LOB_ADMIN_KEYS` environment variables (preferred in
production). `config/api_keys.json` is git-ignored.

## Tests

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_forecast.py tests/test_capacity.py
```

## Deployment

See [`deploy/AZURE_DEPLOY.md`](deploy/AZURE_DEPLOY.md) and `deploy_azure.ps1`
for deploying to Azure App Service (Linux, Python).

## Stack

FastAPI · scikit-learn · pandas · Chart.js (CDN) · vanilla JS. Dependency-light
on purpose — no statsmodels/Prophet, so it builds anywhere without native deps.
