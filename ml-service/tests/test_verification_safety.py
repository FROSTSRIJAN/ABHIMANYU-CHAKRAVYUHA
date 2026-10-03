from app.core.schemas import EvidenceRecord
from app.pipelines.verifier import verify_claim

def test_unsupported_acquisition_claim_is_not_refuted_by_demo_overlap():
    evidence = [EvidenceRecord(
        document_id="demo",
        passage="A company announcement may be scheduled for next month, but an announcement is not a guarantee of a share-price increase.",
        source_name="Demo evidence corpus",
    )]
    result = verify_claim("The company secretly plans to acquire another company tomorrow.", evidence)
    assert result["label"] == "INSUFFICIENT_EVIDENCE"

def test_generic_overlap_is_insufficient():
    evidence = [EvidenceRecord(document_id="unrelated", passage="The company reported a new office.", source_name="test")]
    result = verify_claim("The company plans to acquire another company tomorrow.", evidence)
    assert result["label"] == "INSUFFICIENT_EVIDENCE"

def test_relevant_supporting_evidence_is_supported():
    evidence = [EvidenceRecord(document_id="support", passage="Acme launched a new application in June 2026.", source_name="test")]
    result = verify_claim("Acme launched a new application in June 2026.", evidence)
    assert result["label"] == "SUPPORTED"

def test_relevant_contradictory_evidence_is_refuted():
    evidence = [EvidenceRecord(document_id="refute", passage="Acme did not launch a new application in June 2026.", source_name="test")]
    result = verify_claim("Acme launched a new application in June 2026.", evidence)
    assert result["label"] == "REFUTED"

def test_empty_evidence_is_insufficient():
    assert verify_claim("A claim with no evidence.", [])["label"] == "INSUFFICIENT_EVIDENCE"

def test_irrelevant_evidence_is_abstained_with_relevance_metadata():
    result = verify_claim(
        "The company plans to acquire a satellite operator tomorrow.",
        [EvidenceRecord(document_id="weak", passage="The company reported quarterly revenue.", source_name="test")],
    )
    assert result["label"] == "INSUFFICIENT_EVIDENCE"
    assert result["explanation"]["abstention_reason"]
    assert result["explanation"]["relevance"][0]["status"] == "weak"

def test_demo_evidence_is_not_presented_as_authoritative():
    result = verify_claim(
        "A company announcement is scheduled next month.",
        [EvidenceRecord(document_id="demo", passage="A company announcement may be scheduled next month.", source_name="Demo evidence corpus")],
    )
    assert any("not authoritative" in limitation for limitation in result["limitations"])
    assert result["label"] == "INSUFFICIENT_EVIDENCE"

def test_explicit_demo_evidence_is_ineligible_for_decision():
    result = verify_claim(
        "The market rose today.",
        [EvidenceRecord(document_id="demo", passage="The market rose today.", source_name="Corpus", source_type="demonstration")],
    )
    assert result["label"] == "INSUFFICIENT_EVIDENCE"

def test_demo_evidence_does_not_override_provided_evidence():
    result = verify_claim(
        "The market rose today.",
        [
            EvidenceRecord(document_id="demo", passage="The market rose today.", source_name="Corpus", source_type="demonstration"),
            EvidenceRecord(document_id="provided", passage="The market did not rise today.", source_name="review", source_type="provided"),
        ],
    )
    assert result["label"] == "REFUTED"

def test_today_claim_ignores_future_qualifier_negation():
    result = verify_claim(
        "The market rose today.",
        [EvidenceRecord(document_id="future", passage="The market rose today but this passage does not establish whether tomorrow will rise.", source_name="review", source_type="provided")],
    )
    assert result["label"] == "SUPPORTED"

def test_direct_contradiction_is_refuted():
    result = verify_claim(
        "The market rose today.",
        [EvidenceRecord(document_id="refute", passage="The market did not rise today.", source_name="review", source_type="provided")],
    )
    assert result["label"] == "REFUTED"

def test_ambiguous_negation_abstains():
    result = verify_claim(
        "The market rose today.",
        [EvidenceRecord(document_id="uncertain", passage="The market may not have risen today.", source_name="review", source_type="provided")],
    )
    assert result["label"] == "INSUFFICIENT_EVIDENCE"

def test_direct_support_with_unrelated_negated_clause_is_supported():
    result = verify_claim(
        "Revenue increased by 5% in 2025.",
        [EvidenceRecord(document_id="support", passage="Revenue increased by 5% in 2025, but the report does not establish growth in 2026.", source_name="review", source_type="provided")],
    )
    assert result["label"] == "SUPPORTED"

def test_different_date_negation_abstains():
    result = verify_claim(
        "Revenue increased in 2025.",
        [EvidenceRecord(document_id="different-date", passage="Revenue did not increase in 2024.", source_name="review", source_type="provided")],
    )
    assert result["label"] == "INSUFFICIENT_EVIDENCE"

def test_different_numeric_qualifier_negation_abstains():
    result = verify_claim(
        "The product sold 500 units.",
        [EvidenceRecord(document_id="different-number", passage="The product did not sell 600 units.", source_name="review", source_type="provided")],
    )
    assert result["label"] == "INSUFFICIENT_EVIDENCE"

def test_multiple_evidence_conflict_is_explicit():
    records = [
        EvidenceRecord(document_id="support", passage="Acme launched a new application in June 2026.", source_name="verified-test"),
        EvidenceRecord(document_id="refute", passage="Acme did not launch a new application in June 2026.", source_name="verified-test"),
    ]
    result = verify_claim("Acme launched a new application in June 2026.", records)
    assert result["label"] == "CONFLICTING"
    assert result["explanation"]["abstention_reason"]

def test_evidence_result_includes_structured_explanation():
    result = verify_claim("Acme launched a new application in June 2026.", [
        EvidenceRecord(document_id="support", passage="Acme launched a new application in June 2026.", source_name="test")
    ])
    assert result["explanation"]["verdict"] == "SUPPORTED"
    assert result["explanation"]["evidence_used"] == ["support"]

def test_optional_nli_mapping_is_used_when_available(monkeypatch):
    class FakeNli:
        def __call__(self, text, top_k=None):
            return [
                {"label": "entailment", "score": 0.91},
                {"label": "neutral", "score": 0.06},
                {"label": "contradiction", "score": 0.03},
            ]
    monkeypatch.setattr("app.pipelines.verifier.ModelManager.nli_model", lambda self: FakeNli())
    result = verify_claim("Acme launched a new application in June 2026.", [
        EvidenceRecord(document_id="support", passage="Acme launched a new application in June 2026.", source_name="test")
    ])
    assert result["method"] == "model"
    assert result["label"] == "SUPPORTED"
    assert result["evidence"][0].nli_scores["ENTAILMENT"] == 0.91
