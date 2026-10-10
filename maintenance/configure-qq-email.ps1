$ErrorActionPreference='Stop'
$ProgressPreference='SilentlyContinue'
$identity=[Security.Principal.WindowsIdentity]::GetCurrent()
$principal=New-Object Security.Principal.WindowsPrincipal($identity)
if(-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)){throw 'Run this script in an elevated PowerShell on the server.'}
$sender=(Read-Host 'QQ sender email (example: 123456@qq.com)').Trim()
if($sender -notmatch '^[A-Za-z0-9._%+-]+@qq\.com$'){throw 'Enter a valid QQ email address.'}
$authorization=Read-Host 'QQ SMTP authorization code (hidden input)' -AsSecureString
$handle=[Runtime.InteropServices.Marshal]::SecureStringToBSTR($authorization)
try {
 $smtpCode=[Runtime.InteropServices.Marshal]::PtrToStringBSTR($handle)
 if([string]::IsNullOrWhiteSpace($smtpCode)){throw 'Authorization code cannot be empty.'}
 [Environment]::SetEnvironmentVariable('IT_ASSET_SMTP_HOST','smtp.qq.com','Machine')
 [Environment]::SetEnvironmentVariable('IT_ASSET_SMTP_PORT','465','Machine')
 [Environment]::SetEnvironmentVariable('IT_ASSET_SMTP_USER',$sender,'Machine')
 [Environment]::SetEnvironmentVariable('IT_ASSET_SMTP_PASS',$smtpCode.Trim(),'Machine')
} finally {
 [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($handle)
 $smtpCode=$null
}
$root='C:\FixedAssetSystem'
$startup=Join-Path $root 'maintenance\runtime\start-fixed-assets.ps1'
$content=[IO.File]::ReadAllText($startup)
if(-not $content.Contains('IT_ASSET_SMTP_HOST')){
 Copy-Item -LiteralPath $startup -Destination ($startup+'.pre-mail-'+(Get-Date -Format 'yyyyMMdd-HHmmss'))
 $environment=@'
foreach($mailSetting in @('IT_ASSET_SMTP_HOST','IT_ASSET_SMTP_PORT','IT_ASSET_SMTP_USER','IT_ASSET_SMTP_PASS','IT_ASSET_SMTP_FROM')) {
    $mailValue=[Environment]::GetEnvironmentVariable($mailSetting,'Machine')
    if($mailValue){[Environment]::SetEnvironmentVariable($mailSetting,$mailValue,'Process')}
}
'@
 [IO.File]::WriteAllText($startup,$environment+"`r`n"+$content,(New-Object Text.UTF8Encoding($true)))
}
Stop-ScheduledTask -TaskName 'IT-Asset-System'
Start-Sleep -Seconds 2
$connections=Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
foreach($ownerId in ($connections | Select-Object -ExpandProperty OwningProcess -Unique)){
 $process=Get-CimInstance Win32_Process -Filter "ProcessId=$ownerId"
 if($process.CommandLine -notmatch 'uvicorn.*main:app'){throw 'Port 8000 belongs to an unexpected process.'}
 Stop-Process -Id $ownerId -Force
}
Start-ScheduledTask -TaskName 'IT-Asset-System'
for($attempt=0;$attempt -lt 15;$attempt++){
 Start-Sleep -Seconds 2
 try{if((Invoke-WebRequest 'http://127.0.0.1:8000/docs' -UseBasicParsing -TimeoutSec 3).StatusCode -eq 200){Write-Output 'QQ SMTP settings saved. Backend is running. No email has been sent.';exit 0}}catch{}
}
throw 'Settings saved, but backend startup timed out. Check server logs.'
