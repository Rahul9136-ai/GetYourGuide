"""
Simple API-key -> tenant authentication.

A request authenticates with an `X-API-Key` header. The key is looked up
in a key->tenant map, and the resolved tenant is what the API uses to scope
data -- clients can NOT pick their tenant via a header. Admin keys unlock
cross-tenant management endpoints.

Keys are loaded from (highest priority first):
  1. env LOB_API_KEYS   ("key1:tenant1,key2:tenant2")
     env LOB_ADMIN_KEYS ("adminkey1,adminkey2")
  2. config/api_keys.json  ({"keys": {...}, "admin_keys": [...]})

Mint a fresh random key:
    python src/auth.py
"""

from __future__ import annotations

import hmac
import json
import os
import secrets

from fastapi import Header, HTTPException

BASE_DIR = os.path.join(os.path.dirname(__file__), "..")
CONFIG_PATH = os.path.join(BASE_DIR, "config", "api_keys.json")


def load_config(config_path: str = CONFIG_PATH) -> tuple[dict[str, str], set[str]]:
    """Merge key->tenant map and admin keys from env + JSON file."""
    keys: dict[str, str] = {}
    admin_keys: set[str] = set()

    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        keys.update({str(k): str(v) for k, v in cfg.get("keys", {}).items()})
        admin_keys |= {str(k) for k in cfg.get("admin_keys", [])}

    # Env overrides / augments the file so prod can inject secrets out-of-band.
    env_keys = os.environ.get("LOB_API_KEYS", "")
    for pair in filter(None, (p.strip() for p in env_keys.split(","))):
        k, _, tenant = pair.partition(":")
        if k.strip() and tenant.strip():
            keys[k.strip()] = tenant.strip()

    env_admin = os.environ.get("LOB_ADMIN_KEYS", "")
    admin_keys |= {k.strip() for k in env_admin.split(",") if k.strip()}

    return keys, admin_keys


class ApiKeyAuth:
    """Resolves API keys to tenants using constant-time comparison."""

    def __init__(self, keys: dict[str, str], admin_keys: set[str] | None = None):
        self.keys = keys
        self.admin_keys = set(admin_keys or set())

    @classmethod
    def from_config(cls, config_path: str = CONFIG_PATH) -> "ApiKeyAuth":
        return cls(*load_config(config_path))

    def resolve_tenant(self, api_key: str) -> str | None:
        for key, tenant in self.keys.items():
            if hmac.compare_digest(api_key, key):
                return tenant
        return None

    def is_admin(self, api_key: str) -> bool:
        return any(hmac.compare_digest(api_key, k) for k in self.admin_keys)

    # --- FastAPI dependencies -------------------------------------------------

    def tenant_dependency(self):
        """Dependency returning the authenticated tenant id."""
        def dep(x_api_key: str | None = Header(None)) -> str:
            if not x_api_key:
                raise HTTPException(status_code=401, detail="Missing X-API-Key header.")
            tenant = self.resolve_tenant(x_api_key)
            if tenant is None:
                raise HTTPException(status_code=403, detail="Invalid API key.")
            return tenant
        return dep

    def admin_dependency(self):
        """Dependency that allows only admin keys through."""
        def dep(x_api_key: str | None = Header(None)) -> bool:
            if not x_api_key:
                raise HTTPException(status_code=401, detail="Missing X-API-Key header.")
            if not self.is_admin(x_api_key):
                raise HTTPException(status_code=403, detail="Admin API key required.")
            return True
        return dep


def generate_key(nbytes: int = 24) -> str:
    return secrets.token_urlsafe(nbytes)


def main():
    print(generate_key())


if __name__ == "__main__":
    main()
