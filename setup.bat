@echo off
REM ============================================================
REM Setup: .env-Datei anlegen (einmalig vor dem ersten Start)
REM ============================================================
REM Verwendung: Doppelklick auf setup.bat  ODER  setup.bat im CMD
REM ============================================================

echo.
echo === Triple-Extraktion Pipeline - Ersteinrichtung ===
echo.

IF NOT EXIST ".env.example" (
    echo FEHLER: .env.example nicht gefunden.
    echo Bitte im Projektverzeichnis ausfuehren.
    pause
    exit /b 1
)

IF EXIST ".env" (
    echo .env existiert bereits - ueberspringe.
) ELSE (
    copy ".env.example" ".env" >nul
    echo .env wurde aus .env.example erstellt.
)

echo.
echo ----------------------------------------------------------
echo NAECHSTER SCHRITT:
echo   Oeffne die Datei .env und trage deinen API-Key ein,
echo   z. B.:
echo.
echo   ANTHROPIC_API_KEY=sk-ant-...
echo   oder OPENAI_API_KEY=sk-...
echo.
echo Danach starte die Pipeline:
echo   - Docker Desktop oeffnen
echo   - compose.yaml im Projektordner auswaehlen und "Run" klicken
echo ----------------------------------------------------------
echo.
pause
