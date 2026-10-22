@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title MedSafe-AI - Notebook 44 CRAFT + TrOCR setup
echo ======================================================
echo  MedSafe-AI Notebook 44 fine-tuned model setup
echo ======================================================
echo.
echo The trained checkpoint is NOT bundled with GitHub.
echo Download the complete best_model_DEVELOPMENT_ONLY folder
echo from MedSafe_AI_Project / 02_models in your Google Drive.
echo This installer will not substitute a generic model.
echo.
set "DEFAULT_DIR=%CD%\02_models\trocr_notebook44\best_model_DEVELOPMENT_ONLY"
if not defined MEDSAFE_TROCR_MODEL_DIR if exist "%DEFAULT_DIR%\config.json" set "MEDSAFE_TROCR_MODEL_DIR=%DEFAULT_DIR%"
if defined MEDSAFE_TROCR_MODEL_DIR goto validate
echo Paste the FULL local path to best_model_DEVELOPMENT_ONLY
echo (you may drag its folder into this window and press Enter).
set /p "MEDSAFE_TROCR_MODEL_DIR=Checkpoint folder: "
set "MEDSAFE_TROCR_MODEL_DIR=%MEDSAFE_TROCR_MODEL_DIR:"=%"
:validate
if not defined MEDSAFE_TROCR_MODEL_DIR goto no_model
if not exist "%MEDSAFE_TROCR_MODEL_DIR%\config.json" goto no_model
if not exist "%MEDSAFE_TROCR_MODEL_DIR%\model.safetensors" goto no_model
if not exist "%MEDSAFE_TROCR_MODEL_DIR%\tokenizer.json" goto no_model
if not exist "%MEDSAFE_TROCR_MODEL_DIR%\tokenizer_config.json" goto no_model
if not exist "%MEDSAFE_TROCR_MODEL_DIR%\processor_config.json" goto no_model
if not exist "%MEDSAFE_TROCR_MODEL_DIR%\preprocessor_config.json" goto no_model
echo.
echo Checkpoint assets found: "%MEDSAFE_TROCR_MODEL_DIR%"
if not exist ".venv\Scripts\python.exe" (
  where py >nul 2>nul
  if errorlevel 1 goto no_python
  py -3.11 -m venv .venv
  if errorlevel 1 py -3 -m venv .venv
  if errorlevel 1 goto no_python
)
echo.
echo Installing OCR dependencies into the same environment used by the app...
".venv\Scripts\python.exe" -m pip install -r requirements-ocr.txt
if errorlevel 1 goto failed
echo.
echo Loading CRAFT and the actual fine-tuned Notebook 44 checkpoint...
".venv\Scripts\python.exe" setup_and_verify_models.py --model-id "%MEDSAFE_TROCR_MODEL_DIR%"
if errorlevel 1 goto failed
echo.
echo PASS: CRAFT + Notebook 44 inference completed.
echo The checkpoint path is active for this window.
echo You may now launch MedSafe-AI using this same window.
choice /M "Start MedSafe-AI now"
if errorlevel 2 goto done
call "%~dp0start_windows.bat"
goto done
:no_model
echo.
echo ERROR: Missing or incomplete Notebook 44 checkpoint.
echo Selected folder: "%MEDSAFE_TROCR_MODEL_DIR%"
echo Copy the ENTIRE best_model_DEVELOPMENT_ONLY folder from Drive.
echo Required: config.json, model.safetensors, tokenizer.json,
echo tokenizer_config.json, processor_config.json, preprocessor_config.json
goto failed
:no_python
echo ERROR: Install Python 3.11 or 3.12 and enable the py launcher.
:failed
echo.
echo The model has NOT been verified. See runtime_data\ocr_model_smoke_test.json
echo if the verification script was reached.
pause
exit /b 1
:done
echo.
pause
exit /b 0
