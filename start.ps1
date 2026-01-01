# Start W-Intel v2.0 Services on Windows
# ----------------------------------------------------------------------

# 1. Define Paths
$ScriptDir = $PSScriptRoot
$BackendDir = Join-Path $ScriptDir "backend"
$FrontendDir = Join-Path $ScriptDir "frontend"
$VenvPython = Join-Path $BackendDir "venv\Scripts\python.exe"

Write-Host "[start.ps1] Starting W-Intel v2.0 on Windows..." -ForegroundColor Cyan

# 2. Check Python Environment
if (Test-Path $VenvPython) {
    $PyCmd = $VenvPython
    Write-Host "[start.ps1] Using Virtual Environment: $PyCmd" -ForegroundColor Green
} else {
    $PyCmd = "python"
    Write-Host "[start.ps1] Virtual environment not found. Using system python." -ForegroundColor Yellow
}

# 3. Start Backend (in a new window/process)
Write-Host "[start.ps1] Starting Backend Service..." -ForegroundColor Cyan
try {
    # Using Start-Process to keep it separate. 
    # -WindowStyle Hidden can be used if you don't want a popup, but seeing logs is good.
    $BackendArgs = "-m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --reload-exclude '*.db' --reload-exclude '*.log'"
    Start-Process -FilePath $PyCmd -ArgumentList $BackendArgs -WorkingDirectory $BackendDir -NoNewWindow:$false
    Write-Host " -> Backend launched."
} catch {
    Write-Error "Failed to start Backend: $_"
}

# 4. Start Frontend
Write-Host "[start.ps1] Starting Frontend Service..." -ForegroundColor Cyan
try {
    # Assuming npm is in PATH. 
    Start-Process -FilePath "npm" -ArgumentList "run dev" -WorkingDirectory $FrontendDir -NoNewWindow:$false
    Write-Host " -> Frontend launched."
} catch {
    Write-Error "Failed to start Frontend: $_"
}

Write-Host "--------------------------------------------------------"
Write-Host "Services are running in separate windows."
Write-Host "Backend: http://localhost:8000"
Write-Host "Frontend: http://localhost:5173 (usually)"
Write-Host "--------------------------------------------------------"
