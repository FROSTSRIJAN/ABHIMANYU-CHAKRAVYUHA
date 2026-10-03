"""Optional Groq semantic interpretation with strict, non-verifying output."""

from __future__ import annotations

import json
import time
from typing import Any

from app.core.config import GROQ_API_KEY, GROQ_ENABLED, GROQ_MAX_RETRIES, GROQ_MODEL, GROQ_TIMEOUT

ALLOWED_RELATIONSHIPS = {"ALIGNED", "RELATED_BUT_UNALIGNED", "DISTINCT", "UNKNOWN", "ABSTAIN"}
ALLOWED_MUTATIONS = {
    "CERTAINTY_ESCALATION",
    "CERTAINTY_REDUCTION",
    "NEGATION_MUTATION",
    "NUMERICAL_MUTATION",
    "TEMPORAL_MUTATION",
    "ENTITY_MUTATION",
}


def provider_status() -> dict[str, Any]:
    if not GROQ_ENABLED:
        return {"provider": "groq", "enabled": False, "available": False, "status": "disabled"}
    if not GROQ_API_KEY.strip():
        return {"provider": "groq", "enabled": True, "available": False, "status": "missing_api_key"}
    try:
        import openai  # noqa: F401
    except ImportError:
        return {"provider": "groq", "enabled": True, "available": False, "status": "missing_openai_dependency"}
    return {"provider": "groq", "enabled": True, "available": True, "status": "ready"}


def _validate(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("Provider response must be a JSON object.")
    relationship = payload.get("relationship", "UNKNOWN")
    if relationship not in ALLOWED_RELATIONSHIPS:
        raise ValueError("Provider returned an unsupported relationship.")
    mutations = payload.get("mutation_types", [])
    if not isinstance(mutations, list) or any(item not in ALLOWED_MUTATIONS for item in mutations):
        raise ValueError("Provider returned unsupported mutation types.")
    explanation = payload.get("explanation", "")
    if not isinstance(explanation, str) or not explanation.strip():
        raise ValueError("Provider explanation is missing.")
    return {
        "relationship": relationship,
        "mutation_types": mutations,
        "abstain": bool(payload.get("abstain", True)),
        "explanation": explanation.strip(),
        "confidence_type": "provider_heuristic",
        "provider": "groq",
        "provider_role": "semantic_interpretation_only",
        "factual_verification": "not_performed",
        "evidence": [],
    }


def interpret_claim_pair(first: str, second: str, client: Any = None) -> dict[str, Any]:
    """Return a validated interpretation, or an explicit unavailable result."""
    status = provider_status()
    if not status["available"]:
        return {
            **status,
            "relationship": "ABSTAIN",
            "mutation_types": [],
            "abstain": True,
            "explanation": "Groq semantic interpretation is unavailable.",
            "confidence_type": "unknown",
            "provider_role": "semantic_interpretation_only",
            "factual_verification": "not_performed",
            "evidence": [],
        }
    if client is None:
        from openai import OpenAI
        client = OpenAI(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1", timeout=GROQ_TIMEOUT, max_retries=0)
    messages = [
        {
            "role": "system",
            "content": (
                "Classify claim relationship only. Return JSON with relationship, mutation_types, "
                "abstain, explanation. relationship must be exactly one of "
                "ALIGNED, RELATED_BUT_UNALIGNED, DISTINCT, UNKNOWN, or ABSTAIN. "
                "mutation_types must contain only supported mutation labels or be empty. "
                "Do not verify facts. Do not create evidence, sources, URLs, citations, "
                "or factual verdicts. Use ABSTAIN when uncertain."
            ),
        },
        {"role": "user", "content": json.dumps({"original_claim": first, "modified_claim": second}, ensure_ascii=False)},
    ]
    last_error = "unknown provider failure"
    for attempt in range(GROQ_MAX_RETRIES + 1):
        try:
            response = client.chat.completions.create(
                model=GROQ_MODEL,
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0,
            )
            content = response.choices[0].message.content
            result = _validate(json.loads(content))
            return {**status, **result, "attempts": attempt + 1}
        except (ValueError, TypeError, KeyError, json.JSONDecodeError) as error:
            last_error = f"malformed provider response: {error}"
        except Exception as error:
            last_error = f"provider request failed: {type(error).__name__}"
        if attempt < GROQ_MAX_RETRIES:
            time.sleep(0.1 * (attempt + 1))
    return {
        **status,
        "status": "failed",
        "relationship": "ABSTAIN",
        "mutation_types": [],
        "abstain": True,
        "explanation": "Groq semantic interpretation failed; local safeguards remain authoritative.",
        "confidence_type": "unknown",
        "provider_role": "semantic_interpretation_only",
        "factual_verification": "not_performed",
        "evidence": [],
        "error": last_error,
    }
