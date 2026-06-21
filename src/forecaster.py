"""
Multi-algorithm time-series forecaster for a dynamic set of LOBs.

For every Line of Business we train a whole roster of ML regressors on lag /
rolling / calendar features, backtest each on a hold-out window, score them
(MAE / RMSE / MAPE / R2 / accuracy) and keep the winner for forecasting. The
full per-algorithm scoreboard is retained so the UI can show the numbers and
how each model compares.

Forecasts are produced recursively: each predicted day is fed back in to build
the lag features for the next day.
"""

from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, RegressorMixin
from sklearn.ensemble import (
    AdaBoostRegressor,
    BaggingRegressor,
    ExtraTreesRegressor,
    GradientBoostingRegressor,
    HistGradientBoostingRegressor,
    RandomForestRegressor,
)
from sklearn.linear_model import ElasticNet, Lasso, LinearRegression, Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.neighbors import KNeighborsRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVR
from sklearn.tree import DecisionTreeRegressor

# Lag features (in days) and rolling-window sizes used by the models.
LAGS = [1, 2, 3, 7, 14, 28]
ROLL_WINDOWS = [7, 14, 28]


# --- Classical statistical baselines -----------------------------------------
# These forecast directly from the engineered lag/rolling columns, so they plug
# into the same training, scoring and recursive-forecast machinery as the ML
# models — no extra dependencies, evaluated on the exact same footing.

class _ColumnBaseline(BaseEstimator, RegressorMixin):
    """Statistical baseline that predicts a single engineered column:
    lag_1 = Naive/random-walk, lag_7 = Seasonal Naive, roll_mean_7 = Moving Average."""

    def __init__(self, column: str = "lag_1"):
        self.column = column

    def fit(self, X, y=None):
        self.fitted_ = True
        return self

    def predict(self, X):
        return np.asarray(X[self.column], dtype=float)


class _DriftBaseline(BaseEstimator, RegressorMixin):
    """Random walk with drift: yhat = last value + the average daily change
    observed during training (the classic 'drift' method)."""

    def fit(self, X, y):
        lag1 = np.asarray(X["lag_1"], dtype=float)
        self.drift_ = float(np.mean(np.asarray(y, dtype=float) - lag1))
        return self

    def predict(self, X):
        return np.asarray(X["lag_1"], dtype=float) + getattr(self, "drift_", 0.0)


def candidate_models() -> dict:
    """The full roster of methods we train and compare per LOB — classical
    statistical baselines plus ML regressors.

    Scale-sensitive models are wrapped with a StandardScaler. A fresh dict is
    built on each call so callers always get unfitted estimators.
    """
    return {
        # Statistical baselines
        "Naive (random walk)": _ColumnBaseline("lag_1"),
        "Seasonal Naive (weekly)": _ColumnBaseline("lag_7"),
        "Moving Average (7d)": _ColumnBaseline("roll_mean_7"),
        "Drift method": _DriftBaseline(),
        # Machine-learning regressors
        "Linear Regression": make_pipeline(StandardScaler(), LinearRegression()),
        "Ridge": make_pipeline(StandardScaler(), Ridge(alpha=1.0)),
        "Lasso": make_pipeline(StandardScaler(), Lasso(alpha=0.1, max_iter=5000)),
        "ElasticNet": make_pipeline(StandardScaler(), ElasticNet(alpha=0.1, l1_ratio=0.5, max_iter=5000)),
        "K-Nearest Neighbors": make_pipeline(StandardScaler(), KNeighborsRegressor(n_neighbors=10)),
        "Decision Tree": DecisionTreeRegressor(max_depth=10, random_state=42),
        "Random Forest": RandomForestRegressor(n_estimators=150, random_state=42, n_jobs=-1),
        "Extra Trees": ExtraTreesRegressor(n_estimators=150, random_state=42, n_jobs=-1),
        "Gradient Boosting": GradientBoostingRegressor(n_estimators=150, random_state=42),
        "HistGradientBoosting": HistGradientBoostingRegressor(max_iter=300, learning_rate=0.05, random_state=42),
        "AdaBoost": AdaBoostRegressor(n_estimators=100, random_state=42),
        "Bagging": BaggingRegressor(n_estimators=50, random_state=42, n_jobs=-1),
        "Support Vector Regr.": make_pipeline(StandardScaler(), SVR(C=10.0, gamma="scale")),
        "Neural Net (MLP)": make_pipeline(
            StandardScaler(), MLPRegressor(hidden_layer_sizes=(64, 32), max_iter=600, random_state=42)
        ),
    }


