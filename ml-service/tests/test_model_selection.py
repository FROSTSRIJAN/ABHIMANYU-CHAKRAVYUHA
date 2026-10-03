from pathlib import Path

from app.services import model_manager


def _fresh_manager():
    model_manager.ModelManager._instance = None
    return model_manager.ModelManager()


def test_missing_configured_checkpoint_uses_explicit_failed_state(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(model_manager, "ENABLE_TRANSFORMERS", True)
    monkeypatch.setattr(model_manager, "EMBEDDING_MODEL_PATH", str(tmp_path / "missing"))
    manager = _fresh_manager()

    assert manager.embedding_model() is None
    state = next(item for item in manager.models() if item["component"] == "embedding")
    assert state["initialization_status"] == "failed"
    assert state["fallback_active"] is True
    assert "does not exist" in state["limitation"]


def test_default_model_selection_remains_disabled(monkeypatch):
    monkeypatch.setattr(model_manager, "ENABLE_TRANSFORMERS", False)
    monkeypatch.setattr(model_manager, "EMBEDDING_MODEL_PATH", "")
    manager = _fresh_manager()

    assert manager.embedding_model() is None
    state = next(item for item in manager.models() if item["component"] == "embedding")
    assert state["initialization_status"] == "disabled"
    assert state["fallback_active"] is True
