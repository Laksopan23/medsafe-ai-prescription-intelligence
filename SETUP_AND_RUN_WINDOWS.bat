@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
if errorlevel 1 goto failed

set "PROJECT_ROOT=%CD%"
set "MODEL_DEST=%PROJECT_ROOT%\02_models\trocr_notebook44\best_model_DEVELOPMENT_ONLY"
set "EXPECTED_MODEL_SHA256=a646621570f74db93c0a9354795860ccdd44bae3267624a140a4087ac6113a80"
set "SOURCE_MODEL=%~1"
if /I "%~1"=="--setup-only" (
  set "SOURCE_MODEL="
  set "SETUP_ONLY=1"
)
set "EXIT_CODE=1"

echo.
echo ====================================================
echo MedSafe AI - complete Windows setup and run
echo ====================================================
echo First setup can take a long time and needs internet access.
echo The fine-tuned research model is copied from your own Drive.
echo No public replacement model will be downloaded.
echo.

call :find_python
if defined PYTHON_EXE goto have_python
where winget >nul 2>nul
if errorlevel 1 (
  echo ERROR: Install Python 3.11, 3.12, or 3.13 and rerun this file.
  goto failed
)
echo Installing Python 3.12...
winget install --id Python.Python.3.12 -e --silent --accept-source-agreements --accept-package-agreements
if errorlevel 1 goto failed
call :find_python
if not defined PYTHON_EXE (
  echo Python was installed, but this terminal cannot locate it yet.
  echo Open a new terminal and run this same file again.
  goto failed
)
:have_python

where npm >nul 2>nul
if not errorlevel 1 goto have_node
where winget >nul 2>nul
if errorlevel 1 (
  echo ERROR: Install Node.js 20 or later and rerun this file.
  goto failed
)
echo Installing Node.js...
winget install --id OpenJS.NodeJS.LTS -e --silent --accept-source-agreements --accept-package-agreements
if errorlevel 1 goto failed
if exist "%ProgramFiles%\nodejs\npm.cmd" set "PATH=%ProgramFiles%\nodejs;%PATH%"
where npm >nul 2>nul
if errorlevel 1 (
  echo Node.js was installed, but this terminal cannot locate npm yet.
  echo Open a new terminal and run this same file again.
  goto failed
)
:have_node

where tesseract >nul 2>nul
if not errorlevel 1 goto have_tesseract
if exist "%ProgramFiles%\Tesseract-OCR\tesseract.exe" set "PATH=%ProgramFiles%\Tesseract-OCR;%PATH%"
where tesseract >nul 2>nul
if not errorlevel 1 goto have_tesseract
where winget >nul 2>nul
if errorlevel 1 (
  echo ERROR: Install Tesseract OCR and rerun this file.
  goto failed
)
echo Installing Tesseract OCR...
winget install --id UB-Mannheim.TesseractOCR -e --silent --accept-source-agreements --accept-package-agreements
if errorlevel 1 goto failed
if exist "%ProgramFiles%\Tesseract-OCR\tesseract.exe" set "PATH=%ProgramFiles%\Tesseract-OCR;%PATH%"
where tesseract >nul 2>nul
if errorlevel 1 (
  echo Tesseract was installed, but is not visible in this terminal.
  echo Open a new terminal and run this same file again.
  goto failed
)
:have_tesseract

if not exist ".venv\Scripts\python.exe" (
  echo Creating the Python environment...
  "%PYTHON_EXE%" %PYTHON_ARGS% -m venv .venv
  if errorlevel 1 goto failed
)

echo Installing all application and optional OCR packages...
".venv\Scripts\python.exe" -m pip install -r requirements-ocr.txt
if errorlevel 1 goto failed

set "MEDSAFE_TROCR_MODEL_DIR=%MODEL_DEST%"
call :verify_checkpoint
if not errorlevel 1 goto model_ready

if defined SOURCE_MODEL goto copy_model
for %%D in (C D E F G H I J K L M N O P Q R S T U V W X Y Z) do (
  if not defined SOURCE_MODEL if exist "%%D:\My Drive\MedSafe_AI_Project\02_models\trocr_finetuned_official_source_dev_notebook44\943e9bd2b5f1a54d\best_model_DEVELOPMENT_ONLY\model.safetensors" set "SOURCE_MODEL=%%D:\My Drive\MedSafe_AI_Project\02_models\trocr_finetuned_official_source_dev_notebook44\943e9bd2b5f1a54d\best_model_DEVELOPMENT_ONLY"
)
if not defined SOURCE_MODEL (
  echo.
  echo The fine-tuned Notebook 44 model was not found locally or on a mounted Drive.
  echo Connect Google Drive for desktop, or paste the full path to its
  echo best_model_DEVELOPMENT_ONLY folder below.
  set /p "SOURCE_MODEL=Model source folder: "
)
set "SOURCE_MODEL=%SOURCE_MODEL:"=%"

