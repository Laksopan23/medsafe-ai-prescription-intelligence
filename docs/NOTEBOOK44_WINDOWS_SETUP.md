# Notebook 44 model: Windows setup and troubleshooting

The CRAFT + TrOCR comparison engine requires the **actual Notebook 44 fine-tuned checkpoint**, which is **not in GitHub**. Its absence is why the app shows "Notebook 44 fine-tuned TrOCR checkpoint is missing or incomplete". This setup does not train, synthesize, or silently replace the model.

## One-time Windows setup

1. From your Google Drive MedSafe_AI_Project, find `02_models/trocr_finetuned_official_source_dev_notebook44/943e9bd2b5f1a54d/best_model_DEVELOPMENT_ONLY`.
2. Download the **complete** `best_model_DEVELOPMENT_ONLY` directory, including `model.safetensors` (~1.3 GB), `config.json`, `tokenizer.json`, `tokenizer_config.json`, `processor_config.json`, `preprocessor_config.json` and other assets. Check the files are fully downloaded, not Google Drive shortcuts.
3. Copy it into the repository at `02_models/trocr_notebook44/best_model_DEVELOPMENT_ONLY`. Alternatively leave it anywhere on disk.
4. Double-click `setup_notebook44_windows.bat`. If it asks for a path, paste the **folder** containing the model files. The script creates or reuses the app's `.venv`, installs OCR dependencies, and performs actual CRAFT + TrOCR smoke-test inference. First run may download CRAFT detector weights.
5. If the verification passes, accept the prompt to launch MedSafe-AI in the **same window**, preserving `MEDSAFE_TROCR_MODEL_DIR`. Re-run the four-engine comparison.
6. Check `runtime_data/ocr_model_smoke_test.json` for the exact result. The checkpoint is development-only; loading it does not prove thesis accuracy or clinical safety.

## Command-line alternative

In PowerShell, from the repository root:

```powershell
$env:MEDSAFE_TROCR_MODEL_DIR = "D:\\path\\to\\best_model_DEVELOPMENT_ONLY"
.\.venv\Scripts\python.exe -m pip install -r requirements-ocr.txt
.\.venv\Scripts\python.exe setup_and_verify_models.py --model-id "$env:MEDSAFE_TROCR_MODEL_DIR"
.\start_windows.bat
```

The app now also searches the standard in-repository folder when the environment variable is absent. An explicitly set environment variable takes priority; if it points to an incomplete folder, the app reports that error rather than silently loading different weights.

## Troubleshooting

- **Missing/incomplete**: inspect the reported missing filenames; ensure the folder is the checkpoint itself, not its parent.
- **Dependency error**: run the installer from the repository root; check available disk space and Python version.
- **CRAFT download failure**: first-run detector weights need internet access; re-run with connectivity.
- **Memory/CPU slowness**: the checkpoint is large and may be slow on CPU; no latency claim can be made without a timed inference run.
- **Model loads but no text regions**: use a readable sample image and inspect the proposed CRAFT boxes. A successful model load is not evidence of prescription-level accuracy.
- **Model still unavailable after setup**: restart the server from the same terminal session; `setlocal` environment variables do not persist after the setup window closes.

No model weights, secrets or patient prescriptions are committed by this change.
