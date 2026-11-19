#!/usr/bin/env bash
# AEGIS-0 Unified One-Command Launcher (Linux / macOS)
set -e

echo "=========================================================="
echo "  AEGIS-0: Zero-Trust Token-Optimal Autonomous System     "
echo "=========================================================="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

VENV_PYTHON="${SCRIPT_DIR}/.venv/bin/python"
if [ ! -f "$VENV_PYTHON" ]; then
    VENV_PYTHON="python3"
fi

echo "[1/2] Starting AEGIS-0 FastAPI Master Orchestrator on :8000..."
$VENV_PYTHON -m uvicorn orchestrator.main:app --port 8000 --host 0.0.0.0 &
BACKEND_PID=$!

echo "[2/2] Starting AEGIS-0 Mission Control Workbench on :3000..."
cd "${SCRIPT_DIR}/mission-control" && npm run dev &
FRONTEND_PID=$!

cleanup() {
    echo "Shutting down AEGIS-0 services..."
    kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
}
trap cleanup SIGINT SIGTERM EXIT

echo ""
echo "✓ AEGIS-0 Dual-Stack System Initialized!"
echo "  • Mission Control UI : http://localhost:3000/workbench"
echo "  • Backend API & Docs : http://localhost:8000/docs"
echo "  • Telemetry Stream   : ws://localhost:8000/ws/telemetry"
echo ""
echo "Press Ctrl+C to terminate services..."

wait
