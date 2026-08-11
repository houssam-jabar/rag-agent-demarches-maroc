Set objShell = CreateObject("WScript.Shell")

objShell.Run "cmd /c cd /d ""C:\pfa"" && venv\Scripts\python.exe -m uvicorn api.main:app --host 127.0.0.1 --port 8000", 0, False

objShell.Run "cmd /c cd /d ""C:\pfa\frontend"" && npm run dev", 0, False

WScript.Sleep 6000

objShell.Run "http://localhost:5173", 1, False
