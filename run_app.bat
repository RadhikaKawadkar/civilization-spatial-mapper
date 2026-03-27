@echo off
echo =======================================================
echo Building Civilization Spatial Intelligence System
echo =======================================================
g++ -std=c++17 -Wall -O2 -o mapper.exe civilization_mapper.cpp
if %errorlevel% neq 0 (
    echo [!] Compilation failed. Please check your g++ installation or errors above.
    pause
    exit /b %errorlevel%
)

echo.
echo =======================================================
echo Starting REST API Server Backend (Port 8080)
echo =======================================================
start "Backend API Server" cmd /c "mapper.exe"

echo.
echo Waiting 2 seconds for server to initialize...
timeout /t 2 /nobreak > nul

echo.
echo =======================================================
echo Launching Frontend in Default Browser...
echo =======================================================
start civilization_mapper_frontend.html

echo.
echo [!] Both Frontend and Backend are now running parallelly in sync!
echo [!] Close the "Backend API Server" cmd window when you want to stop the server.
echo.
pause
