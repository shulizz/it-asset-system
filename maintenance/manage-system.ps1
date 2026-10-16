param([ValidateSet('Status','Start','Stop','Restart')] [string]$Action = 'Status')
$ErrorActionPreference = 'Stop'
$taskName = 'IT-Asset-System'
$expectedInterpreter = [regex]::Escape('C:\FixedAssetSystem\backend\.venv\Scripts\python.exe')
if ($Action -in @('Stop','Restart')) {
    Stop-ScheduledTask -TaskName $taskName
    Start-Sleep -Seconds 2
    $owners = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue |
        Select-Object -ExpandProperty OwningProcess -Unique
    foreach ($ownerId in $owners) {
        $backendProcess = Get-CimInstance Win32_Process -Filter "ProcessId=$ownerId"
        if ($backendProcess.CommandLine -notmatch ('^\s*"?' + $expectedInterpreter + '"?\s+-m\s+uvicorn\s+main:app(?:\s|$)')) {
            throw 'Port 8000 is owned by an unexpected process; no process was stopped.'
        }
        Stop-Process -Id $ownerId -Force
    }
}
if ($Action -in @('Start','Restart')) { Start-ScheduledTask -TaskName $taskName }
Get-ScheduledTask -TaskName $taskName | Select-Object TaskName,State
Get-Service -Name 'FixedAssets-Gateway' | Select-Object Name,Status
