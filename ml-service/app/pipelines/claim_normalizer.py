import re
from dataclasses import asdict, dataclass

from app.pipelines.language_detector import assess_language, detect_language
from app.pipelines.preprocessing import split_sentences

QUALIFIERS = ("may", "might", "could", "possibly", "potentially", "expected", "likely", "allegedly", "reportedly")
CONDITIONALS = ("if ", "unless ", "provided that", "subject to", "when ")
NEGATIONS = ("not", "no", "never", "cannot", "can't", "without")
MONTHS = (
    "january", "february", "march", "april", "may", "june",
    "july", "august", "september", "october", "november", "december",
)
WEEKDAYS = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")
TEMPORAL_WORDS = {"today", "tomorrow", "yesterday", "next", "month", "quarter", "year", "week"}
MONTH_PATTERN = r"(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)"
DATE_PATTERN = re.compile(
    rf"\b(?:today|tomorrow|yesterday|next\s+(?:month|quarter|year|week|friday)|"
    rf"(?:{'|'.join(WEEKDAYS)})(?:\s+\d{{4}})?|{MONTH_PATTERN}(?:\s+\d{{4}})?|\d{{1,2}}[/-]\d{{1,2}}[/-]\d{{2,4}})\b",
    re.I,
)
CONTEXTUAL_MONTH_PATTERN = re.compile(
    r"\b(?:in|for|on|during)\s+(may)(?:\s+\d{4})?\b", re.I
)
CONTEXTUAL_YEAR_PATTERN = re.compile(r"\b(?:in|during|since|until|by|fiscal year|year)\s+(\d{4})\b", re.I)
NUMBER_PATTERN = re.compile(r"(?<!\w)(?:(?:[$€£₹]|Rs\.?|INR)\s*\d[\d,]*(?:\.\d+)?|\d[\d,]*(?:\.\d+)?\s?(?:%|percent|percentage)?)(?!\w)", re.I)
STRUCTURED_NUMBER_PATTERN = re.compile(
    r"(?<!\w)(?P<currency>[$€£₹]|Rs\.?|INR)\s*(?P<value>\d[\d,]*(?:\.\d+)?)\s*(?P<percent>%|percent|percentage)?|(?<!\w)(?P<plain>\d[\d,]*(?:\.\d+)?)\s*(?P<plain_percent>%|percent|percentage)?",
    re.I,
)
ENTITY_PATTERN = re.compile(r"\b(?:[A-Z][\w&.-]*\s+){0,3}[A-Z][\w&.-]*\b")
LOCATION_CONTEXT = re.compile(r"\b(?:in|at|near|from|to|of)\s+(?P<location>[A-Z][\w.-]*)\b")

@dataclass
class Claim:
    claim_id: str
    original_text: str
    normalized_text: str
    source_message_id: str
    entities: list[str]
    numbers: list[str]
    dates: list[str]
    qualifiers: list[str]
    language: str
    negated: bool
    conditional: bool
    numeric_attributes: list[dict]
    temporal_attributes: list[dict]
    entity_attributes: list[dict]
    negation_scope: str

    def as_dict(self) -> dict:
        return asdict(self)

def normalize_claim(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip()).strip(" \t")


def _numeric_attributes(text: str) -> list[dict]:
    attributes = []
    for match in STRUCTURED_NUMBER_PATTERN.finditer(text):
        raw = match.group(0).strip()
        if not raw or not re.search(r"\d", raw):
            continue
        value_text = match.group("value") or match.group("plain")
        percent_text = match.group("percent") or match.group("plain_percent")
        value = float(value_text.replace(",", ""))
        numeric_type = "percentage" if percent_text else "number"
        currency = match.group("currency")
        currency_map = {"₹": "INR", "Rs": "INR", "Rs.": "INR", "INR": "INR", "$": "USD", "€": "EUR", "£": "GBP"}
        if currency:
            currency = currency_map.get(currency, currency.upper())
        attributes.append({
            "raw_text": raw,
            "normalized_value": int(value) if value.is_integer() else value,
            "currency": currency,
            "unit": "%" if numeric_type == "percentage" else None,
            "numeric_type": numeric_type,
            "source_span": [match.start(), match.end()],
            "normalization_method": "deterministic_numeric_pattern",
        })
    return attributes


