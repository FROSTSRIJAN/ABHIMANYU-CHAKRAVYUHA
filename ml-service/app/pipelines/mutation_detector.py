import re
from app.pipelines.preprocessing import normalize
from app.pipelines.semantic_analyzer import analyze_similarity
from app.pipelines.language_detector import assess_language
from app.pipelines.alignment_engine import align_claims

CERTAINTY = ("may", "might", "could", "possibly", "expected", "likely", "will", "definitely", "guaranteed")
URGENCY = ("buy now", "buy immediately", "immediately", "act now", "before it is too late", "limited time", "last opportunity")
PERSUASION = ("buy now", "buy immediately", "sell now", "sell immediately", "guaranteed", "guarantee", "risk-free", "risk free", "double your money", "limited opportunity")
QUALIFIERS = ("may", "might", "could", "possibly", "expected", "likely", "if", "subject to", "alleged")
CERTAINTY_LEVELS = {
    "may": 1, "might": 1, "could": 1, "possibly": 1,
    "expected": 2, "likely": 2,
    "will": 3, "definitely": 4, "guaranteed": 4,
}
MULTILINGUAL_CERTAINTY = {
    "hi": {
        "may": (("कर सकती", "कर सकता", "कर सकते", "शायद"), 1),
        "likely": (("संभावित", "उम्मीद", "अपेक्षित"), 2),
        "definitely": (("निश्चित रूप से", "जरूर", "अवश्य"), 4),
    },
    "es": {
        "may": (("puede", "podría", "quizás"), 1),
        "likely": (("probablemente", "se espera"), 2),
        "will": (("lanzara", "lanzará", "será", "sera"), 3),
        "definitely": (("definitivamente", "sin duda"), 4),
    },
}
MULTILINGUAL_NEGATIONS = {
    "hi": ("नहीं", "कभी नहीं"),
    "es": ("no", "nunca", "sin"),
}

def _present(text: str, terms: tuple[str, ...]) -> bool:
    lowered = normalize(text).lower()
    return any(term in lowered for term in terms)

