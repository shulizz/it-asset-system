$ErrorActionPreference = 'Stop'
foreach ($setting in @('IT_ASSET_SMTP_HOST','IT_ASSET_SMTP_PORT','IT_ASSET_SMTP_USER','IT_ASSET_SMTP_PASS','IT_ASSET_SMTP_FROM','IT_ASSET_SECRET_KEY')) {
    $value = [Environment]::GetEnvironmentVariable($setting, 'Machine')
    if ($value) { [Environment]::SetEnvironmentVariable($setting, $value, 'Process') }
}
$root = 'C:\FixedAssetSystem'
$logRoot = Join-Path $root 'logs'
New-Item -ItemType Directory -Path $logRoot -Force | Out-Null
Set-Location -LiteralPath (Join-Path $root 'backend')
# Windows PowerShell 5 treats native stderr log messages as error records.
# Keep setup failures terminating, but let the long-running server write its logs.
$ErrorActionPreference = 'Continue'
& (Join-Path $root 'backend\.venv\Scripts\python.exe') `
    -m uvicorn main:app --host 127.0.0.1 --port 8000 `
    --proxy-headers --forwarded-allow-ips 127.0.0.1 `
    1>> (Join-Path $logRoot 'backend.log') `
    2>> (Join-Path $logRoot 'backend-error.log')
exit $LASTEXITCODE
