#!/bin/bash
# Azure App Service (Linux) startup command.
# Single worker so the in-memory per-tenant cache stays consistent with disk.
gunicorn forecast_api:app \
  -k uvicorn.workers.UvicornWorker \
  -w 1 \
  -b 0.0.0.0:${PORT:-8000} \
  --timeout 120
