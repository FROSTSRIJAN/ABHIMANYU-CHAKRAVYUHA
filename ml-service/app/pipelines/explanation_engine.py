def uncertainty_for(verification: dict, mutation: dict) -> dict:
    if verification["label"] in {"INSUFFICIENT_EVIDENCE", "CONFLICTING"}:
        return {"level": "high", "reason": "Evidence is missing or conflicting."}
    if mutation["certainty_escalation"] or mutation["urgency_escalation"]:
        return {"level": "medium", "reason": "The result includes rule-based mutation indicators that require human review."}
    return {"level": "medium", "reason": "The result is based on a small local corpus and a lexical MVP verifier."}
