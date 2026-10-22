@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"

echo.
echo ====================================================
echo MedSafe AI - direct cloud model download
echo ====================================================
echo This downloads the required research checkpoint from Google Drive.
echo The download is about 1.3 GB and may take several minutes.
echo.

if not exist ".venv\Scripts\python.exe" (
  echo Creating the Python environment...
  py -3.13 -m venv .venv 2>nul
  if errorlevel 1 py -3.12 -m venv .venv 2>nul
  if errorlevel 1 py -3.11 -m venv .venv 2>nul
  if errorlevel 1 (
    echo ERROR: Python 3.11, 3.12, or 3.13 is required.
    pause
    exit /b 1
  )
)

".venv\Scripts\python.exe" -m pip install --disable-pip-version-check --quiet gdown
if errorlevel 1 goto failed

set "DEST=02_models\trocr_notebook44\best_model_DEVELOPMENT_ONLY"
if not exist "%DEST%" mkdir "%DEST%"

call :download "1lD8qG__rTJxTAlLqUKOp-NkvE2MUnh3P" "config.json"
call :download "1kmkXRqq7YFza1AhWiV70ErSZT62feIHl" "generation_config.json"
call :download "1ZQPX3ahQ2k8dn1CBOfsJZNbTfAedzUHN" "preprocessor_config.json"
call :download "1kjAUczyWFtYsSqBfm5T9LjQC8na60LZS" "processor_config.json"
call :download "1CWODzjDT0Mi7zg_9OnqHdqSVaJyrTQZ-" "tokenizer.json"
call :download "1HAtuMxjBUDvDoAAeJNMX9h5QYp_P5tPe" "tokenizer_config.json"
call :download "1RiIMUHaazgB2_n17VeO6953-h8qTMk_G" "model.safetensors"
if errorlevel 1 goto failed

echo.
echo Cloud model files downloaded. Verifying the exact checkpoint...
call ".\SETUP_AND_RUN_WINDOWS.bat" --setup-only
exit /b %errorlevel%

:download
echo Downloading %~2 ...
".venv\Scripts\python.exe" -m gdown "https://drive.google.com/uc?id=%~1" -O "%DEST%\%~2" --no-cookies
if errorlevel 1 (
  echo ERROR: Could not download %~2.
  echo Confirm that the Drive file is shared with download permission.
  exit /b 1
)
exit /b 0

:failed
echo.
echo Cloud model setup failed. Check Drive permissions and internet access.
pause
exit /b 1
