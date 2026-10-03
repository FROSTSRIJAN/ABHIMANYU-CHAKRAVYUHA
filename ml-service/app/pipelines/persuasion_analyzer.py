from app.pipelines.mutation_detector import PERSUASION

def detect_persuasion(text: str) -> bool:
    lowered = text.lower()
    return any(term in lowered for term in PERSUASION)
