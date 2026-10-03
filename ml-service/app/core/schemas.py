from typing import Literal
from pydantic import BaseModel, Field, field_validator

VerificationLabel = Literal["SUPPORTED", "REFUTED", "INSUFFICIENT_EVIDENCE", "CONFLICTING"]

class AnalyzeRequest(BaseModel):
    messages: list[str] = Field(min_length=1, max_length=20)
    evidence: list["EvidenceRecord"] | None = None
    @field_validator("messages")
    @classmethod
    def validate_messages(cls, value: list[str]) -> list[str]:
        if any(not message.strip() for message in value):
            raise ValueError("messages must not contain empty strings")
        return value

class CompareRequest(BaseModel):
    first: str = Field(min_length=1)
    second: str = Field(min_length=1)
    @field_validator("first", "second")
    @classmethod
    def validate_claim_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("claim text must not be blank")
        return value

class VerifyRequest(BaseModel):
    claim: str = Field(min_length=1)
    evidence: list["EvidenceRecord"] | None = None
    @field_validator("claim")
    @classmethod
    def validate_claim(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("claim must not be blank")
        return value

class EvidenceRecord(BaseModel):
    document_id: str
    passage: str = Field(min_length=1)
    source_name: str
    source_type: Literal["provided", "demonstration"] | None = None
    source_url: str | None = None
    publication_date: str | None = None
    text: str | None = None
    provenance_verified: bool = True
    @field_validator("passage", "source_name", "document_id")
    @classmethod
    def validate_metadata_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("evidence text fields must not be blank")
        return value

class EvidenceResult(EvidenceRecord):
    retrieval_score: float = Field(ge=0, le=1)
    stance: Literal["SUPPORTS", "REFUTES", "UNKNOWN"]
    retrieval_method: str = "lexical_fallback"
    nli_scores: dict[str, float] | None = None

class MutationAnalysis(BaseModel):
    certainty_escalation: bool
    urgency_escalation: bool
    investment_persuasion: bool
    added_claims: list[str]
    removed_qualifiers: list[str]
    explanation: list[str]
    certainty_change: Literal["INCREASED", "DECREASED", "UNCHANGED", "AMBIGUOUS"] = "UNCHANGED"
    urgency_change: Literal["INCREASED", "DECREASED", "UNCHANGED", "AMBIGUOUS"] = "UNCHANGED"
    persuasion_indicators: list[str] = []
    changed_attributes: list[dict] = []
    supporting_spans: list[str] = []
    confidence: str = "unknown"
    confidence_type: Literal["heuristic", "model", "unknown"] = "heuristic"
    limitations: list[str] = []
    comparison_status: Literal["RELATED", "DISTINCT", "UNKNOWN", "ABSTAIN"] = "UNKNOWN"
    abstention_reason: str | None = None
    language_original: str | None = None
    language_modified: str | None = None
    alignment_status: Literal["ALIGNED", "RELATED_BUT_UNALIGNED", "DISTINCT", "UNKNOWN", "ABSTAIN"] = "UNKNOWN"
    alignment_method: str | None = None
    language_pair: str | None = None

class VerificationResult(BaseModel):
    label: VerificationLabel
    evidence: list[EvidenceResult]
    limitations: list[str]
    method: Literal["model", "rule_based_fallback", "unavailable"] = "rule_based_fallback"
    explanation: dict | None = None

class Uncertainty(BaseModel):
    level: Literal["low", "medium", "high"]
    reason: str

class AnalysisResponse(BaseModel):
    status: Literal["success"] = "success"
    language: str
    claims: list[str]
    semantic_similarity: float | None
    mutation_analysis: MutationAnalysis
    verification: VerificationResult
    uncertainty: Uncertainty
    explanation: dict | None = None
    support_status: str | None = None

class SequenceRequest(BaseModel):
    messages: list[str] = Field(min_length=2, max_length=20)
    @field_validator("messages")
    @classmethod
    def validate_sequence(cls, value: list[str]) -> list[str]:
        if any(not message.strip() for message in value):
            raise ValueError("messages must not contain empty strings")
        return value

class GraphRequest(BaseModel):
    messages: list[str] = Field(min_length=1, max_length=20)
    evidence: list[EvidenceRecord] | None = None
    @field_validator("messages")
    @classmethod
    def validate_graph_messages(cls, value: list[str]) -> list[str]:
        if any(not message.strip() for message in value):
            raise ValueError("messages must not contain empty strings")
        return value