:copy_model
if not exist "%SOURCE_MODEL%\model.safetensors" (
  echo ERROR: The selected source has no model.safetensors file.
  echo The exact Notebook 44 checkpoint is required; no substitute will be used.
  goto failed
)
if /I "%SOURCE_MODEL%"=="%MODEL_DEST%" (
  echo ERROR: The destination model is incomplete. Select a different source folder.
  goto failed
)
if not exist "%MODEL_DEST%" mkdir "%MODEL_DEST%"
if errorlevel 1 goto failed
echo Copying the research checkpoint. This file is about 1.3 GB...
robocopy "%SOURCE_MODEL%" "%MODEL_DEST%" /E /Z /J /R:3 /W:3
if errorlevel 8 (
  echo ERROR: Checkpoint copy failed. Check Drive sync and disk space.
  goto failed
)
call :verify_checkpoint
if errorlevel 1 (
  echo ERROR: Copied checkpoint is missing files or has incomplete weights.
  goto failed
)

:model_ready
echo Research checkpoint is complete.
if exist "runtime_data\ocr_model_smoke_test.json" (
  ".venv\Scripts\python.exe" -c "import json,os,pathlib; m=pathlib.Path(os.environ['MEDSAFE_TROCR_MODEL_DIR']); r=json.loads(pathlib.Path('runtime_data/ocr_model_smoke_test.json').read_text(encoding='utf-8')); ok=r.get('status')=='PASSED' and pathlib.Path(r.get('model','')).resolve()==m.resolve() and r.get('model_weight_bytes')==(m/'model.safetensors').stat().st_size; raise SystemExit(0 if ok else 1)" >nul 2>nul
  if not errorlevel 1 goto smoke_ready
)
echo Checking model initialization and real OCR on a synthetic image...
".venv\Scripts\python.exe" setup_and_verify_models.py --model-id "%MODEL_DEST%"
if errorlevel 1 (
  echo ERROR: Model verification failed. See runtime_data\ocr_model_smoke_test.json.
  goto failed
)
:smoke_ready

if not exist "runtime_data\optional_ocr_ready.txt" (
  echo Downloading and initializing the other optional readers...
  ".venv\Scripts\python.exe" -c "from medsafe.ocr_product import _easy_reader, _paddle_reader; _easy_reader(); _paddle_reader(); print('EasyOCR and PaddleOCR ready')"
  if errorlevel 1 goto failed
  ".venv\Scripts\python.exe" -c "from pathlib import Path; p=Path('runtime_data/optional_ocr_ready.txt'); p.parent.mkdir(exist_ok=True); p.write_text('Ready',encoding='utf-8')"
  if errorlevel 1 goto failed
)

echo Installing and building the web interface...
pushd frontend
if errorlevel 1 goto failed
call npm ci --no-audit --no-fund
if errorlevel 1 (
  popd
  goto failed
)
call npm run build
if errorlevel 1 (
  popd
  goto failed
)
popd

echo.
echo Setup and model checks passed.
if defined SETUP_ONLY (
  set "EXIT_CODE=0"
  goto done
)
echo Open http://127.0.0.1:8000 after the server starts.
echo Press CTRL+C to stop it.
echo.
netstat -ano | findstr /R /C:"127.0.0.1:8000 .*LISTENING" >nul 2>nul
if not errorlevel 1 (
  echo The application is already running on http://127.0.0.1:8000.
  echo Reuse the open browser page, or stop the existing server before running this file again.
  set "EXIT_CODE=0"
  goto done
)
".venv\Scripts\python.exe" -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
set "EXIT_CODE=%errorlevel%"
goto done

:find_python
set "PYTHON_EXE="
set "PYTHON_ARGS="
py -3.13 -c "import sys" >nul 2>nul
if not errorlevel 1 (
  set "PYTHON_EXE=py"
  set "PYTHON_ARGS=-3.13"
  exit /b 0
)
py -3.12 -c "import sys" >nul 2>nul
if not errorlevel 1 (
  set "PYTHON_EXE=py"
  set "PYTHON_ARGS=-3.12"
  exit /b 0
)
py -3.11 -c "import sys" >nul 2>nul
if not errorlevel 1 (
  set "PYTHON_EXE=py"
  set "PYTHON_ARGS=-3.11"
  exit /b 0
)
if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" set "PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
exit /b 0

:verify_checkpoint
".venv\Scripts\python.exe" -c "import hashlib,os; from pathlib import Path; from medsafe.trocr import checkpoint_status; s=checkpoint_status(); p=Path(os.environ['MEDSAFE_TROCR_MODEL_DIR'])/'model.safetensors'; digest=hashlib.file_digest(p.open('rb'),'sha256').hexdigest() if s['ready_for_load'] else ''; ok=s['ready_for_load'] and digest==os.environ['EXPECTED_MODEL_SHA256']; print('Research checkpoint verified:',ok); print('Reason:',s.get('reason') or ('Wrong checkpoint SHA-256' if not ok else 'none')); raise SystemExit(0 if ok else 1)"
exit /b %errorlevel%

:failed
echo.
echo Setup stopped before launching the app. Resolve the error above and
echo run this same file again; completed downloads will be reused.
set "EXIT_CODE=1"
:done
if not defined SETUP_ONLY pause
exit /b %EXIT_CODE%
