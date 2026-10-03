import re

from app.core.config import EVIDENCE_MAX_CANDIDATES, EVIDENCE_RELEVANCE_THRESHOLD
from app.core.schemas import EvidenceResult
from app.pipelines.evidence_retriever import EvidenceCandidate, retrieve
from app.services.model_manager import ModelManager

NEGATION_MARKERS = ("not", "no", "never", "cannot", "can't", "without")
UNCERTAINTY_MARKERS = ("may", "might", "could", "possibly", "unclear", "uncertain")
CLAUSE_BOUNDARIES = re.compile(r",|;|\bbut\b|\bhowever\b|\balthough\b|\bwhile\b", re.IGNORECASE)
QUALIFIER_TOKENS = re.compile(
    r"\b(?:today|tomorrow|yesterday|next|last|this|week|month|year|"
    r"january|february|march|april|may|june|july|august|september|"
    r"october|november|december|\d+(?:\.\d+)?)\b",
    re.IGNORECASE,
)


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"\w+", text.lower()))


def _has_negation(text: str) -> bool:
    lowered = text.lower()
    return any(re.search(rf"\b{re.escape(marker)}\b", lowered) for marker in NEGATION_MARKERS)


def _relevant_clause(claim: str, passage: str) -> str:
    claim_words = _tokens(claim)
    clauses = [clause.strip() for clause in CLAUSE_BOUNDARIES.split(passage) if clause.strip()]
    if not clauses:
        return passage
    return max(enumerate(clauses), key=lambda item: (len(claim_words & _tokens(item[1])), -item[0]))[1]


def _proposition_stance(claim: str, passage: str) -> str:
    clause = _relevant_clause(claim, passage)
    claim_qualifiers = {item.lower() for item in QUALIFIER_TOKENS.findall(claim)}
    clause_qualifiers = {item.lower() for item in QUALIFIER_TOKENS.findall(clause)}
    if claim_qualifiers and clause_qualifiers and claim_qualifiers.isdisjoint(clause_qualifiers):
        return "UNKNOWN"
    if not (_has_negation(clause) or _has_negation(claim)):
        return "SUPPORTS"
    if any(re.search(rf"\b{re.escape(marker)}\b", clause.lower()) for marker in UNCERTAINTY_MARKERS):
        return "UNKNOWN"
    if _has_negation(claim) == _has_negation(clause):
        return "SUPPORTS"
    return "REFUTES"


def _fallback_stance(claim: str, passage: str, candidate: EvidenceCandidate) -> str:
    if candidate.relevance_status != "relevant":
        return "UNKNOWN"
    claim_words = _tokens(claim)
    passage_words = _tokens(passage)
    shared_words = claim_words & passage_words
    if len(shared_words) < (2 if _has_negation(passage) else 3):
        return "UNKNOWN"
    return _proposition_stance(claim, passage)


def _nli_stance(nli, passage: str, claim: str) -> tuple[str, dict[str, float]]:
    raw = nli(f"{passage} </s> {claim}", top_k=None)
    items = raw if isinstance(raw, list) else [raw]
    scores: dict[str, float] = {}
    for item in items:
        label = str(item.get("label", "")).upper()
        scores[label] = round(float(item.get("score", 0.0)), 4)
    if not scores:
        return "UNKNOWN", scores
    top_label = max(scores, key=scores.get)
    top_score = scores[top_label]
    if top_score < 0.75:
        return "UNKNOWN", scores
    return {
        "ENTAILMENT": "SUPPORTS",
        "CONTRADICTION": "REFUTES",
        "NEUTRAL": "UNKNOWN",
        "LABEL_0": "SUPPORTS",
        "LABEL_1": "UNKNOWN",
        "LABEL_2": "REFUTES",
    }.get(top_label, "UNKNOWN"), scores


def verify_claim(claim: str, records):
    matches: list[EvidenceResult] = []
    has_unverified_provided = False
    nli = ModelManager().nli_model()
    method = "model" if nli is not None else "rule_based_fallback"
    for candidate in retrieve(claim, records, limit=EVIDENCE_MAX_CANDIDATES):
        passage = candidate.record.text or candidate.record.passage
        if candidate.record.source_type is None and candidate.source_type == "provided":
            has_unverified_provided = True
        stance = (
            "UNKNOWN"
            if candidate.source_type == "demonstration" or not candidate.record.provenance_verified
            else _fallback_stance(claim, passage, candidate)
        )
        nli_scores = None
        if (
            nli is not None
            and candidate.relevance_status == "relevant"
            and candidate.source_type != "demonstration"
            and candidate.record.provenance_verified
        ):
            try:
                stance, nli_scores = _nli_stance(nli, passage, claim)
            except (KeyError, TypeError, ValueError, RuntimeError):
                stance = "UNKNOWN"
                nli_scores = None
        evidence_data = candidate.record.model_dump()
        evidence_data["source_type"] = candidate.source_type
        matches.append(EvidenceResult(
            **evidence_data,
            retrieval_score=candidate.retrieval_score,
            stance=stance,
            retrieval_method=candidate.retrieval_method,
            nli_scores=nli_scores,
        ))
    stances = {item.stance for item in matches}
    if "SUPPORTS" in stances and "REFUTES" in stances:
        label = "CONFLICTING"
    elif "REFUTES" in stances:
        label = "REFUTED"
    elif "SUPPORTS" in stances:
        label = "SUPPORTED"
    else:
        label = "INSUFFICIENT_EVIDENCE"
    limitations = []
    if nli is None:
        limitations.append("NLI model is unavailable; lexical retrieval and rules are a conservative fallback, not calibrated probabilities.")
    if not matches:
        limitations.append("No candidate evidence was retrieved.")
    elif label == "INSUFFICIENT_EVIDENCE":
        limitations.append(f"No evidence exceeded the relevance threshold ({EVIDENCE_RELEVANCE_THRESHOLD:.2f}) with a supporting or contradictory relationship.")
    if any(item.source_type == "demonstration" for item in matches):
        limitations.append("Demonstration evidence is illustrative and is not authoritative external factual evidence.")
    if has_unverified_provided:
        limitations.append("Provided evidence provenance was not independently verified.")
    if any(not item.provenance_verified for item in matches):
        limitations.append("Caller-supplied evidence is non-authoritative until verified against a trusted evidence store.")
    explanation = {
        "verdict": label,
        "evidence_used": [item.document_id for item in matches if item.stance != "UNKNOWN"],
        "relevance": [{"document_id": item.document_id, "score": item.retrieval_score, "status": "relevant" if item.retrieval_score >= EVIDENCE_RELEVANCE_THRESHOLD else "weak"} for item in matches],
        "uncertainty": "high" if label in {"INSUFFICIENT_EVIDENCE", "CONFLICTING"} else "medium",
        "abstention_reason": "Evidence was absent, weak, neutral, or conflicting." if label in {"INSUFFICIENT_EVIDENCE", "CONFLICTING"} else None,
        "authoritative": False,
    }
    return {"label": label, "evidence": matches, "limitations": limitations, "method": method, "explanation": explanation}
