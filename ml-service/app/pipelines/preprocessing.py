import re

def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())

def split_sentences(text: str) -> list[str]:
    normalized = normalize(text).replace("Rs.", "Rs")
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+", normalized) if part.strip()]
