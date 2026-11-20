@echo off
chcp 65001 >nul
title AI Data Analyst Agent - Dang Chay
cd /d "%~dp0"

echo ====================================================================
echo      AI DATA ANALYST AGENT - MAY CHU PHAN TICH DANG HOAT DONG
echo ====================================================================
echo.

set PYTHON_BIN=python
if exist "C:\Users\admin\AppData\Local\Programs\Python\Python311\python.exe" (
    set PYTHON_BIN="C:\Users\admin\AppData\Local\Programs\Python\Python311\python.exe"
)

echo  [1] Trinh duyet web dang tu dong mo tai: http://localhost:8080
echo.
echo  [2] *** LUU Y QUAN TRONG ***:
echo      - Cua so nay la MAY CHU (Server) dang phuc vu web.
echo      - Ban hay THU NHO (Minimize) cua so nay xuong thanh taskbar.
echo      - KHONG BAM DAU X DE DONG cua so nay (dong se lam web bi ngat).
echo.
echo ====================================================================

start http://localhost:8080

%PYTHON_BIN% -u app.py
pause
