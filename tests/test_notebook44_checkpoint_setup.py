"""Checkpoint discovery and missing-assets regression tests; no model weights needed."""
from pathlib import Path
from medsafe import trocr

def test_environment_path_has_priority(monkeypatch, tmp_path):
    path=tmp_path/"selected"
    path.mkdir()
    monkeypatch.setenv("MEDSAFE_TROCR_MODEL_DIR",str(path))
    monkeypatch.setattr(trocr,"_LOCAL_CHECKPOINTS",(tmp_path/"other",))
    assert trocr.configured_checkpoint()==path
    state=trocr.checkpoint_status()
    assert state["configured"] is True
    assert state["ready_for_load"] is False
    assert "model.safetensors" in state["missing_files"]
    assert "model.safetensors" in state["reason"]

def test_in_repository_checkpoint_autodiscovery(monkeypatch,tmp_path):
    path=tmp_path/"02_models"/"trocr_notebook44"/"best_model_DEVELOPMENT_ONLY"
    path.mkdir(parents=True)
    monkeypatch.delenv("MEDSAFE_TROCR_MODEL_DIR",raising=False)
    monkeypatch.setattr(trocr,"_LOCAL_CHECKPOINTS",(path,))
    assert trocr.configured_checkpoint()==path
    for filename in trocr._REQUIRED:
        (path/filename).write_text("test placeholder",encoding="utf-8")
    state=trocr.checkpoint_status()
    assert state["ready_for_load"] is True
    assert state["weights_verified_by_inference"] is False
    assert state["checkpoint_path"]==str(path)

def test_absent_checkpoint_is_unavailable(monkeypatch,tmp_path):
    monkeypatch.delenv("MEDSAFE_TROCR_MODEL_DIR",raising=False)
    monkeypatch.setattr(trocr,"_LOCAL_CHECKPOINTS",(tmp_path/"missing",))
    monkeypatch.setattr(trocr,"NOTEBOOK44_CHECKPOINT",str(tmp_path/"drive-missing"))
    state=trocr.checkpoint_status()
    assert state["ready_for_load"] is False
    assert "setup_notebook44_windows.bat" in state["reason"]
