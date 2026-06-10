@echo off
echo =======================================================
echo  Civilization Spatial Intelligence Mapper
echo =======================================================
echo.

echo [1/3] Installing backend dependencies...
pip install -r backend\requirements.txt >nul 2>&1

echo [2/3] Starting FastAPI backend on http://localhost:8080 ...
start "FastAPI Server - Civilization Mapper" cmd /k "cd backend && uvicorn main:app --reload --port 8080"

echo.
echo [3/3] Waiting 4 seconds for server to start...
timeout /t 4 /nobreak >nul

echo.
echo =======================================================
echo  Opening http://localhost:8080 in your browser
echo  (Do NOT open the .html file directly)
echo =======================================================
start http://localhost:8080

echo.
echo [OK] App is running at http://localhost:8080
echo [OK] Close the "FastAPI Server" terminal window to stop.
echo.
pause
