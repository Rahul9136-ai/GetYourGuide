"""Tests for the WFM capacity planning logic."""

import os
import sys

import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from capacity import agents_for_service_level, capacity_plan, service_level  # noqa: E402


def _flat_forecast(value=1000, days=30):
    idx = pd.date_range("2025-01-01", periods=days, freq="D")
    return pd.Series([value] * days, index=idx)


def test_capacity_plan_structure():
    plan = capacity_plan(_flat_forecast(), aht_sec=300, shrinkage=0.3, max_occupancy=0.85, hours_per_fte=7.5)
    assert set(plan) == {"daily", "weekly", "summary"}
    assert len(plan["daily"]) == 30
    s = plan["summary"]
    assert s["recommended_fte"] >= s["peak_fte"] - 1  # ceil of peak
    assert s["peak_fte"] >= s["avg_fte"]
    assert s["erlang"]["peak_interval_agents"] >= 1


def test_more_volume_needs_more_staff():
    low = capacity_plan(_flat_forecast(500), aht_sec=300, shrinkage=0.3, max_occupancy=0.85, hours_per_fte=7.5)
    high = capacity_plan(_flat_forecast(2000), aht_sec=300, shrinkage=0.3, max_occupancy=0.85, hours_per_fte=7.5)
    assert high["summary"]["peak_fte"] > low["summary"]["peak_fte"]


def test_higher_shrinkage_needs_more_staff():
    a = capacity_plan(_flat_forecast(), aht_sec=300, shrinkage=0.20, max_occupancy=0.85, hours_per_fte=7.5)
    b = capacity_plan(_flat_forecast(), aht_sec=300, shrinkage=0.45, max_occupancy=0.85, hours_per_fte=7.5)
    assert b["summary"]["peak_fte"] > a["summary"]["peak_fte"]


def test_erlang_service_level_monotonic():
    # More agents must not lower the achieved service level.
    sl_low = service_level(10.0, 12, 300, 20)
    sl_high = service_level(10.0, 16, 300, 20)
    assert sl_high >= sl_low
    assert agents_for_service_level(50, 300, 1800, 0.8, 20) >= 1
