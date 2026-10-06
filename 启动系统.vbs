Set ws = CreateObject("Wscript.Shell")
ws.CurrentDirectory = "D:\backend-deploy"
ws.Run "cmd /c python -m uvicorn main:app --host 0.0.0.0 --port 8000", 0, False
WScript.Sleep 3000
ws.Run "cmd /c ngrok.exe http --url=https://promptly-equation-cinch.ngrok-free.dev 8000", 0, False