def analyze_mutation(messages: list[str]) -> dict:
    original_info = assess_language(messages[0]) if messages else assess_language("")
    modified_info = assess_language(messages[-1]) if messages else assess_language("")
    language_safe = (
        len(messages) >= 2
        and original_info["support_status"] == "SUPPORTED"
        and modified_info["support_status"] == "SUPPORTED"
        and original_info["language_code"] == modified_info["language_code"]
    )
    if len(messages) < 2:
        indicators = [term for term in PERSUASION if _present(messages[0], (term,))]
        return {"certainty_escalation": False, "urgency_escalation": False, "investment_persuasion": bool(indicators), "added_claims": [], "removed_qualifiers": [], "explanation": ["At least two messages are required to measure propagation changes."], "certainty_change": "UNCHANGED", "urgency_change": "UNCHANGED", "persuasion_indicators": indicators, "changed_attributes": [], "supporting_spans": [], "confidence": "unknown", "confidence_type": "heuristic", "limitations": ["Rule-based comparison is not calibrated."], "comparison_status": "UNKNOWN", "abstention_reason": None, "language_original": original_info["language_code"], "language_modified": modified_info["language_code"]}
    if not language_safe:
        reason = "Deterministic English mutation rules are disabled because language support or language alignment is insufficient."
        return {
            "certainty_escalation": False, "urgency_escalation": False,
            "investment_persuasion": False, "added_claims": [], "removed_qualifiers": [],
            "explanation": [reason], "certainty_change": "AMBIGUOUS", "urgency_change": "AMBIGUOUS",
            "persuasion_indicators": [], "changed_attributes": [], "supporting_spans": [],
            "confidence": "unknown", "confidence_type": "heuristic",
            "limitations": [reason], "comparison_status": "ABSTAIN",
            "abstention_reason": reason,
            "language_original": original_info["language_code"],
            "language_modified": modified_info["language_code"],
        }
    first, latest = messages[0], messages[-1]
    first_rank = max((CERTAINTY.index(term) for term in CERTAINTY if _present(first, (term,))), default=-1)
    latest_rank = max((CERTAINTY.index(term) for term in CERTAINTY if _present(latest, (term,))), default=-1)
    removed = [term for term in QUALIFIERS if _present(first, (term,)) and not _present(latest, (term,))]
    added = []
    first_words = set(re.findall(r"\b[\w'-]{4,}\b", first.lower()))
    for sentence in messages[1:]:
        new_words = [word for word in re.findall(r"\b[\w'-]{4,}\b", sentence.lower()) if word not in first_words]
        if new_words:
            added.append(sentence)
    explanations = []
    if latest_rank > first_rank:
        explanations.append("The latest message uses stronger certainty language than the first message.")
    first_urgency = _present(first, URGENCY)
    latest_urgency = _present(latest, URGENCY)
    if latest_urgency and not first_urgency:
        explanations.append("Urgency language appears in a later message.")
    if removed:
        explanations.append("Earlier qualifications are absent from the latest message.")
    if _present(latest, PERSUASION):
        explanations.append("Investment-persuasion indicators are present; these are language signals, not proof of fraud.")
    if not explanations:
        explanations.append("No rule-based escalation signal was detected.")
    certainty_change = "INCREASED" if latest_rank > first_rank else "DECREASED" if latest_rank < first_rank else "UNCHANGED"
    urgency_change = "INCREASED" if latest_urgency and not first_urgency else "DECREASED" if first_urgency and not latest_urgency else "UNCHANGED"
    indicators = [term for term in PERSUASION if _present(latest, (term,))]
    return {"certainty_escalation": certainty_change == "INCREASED", "urgency_escalation": urgency_change == "INCREASED", "investment_persuasion": bool(indicators), "added_claims": added, "removed_qualifiers": removed, "explanation": explanations, "certainty_change": certainty_change, "urgency_change": urgency_change, "persuasion_indicators": indicators, "changed_attributes": [], "supporting_spans": [], "confidence": "heuristic", "confidence_type": "heuristic", "limitations": ["Rule-based comparison is not calibrated."], "comparison_status": "RELATED", "abstention_reason": None, "language_original": original_info["language_code"], "language_modified": modified_info["language_code"]}

def _rank(text: str, terms: tuple[str, ...]) -> int:
    return max((terms.index(term) for term in terms if _present(text, (term,))), default=-1)


def _negation_comparison(source: dict, target: dict) -> tuple[bool, str]:
    if source["negated"] == target["negated"]:
        return False, "none"
    source_words = set(re.findall(r"\b[\w'-]{3,}\b", source["normalized_text"].lower()))
    target_words = set(re.findall(r"\b[\w'-]{3,}\b", target["normalized_text"].lower()))
    if len(source_words & target_words) < 2:
        return False, "ambiguous"
    negation_clauses = re.split(r",|;|\bbut\b|\bhowever\b|\balthough\b|\bwhile\b", target["normalized_text"], flags=re.IGNORECASE)
    for clause in negation_clauses:
        if any(re.search(rf"\b{re.escape(marker)}\b", clause.lower()) for marker in ("not", "no", "never", "cannot", "can't", "without")):
            if len(source_words & set(re.findall(r"\b[\w'-]{3,}\b", clause.lower()))) < 2:
                return False, "ambiguous"
    if any(term in target["normalized_text"].lower() for term in ("may not", "might not", "could not", "possibly not")):
        return False, "ambiguous"
    return True, "direct"


def _numeric_signature(claim: dict) -> list[tuple]:
    return [
        (item.get("normalized_value"), item.get("currency"), item.get("unit"), item.get("numeric_type"))
        for item in claim.get("numeric_attributes", [])
    ]

def _certainty_for_claim(text: str, language: str) -> tuple[int | None, list[str]]:
    if language == "en":
        terms = [term for term in CERTAINTY_LEVELS if _present(text, (term,))]
        return max((CERTAINTY_LEVELS[term] for term in terms), default=None), terms
    found: list[str] = []
    levels = MULTILINGUAL_CERTAINTY.get(language, {})
    for label, (terms, level) in levels.items():
        if any(term in text.lower() for term in terms):
            found.append(label)
    return max((levels[label][1] for label in found), default=None), found


