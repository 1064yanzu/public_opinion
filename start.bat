@echo off
REM Data Analysis System - Windows Launcher
REM This script provides a convenient way to start the system on Windows

SETLOCAL EnableDelayedExpansion

echo =====================================
echo   Data Analysis System v2.0
echo   Windows Launcher
echo =====================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.8 or higher from https://www.python.org/
    pause
    exit /b 1
)

REM Check Python version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [INFO] Python version: %PYTHON_VERSION%

REM Use the cross-platform launcher
if exist "launcher.py" (
    python launcher.py %*
) else (
    echo [ERROR] launcher.py not found
    pause
    exit /b 1
)

pause
