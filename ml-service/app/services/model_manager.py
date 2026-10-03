from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.core.config import (
    ENABLE_NLI,
    ENABLE_TRANSFORMERS,
    EMBEDDING_MODEL_NAME,
    EMBEDDING_MODEL_PATH,
    MODEL_DEVICE,
    NLI_MODEL_NAME,
)

@dataclass
class ModelState:
    name: str
    component: str
    version: str
    loaded: bool = False
    device: str = MODEL_DEVICE
    fallback_active: bool = True
    initialization_status: str = "not_initialized"
    limitation: str | None = None
    instance: Any = None

class ModelManager:
    _instance: "ModelManager | None" = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._states = {
                "embedding": ModelState(EMBEDDING_MODEL_NAME, "embedding", "configured"),
                "nli": ModelState(NLI_MODEL_NAME, "nli", "configured"),
                "fallback": ModelState("lexical-mvp", "fallback", "0.2", loaded=True, fallback_active=True, initialization_status="ready", limitation="Lexical similarity and rules are not calibrated model probabilities."),
            }
        return cls._instance

    def _load_embedding(self) -> ModelState:
        state = self._states["embedding"]
        if state.initialization_status != "not_initialized":
            return state
        state.initialization_status = "disabled"
        state.limitation = "Transformer embeddings are disabled by default; set ENABLE_TRANSFORMERS=true and install sentence-transformers."
        if not ENABLE_TRANSFORMERS:
            return state
        try:
            from sentence_transformers import SentenceTransformer
            model_source = EMBEDDING_MODEL_PATH or state.name
            if EMBEDDING_MODEL_PATH and not Path(EMBEDDING_MODEL_PATH).is_dir():
                state.initialization_status = "failed"
                state.limitation = f"Configured embedding checkpoint does not exist: {EMBEDDING_MODEL_PATH}"
                return state
            state.instance = SentenceTransformer(
                model_source,
                device=state.device,
                local_files_only=bool(EMBEDDING_MODEL_PATH),
            )
            state.name = model_source
            state.version = "configured_checkpoint" if EMBEDDING_MODEL_PATH else "configured"
            state.loaded = True
            state.fallback_active = False
            state.initialization_status = "ready"
            state.limitation = None
        except (ImportError, OSError, RuntimeError, ValueError, TimeoutError, ConnectionError) as error:
            state.initialization_status = "failed"
            state.limitation = f"Embedding model unavailable: {error}"
        return state

    def _load_nli(self) -> ModelState:
        state = self._states["nli"]
        if state.initialization_status != "not_initialized":
            return state
        state.initialization_status = "disabled"
        state.limitation = "NLI is disabled by default; set ENABLE_NLI=true and install transformers and torch."
        if not ENABLE_NLI:
            return state
        try:
            from transformers import pipeline
            state.instance = pipeline("text-classification", model=state.name, device=0 if state.device != "cpu" else -1)
            state.loaded = True
            state.fallback_active = False
            state.initialization_status = "ready"
            state.limitation = None
        except (ImportError, OSError, RuntimeError, ValueError, TimeoutError, ConnectionError) as error:
            state.initialization_status = "failed"
            state.limitation = f"NLI model unavailable: {error}"
        return state

    def embedding_model(self):
        return self._load_embedding().instance

    def nli_model(self):
        return self._load_nli().instance

    def models(self) -> list[dict]:
        return [
            {key: value for key, value in state.__dict__.items() if key != "instance"}
            for state in (self._load_embedding(), self._load_nli(), self._states["fallback"])
        ]
