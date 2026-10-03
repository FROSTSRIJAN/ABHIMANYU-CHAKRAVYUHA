from app.pipelines.preprocessing import normalize, split_sentences

def test_normalize_and_split():
    assert normalize("  one   two ") == "one two"
    assert split_sentences("One. Two!") == ["One.", "Two!"]
