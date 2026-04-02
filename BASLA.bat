@echo off
chcp 65001 >nul
title Bura - Satin Alma Talebi Asistani

:: Python kontrolu
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [HATA] Python bulunamadi. Lutfen once KURULUM.bat calistirin.
    pause
    exit /b 1
)

:: Uygulamayi baslat (konsol penceresi gizli kalsin)
start "" pythonw "%~dp0bura_app\main.py"
