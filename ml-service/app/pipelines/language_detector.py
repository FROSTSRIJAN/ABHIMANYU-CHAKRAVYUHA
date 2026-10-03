import re

SUPPORTED_LANGUAGES = {"en": "English", "hi": "Hindi", "bn": "Bengali", "pa": "Punjabi", "ta": "Tamil", "te": "Telugu"}
SUPPORT_STATUS = {"SUPPORTED", "LIMITED", "UNKNOWN", "UNSUPPORTED"}

_LATIN_LANGUAGE_MARKERS = {
    "es": {"el", "la", "los", "las", "producto", "cuesta", "para", "que", "empresa", "regulador", "ingresos", "aumentaron", "mercado", "lluvia", "llegara", "subio", "llegará", "subió", "lanzara", "lanzará"},
    "fr": {"le", "la", "les", "produit", "coûte", "coute", "marche", "augmente", "pour", "que"},
}
_ENGLISH_MARKERS = {"the", "a", "an", "is", "are", "was", "were", "may", "might", "will", "could", "not", "has", "have", "to", "in", "on", "today", "tomorrow", "company", "product", "market", "rose", "revenue", "increased", "by", "launch", "costs", "regulator", "approve", "filing", "expand"}
_SCRIPT_RANGES = (
    ("hi", r"[\u0900-\u097F]"),
    ("ta", r"[\u0B80-\u0BFF]"),
    ("te", r"[\u0C00-\u0C7F]"),
    ("bn", r"[\u0980-\u09FF]"),
    ("pa", r"[\u0A00-\u0A7F]"),
)

def detect_language(text: str) -> str:
    assessment = assess_language(text)
    return assessment["language_code"]


def assess_language(text: str) -> dict:
    """Return conservative language metadata without claiming calibrated confidence."""
    stripped = text.strip()
    if not stripped:
        return {
            "language_code": "unknown",
            "language_name": "Unknown",
            "detector_method": "empty_input",
            "support_status": "UNKNOWN",
            "confidence_type": "unknown",
            "limitations": ["No language-bearing text was provided."],
        }

    script_text = re.sub(r"[\W\d_]", "", stripped, flags=re.UNICODE)
    script_matches = [code for code, pattern in _SCRIPT_RANGES if re.search(pattern, script_text)]
    latin_words = set(re.findall(r"[A-Za-zÀ-ÿ]+", stripped.lower()))
    if len(script_matches) > 1 or (script_matches and latin_words):
        return {
            "language_code": "unknown",
            "language_name": "Unknown",
            "detector_method": "mixed_script",
            "support_status": "UNKNOWN",
            "confidence_type": "heuristic",
            "limitations": ["Mixed-script text was not assigned a language for mutation rules."],
        }
    if script_matches:
        code = script_matches[0]
        return {
            "language_code": code,
            "language_name": SUPPORTED_LANGUAGES[code],
            "detector_method": "unicode_script",
            "support_status": "LIMITED",
            "confidence_type": "script_based",
            "limitations": ["Script detection is not full language identification; English-only linguistic rules are disabled."],
        }
    if not latin_words:
        return {
            "language_code": "unknown",
            "language_name": "Unknown",
            "detector_method": "no_language_tokens",
            "support_status": "UNKNOWN",
            "confidence_type": "unknown",
            "limitations": ["The input contains no language-bearing tokens."],
        }
    marker_matches = {code: len(latin_words & markers) for code, markers in _LATIN_LANGUAGE_MARKERS.items()}
    if marker_matches and max(marker_matches.values()) >= 2:
        code = max(marker_matches, key=marker_matches.get)
        return {
            "language_code": code,
            "language_name": {"es": "Spanish", "fr": "French"}[code],
            "detector_method": "limited_latin_marker_heuristic",
            "support_status": "UNSUPPORTED",
            "confidence_type": "heuristic",
            "limitations": ["The language was recognized but has no supported mutation lexicon."],
        }
    if latin_words & _ENGLISH_MARKERS:
        return {
            "language_code": "en",
            "language_name": "English",
            "detector_method": "latin_default",
            "support_status": "SUPPORTED",
            "confidence_type": "heuristic",
            "limitations": ["Latin-script detection cannot reliably distinguish every language; English behavior is intended for English inputs."],
        }
    return {
        "language_code": "unknown",
        "language_name": "Unknown",
        "detector_method": "unrecognized_latin",
        "support_status": "UNSUPPORTED",
        "confidence_type": "unknown",
        "limitations": ["Latin-script language was not identified as English or a supported language."],
    }
