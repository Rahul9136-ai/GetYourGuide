"""
FastAPI backend that serves time-series forecasts for a dynamic, per-tenant
set of LOBs.

Each app user / account is a "tenant". Requests authenticate with an
`X-API-Key` header; the tenant is derived from the verified key (clients
cannot pick their own tenant). Tenants manage their own Lines of Business
independently: upload a CSV to add or retrain LOBs, delete LOBs they no
longer want, and forecast any subset. One tenant's changes never affect
another's, and every change is persisted so it survives restarts.
Cross-tenant management endpoints require an admin key.

Run with:
    uvicorn forecast_api:app --reload
Then open http://127.0.0.1:8000/docs for the interactive API.
"""

import io
import os
import sys

import pandas as pd
from fastapi import Depends, FastAPI, File, HTTPException, Query, UploadFile
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

# Make the app modules importable wherever they live, so joblib can unpickle
# the LOBForecaster class. Locally they sit in src/; in the deployed package
# they sit next to this file at the app root — add both, plus this file's own
# directory, so gunicorn finds them regardless of the working directory.
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.join(_HERE, "src"))

from ai_summary import generate_ai_summary  # noqa: E402
from auth import ApiKeyAuth  # noqa: E402
from capacity import capacity_plan  # noqa: E402
from forecaster import ALGORITHM_NAMES  # noqa: E402
from tenant_store import TenantStore  # noqa: E402

app = FastAPI(
    title="LOB Time-Series Forecasting API",
    description="Per-tenant forecasting for a user-managed set of Lines of Business.",
    version="3.0.0",
)

store = TenantStore()
auth = ApiKeyAuth.from_config()

# Dependencies: `tenant` is the authenticated tenant id; `require_admin` gates
# cross-tenant endpoints.
tenant_param = Depends(auth.tenant_dependency())
require_admin = Depends(auth.admin_dependency())


def _read_long_csv(raw: bytes) -> pd.DataFrame:
    try:
        df = pd.read_csv(io.BytesIO(raw))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not parse CSV: {e}")
    required = {"date", "lob", "value"}
    missing = required - set(df.columns)
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"CSV must have columns date, lob, value. Missing: {sorted(missing)}",
        )
    return df


@app.get("/")
def root():
    """Send browsers to the dashboard."""
    return RedirectResponse(url="/ui/")


@app.get("/health")
def health():
    """Public liveness check (no auth, no tenant info)."""
    return {"status": "ok"}


@app.get("/tenants")
def list_tenants(_: bool = require_admin):
    """[admin] List every tenant that has saved a LOB set."""
    return {"tenants": store.list_tenants()}


@app.delete("/tenants/{tenant_id}")
def delete_tenant(tenant_id: str, _: bool = require_admin):
    """[admin] Delete an entire tenant and all of its LOBs."""
    existed = store.delete_tenant(tenant_id)
    if not existed:
        raise HTTPException(status_code=404, detail=f"No such tenant '{tenant_id}'.")
    return {"deleted_tenant": tenant_id}


@app.get("/lobs")
def list_lobs(tenant: str = tenant_param):
    """List the Lines of Business managed by the calling tenant."""
    return {"tenant": tenant, "lobs": store.get(tenant).lobs}


@app.get("/metrics")
def metrics(tenant: str = tenant_param):
    """Per-LOB algorithm scoreboard: best model, accuracy, and every algorithm's scores."""
    fc = store.get(tenant)
    return {
        "tenant": tenant,
        "n_algorithms": len(ALGORITHM_NAMES),
        "algorithms": ALGORITHM_NAMES,
        "metrics": getattr(fc, "metrics", {}),
    }


@app.post("/lobs")
def add_lobs(
    file: UploadFile = File(..., description="CSV with columns: date, lob, value"),
    replace: bool = Query(True, description="Retrain LOBs that already exist"),
    tenant: str = tenant_param,
):
    """Scale UP: add new LOBs (or retrain existing ones) from an uploaded CSV.

    The CSV may contain one or many LOBs; each needs at least
    `LOBForecaster.MIN_OBS` days of history.
    """
    df = _read_long_csv(file.file.read())
    fc = store.get(tenant)
    try:
        added = fc.add_lobs(df, replace=replace)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    store.save(tenant)
    return {"tenant": tenant, "added": added, "lobs": fc.lobs}


@app.delete("/lobs/{lob}")
def delete_lob(lob: str, tenant: str = tenant_param):
    """Scale DOWN: remove a LOB the tenant no longer wants to track."""
    fc = store.get(tenant)
    try:
        fc.remove_lob(lob)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    store.save(tenant)
    return {"tenant": tenant, "removed": lob, "lobs": fc.lobs}


@app.get("/history/{lob}")
def history(lob: str, days: int = Query(60, ge=1, le=2000), tenant: str = tenant_param):
    """Return the most recent `days` of observed history for a LOB."""
    fc = store.get(tenant)
    if lob not in fc.history:
        raise HTTPException(status_code=404, detail=f"Unknown LOB '{lob}'. Available: {fc.lobs}")
    series = fc.history[lob].tail(days)
    return {
        "tenant": tenant,
        "lob": lob,
        "history": [
            {"date": d.strftime("%Y-%m-%d"), "value": round(float(v), 2)}
            for d, v in series.items()
        ],
    }


