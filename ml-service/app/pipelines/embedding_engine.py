import math
import re
from collections import Counter

from app.services.model_manager import ModelManager

def _tokens(text: str) -> Counter[str]:
    return Counter(re.findall(r"\w+", text.lower(), flags=re.UNICODE))

def _lexical_similarity(first: str, second: str) -> float:
    left, right = _tokens(first), _tokens(second)
    if not left or not right:
        return 0.0
    common = set(left) & set(right)
    numerator = sum(left[token] * right[token] for token in common)
    denominator = math.sqrt(sum(value * value for value in left.values()) * sum(value * value for value in right.values()))
    return round(numerator / denominator, 4) if denominator else 0.0

def similarity(first: str, second: str) -> float:
    model = ModelManager().embedding_model()
    if model is None:
        return _lexical_similarity(first, second)
    vectors = model.encode([first, second], normalize_embeddings=True)
    return round(float(vectors[0] @ vectors[1]), 4)
