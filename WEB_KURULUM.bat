@echo off
chcp 65001 >nul
title Bura - Web Kurulum
color 0A

echo ================================================
echo   BURA - Web Uygulamasi Kurulumu
echo ================================================
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [HATA] Python bulunamadi!
    echo Lutfen https://www.python.org/downloads adresinden indirin.
    echo Kurulum sirasinda "Add Python to PATH" kutusunu isaretleyin!
    pause
    exit /b 1
)

echo [OK] Python bulundu.
echo.
echo Gerekli kutuphaneler yukleniyor...
echo.

pip install flask pywin32 pdfplumber googlesearch-python requests beautifulsoup4 --quiet --upgrade

if %errorlevel% neq 0 (
    echo.
    echo [HATA] Kutuphaneler yuklenemedi. Internet baglantisini kontrol edin.
    pause
    exit /b 1
)

echo.
echo ================================================
echo   Kurulum TAMAMLANDI!
echo   Artik WEB_BASLA.bat ile sunucuyu baslatin.
echo ================================================
echo.
pause
