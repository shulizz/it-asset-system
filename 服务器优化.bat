@echo off
echo === ???????????????? ===
powercfg /change standby-timeout-ac 0
powercfg /change monitor-timeout-ac 0
powercfg /change hibernate-timeout-ac 0
powercfg /change disk-timeout-ac 0

echo === ?????? ===
reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\WindowsUpdate\Auto Update" /v AUOptions /t REG_DWORD /d 1 /f
reg add "HKLM\SYSTEM\CurrentControlSet\Control\Update" /v SetUpdateManagement /t REG_DWORD /d 1 /f

echo === ???????? ===
reg add "HKLM\SYSTEM\CurrentControlSet\Control\CrashControl" /v AutoReboot /t REG_DWORD /d 0 /f

echo.
echo ???????????
pause
