from app.pipelines.semantic_analyzer import compare_claims

def test_identical_claims_score_one():
    assert compare_claims("Markets open today", "Markets open today") == 1.0

def test_unrelated_claims_score_low():
    assert compare_claims("The moon is bright", "Stocks declined") < 0.5

def test_cross_language_fallback_is_explicitly_uncertain():
    from app.pipelines.semantic_analyzer import analyze_similarity
    result = analyze_similarity("The company may announce news.", "कंपनी समाचार घोषित कर सकती है।")
    assert result["comparison_status"] == "ABSTAIN"
    assert result["semantic_relationship"] == "ABSTAIN"
    assert result["method"] == "lexical_fallback"