def _temporal_attributes(text: str, dates: list[str]) -> list[dict]:
    attributes = []
    for date in dates:
        start = text.lower().find(date.lower())
        granularity = "year" if re.fullmatch(r"\d{4}", date) else (
            "month" if date.lower() in MONTHS or re.match(r"^[a-z]{3,9}(?:\s+\d{4})?$", date, re.I) else "relative"
        )
        if date.lower() in {"today", "tomorrow", "yesterday"} or date.lower().startswith("next "):
            granularity = "relative"
        attributes.append({
            "raw_text": date,
            "normalized_form": date.lower(),
            "granularity": granularity,
            "temporal_type": "absolute" if granularity in {"year", "month"} else "relative",
            "source_span": [start, start + len(date)] if start >= 0 else None,
            "normalization_method": "deterministic_temporal_pattern",
        })
    return attributes

def extract_claims(messages: list[str]) -> list[dict]:
    claims: list[dict] = []
    for message_index, message in enumerate(messages, start=1):
        message_id = f"message_{message_index:03d}"
        for sentence in split_sentences(message):
            normalized = normalize_claim(sentence)
            if not normalized or normalized.endswith("?"):
                continue
            lowered = normalized.lower()
            language_info = assess_language(normalized)
            english_rules = language_info["language_code"] == "en" and language_info["support_status"] == "SUPPORTED"
            qualifiers = [term for term in QUALIFIERS if re.search(rf"\b{re.escape(term)}\b", lowered)] if english_rules else []
            dates = DATE_PATTERN.findall(normalized)
            dates = [item.lower() if isinstance(item, str) else item[0].lower() for item in dates]
            dates.extend(match.group(1).lower() for match in CONTEXTUAL_MONTH_PATTERN.finditer(normalized))
            dates.extend(match.group(1).lower() for match in CONTEXTUAL_YEAR_PATTERN.finditer(normalized))
            dates = list(dict.fromkeys(dates))
            numbers = NUMBER_PATTERN.findall(normalized)
            numbers = [number for number in numbers if not any(number in date for date in dates)]
            numeric_attributes = _numeric_attributes(normalized)
            temporal_attributes = _temporal_attributes(normalized, dates)
            entities = []
            for match in ENTITY_PATTERN.findall(normalized) if english_rules else []:
                if (
                    match not in entities
                    and match.lower() not in {"the", "a", "an"}
                    and match.lower() not in MONTHS
                    and match.lower() not in WEEKDAYS
                    and match.lower() not in TEMPORAL_WORDS
                    and match.lower() not in {"rs", "inr"}
                    and not any(match.lower() == date.lower() for date in dates)
                ):
                    entities.append(match)
            claim = Claim(
                claim_id=f"claim_{len(claims) + 1:03d}",
                original_text=sentence,
                normalized_text=normalized,
                source_message_id=message_id,
                entities=entities,
                numbers=numbers,
                dates=dates,
                qualifiers=qualifiers + (["conditional"] if any(token in lowered for token in CONDITIONALS) else []),
                language=detect_language(normalized),
                negated=any(re.search(rf"\b{re.escape(token)}\b", lowered) for token in NEGATIONS) if english_rules else False,
                conditional=any(token in lowered for token in CONDITIONALS) if english_rules else False,
                numeric_attributes=numeric_attributes,
                temporal_attributes=temporal_attributes,
                entity_attributes=[
                    {
                        "raw_text": entity,
                        "entity_type": "location" if any(match.group("location") == entity for match in LOCATION_CONTEXT.finditer(normalized)) else "unknown",
                        "source_span": [normalized.find(entity), normalized.find(entity) + len(entity)],
                        "normalization_method": "capitalization_and_context_heuristic",
                    }
                    for entity in entities
                ],
                negation_scope="sentence" if english_rules and any(re.search(rf"\b{re.escape(token)}\b", lowered) for token in NEGATIONS) else "none",
            )
            claim_data = claim.as_dict()
            claim_data["language_metadata"] = language_info
            if not english_rules:
                claim_data["negated"] = False
                claim_data["negation_scope"] = "unknown"
            claims.append(claim_data)
    return claims
