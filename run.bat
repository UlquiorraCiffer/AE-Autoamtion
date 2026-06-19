@echo off
REM ─── AnimeEdit AI — Startup Script ─────────────────────────
REM Run this from the project root to start the backend server.
REM The CEP panel is loaded by After Effects automatically when
REM the extension is installed in the CEP extensions folder.
REM ────────────────────────────────────────────────────────────

setlocal enabledelayedexpansion

echo.
echo  ╔═══════════════════════════════════════════╗
echo  ║        AnimeEdit AI — Backend Server      ║
echo  ╚═══════════════════════════════════════════╝
echo.

REM ─── Check Python ───
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python 3.10+ is not on PATH. Install it from https://python.org
    pause
    exit /b 1
)

REM ─── Check FFmpeg ───
ffmpeg -version >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARN] FFmpeg not found on PATH. Scene detection will use OpenCV fallback.
    echo        Install from https://ffmpeg.org for best results.
    echo.
)

REM ─── Install dependencies ───
echo [1/3] Installing Python dependencies...
pip install -r backend\requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] pip install failed.
    pause
    exit /b 1
)
echo.

REM ─── Run tests ───
echo [2/3] Running test suite...
python -m pytest backend\tests\ -v --tb=short
echo.

REM ─── Start server ───
echo [3/3] Starting backend on http://127.0.0.1:8000
echo.
echo       API endpoints:
echo       GET  /health           Health check
echo       POST /analyze          Analyze editing prompt
echo       POST /detect-scenes    Detect scene changes
echo       POST /detect-beats     Detect audio beats
echo       POST /generate-plan    Generate edit plan
echo       POST /apply-edit       Generate AE ExtendScript
echo.
echo       Press Ctrl+C to stop.
echo ───────────────────────────────────────────────
echo.

python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
if %errorlevel% neq 0 (
    echo [ERROR] Server failed to start.
    pause
    exit /b 1
)

endlocal
