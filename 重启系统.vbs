Set ws = CreateObject("Wscript.Shell")
' 先杀掉旧的后端
ws.Run "cmd /c taskkill /f /im python.exe", 0, True
WScript.Sleep 2000
' 启动新后端
ws.CurrentDirectory = "D:\backend-deploy"
ws.Run "cmd /c python -m uvicorn main:app --host 0.0.0.0 --port 8000", 0, False
' 启动ngrok
WScript.Sleep 3000
ws.Run "cmd /c ngrok.exe http --url=https://promptly-equation-cinch.ngrok-free.dev 8000", 0, False
