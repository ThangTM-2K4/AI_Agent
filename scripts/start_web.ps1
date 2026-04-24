$ErrorActionPreference = "Stop"

Set-Location (Join-Path $PSScriptRoot "..")

$pythonExe = Join-Path (Get-Location) ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    Write-Host "[ERROR] Khong tim thay .venv. Hay tao moi truong ao truoc:" -ForegroundColor Red
    Write-Host "python -m venv .venv"
    Write-Host ".venv\Scripts\python.exe -m pip install -r requirements.txt"
    exit 1
}

$port = 8010
$existing = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue | Select-Object -First 1
if ($existing) {
    Write-Host "[INFO] Port $port dang duoc su dung boi PID $($existing.OwningProcess). Dang dung tien trinh cu..."
    Stop-Process -Id $existing.OwningProcess -Force -ErrorAction SilentlyContinue
}

Write-Host "[INFO] Starting web at http://127.0.0.1:$port" -ForegroundColor Green
& $pythonExe -m uvicorn app.main:app --host 127.0.0.1 --port $port --reload