ALGORITHM_NAMES = list(candidate_models().keys())


def _calendar_features(dates: pd.DatetimeIndex) -> pd.DataFrame:
    """Cyclical calendar features so the models can learn seasonality."""
    dow = dates.dayofweek.values
    month = dates.month.values
    doy = dates.dayofyear.values
    return pd.DataFrame(
        {
            "dow_sin": np.sin(2 * np.pi * dow / 7.0),
            "dow_cos": np.cos(2 * np.pi * dow / 7.0),
            "month_sin": np.sin(2 * np.pi * month / 12.0),
            "month_cos": np.cos(2 * np.pi * month / 12.0),
            "doy_sin": np.sin(2 * np.pi * doy / 365.25),
            "doy_cos": np.cos(2 * np.pi * doy / 365.25),
            "is_weekend": (dow >= 5).astype(float),
        },
        index=dates,
    )


def _build_features(series: pd.Series) -> pd.DataFrame:
    """Build the lag/rolling/calendar feature matrix for a single series."""
    df = pd.DataFrame({"value": series})

    for lag in LAGS:
        df[f"lag_{lag}"] = df["value"].shift(lag)

    for w in ROLL_WINDOWS:
        rolled = df["value"].shift(1).rolling(w)  # shift(1) avoids leakage
        df[f"roll_mean_{w}"] = rolled.mean()
        df[f"roll_std_{w}"] = rolled.std()

    cal = _calendar_features(series.index)
    return pd.concat([df, cal], axis=1)


def _feature_columns() -> list[str]:
    cols = [f"lag_{l}" for l in LAGS]
    cols += [f"roll_mean_{w}" for w in ROLL_WINDOWS]
    cols += [f"roll_std_{w}" for w in ROLL_WINDOWS]
    cols += ["dow_sin", "dow_cos", "month_sin", "month_cos", "doy_sin", "doy_cos", "is_weekend"]
    return cols


def _score(actual: np.ndarray, pred: np.ndarray) -> dict:
    actual = np.asarray(actual, dtype=float)
    pred = np.asarray(pred, dtype=float)
    mae = float(mean_absolute_error(actual, pred))
    rmse = float(np.sqrt(mean_squared_error(actual, pred)))
    r2 = float(r2_score(actual, pred))
    nz = actual != 0
    mape = float(np.mean(np.abs((actual[nz] - pred[nz]) / actual[nz])) * 100) if nz.any() else float("nan")
    accuracy = float(max(0.0, 100.0 - mape)) if mape == mape else 0.0  # NaN-safe
    return {
        "mae": round(mae, 2),
        "rmse": round(rmse, 2),
        "mape": round(mape, 2),
        "r2": round(r2, 4),
        "accuracy": round(accuracy, 2),
    }