def _negated_for_claim(claim: dict, language: str) -> bool | None:
    if language == "en":
        return claim["negated"]
    markers = MULTILINGUAL_NEGATIONS.get(language)
    if markers is None:
        return None
    lowered = claim["normalized_text"].lower()
    return any(marker in lowered for marker in markers)


def compare_claim_versions(source: dict, target: dict, semantic_result: dict | None = None) -> dict:
    source_text = source["normalized_text"]
    target_text = target["normalized_text"]
    similarity = semantic_result or analyze_similarity(source_text, target_text)
    alignment = align_claims(source_text, target_text, similarity)
    source_language = source.get("language_metadata") or assess_language(source_text)
    target_language = target.get("language_metadata") or assess_language(target_text)
    cross_language = source_language["language_code"] != target_language["language_code"]
    if (
        alignment["alignment_status"] in {"ABSTAIN", "UNKNOWN"}
        or (cross_language and alignment["alignment_status"] != "ALIGNED")
        or alignment["alignment_status"] != "ALIGNED" and cross_language
    ):
        reason = alignment.get("abstention_reason") or "Structured mutation comparison is unavailable for unsupported or insufficiently aligned languages."
        return {
            "mutation_types": [], "source_claim": source, "target_claim": target,
            "supporting_spans": [], "changed_attributes": [], "confidence": "unknown",
            "confidence_type": "heuristic", "semantic_similarity": similarity["similarity"],
            "detection_method": similarity["method"], "limitations": alignment["limitations"],
            "relationship": "UNKNOWN", "comparison_status": similarity["comparison_status"],
            "abstention_reason": reason, "language_original": source_language["language_code"],
            "language_modified": target_language["language_code"], "alignment_status": alignment["alignment_status"],
            "alignment_method": alignment["alignment_method"], "language_pair": alignment["language_pair"],
            "explanation": [reason],
        }
    mutation_types: list[str] = []
    spans: list[str] = []
    changed_attributes: list[dict] = []
    source_certainty, source_certainty_terms = _certainty_for_claim(source_text, source_language["language_code"])
    target_certainty, target_certainty_terms = _certainty_for_claim(target_text, target_language["language_code"])
    semantically_comparable = similarity["similarity"] >= 0.65
    if source_certainty is not None and target_certainty is not None and target_certainty > source_certainty:
        mutation_types.append("CERTAINTY_ESCALATION")
        spans.extend(target_certainty_terms)
    elif source_certainty is not None and target_certainty is not None and target_certainty < source_certainty:
        if similarity["similarity"] < 0.35:
            target_certainty = source_certainty
        else:
            mutation_types.append("CERTAINTY_REDUCTION")
            spans.extend(source_certainty_terms)
    elif source_certainty is not None and target_certainty is None and semantically_comparable:
        mutation_types.append("CERTAINTY_ESCALATION")
        spans.extend(source_certainty_terms)
    if source["qualifiers"] and not target["qualifiers"] and semantically_comparable and not cross_language:
        mutation_types.append("QUALIFIER_REMOVAL")
        spans.extend(source["qualifiers"])
    source_urgency = _present(source_text, URGENCY)
    target_urgency = _present(target_text, URGENCY)
    if target_urgency and not source_urgency:
        mutation_types.append("URGENCY_ESCALATION")
        spans.extend(term for term in URGENCY if _present(target_text, (term,)))
    elif source_urgency and not target_urgency:
        mutation_types.append("URGENCY_REDUCTION")
    source_numeric = _numeric_signature(source)
    target_numeric = _numeric_signature(target)
    date_change = source["dates"] != target["dates"] and bool(source["dates"] or target["dates"])
    if source_numeric != target_numeric and (source_numeric or target_numeric) and not (cross_language and date_change):
        mutation_types.append("NUMERICAL_MUTATION")
        spans.extend(target["numbers"])
        changed_attributes.append({"category": "NUMERICAL_MUTATION", "original": source.get("numeric_attributes", []), "modified": target.get("numeric_attributes", []), "method": "deterministic_numeric_extraction", "confidence": "high", "confidence_type": "heuristic"})
    if (
        source["entities"] != target["entities"]
        and (source["entities"] or target["entities"])
        and not cross_language
    ):
        mutation_types.append("ENTITY_MUTATION")
        spans.extend(target["entities"])
        source_types = {item["entity_type"] for item in source.get("entity_attributes", [])}
        target_types = {item["entity_type"] for item in target.get("entity_attributes", [])}
        changed_attributes.append({"category": "ENTITY_MUTATION", "original": source["entities"], "modified": target["entities"], "entity_type": "location" if source_types == {"location"} and target_types == {"location"} else "unknown", "method": "deterministic_entity_extraction", "confidence": "medium", "confidence_type": "heuristic"})
    if source["dates"] != target["dates"] and (source["dates"] or target["dates"]) and (
        not cross_language or (source["dates"] and target["dates"])
    ):
        mutation_types.append("TEMPORAL_MUTATION")
        spans.extend(target["dates"])
        changed_attributes.append({"category": "TEMPORAL_MUTATION", "original": source.get("temporal_attributes", []), "modified": target.get("temporal_attributes", []), "method": "deterministic_temporal_extraction", "confidence": "high", "confidence_type": "heuristic"})
    source_negated = _negated_for_claim(source, source_language["language_code"])
    target_negated = _negated_for_claim(target, target_language["language_code"])
    if source_negated is not None and target_negated is not None:
        if cross_language and alignment["alignment_status"] == "ALIGNED":
            negation_changed = source_negated != target_negated
            negation_scope = "aligned_language_model"
        else:
            negation_changed, negation_scope = _negation_comparison(
                {**source, "negated": source_negated},
                {**target, "negated": target_negated},
            )
    else:
        negation_changed, negation_scope = False, "unavailable"
    if negation_changed:
        mutation_types.append("NEGATION_MUTATION")
        spans.append("negation")
        changed_attributes.append({"category": "NEGATION_MUTATION", "original": source["negated"], "modified": target["negated"], "scope": negation_scope, "method": "deterministic_negation_comparison", "confidence": "medium", "confidence_type": "heuristic"})
    source_has_extra_clause = bool(re.search(r"\b(?:and|because|but|while|although)\b", source_text.lower()))
    target_has_extra_clause = bool(re.search(r"\b(?:and|because|but|while|although)\b", target_text.lower()))
    if target_has_extra_clause and not source_has_extra_clause:
        mutation_types.append("CLAIM_ADDITION")
    if source_has_extra_clause and not target_has_extra_clause:
        mutation_types.append("CLAIM_REMOVAL")
    if similarity["similarity"] < 0.35:
        mutation_types.append("SEMANTIC_DRIFT")
    if not mutation_types and source_text == target_text:
        relationship = "SAME_CLAIM"
    elif not mutation_types or similarity["similarity"] >= 0.75:
        relationship = "PARAPHRASE"
    elif "NEGATION_MUTATION" in mutation_types:
        relationship = "CONTRADICTION"
    else:
        relationship = "MODIFIED_CLAIM"
    result = {
        "mutation_types": list(dict.fromkeys(mutation_types)),
        "source_claim": source,
        "target_claim": target,
        "supporting_spans": list(dict.fromkeys(spans)),
        "changed_attributes": changed_attributes,
        "confidence": "high" if changed_attributes and all(item["confidence"] == "high" for item in changed_attributes) else "medium" if changed_attributes else "unknown",
        "confidence_type": "heuristic",
        "semantic_similarity": similarity["similarity"],
        "detection_method": similarity["method"],
        "limitations": similarity["limitations"] + ["Rule-based comparisons identify textual changes; they do not establish causation or intent."],
        "relationship": relationship,
        "comparison_status": similarity["comparison_status"],
        "abstention_reason": None,
        "language_original": source_language["language_code"],
        "language_modified": target_language["language_code"],
        "alignment_status": alignment["alignment_status"],
        "alignment_method": alignment["alignment_method"],
        "language_pair": alignment["language_pair"],
    }
    from app.pipelines.mutation_explainer import explain_mutation
    result["explanation"] = explain_mutation(result)
    return result
