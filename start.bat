@echo off
:: ============================================================
:: start.bat
:: Dublu-click pe acest fisier ca sa pornesti aplicatia DIIP
:: ============================================================

title DIIP — Digital Infrastructure Intelligence Platform

echo.
echo  ==========================================
echo   DIIP Platform — Se porneste...
echo  ==========================================
echo.

:: Ne mutam in folderul proiectului
cd /d "C:\Users\Ionut\PycharmProjects\PythonProject2"

:: Activam virtual environment
call .venv\Scripts\activate.bat

:: Adaugam Git si Nmap in PATH (in caz ca nu sunt)
set PATH=%PATH%;C:\Program Files\Git\cmd
set PATH=%PATH%;C:\Program Files (x86)\Nmap

:: Pornim aplicatia
echo  Deschide browserul la: http://127.0.0.1:8080
echo  Apasa CTRL+C ca sa opresti aplicatia.
echo.
python -m uvicorn main:app --port 8080 --host 0.0.0.0

pause
