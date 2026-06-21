"""
Train per-LOB multi-algorithm forecasters on the synthetic data and save them.

Loads data/lob_timeseries.csv, trains the full roster of ML algorithms for
each LOB (each one self-backtests and keeps the winner), prints a scoreboard,
and saves the bundle to models/lob_forecasters.joblib.

Run with:
    python src/train_forecast.py
"""

import json
import os
import warnings

import joblib
import pandas as pd

from forecaster import ALGORITHM_NAMES, LOBForecaster

BASE_DIR = os.path.join(os.path.dirname(__file__), "..")
DATA_PATH = os.path.join(BASE_DIR, "data", "lob_timeseries.csv")
MODEL_DIR = os.path.join(BASE_DIR, "models")
MODEL_PATH = os.path.join(MODEL_DIR, "lob_forecasters.joblib")
REPORT_PATH = os.path.join(MODEL_DIR, "forecast_report.json")


def main():
    os.makedirs(MODEL_DIR, exist_ok=True)
    warnings.simplefilter("ignore")

    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(f"{DATA_PATH} not found. Run `python src/generate_timeseries.py` first.")

    df = pd.read_csv(DATA_PATH)
    print(f"Loaded {len(df)} rows across {df['lob'].nunique()} LOBs")
    print(f"Training {len(ALGORITHM_NAMES)} algorithms per LOB: {', '.join(ALGORITHM_NAMES)}\n")

    forecaster = LOBForecaster().fit(df)

    report = {}
    for lob in forecaster.lobs:
        m = forecaster.metrics[lob]
        report[lob] = m
        print(f"== {lob} ==  best: {m['best_model']}  (accuracy {m['best_accuracy']}%)")
        ranked = sorted(m["scores"].items(), key=lambda kv: kv[1]["rmse"])
        for name, s in ranked[:5]:
            print(f"   {name:<22} acc={s['accuracy']:>6.2f}%  MAE={s['mae']:>8}  RMSE={s['rmse']:>8}  R2={s['r2']}")
        print()

    joblib.dump(forecaster, MODEL_PATH)
    print(f"Saved forecaster bundle ({len(forecaster.lobs)} LOBs) to {MODEL_PATH}")

    with open(REPORT_PATH, "w") as f:
        json.dump(report, f, indent=2)
    print(f"Saved metrics report to {REPORT_PATH}")


if __name__ == "__main__":
    main()
