@echo off
title Free Fire Like API - Gohar Rehman
cd /d "%~dp0"
echo ===================================================
echo   GOHAR REHMAN - FREE FIRE LIKE API (OB55)
echo ===================================================
echo [*] Starting High-Speed Like Engine on port 8000...
python -m uvicorn app:app --host 0.0.0.0 --port 8000
pause
