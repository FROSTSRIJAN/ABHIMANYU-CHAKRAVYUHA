"""Opt-in integration checks for downloaded transformer models.

Run separately with:
ENABLE_TRANSFORMERS=true ENABLE_NLI=true python -m pytest -m integration -q
"""
import os
import pytest

pytestmark = pytest.mark.integration

if os.getenv("ENABLE_TRANSFORMERS", "").lower() != "true" or os.getenv("ENABLE_NLI", "").lower() != "true":
    pytestmark = [pytest.mark.integration, pytest.mark.skip(reason="Set ENABLE_TRANSFORMERS=true and ENABLE_NLI=true.")]

def test_real_embedding_and_nli_models():
    from app.services.model_manager import ModelManager
    from app.pipelines.embedding_engine import similarity
    from app.pipelines.verifier import verify_claim
    from app.core.schemas import EvidenceRecord

    manager = ModelManager()
    assert manager.embedding_model() is not None
    assert manager.nli_model() is not None
    assert similarity("A product launches next month.", "A product is expected next month.") > 0.5
    result = verify_claim(
        "The product launches next month.",
        [EvidenceRecord(document_id="integration", passage="The product launches next month.", source_name="integration")],
    )
    assert result["method"] == "model"
    assert result["evidence"][0].nli_scores
