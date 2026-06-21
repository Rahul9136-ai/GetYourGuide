<#
  Launch the GetYourGuide LOB Forecasting app on your machine.

  Double-click run_local.bat, or run:  ./run_local.ps1
  Then open http://127.0.0.1:8000/  (API key is pre-filled: dev-key-default)
#>
$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
Set-Location $root

$py = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) { $py = "python" }

Write-Host "Using Python: $py" -ForegroundColor DarkGray

# Make sure dependencies are present.
& $py -c "import fastapi, uvicorn, sklearn, pandas" 2>$null
if ($LASTEXITCODE -ne 0) {
  Write-Host "Installing dependencies..." -ForegroundColor Cyan
  & $py -m pip install -r (Join-Path $root "requirements.txt")
}

# First run: generate synthetic data + train the models.
if (-not (Test-Path (Join-Path $root "models\lob_forecasters.joblib"))) {
  Write-Host "First run - generating synthetic data and training 14 models per LOB..." -ForegroundColor Cyan
  & $py (Join-Path $root "src\generate_timeseries.py")
  & $py (Join-Path $root "src\train_forecast.py")
}

Write-Host ""
Write-Host "==================================================================" -ForegroundColor Green
Write-Host "  GetYourGuide - Demand Forecasting Studio" -ForegroundColor Green
Write-Host "  Starting server... your browser will open automatically." -ForegroundColor Green
Write-Host "  URL:  http://127.0.0.1:8000/   (API key pre-filled: dev-key-default)" -ForegroundColor Green
Write-Host "  Press Ctrl+C in this window to stop the server." -ForegroundColor Green
Write-Host "==================================================================" -ForegroundColor Green
Write-Host ""

# Open the browser only AFTER the server is actually listening (avoids the
# 'connection refused' you get if the browser opens before uvicorn is up).
Start-Job -ScriptBlock {
  for ($i = 0; $i -lt 90; $i++) {
    try {
      if ((Invoke-WebRequest "http://127.0.0.1:8000/health" -UseBasicParsing -TimeoutSec 2).StatusCode -eq 200) {
        Start-Process "http://127.0.0.1:8000/"; break
      }
    } catch {}
    Start-Sleep -Milliseconds 800
  }
} | Out-Null

& $py -m uvicorn forecast_api:app --host 127.0.0.1 --port 8000
