"""
Workforce-management capacity planning on top of the demand forecast.

Turns a forecast of daily contact volume into a required-headcount plan using
standard WFM assumptions:

  * AHT (average handle time)        - seconds per contact
  * shrinkage                        - % of paid time not available (breaks, training, absence)
  * max occupancy                    - cap on productive utilisation
  * hours per FTE                    - paid hours per agent per day
  * service level / Erlang C         - target % answered within X seconds

Two views are produced:
  1. Workload method  -> required FTE per day (capacity plan over the horizon).
  2. Erlang C         -> agents needed at the busiest interval to hit the
                         service-level target (intraday staffing check).
"""

from __future__ import annotations

import math

import pandas as pd


def _erlang_c_wait_prob(traffic: float, agents: int) -> float:
    """Probability a contact waits (Erlang C), via the stable Erlang B recursion."""
    if agents <= traffic:
        return 1.0
    b = 1.0
    for k in range(1, agents + 1):
        b = (traffic * b) / (k + traffic * b)
    rho = traffic / agents
    return b / (1.0 - rho * (1.0 - b))


def service_level(traffic: float, agents: int, aht_sec: float, awt_sec: float) -> float:
    """Fraction of contacts answered within awt_sec for a given staffing level."""
    if agents <= traffic:
        return 0.0
    pw = _erlang_c_wait_prob(traffic, agents)
    return max(0.0, 1.0 - pw * math.exp(-(agents - traffic) * (awt_sec / aht_sec)))


def agents_for_service_level(calls: float, aht_sec: float, interval_sec: float,
                             target_sl: float, awt_sec: float, max_agents: int = 2000) -> int:
    """Minimum agents to hit the service-level target for `calls` in one interval."""
    if calls <= 0:
        return 0
    traffic = calls * aht_sec / interval_sec  # offered load in Erlangs
    n = max(1, int(math.floor(traffic)) + 1)
    while n < max_agents:
        if service_level(traffic, n, aht_sec, awt_sec) >= target_sl:
            return n
        n += 1
    return n


def capacity_plan(
    forecast: pd.Series,
    *,
    aht_sec: float = 300.0,
    shrinkage: float = 0.30,
    max_occupancy: float = 0.85,
    hours_per_fte: float = 7.5,
    operating_hours: float = 12.0,
    interval_min: int = 30,
    service_level_target: float = 0.80,
    awt_sec: float = 20.0,
    peak_factor: float = 1.20,
) -> dict:
    """Build a capacity plan from a forecast Series (index=date, value=volume)."""
    shrinkage = min(max(shrinkage, 0.0), 0.95)
    max_occupancy = min(max(max_occupancy, 0.05), 1.0)
    interval_sec = interval_min * 60
    intervals_per_day = max(1.0, operating_hours * 60 / interval_min)

    daily = []
    total_rostered = 0.0
    for date, vol in forecast.items():
        vol = max(0.0, float(vol))
        workload_hours = vol * aht_sec / 3600.0
        productive_hours = workload_hours / max_occupancy
        rostered_hours = productive_hours / (1.0 - shrinkage)
        fte = rostered_hours / hours_per_fte if hours_per_fte > 0 else 0.0
        total_rostered += rostered_hours
        daily.append({
            "date": pd.Timestamp(date).strftime("%Y-%m-%d"),
            "volume": round(vol),
            "workload_hours": round(workload_hours, 1),
            "rostered_hours": round(rostered_hours, 1),
            "required_fte": round(fte, 1),
        })

    ftes = [d["required_fte"] for d in daily]
    volumes = [d["volume"] for d in daily]
    peak_day_volume = max(volumes) if volumes else 0

    # Erlang C check on the busiest interval of the busiest day.
    avg_calls_interval = peak_day_volume / intervals_per_day
    peak_calls = avg_calls_interval * peak_factor
    peak_agents = agents_for_service_level(peak_calls, aht_sec, interval_sec, service_level_target, awt_sec)
    traffic = peak_calls * aht_sec / interval_sec
    achieved_sl = service_level(traffic, peak_agents, aht_sec, awt_sec) if peak_calls > 0 else 1.0
    occupancy = (traffic / peak_agents) if peak_agents > 0 else 0.0
    # Convert peak concurrent agents to FTE allowing for shrinkage.
    peak_interval_fte = peak_agents / (1.0 - shrinkage)

    summary = {
        "recommended_fte": math.ceil(max(ftes)) if ftes else 0,
        "peak_fte": round(max(ftes), 1) if ftes else 0.0,
        "avg_fte": round(sum(ftes) / len(ftes), 1) if ftes else 0.0,
        "total_volume": int(sum(volumes)),
        "total_agent_hours": round(total_rostered),
        "erlang": {
            "peak_interval_calls": round(peak_calls, 1),
            "peak_interval_agents": peak_agents,
            "peak_interval_fte": round(peak_interval_fte, 1),
            "achieved_service_level": round(achieved_sl * 100, 1),
            "occupancy": round(occupancy * 100, 1),
        },
    }

    # Weekly roll-up for a compact table.
    df = pd.DataFrame(daily)
    df["dt"] = pd.to_datetime(df["date"])
    weekly = []
    for wk, grp in df.groupby(df["dt"].dt.to_period("W")):
        weekly.append({
            "week_start": grp["dt"].min().strftime("%Y-%m-%d"),
            "volume": int(grp["volume"].sum()),
            "avg_fte": round(grp["required_fte"].mean(), 1),
            "peak_fte": round(grp["required_fte"].max(), 1),
            "agent_hours": round(grp["rostered_hours"].sum()),
        })

    return {"daily": daily, "weekly": weekly, "summary": summary}
