# AEGIS-0 Unified One-Command Launcher (Windows PowerShell)
Write-Host "==========================================================" -ForegroundColor Magenta
Write-Host "  AEGIS-0: Zero-Trust Token-Optimal Autonomous System     " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Magenta

$VENV_PYTHON = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $VENV_PYTHON)) {
    $VENV_PYTHON = "python"
}

Write-Host "[1/2] Starting AEGIS-0 FastAPI Master Orchestrator on :8000..." -ForegroundColor Yellow
$backendProcess = Start-Process -FilePath $VENV_PYTHON -ArgumentList "-m", "uvicorn", "orchestrator.main:app", "--port", "8000", "--host", "0.0.0.0" -PassThru

Write-Host "[2/2] Starting AEGIS-0 Mission Control Workbench on :3000..." -ForegroundColor Yellow
$frontendDir = Join-Path $PSScriptRoot "mission-control"
$frontendProcess = Start-Process -FilePath "cmd.exe" -ArgumentList "/c", "npm", "run", "dev" -WorkingDirectory $frontendDir -PassThru

Write-Host "`n✓ AEGIS-0 Dual-Stack System Initialized!" -ForegroundColor Green
Write-Host "  • Mission Control UI : http://localhost:3000/workbench" -ForegroundColor Cyan
Write-Host "  • Backend API & Docs : http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "  • Telemetry Stream   : ws://localhost:8000/ws/telemetry" -ForegroundColor Cyan
Write-Host "`nTo terminate AEGIS-0, close the spawned service windows or press Enter to shut down." -ForegroundColor White

Read-Host "Press Enter to stop all AEGIS-0 services"

Stop-Process -Id $backendProcess.Id -Force -ErrorAction SilentlyContinue
Stop-Process -Id $frontendProcess.Id -Force -ErrorAction SilentlyContinue
Write-Host "AEGIS-0 services stopped cleanly." -ForegroundColor Yellow
