"""Tests for the LOB time-series forecaster."""

import os
import sys

import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from forecaster import LOBForecaster  # noqa: E402
from generate_timeseries import generate, LOBS  # noqa: E402
from tenant_store import TenantStore  # noqa: E402
from auth import ApiKeyAuth, load_config, generate_key  # noqa: E402


@pytest.fixture(scope="module")
def df(tmp_path_factory):
    path = tmp_path_factory.mktemp("data") / "lob.csv"
    return generate(str(path))


@pytest.fixture(scope="module")
def fitted(df):
    return LOBForecaster().fit(df)


def test_generate_has_five_lobs(df):
    assert df["lob"].nunique() == 5
    assert set(df["lob"].unique()) == set(LOBS.keys())
    assert (df["value"] >= 0).all()


def test_fit_creates_a_model_per_lob(fitted):
    assert len(fitted.lobs) == 5


def test_forecast_shape_and_horizon(fitted):
    horizon = 14
    out = fitted.forecast(horizon=horizon)
    assert set(out.columns) == {"date", "lob", "forecast"}
    assert len(out) == horizon * 5
    # Each LOB gets exactly `horizon` future days.
    assert (out.groupby("lob").size() == horizon).all()


def test_forecast_single_lob(fitted):
    out = fitted.forecast(horizon=7, lobs=["Auto"])
    assert out["lob"].unique().tolist() == ["Auto"]
    assert len(out) == 7
    assert (out["forecast"] >= 0).all()


def test_summarize_structure(fitted):
    s = fitted.summarize("Auto", horizon=30)
    assert s["lob"] == "Auto" and s["horizon"] == 30
    assert s["direction"] in {"inflated", "deflated", "stable"}
    assert s["trend"]["direction"] in {"rising", "falling", "flat"}
    assert isinstance(s["drivers"], list) and len(s["drivers"]) >= 1
    assert isinstance(s["narrative"], str) and "Auto" in s["narrative"]
    assert "peak_date" in s and "trough_date" in s


def test_summarize_unknown_lob_raises(fitted):
    with pytest.raises(ValueError):
        fitted.summarize("Nope")


def test_forecast_dates_are_future(fitted):
    out = fitted.forecast(horizon=5, lobs=["Home"])
    last_hist = fitted.history["Home"].index[-1]
    assert (pd.to_datetime(out["date"]) > last_hist).all()


def test_unknown_lob_raises(fitted):
    with pytest.raises(ValueError):
        fitted.forecast(horizon=5, lobs=["Nonexistent"])


def _one_lob_frame(name, start="2022-01-01", days=120, value=100.0):
    dates = pd.date_range(start, periods=days, freq="D")
    return pd.DataFrame({"date": dates, "lob": name, "value": value})


def test_scale_up_adds_new_lob(df):
    fc = LOBForecaster().fit(df)
    before = set(fc.lobs)
    added = fc.add_lobs(_one_lob_frame("Cyber"))
    assert added == ["Cyber"]
    assert "Cyber" in fc.lobs and set(fc.lobs) - before == {"Cyber"}
    out = fc.forecast(horizon=3, lobs=["Cyber"])
    assert len(out) == 3


def test_scale_down_removes_lob(df):
    fc = LOBForecaster().fit(df)
    fc.remove_lob("Auto")
    assert "Auto" not in fc.lobs
    with pytest.raises(KeyError):
        fc.remove_lob("Auto")


def test_replace_false_skips_existing(df):
    fc = LOBForecaster().fit(df)
    added = fc.add_lobs(_one_lob_frame("Auto"), replace=False)
    assert added == []


def test_too_few_observations_rejected():
    fc = LOBForecaster()
    with pytest.raises(ValueError):
        fc.add_lobs(_one_lob_frame("Tiny", days=10))


def test_tenants_are_isolated(tmp_path):
    store = TenantStore(tenant_dir=str(tmp_path))

    store.get("acme").add_lobs(_one_lob_frame("Auto"))
    store.save("acme")
    store.get("globex").add_lobs(_one_lob_frame("Cyber"))
    store.save("globex")

    assert store.get("acme").lobs == ["Auto"]
    assert store.get("globex").lobs == ["Cyber"]


def test_tenant_persists_and_reloads(tmp_path):
    store = TenantStore(tenant_dir=str(tmp_path))
    store.get("acme").add_lobs(_one_lob_frame("Auto"))
    store.save("acme")

    fresh = TenantStore(tenant_dir=str(tmp_path))  # cold load from disk
    assert fresh.get("acme").lobs == ["Auto"]
    assert "acme" in fresh.list_tenants()


def test_delete_tenant(tmp_path):
    store = TenantStore(tenant_dir=str(tmp_path))
    store.get("acme").add_lobs(_one_lob_frame("Auto"))
    store.save("acme")

    assert store.delete_tenant("acme") is True
    assert store.delete_tenant("acme") is False
    assert store.get("acme").lobs == []  # fresh empty bundle after deletion


def test_blank_tenant_id_rejected(tmp_path):
    store = TenantStore(tenant_dir=str(tmp_path))
    with pytest.raises(ValueError):
        store.get("   ")


# --- API-key auth ------------------------------------------------------------

def test_auth_resolves_key_to_tenant():
    auth = ApiKeyAuth(keys={"k-acme": "acme", "k-globex": "globex"}, admin_keys={"k-admin"})
    assert auth.resolve_tenant("k-acme") == "acme"
    assert auth.resolve_tenant("k-globex") == "globex"
    assert auth.resolve_tenant("nope") is None


def test_auth_admin_flag():
    auth = ApiKeyAuth(keys={"k-acme": "acme"}, admin_keys={"k-admin"})
    assert auth.is_admin("k-admin") is True
    assert auth.is_admin("k-acme") is False


def test_auth_load_config_from_env(monkeypatch, tmp_path):
    monkeypatch.setenv("LOB_API_KEYS", "envkey:envtenant , k2:t2")
    monkeypatch.setenv("LOB_ADMIN_KEYS", "adminA, adminB")
    keys, admin = load_config(config_path=str(tmp_path / "missing.json"))
    assert keys == {"envkey": "envtenant", "k2": "t2"}
    assert admin == {"adminA", "adminB"}


def test_generate_key_is_random_and_long():
    a, b = generate_key(), generate_key()
    assert a != b and len(a) >= 20
