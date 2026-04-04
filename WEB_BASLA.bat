@echo off
chcp 65001 >nul
title Bura - Web Sunucusu

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [HATA] Python bulunamadi. Lutfen once WEB_KURULUM.bat calistirin.
    pause
    exit /b 1
)

echo.
echo ================================================
echo   BURA Web Sunucusu Baslatiliyor...
echo ================================================
echo.

:: Bilgisayarin IP adresini goster
echo Bilgisayarinizin IP adresi:
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /i "IPv4"') do (
    set ip=%%a
    echo   http:%%a:5000
)

echo.
echo PC'nizden:    http://localhost:5000
echo Telefondan:   Yukaridaki adresi tarayiciya yazin (ayni WiFi olmali)
echo.
echo Kapatmak icin bu pencereyi kapatin.
echo ================================================
echo.

cd /d "%~dp0web_app"
python app.py

pause
