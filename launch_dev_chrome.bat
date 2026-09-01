@echo off
echo ============================================
echo  Launching Chrome for Razorpay Development
echo  (Private Network Access restrictions OFF)
echo ============================================
echo.

REM Close existing Chrome instances (optional)
REM taskkill /f /im chrome.exe >nul 2>&1

REM Chrome path - try common locations
set CHROME_PATH=""
if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" (
    set CHROME_PATH="C:\Program Files\Google\Chrome\Application\chrome.exe"
) else if exist "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" (
    set CHROME_PATH="C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
) else if exist "%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe" (
    set CHROME_PATH="%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"
)

if %CHROME_PATH%=="" (
    echo ERROR: Chrome not found! Please edit this script with your Chrome path.
    pause
    exit /b 1
)

echo Opening: http://127.0.0.1:8000/olympiad-form/
echo.
echo [Flags enabled]
echo  --disable-features=BlockInsecurePrivateNetworkRequests
echo  --disable-web-security (dev only)
echo  --allow-running-insecure-content
echo.

start "" %CHROME_PATH% ^
    --disable-features=BlockInsecurePrivateNetworkRequests ^
    --allow-running-insecure-content ^
    --disable-blink-features=AutomationControlled ^
    --user-data-dir="%TEMP%\razorpay-dev-profile" ^
    "http://127.0.0.1:8000/olympiad-form/"

echo Chrome launched! Console errors should be gone now.
echo.
echo NOTE: Use this ONLY for local development testing.
echo       Never use these flags in production or for real browsing.
echo.
pause
