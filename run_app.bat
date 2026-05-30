@echo off
echo =======================================================
echo Building Civilization Spatial Intelligence System
echo =======================================================
g++ -std=c++17 -Wall -O2 -o mapper.exe civilization_mapper.cpp -lws2_32 -mthreads
if %errorlevel% equ 0 (
    echo [!] Compilation successful. Starting C++ Server Backend (Port 8080)
    start "C++ API Server" cmd /k "mapper.exe"
) else (
    echo [!] Compilation failed. Falling back to FastAPI Python Backend (Port 8080)
    echo Installing backend dependencies...
    pip install -r backend\requirements.txt
    start "FastAPI Server" cmd /k "cd backend && uvicorn main:app --reload --port 8080"
)

echo.
echo Waiting 5 seconds for server to initialize...
timeout /t 5 /nobreak > nul

echo.
echo =======================================================
echo Launching Frontend in Default Browser...
echo =======================================================
start civilization_mapper_frontend.html

echo.
echo [!] Frontend and Backend are now running!
echo [!] Close the API Server cmd window when you want to stop the server.
echo.
pause
