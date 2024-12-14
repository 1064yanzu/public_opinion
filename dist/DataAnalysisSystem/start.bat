@echo off
chcp 65001 > nul

title DataAnalysisSystem
color 0A

echo [INFO] Checking environment...
timeout /t 1 /nobreak > nul

rem Check if the executable exists
if not exist "DataAnalysisSystem.exe" (
    color 0C
    echo [ERROR] DataAnalysisSystem.exe not found!
    echo [ERROR] Please make sure you are running this script from the correct directory.
    pause
    exit /b 1
)

rem Create data directory if it doesn't exist
if not exist "persistent_data" (
    echo [INFO] Creating persistent_data directory...
    mkdir "persistent_data"
)

rem Check if port is in use
netstat -ano | find ":5000" > nul
if %errorlevel% equ 0 (
    color 0E
    echo [WARN] Port 5000 is in use
    echo [INFO] Attempting to close process...
    for /f "tokens=5" %%a in ('netstat -ano ^| find ":5000"') do (
        taskkill /f /pid %%a > nul 2>&1
    )
    timeout /t 2 /nobreak > nul
)

echo [INFO] Starting system...
echo [INFO] Browser will open automatically...
timeout /t 2 /nobreak > nul

rem Start application
start /min "" "DataAnalysisSystem.exe"
if errorlevel 1 (
    color 0C
    echo [ERROR] Failed to start DataAnalysisSystem.exe
    echo [ERROR] Please check if the file exists and try again.
    pause
    exit /b 1
)
timeout /t 3 /nobreak > nul

rem Wait for service to start with timeout
set /a attempts=0
:check_service
timeout /t 1 /nobreak > nul
netstat -ano | find ":5000" > nul
if %errorlevel% neq 0 (
    set /a attempts+=1
    if %attempts% gtr 30 (
        color 0C
        echo [ERROR] Service failed to start after 30 seconds
        echo [ERROR] Please check the application logs for more information.
        echo [ERROR] You can find the logs in app.log
        pause
        exit /b 1
    )
    goto check_service
)

rem Try to connect to the service
powershell -Command "(New-Object Net.WebClient).DownloadString('http://localhost:5000')" > nul 2>&1
if errorlevel 1 (
    color 0E
    echo [WARN] Service is running but may not be responding correctly
)

start http://localhost:5000

color 0A
echo [SUCCESS] System started successfully!
echo [INFO] If browser did not open, visit: http://localhost:5000
echo.
echo [IMPORTANT] Do not close this window. Closing it will exit the system.
echo [TIP] To exit the system, simply close this window.
echo [INFO] Log file is available at: app.log

rem Monitor the application
:monitor_loop
timeout /t 5 /nobreak > nul
tasklist | find "DataAnalysisSystem.exe" > nul
if errorlevel 1 (
    color 0C
    echo [ERROR] Application has stopped unexpectedly!
    echo [ERROR] Please check app.log for details.
    pause
    exit /b 1
)
goto monitor_loop 