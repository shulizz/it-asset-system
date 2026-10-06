@echo off
cd /d D:\backend-deploy
start /min "" cmd /c "python -m uvicorn main:app --host 0.0.0.0 --port 8000"
timeout /t 3 /nobreak >nul
start /min "" cmd /c "ngrok.exe http --url=https://promptly-equation-cinch.ngrok-free.dev 8000"
exit
