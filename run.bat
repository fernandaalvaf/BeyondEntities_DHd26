@echo off
setlocal enableextensions

REM ============================================================
REM run.bat - Windows-Wrapper fuer die Triple-Extraktion Pipeline
REM ============================================================
REM Verwendung:
REM   run.bat
REM   run.bat --profile anthropic --model claude-haiku-4-5 --limit 5
REM   run.bat --beispieldaten
REM ============================================================

set "SCRIPT_DIR=%~dp0"
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

set "PIPELINE_DIR=%SCRIPT_DIR%\pipeline"
set "DATA_DIR=%SCRIPT_DIR%\data\uebung_1"

if /I "%~1"=="--help" goto :help
if /I "%~1"=="-h" goto :help
if /I "%~1"=="--beispieldaten" goto :beispieldaten

goto :run

:ensure_dirs
if not exist "%PIPELINE_DIR%\analyze" mkdir "%PIPELINE_DIR%\analyze"
if not exist "%PIPELINE_DIR%\output_json" mkdir "%PIPELINE_DIR%\output_json"
if not exist "%PIPELINE_DIR%\csv" mkdir "%PIPELINE_DIR%\csv"
if not exist "%PIPELINE_DIR%\logs" mkdir "%PIPELINE_DIR%\logs"
goto :eof

:beispieldaten
call :ensure_dirs

if not exist "%DATA_DIR%" (
  echo [ERROR] Beispieldaten nicht gefunden unter: "%DATA_DIR%"
  exit /b 1
)

echo [INFO] Kopiere Beispieldaten nach "%PIPELINE_DIR%\analyze" ...
for /d %%D in ("%DATA_DIR%\dataset_*") do (
  xcopy "%%~fD" "%PIPELINE_DIR%\analyze\%%~nxD\" /E /I /Y >nul
)
echo [INFO] Fertig.
exit /b 0

:run
call :ensure_dirs

if not exist "%PIPELINE_DIR%\config.yaml" (
  echo [ERROR] Keine pipeline\config.yaml gefunden - bitte Repository aktualisieren ^(git pull^).
  exit /b 1
)

if not exist "%SCRIPT_DIR%\.env" (
  echo [WARN] Keine .env gefunden - API-Keys fehlen.
  echo [INFO] Tipp: copy .env.example .env und Keys eintragen.
  type nul > "%SCRIPT_DIR%\.env"
)

echo [INFO] Starte Triple-Extraktion Pipeline ^(Docker^) ...
echo.
docker compose run --rm pipeline %*
exit /b %errorlevel%

:help
echo Verwendung:
echo   run.bat
echo   run.bat --profile anthropic --model claude-haiku-4-5 --limit 5
echo   run.bat --beispieldaten
exit /b 0
