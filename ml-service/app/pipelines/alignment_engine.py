from app.pipelines.language_detector import assess_language
from app.pipelines.semantic_analyzer import analyze_similarity

ALIGNMENT_STATES = {"ALIGNED", "RELATED_BUT_UNALIGNED", "DISTINCT", "UNKNOWN", "ABSTAIN"}
SUPPORTED_ALIGNMENT_PAIRS = {("en", "hi"), ("hi", "en"), ("en", "es"), ("es", "en")}


def align_claims(source: str, target: str, semantic_result: dict | None = None) -> dict:
    """Assess claim alignment separately from semantic similarity."""
    source_language = assess_language(source)
    target_language = assess_language(target)
    semantic = semantic_result or analyze_similarity(source, target)
    source_code = source_language["language_code"]
    target_code = target_language["language_code"]
    language_pair = f"{source_code}-{target_code}"
    cross_language = source_code != target_code

    if source_code == "unknown" or target_code == "unknown":
        status = "UNKNOWN"
        reason = "A claim language could not be identified."
    elif cross_language and (source_code, target_code) not in SUPPORTED_ALIGNMENT_PAIRS:
        status = "ABSTAIN"
        reason = "This language pair is outside the Stage 6.1B alignment scope."
    elif cross_language and semantic["method"] != "transformer_embedding":
        status = "ABSTAIN"
        reason = "Cross-language alignment requires the optional multilingual embedding model."
    elif (
        source_language["support_status"] == "UNSUPPORTED"
        or target_language["support_status"] == "UNSUPPORTED"
    ) and (source_code, target_code) != ("en", "es") and (source_code, target_code) != ("es", "en"):
        status = "ABSTAIN"
        reason = "Semantic alignment may be attempted, but structured mutation extraction is unavailable for this language."
    elif semantic["similarity"] >= 0.75:
        status = "ALIGNED"
        reason = None
    elif semantic["similarity"] >= 0.35:
        status = "RELATED_BUT_UNALIGNED"
        reason = "The claims appear related, but the conservative alignment threshold was not met."
    else:
        status = "DISTINCT"
        reason = None

    limitations = list(semantic.get("limitations", []))
    if reason and reason not in limitations:
        limitations.append(reason)
    return {
        "alignment_status": status,
        "alignment_method": semantic["method"],
        "semantic_similarity": semantic["similarity"],
        "language_pair": language_pair,
        "source_language": source_language,
        "target_language": target_language,
        "confidence_type": "heuristic" if semantic["method"] == "lexical_fallback" else "model",
        "limitations": limitations,
        "abstention_reason": reason,
    }
