from app.pipelines.embedding_engine import similarity
from app.pipelines.language_detector import assess_language
from app.services.model_manager import ModelManager
from app.services.groq_provider import interpret_claim_pair

def analyze_similarity(first: str, second: str) -> dict:
    state = next(model for model in ModelManager().models() if model["component"] == "embedding")
    first_language = assess_language(first)
    second_language = assess_language(second)
    cross_language = first_language["language_code"] != second_language["language_code"]
    model_available = state["loaded"]
    score = similarity(first, second)
    if cross_language and not model_available:
        groq = interpret_claim_pair(first, second)
        relationship = "ABSTAIN"
        comparison_status = "ABSTAIN"
        reason = "Cross-language semantic alignment requires the optional multilingual embedding model."
        if groq["status"] == "ready":
            reason = "Groq interpretation is advisory only; local structured alignment remains unavailable."
            groq_metadata = groq
        else:
            groq_metadata = None
    elif first_language["support_status"] in {"UNKNOWN", "UNSUPPORTED"} or second_language["support_status"] in {"UNKNOWN", "UNSUPPORTED"}:
        relationship = "UNKNOWN"
        comparison_status = "UNKNOWN"
        reason = "At least one language is not supported for deterministic semantic comparison."
    else:
        relationship = "RELATED" if score >= 0.35 else "DISTINCT"
        comparison_status = relationship
        reason = None
    limitations = [state["limitation"]] if state["limitation"] else []
    if reason:
        limitations.append(reason)
    return {
        "similarity": score,
        "semantic_relationship": relationship,
        "comparison_status": comparison_status,
        "language_original": first_language,
        "language_modified": second_language,
        "model": state["name"] if state["loaded"] else "lexical-mvp",
        "method": "transformer_embedding" if state["loaded"] else "lexical_fallback",
        "limitations": limitations,
        "abstention_reason": reason,
        "provider_metadata": groq_metadata if cross_language and not model_available else None,
    }

def compare_claims(first: str, second: str) -> float:
    """Backward-compatible scalar similarity used by the original API."""
    return analyze_similarity(first, second)["similarity"]
