$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root
$python = Join-Path $root ".venv\Scripts\python.exe"
Start-Process -FilePath $python -ArgumentList @("-m","streamlit","run","app.py","--server.headless","true","--server.address","127.0.0.1","--server.port","8501") -WindowStyle Hidden
Write-Host "Dashboard started at http://127.0.0.1:8501"
