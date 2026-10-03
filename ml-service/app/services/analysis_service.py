from app.core.config import EVIDENCE_PATH
from app.core.schemas import AnalysisResponse
from app.pipelines.claim_extractor import extract_claims
from app.pipelines.evidence_retriever import load_evidence
from app.pipelines.explanation_engine import uncertainty_for
from app.pipelines.language_detector import assess_language, detect_language
from app.pipelines.mutation_detector import analyze_mutation
from app.pipelines.semantic_analyzer import analyze_similarity
from app.pipelines.verifier import verify_claim

def evidence_or_default(evidence):
    if evidence is None:
        return load_evidence(EVIDENCE_PATH)
    return [item.model_copy(update={"provenance_verified": False}) for item in evidence]

def analyze(messages: list[str], evidence=None) -> AnalysisResponse:
    claims = [claim for message in messages for claim in extract_claims(message)]
    mutation = analyze_mutation(messages)
    verification = verify_claim(claims[-1] if claims else messages[-1], evidence_or_default(evidence))
    semantic = analyze_similarity(messages[0], messages[-1]) if len(messages) > 1 else None
    language_metadata = detect_language(messages[-1])
    language_info = assess_language(messages[-1])
    return AnalysisResponse(language=language_metadata, support_status=language_info["support_status"], claims=claims, semantic_similarity=semantic["similarity"] if semantic else None, mutation_analysis=mutation, verification=verification, uncertainty=uncertainty_for(verification, mutation), explanation={"summary": " ".join(mutation["explanation"]), "observations": mutation["explanation"], "evidence_summary": [item.passage for item in verification["evidence"]], "verification_status": verification["label"], "limitations": verification["limitations"] + mutation.get("limitations", []), "human_review_recommended": verification["label"] in {"CONFLICTING", "INSUFFICIENT_EVIDENCE"}})
