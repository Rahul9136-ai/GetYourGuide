"""
Per-tenant persistence for LOB forecasters.

Each tenant (app user / account) gets its own LOBForecaster bundle on
disk, so one tenant scaling its LOBs up or down never touches another's.
Bundles are cached in memory and lazily loaded.

Layout:
    models/tenants/<tenant_id>.joblib
"""

from __future__ import annotations

import os
import re

import joblib

from forecaster import LOBForecaster

BASE_DIR = os.path.join(os.path.dirname(__file__), "..")
TENANT_DIR = os.path.join(BASE_DIR, "models", "tenants")
# Legacy single-bundle path, migrated into the "default" tenant if present.
LEGACY_PATH = os.path.join(BASE_DIR, "models", "lob_forecasters.joblib")

_SAFE = re.compile(r"[^A-Za-z0-9_-]")


def _safe_id(tenant_id: str) -> str:
    tenant_id = (tenant_id or "").strip()
    if not tenant_id:
        raise ValueError("tenant id must be non-empty")
    cleaned = _SAFE.sub("_", tenant_id)
    if len(cleaned) > 100:
        raise ValueError("tenant id too long (max 100 chars)")
    return cleaned


class TenantStore:
    """Loads, caches and persists one LOBForecaster per tenant."""

    def __init__(self, tenant_dir: str = TENANT_DIR):
        self.tenant_dir = tenant_dir
        self._cache: dict[str, LOBForecaster] = {}
        os.makedirs(self.tenant_dir, exist_ok=True)

    def _path(self, tenant_id: str) -> str:
        return os.path.join(self.tenant_dir, f"{_safe_id(tenant_id)}.joblib")

    def get(self, tenant_id: str) -> LOBForecaster:
        """Return the tenant's forecaster, creating an empty one if new."""
        key = _safe_id(tenant_id)
        if key in self._cache:
            return self._cache[key]

        path = self._path(tenant_id)
        if os.path.exists(path):
            forecaster = joblib.load(path)
        elif key == "default" and os.path.exists(LEGACY_PATH):
            # One-time migration of the old single global bundle.
            forecaster = joblib.load(LEGACY_PATH)
        else:
            forecaster = LOBForecaster()

        self._cache[key] = forecaster
        return forecaster

    def save(self, tenant_id: str) -> None:
        forecaster = self.get(tenant_id)
        joblib.dump(forecaster, self._path(tenant_id))

    def delete_tenant(self, tenant_id: str) -> bool:
        """Remove a tenant entirely (cache + file). Returns True if it existed."""
        key = _safe_id(tenant_id)
        self._cache.pop(key, None)
        path = self._path(tenant_id)
        if os.path.exists(path):
            os.remove(path)
            return True
        return False

    def list_tenants(self) -> list[str]:
        files = [f for f in os.listdir(self.tenant_dir) if f.endswith(".joblib")]
        return sorted(os.path.splitext(f)[0] for f in files)
