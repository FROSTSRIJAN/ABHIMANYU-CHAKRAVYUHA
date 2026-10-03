import json
import re
from dataclasses import dataclass
from pathlib import Path
from app.core.schemas import EvidenceRecord
from app.core.config import EVIDENCE_RELEVANCE_THRESHOLD

@dataclass(frozen=True)
class EvidenceCandidate:
    record: EvidenceRecord
    retrieval_score: float
    retrieval_method: str
    relevance_status: str
    source_type: str

def load_evidence(path: Path) -> list[EvidenceRecord]:
    with path.open(encoding="utf-8") as handle:
        return [EvidenceRecord.model_validate(item) for item in json.load(handle)]

def _tokens(text: str) -> set[str]:
    return set(re.findall(r"\w+", text.lower()))

def _lexical_candidates(claim: str, records: list[EvidenceRecord], limit: int):
    query = _tokens(claim)
    scored = []
    for record in records:
        words = _tokens(record.text or record.passage)
        score = len(query & words) / len(query) if query else 0.0
        if score > 0:
            source_type = record.source_type
            if source_type is None:
                source_type = "demonstration" if record.source_name.lower().startswith("demo") else "provided"
            relevance = "relevant" if score >= EVIDENCE_RELEVANCE_THRESHOLD else "weak"
            scored.append(EvidenceCandidate(record, round(score, 4), "lexical_fallback", relevance, source_type))
    return sorted(scored, key=lambda item: item.retrieval_score, reverse=True)[:limit]

def retrieve(claim: str, records: list[EvidenceRecord], limit: int = 5):
    """Unified retrieval contract; optional BM25/FAISS adapters can replace this stage."""
    return _lexical_candidates(claim, records, limit)
