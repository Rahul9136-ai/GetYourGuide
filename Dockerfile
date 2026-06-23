# GetYourGuide — Demand Forecasting & Capacity Planning API
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install dependencies first (better layer caching). The slim deploy set is
# enough to run the API, generate data, and train the models.
COPY deploy/requirements.txt ./requirements.txt
RUN pip install -r requirements.txt

# Application code
COPY forecast_api.py ./
COPY src/ ./src/
COPY static/ ./static/
COPY config/ ./config/

# Generate synthetic data + train the 18-model bundle at build time so the
# image is self-contained and serves data on first request.
RUN python src/generate_timeseries.py && python src/train_forecast.py

# Default keys so the dashboard's prefilled key works out of the box.
# Override these (and set ANTHROPIC_API_KEY) via the host's env settings.
ENV LOB_API_KEYS="dev-key-default:default" \
    LOB_ADMIN_KEYS="dev-admin-key" \
    PORT=8000

EXPOSE 8000

# Shell form so ${PORT} expands (Render/Cloud Run inject PORT at runtime).
CMD uvicorn forecast_api:app --host 0.0.0.0 --port ${PORT:-8000}
