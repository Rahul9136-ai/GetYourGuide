<#
  Deploy the LOB Forecasting API (FastAPI + UI) to Azure App Service (Linux, Python).

  Stages ONLY the forecasting app's files (the working folder also holds
  unrelated projects that must not be deployed), zips them, and pushes a
  build-on-deploy package to a Linux Python web app.

  Usage:
    ./deploy_azure.ps1                         # uses defaults below
    ./deploy_azure.ps1 -AppName myforecaster -Sku B1
#>
param(
  [string]$ResourceGroup = "lob-forecast-rg",
  [string]$Location      = "centralus",   # B1 quota available here on this subscription
  [string]$AppName       = "lob-forecast-$((Get-Random -Maximum 99999))",
  [string]$Plan          = "lob-forecast-b1",
  [string]$Sku           = "B1",           # F1 (Free) has only 60 CPU-min/day and gets disabled under load
  [string]$TenantKey     = "ywhhgDTrso_0M8CUgDwIULWyCrgyxfEb",
  [string]$AdminKey      = "HNWIf75ewbCZycHYl4kHk8Jjh1YbIgRR"
)

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot

Write-Host "==> Staging application files..." -ForegroundColor Cyan
$stage = Join-Path $env:TEMP "lob-forecast-deploy"
if (Test-Path $stage) { Remove-Item $stage -Recurse -Force }
New-Item -ItemType Directory -Path $stage | Out-Null
New-Item -ItemType Directory -Path (Join-Path $stage "static") | Out-Null
New-Item -ItemType Directory -Path (Join-Path $stage "models") | Out-Null

# App modules go at the ROOT (not src/) so gunicorn imports them directly —
# Oryx's launcher does not honor the sys.path insert that works locally.
Copy-Item (Join-Path $root "forecast_api.py")            (Join-Path $stage "forecast_api.py")
Copy-Item (Join-Path $root "src/forecaster.py")          (Join-Path $stage "forecaster.py")
Copy-Item (Join-Path $root "src/tenant_store.py")        (Join-Path $stage "tenant_store.py")
Copy-Item (Join-Path $root "src/auth.py")                (Join-Path $stage "auth.py")
Copy-Item (Join-Path $root "static/index.html")          (Join-Path $stage "static/index.html")
Copy-Item (Join-Path $root "models/lob_forecasters.joblib") (Join-Path $stage "models/lob_forecasters.joblib")
Copy-Item (Join-Path $root "deploy/requirements.txt")    (Join-Path $stage "requirements.txt")

$zip = Join-Path $env:TEMP "lob-forecast.zip"
if (Test-Path $zip) { Remove-Item $zip -Force }
Compress-Archive -Path (Join-Path $stage "*") -DestinationPath $zip
Write-Host "    package: $zip" -ForegroundColor DarkGray

Write-Host "==> Creating Azure resources ($Sku in $Location)..." -ForegroundColor Cyan
# RG may already exist (possibly in another region); resources still set their own location.
if ((az group exists --name $ResourceGroup) -ne "true") {
  az group create --name $ResourceGroup --location $Location -o none
}
# --location is REQUIRED: without it the plan inherits the RG region (which may have 0 quota).
az appservice plan create --name $Plan --resource-group $ResourceGroup --location $Location --is-linux --sku $Sku -o none
az webapp create --name $AppName --resource-group $ResourceGroup --plan $Plan --runtime "PYTHON:3.11" -o none

Write-Host "==> Configuring app settings + startup..." -ForegroundColor Cyan
# dev-key-default is what the dashboard prefills, so the deployed UI works out of the box.
az webapp config appsettings set --name $AppName --resource-group $ResourceGroup --settings `
  SCM_DO_BUILD_DURING_DEPLOYMENT=true `
  ENABLE_ORYX_BUILD=true `
  WEBSITES_CONTAINER_START_TIME_LIMIT=600 `
  "LOB_API_KEYS=dev-key-default:default,$TenantKey`:default" `
  "LOB_ADMIN_KEYS=$AdminKey" -o none

az webapp config set --name $AppName --resource-group $ResourceGroup --always-on true `
  --startup-file "gunicorn forecast_api:app -k uvicorn.workers.UvicornWorker -w 1 -b 0.0.0.0:8000 --timeout 120" -o none

# Restart so the build flags are active before the package upload triggers a build.
az webapp restart --name $AppName --resource-group $ResourceGroup -o none

Write-Host "==> Deploying package (Oryx will build requirements)..." -ForegroundColor Cyan
az webapp deploy --resource-group $ResourceGroup --name $AppName --src-path $zip --type zip -o none

$url = "https://$AppName.azurewebsites.net"
Write-Host ""
Write-Host "==> Done." -ForegroundColor Green
Write-Host "    URL:        $url"
Write-Host "    UI:         $url/ui/"
Write-Host "    Tenant key: $TenantKey   (header X-API-Key, tenant 'default')"
Write-Host "    Admin key:  $AdminKey"
Write-Host ""
Write-Host "    First request may take ~1-2 min while the build finishes." -ForegroundColor DarkGray
Write-Host "    Tear down with:  az group delete --name $ResourceGroup --yes --no-wait" -ForegroundColor DarkGray