class LOBForecaster:
    """One winning model per LOB, plus the full algorithm scoreboard."""

    MIN_OBS = 120          # min days of history before a LOB can be trained
    VALIDATION_DAYS = 30   # hold-out window used to score / rank algorithms

    def __init__(self):
        self.models: dict = {}                  # lob -> best fitted estimator
        self.history: dict[str, pd.Series] = {} # lob -> observed series
        self.metrics: dict[str, dict] = {}      # lob -> scoreboard
        self.feature_cols = _feature_columns()

    @property
    def lobs(self) -> list[str]:
        return list(self.models.keys())

    def _series_from_group(self, grp: pd.DataFrame) -> pd.Series:
        series = (
            grp.set_index(pd.to_datetime(grp["date"]))["value"].sort_index().asfreq("D")
        )
        return series.interpolate().ffill().bfill()

    def _fit_and_eval(self, series: pd.Series) -> tuple[object, dict]:
        feats = _build_features(series).dropna()
        X = feats[self.feature_cols]
        y = feats["value"]
        if len(feats) < 40:
            raise ValueError("Not enough usable history after feature engineering.")

        n_val = min(self.VALIDATION_DAYS, max(10, len(feats) // 5))
        X_tr, X_val = X.iloc[:-n_val], X.iloc[-n_val:]
        y_tr, y_val = y.iloc[:-n_val], y.iloc[-n_val:]

        scores: dict[str, dict] = {}
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            for name, est in candidate_models().items():
                try:
                    est.fit(X_tr, y_tr)
                    scores[name] = _score(y_val.values, est.predict(X_val))
                except Exception:
                    # Finite sentinel (not inf) so the scoreboard stays JSON-safe.
                    scores[name] = {"mae": None, "rmse": 1e12, "mape": None, "r2": None, "accuracy": 0.0}

        best = min(scores, key=lambda k: scores[k]["rmse"])

        # Refit the winner on the full history for forecasting.
        best_est = candidate_models()[best]
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            best_est.fit(X, y)

        metrics = {
            "best_model": best,
            "best_accuracy": scores[best]["accuracy"],
            "n_observations": int(len(series)),
            "n_train": int(len(X_tr)),
            "n_validation": int(len(X_val)),
            "n_algorithms": len(scores),
            "scores": scores,
        }
        return best_est, metrics

    def add_lobs(self, df: pd.DataFrame, replace: bool = True) -> list[str]:
        """Add (or replace) one or more LOBs from a long-format frame: date, lob, value."""
        required = {"date", "lob", "value"}
        missing = required - set(df.columns)
        if missing:
            raise ValueError(f"Input is missing column(s): {sorted(missing)}")

        added = []
        for lob, grp in df.groupby("lob"):
            lob = str(lob)
            if lob in self.models and not replace:
                continue
            series = self._series_from_group(grp)
            if len(series) < self.MIN_OBS:
                raise ValueError(f"LOB '{lob}' has {len(series)} days; need at least {self.MIN_OBS}.")
            model, metrics = self._fit_and_eval(series)
            self.models[lob] = model
            self.history[lob] = series
            self.metrics[lob] = metrics
            added.append(lob)
        return added

    def remove_lob(self, lob: str) -> None:
        if lob not in self.models:
            raise KeyError(f"Unknown LOB '{lob}'. Available: {self.lobs}")
        del self.models[lob]
        del self.history[lob]
        self.metrics.pop(lob, None)

    def fit(self, df: pd.DataFrame) -> "LOBForecaster":
        """Fit from scratch, discarding any existing LOBs."""
        self.models.clear()
        self.history.clear()
        self.metrics.clear()
        self.add_lobs(df, replace=True)
        return self

    def _forecast_series(self, lob: str, horizon: int) -> pd.Series:
        model = self.models[lob]
        history = self.history[lob].copy()

        preds = {}
        for _ in range(horizon):
            next_date = history.index[-1] + pd.Timedelta(days=1)
            extended = pd.concat([history, pd.Series([np.nan], index=[next_date])])
            feats = _build_features(extended)
            X_next = feats[self.feature_cols].iloc[[-1]]
            yhat = max(0.0, float(model.predict(X_next)[0]))
            preds[next_date] = yhat
            history.loc[next_date] = yhat

        return pd.Series(preds, name=lob)

    def forecast(self, horizon: int = 30, lobs: list[str] | None = None) -> pd.DataFrame:
        """Forecast `horizon` days ahead. Returns long-format: date, lob, forecast."""
        target_lobs = lobs or self.lobs
        unknown = [l for l in target_lobs if l not in self.models]
        if unknown:
            raise ValueError(f"Unknown LOB(s): {unknown}. Available: {self.lobs}")

        frames = []
        for lob in target_lobs:
            s = self._forecast_series(lob, horizon)
            frames.append(pd.DataFrame({"date": s.index, "lob": lob, "forecast": s.values.round(2)}))
        return pd.concat(frames, ignore_index=True)

    def summarize(self, lob: str, horizon: int = 30) -> dict:
        """Explain a LOB's forecast: running trend, whether it is inflated or
        deflated vs recent demand, the seasonal drivers, and a plain narrative."""
        if lob not in self.models:
            raise ValueError(f"Unknown LOB '{lob}'. Available: {self.lobs}")

        history = self.history[lob]
        fc = self._forecast_series(lob, horizon)
        annual_mean = float(history.mean()) or 1.0

        # Running trend: linear fit over the last 90 days (or all if shorter).
        window = min(90, len(history))
        recent = history.tail(window)
        x = np.arange(len(recent), dtype=float)
        slope, intercept = np.polyfit(x, recent.values, 1)
        recent_mean = float(recent.mean()) or 1.0
        pct_per_month = float(slope / recent_mean * 30 * 100)
        fit = slope * x + intercept
        ss_res = float(np.sum((recent.values - fit) ** 2))
        ss_tot = float(np.sum((recent.values - recent_mean) ** 2)) or 1.0
        r2 = 1.0 - ss_res / ss_tot
        trend_dir = "rising" if pct_per_month > 0.5 else "falling" if pct_per_month < -0.5 else "flat"

        # Inflate / deflate: forecast mean vs the most recent `horizon` days.
        last_period = history.tail(horizon)
        last_mean = float(last_period.mean()) or 1.0
        fc_mean = float(fc.mean())
        change_pct = float((fc_mean - last_mean) / last_mean * 100)
        direction = "inflated" if change_pct > 1 else "deflated" if change_pct < -1 else "stable"

        # Seasonality: monthly demand index, forecast window vs recent window.
        monthly_avg = history.groupby(history.index.month).mean()
        fc_season = float(monthly_avg.reindex(fc.index.month).mean())
        last_season = float(monthly_avg.reindex(last_period.index.month).mean())
        season_effect = float((fc_season - last_season) / annual_mean * 100)
        dow_avg = history.groupby(history.index.dayofweek).mean()
        weekly_swing = float((dow_avg.max() - dow_avg.min()) / annual_mean * 100)

        drivers = []
        if trend_dir != "flat":
            verb = "lifting" if trend_dir == "rising" else "dragging down"
            drivers.append(f"The underlying trend is {trend_dir} (~{abs(pct_per_month):.1f}%/month), {verb} the forecast.")
        else:
            drivers.append("The underlying trend is broadly flat.")
        if abs(season_effect) >= 1:
            s = "higher" if season_effect > 0 else "lower"
            drivers.append(f"The forecast window sits in a {s}-demand season ({season_effect:+.1f}% vs the recent period).")
        if weekly_swing >= 3:
            drivers.append(f"There is a strong weekly cycle (~{weekly_swing:.0f}% swing across weekdays).")

        narrative = (
            f"Over the next {horizon} days, {lob} is expected to average {fc_mean:,.0f}/day — "
            f"{abs(change_pct):.1f}% {'above' if change_pct >= 0 else 'below'} the last {horizon} days "
            f"({last_mean:,.0f}/day). The forecast is {direction} mainly because the trend is {trend_dir}"
            + (" and seasonality is " + ("favourable" if season_effect > 0 else "unfavourable") if abs(season_effect) >= 1 else "")
            + "."
        )

        return {
            "lob": lob,
            "horizon": horizon,
            "direction": direction,
            "change_pct": round(change_pct, 1),
            "forecast_mean": round(fc_mean, 1),
            "last_period_mean": round(last_mean, 1),
            "peak_date": fc.idxmax().strftime("%Y-%m-%d"),
            "peak_value": round(float(fc.max()), 1),
            "trough_date": fc.idxmin().strftime("%Y-%m-%d"),
            "trough_value": round(float(fc.min()), 1),
            "trend": {"direction": trend_dir, "pct_per_month": round(pct_per_month, 1), "r2": round(r2, 3)},
            "seasonality": {"effect_pct": round(season_effect, 1), "weekly_swing_pct": round(weekly_swing, 1)},
            "drivers": drivers,
            "narrative": narrative,
        }
