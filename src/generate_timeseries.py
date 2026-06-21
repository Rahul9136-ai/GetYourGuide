"""
Generate synthetic daily time-series data for 5 Lines of Business (LOBs).

Each LOB gets its own trend, weekly + yearly seasonality, occasional
promo spikes and noise, so the forecasting models have something
realistic to learn. Output is a long-format CSV: date, lob, value.

Run with:
    python src/generate_timeseries.py
"""

import os

import numpy as np
import pandas as pd

BASE_DIR = os.path.join(os.path.dirname(__file__), "..")
DATA_PATH = os.path.join(BASE_DIR, "data", "lob_timeseries.csv")

# 5 Lines of Business with different base levels / dynamics.
LOBS = {
    "Auto":       {"base": 1200, "trend": 0.35, "weekly": 0.18, "yearly": 0.12, "noise": 0.05},
    "Home":       {"base": 800,  "trend": 0.15, "weekly": 0.10, "yearly": 0.25, "noise": 0.06},
    "Life":       {"base": 500,  "trend": 0.55, "weekly": 0.05, "yearly": 0.08, "noise": 0.04},
    "Health":     {"base": 1500, "trend": 0.25, "weekly": 0.22, "yearly": 0.30, "noise": 0.07},
    "Commercial": {"base": 950,  "trend": -0.10, "weekly": 0.14, "yearly": 0.18, "noise": 0.08},
}

START_DATE = "2022-01-01"
N_DAYS = 365 * 3 + 1  # ~3 years of daily history
SEED = 42


def _series_for_lob(dates: pd.DatetimeIndex, cfg: dict, rng: np.random.Generator) -> np.ndarray:
    n = len(dates)
    t = np.arange(n)

    base = cfg["base"]

    # Linear trend expressed as fraction of base over the whole window.
    trend = cfg["trend"] * base * (t / n)

    # Weekly seasonality (period 7) and yearly seasonality (period ~365.25).
    dow = dates.dayofweek.values
    weekly = cfg["weekly"] * base * np.sin(2 * np.pi * dow / 7.0)

    doy = dates.dayofyear.values
    yearly = cfg["yearly"] * base * np.sin(2 * np.pi * doy / 365.25)

    # Random promo spikes a few times a year.
    spikes = np.zeros(n)
    n_spikes = max(1, n // 120)
    spike_idx = rng.choice(n, size=n_spikes, replace=False)
    spikes[spike_idx] = rng.uniform(0.15, 0.4, size=n_spikes) * base

    noise = rng.normal(0, cfg["noise"] * base, size=n)

    values = base + trend + weekly + yearly + spikes + noise
    return np.clip(values, 0, None).round(2)


def generate(path: str = DATA_PATH) -> pd.DataFrame:
    rng = np.random.default_rng(SEED)
    dates = pd.date_range(START_DATE, periods=N_DAYS, freq="D")

    frames = []
    for lob, cfg in LOBS.items():
        values = _series_for_lob(dates, cfg, rng)
        frames.append(pd.DataFrame({"date": dates, "lob": lob, "value": values}))

    df = pd.concat(frames, ignore_index=True)

    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_csv(path, index=False)
    return df


def main():
    df = generate()
    print(f"Wrote {len(df)} rows ({df['lob'].nunique()} LOBs) to {DATA_PATH}")
    print(df.groupby("lob")["value"].agg(["min", "mean", "max"]).round(1))


if __name__ == "__main__":
    main()
