@echo off
chcp 65001 >nul
title Bura - Kurulum
color 0A

echo ================================================
echo   BURA - Satin Alma Talebi Asistani
echo   Kurulum Basladi...
echo ================================================
echo.

:: Python kontrolu
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [HATA] Python bulunamadi!
    echo.
    echo Lutfen once Python 3.8 veya uzeri yukleyin:
    echo https://www.python.org/downloads/
    echo.
    echo Kurulum sirasinda "Add Python to PATH" secenegini isaretleyin!
    echo.
    pause
    exit /b 1
)

echo [OK] Python bulundu.
echo.
echo Gerekli kutuphaneler yukleniyor...
echo (Bu islem birka dakika surebilir)
echo.

pip install pywin32 pdfplumber googlesearch-python requests beautifulsoup4 --quiet --upgrade

if %errorlevel% neq 0 (
    echo.
    echo [HATA] Kutuphaneler yuklenemedi!
    echo Lutfen internet baglantinizi kontrol edin.
    pause
    exit /b 1
)

echo.
echo ================================================
echo   Kurulum TAMAMLANDI!
echo   Artik BASLA.bat ile uygulamayi acabilirsiniz.
echo ================================================
echo.
pause
