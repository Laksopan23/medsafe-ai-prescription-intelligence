@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"

echo.
echo ====================================================
echo MedSafe AI - setup from mounted Drive
echo ====================================================
echo Google Drive for desktop must be installed, signed in, and running.
echo.

set "MODEL_SOURCE="
for %%D in (C D E F G H I J K L M N O P Q R S T U V W X Y Z) do (
  if not defined MODEL_SOURCE if exist "%%D:\My Drive\MedSafe_AI_Project\02_models\trocr_finetuned_official_source_dev_notebook44\943e9bd2b5f1a54d\best_model_DEVELOPMENT_ONLY\model.safetensors" set "MODEL_SOURCE=%%D:\My Drive\MedSafe_AI_Project\02_models\trocr_finetuned_official_source_dev_notebook44\943e9bd2b5f1a54d\best_model_DEVELOPMENT_ONLY"
  if not defined MODEL_SOURCE if exist "%%D:\My Drive\MedSafe_AI_Project\02_models\trocr_notebook44\best_model_DEVELOPMENT_ONLY\model.safetensors" set "MODEL_SOURCE=%%D:\My Drive\MedSafe_AI_Project\02_models\trocr_notebook44\best_model_DEVELOPMENT_ONLY"
)

if not defined MODEL_SOURCE (
  echo ERROR: The required research checkpoint was not found on a mounted Drive.
  echo Start Google Drive for desktop, sign in, wait for the files to appear,
  echo and run this file again.
  echo.
  pause
  exit /b 1
)

echo Found checkpoint:
echo %MODEL_SOURCE%
echo.
call "%~dp0SETUP_AND_RUN_WINDOWS.bat" "%MODEL_SOURCE%"
exit /b %errorlevel%