@app.get("/capacity")
def capacity(
    lob: str = Query(..., description="LOB to plan capacity for"),
    horizon: int = Query(30, ge=1, le=365, description="Planning horizon in days"),
    aht_sec: float = Query(300.0, gt=0, description="Average handle time (seconds)"),
    shrinkage: float = Query(0.30, ge=0, le=0.95, description="Shrinkage fraction"),
    max_occupancy: float = Query(0.85, gt=0, le=1.0, description="Max occupancy fraction"),
    hours_per_fte: float = Query(7.5, gt=0, description="Paid hours per FTE per day"),
    operating_hours: float = Query(12.0, gt=0, le=24, description="Operating hours per day"),
    interval_min: int = Query(30, ge=5, le=120, description="Interval length (minutes)"),
    service_level: float = Query(0.80, ge=0, le=1.0, description="Service level target"),
    awt_sec: float = Query(20.0, ge=0, description="Target answer time (seconds)"),
    peak_factor: float = Query(1.20, ge=1.0, le=3.0, description="Busiest-interval uplift"),
    tenant: str = tenant_param,
):
    """Capacity plan: convert the LOB forecast into required FTE using WFM assumptions."""
    fc = store.get(tenant)
    if lob not in fc.lobs:
        raise HTTPException(status_code=404, detail=f"Unknown LOB '{lob}'. Available: {fc.lobs}")

    series = fc._forecast_series(lob, horizon)
    plan = capacity_plan(
        series,
        aht_sec=aht_sec, shrinkage=shrinkage, max_occupancy=max_occupancy,
        hours_per_fte=hours_per_fte, operating_hours=operating_hours, interval_min=interval_min,
        service_level_target=service_level, awt_sec=awt_sec, peak_factor=peak_factor,
    )
    return {
        "tenant": tenant, "lob": lob, "horizon": horizon,
        "assumptions": {
            "aht_sec": aht_sec, "shrinkage": shrinkage, "max_occupancy": max_occupancy,
            "hours_per_fte": hours_per_fte, "operating_hours": operating_hours,
            "interval_min": interval_min, "service_level": service_level,
            "awt_sec": awt_sec, "peak_factor": peak_factor,
        },
        **plan,
    }


@app.get("/ai-summary")
def ai_summary(
    lob: str = Query(..., description="LOB to explain"),
    horizon: int = Query(30, ge=1, le=365, description="Days ahead"),
    tenant: str = tenant_param,
):
    """AI-generated narrative explanation of a LOB's forecast (Claude).

    Falls back to the rule-based narrative if no Anthropic API key is configured.
    """
    fc = store.get(tenant)
    if lob not in fc.lobs:
        raise HTTPException(status_code=404, detail=f"Unknown LOB '{lob}'. Available: {fc.lobs}")

    s = fc.summarize(lob, horizon)
    m = getattr(fc, "metrics", {}).get(lob, {})
    context = {
        "line_of_business": lob,
        "horizon_days": horizon,
        "direction": s["direction"],
        "change_vs_recent_pct": s["change_pct"],
        "forecast_avg_per_day": s["forecast_mean"],
        "recent_avg_per_day": s["last_period_mean"],
        "trend": s["trend"],
        "seasonality": s["seasonality"],
        "peak": {"date": s["peak_date"], "value": s["peak_value"]},
        "trough": {"date": s["trough_date"], "value": s["trough_value"]},
        "drivers": s["drivers"],
        "best_model": m.get("best_model"),
        "best_model_accuracy_pct": m.get("best_accuracy"),
    }

    ai = generate_ai_summary(context)
    return {
        "tenant": tenant,
        "lob": lob,
        "horizon": horizon,
        "ai": ai,
        "fallback": s["narrative"],
    }


@app.get("/summary")
def summary(
    lob: str = Query(..., description="LOB to summarise"),
    horizon: int = Query(30, ge=1, le=365, description="Days ahead"),
    tenant: str = tenant_param,
):
    """Plain-language summary of a LOB's forecast: trend, inflate/deflate vs recent
    demand, seasonal drivers, and a narrative."""
    fc = store.get(tenant)
    if lob not in fc.lobs:
        raise HTTPException(status_code=404, detail=f"Unknown LOB '{lob}'. Available: {fc.lobs}")
    return {"tenant": tenant, **fc.summarize(lob, horizon)}


@app.get("/forecast")
def forecast(
    horizon: int = Query(30, ge=1, le=365, description="Days ahead to forecast"),
    lob: str | None = Query(None, description="Single LOB; omit for all managed LOBs"),
    tenant: str = tenant_param,
):
    """Forecast `horizon` days ahead for one LOB or every LOB this tenant manages."""
    fc = store.get(tenant)
    if not fc.lobs:
        raise HTTPException(
            status_code=503,
            detail="No LOBs trained for this tenant yet. POST a CSV to /lobs to add some.",
        )

    lobs = None
    if lob is not None:
        if lob not in fc.lobs:
            raise HTTPException(status_code=404, detail=f"Unknown LOB '{lob}'. Available: {fc.lobs}")
        lobs = [lob]

    result = fc.forecast(horizon=horizon, lobs=lobs)
    result["date"] = pd.to_datetime(result["date"]).dt.strftime("%Y-%m-%d")

    payload = {}
    for name, grp in result.groupby("lob"):
        payload[name] = grp[["date", "forecast"]].to_dict(orient="records")

    return {"tenant": tenant, "horizon": horizon, "forecasts": payload}


# Serve the dashboard (vanilla HTML/JS) at /ui. Mounted last so it never
# shadows the API routes above.
app.mount(
    "/ui",
    StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static"), html=True),
    name="ui",
)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("forecast_api:app", host="127.0.0.1", port=8000, reload=False)
