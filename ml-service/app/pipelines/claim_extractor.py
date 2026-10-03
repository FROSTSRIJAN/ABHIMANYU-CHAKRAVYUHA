from app.pipelines.preprocessing import split_sentences

def extract_claims(text: str) -> list[str]:
    """Extract statement-like sentences; this is a transparent MVP fallback."""
    return [sentence for sentence in split_sentences(text) if not sentence.endswith("?")]
