# Deploying the LOB Forecasting API to Azure

The app is a FastAPI backend that also serves the dashboard UI, deployed to
**Azure App Service (Linux, Python 3.11)**.

## One-command deploy

```powershell
./deploy_azure.ps1 -Location centralus -Sku F1
```

The script stages **only** the forecasting app's files (the working folder
also contains unrelated projects), zips them, creates the Azure resources,
sets configuration, and pushes a build-on-deploy package.

> **Region/quota note:** some subscriptions have an App Service VM quota of 0
> in certain regions (you'll see `Operation cannot be completed without
> additional quota ... Total VMs: 0`). This deployment used **centralus**,
> where Free-tier (F1) quota was available. If a region fails, try another
> (`centralus`, `westus2`, `eastus2`) or request a quota increase.

## What gets deployed

| Item | Value |
|------|-------|
| Runtime | Python 3.11 on Linux |
| Startup | `gunicorn forecast_api:app -k uvicorn.workers.UvicornWorker -w 1 -b 0.0.0.0:8000` |
| Build | Oryx (`SCM_DO_BUILD_DURING_DEPLOYMENT=true`) installs `deploy/requirements.txt` |
| Auth keys | set as app settings `LOB_API_KEYS` / `LOB_ADMIN_KEYS` (never the dev `config/api_keys.json`) |

Single gunicorn worker on purpose: the per-tenant in-memory cache must stay
consistent with the on-disk bundles.

## After deploy

- App URL:  `https://<app-name>.azurewebsites.net`
- Dashboard: `https://<app-name>.azurewebsites.net/ui/`
- Authenticate with the tenant key via the `X-API-Key` header.

## Important caveats

- **Free tier (F1)** has no Always-On: the app sleeps after idle and the next
  request cold-starts (can take a minute). Upgrade to B1+ for always-on — but
  that needs dedicated-VM quota in the region.
- **Persistence:** tenant bundles are written to `models/tenants/` on the App
  Service filesystem. A redeploy overwrites `wwwroot` and wipes them. For
  durable multi-tenant data, mount Azure Files or use blob storage.
- **Rotate keys** before sharing the URL: set new values with
  ```powershell
  az webapp config appsettings set -g lob-forecast-rg -n <app> --settings "LOB_API_KEYS=<key>:default" "LOB_ADMIN_KEYS=<admin>"
  ```

## Tear down (stop all billing)

```powershell
az group delete --name lob-forecast-rg --yes --no-wait
```
