from app.core.schemas import EvidenceRecord
from app.pipelines.verifier import verify_claim

def test_missing_evidence_is_explicit():
    result = verify_claim("A completely unknown event occurred", [])
    assert result["label"] == "INSUFFICIENT_EVIDENCE"
    assert result["evidence"] == []

def test_conflicting_evidence_is_not_forced():
    records = [
        EvidenceRecord(document_id="a", passage="The market rose today.", source_name="A"),
        EvidenceRecord(document_id="b", passage="The market did not rise today.", source_name="B"),
    ]
    result = verify_claim("The market rose today.", records)
    assert result["label"] == "CONFLICTING"
