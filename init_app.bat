@echo off
rem init_app.bat - create plan.db if missing by calling app.init_db()
setlocal
set DB=%~dp0plan.db
echo Checking for database at %DB%
if exist "%DB%" (
    echo Database exists: %DB%
    exit /b 0
)

echo Database not found. Attempting to create using venv python...
if exist "%~dp0.venv\Scripts\python.exe" (
    "%~dp0.venv\Scripts\python.exe" -c "import sys; sys.path.insert(0, r'.'); import app; app.init_db(); print('INIT_DB_DONE')"
    if %ERRORLEVEL% EQU 0 (
        echo Database created successfully.
        exit /b 0
    ) else (
        echo Failed to initialize DB with venv python. Errorlevel=%ERRORLEVEL%
        exit /b 1
    )
) else (
    echo venv python not found, trying system python...
    python -c "import sys; sys.path.insert(0, r'.'); import app; app.init_db(); print('INIT_DB_DONE')"
    if %ERRORLEVEL% EQU 0 (
        echo Database created successfully using system python.
        exit /b 0
    ) else (
        echo Failed to initialize DB with system python. Errorlevel=%ERRORLEVEL%
        exit /b 1
    )
)

endlocal