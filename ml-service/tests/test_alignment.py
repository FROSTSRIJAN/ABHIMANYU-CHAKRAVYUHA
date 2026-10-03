from app.pipelines.alignment_engine import align_claims
from app.pipelines.claim_normalizer import extract_claims
from app.pipelines.mutation_detector import compare_claim_versions


def test_english_paraphrase_is_aligned_without_mutation():
    result = align_claims(
        "The company may announce a new product.",
        "The company might reveal a new product.",
        {"similarity": 0.86, "method": "lexical_fallback", "limitations": []},
    )
    assert result["alignment_status"] == "ALIGNED"
    assert result["language_pair"] == "en-en"


def test_cross_language_fallback_abstains():
    result = align_claims(
        "The company may announce a new product.",
        "कंपनी एक नया उत्पाद घोषित कर सकती है।",
        {"similarity": 0.0, "method": "lexical_fallback", "limitations": []},
    )
    assert result["alignment_status"] == "ABSTAIN"
    assert result["language_pair"] == "en-hi"


def test_mocked_english_hindi_alignment_can_compare_numbers():
    source = extract_claims(["The product costs 500 rupees."])[0]
    target = extract_claims(["उत्पाद की कीमत 600 रुपये है।"])[0]
    result = compare_claim_versions(source, target)
    assert result["mutation_types"] == []

    mocked = {
        "similarity": 0.88,
        "method": "transformer_embedding",
        "limitations": [],
        "comparison_status": "RELATED",
    }
    aligned = align_claims(source["normalized_text"], target["normalized_text"], mocked)
    assert aligned["alignment_status"] == "ALIGNED"
    assert aligned["language_pair"] == "en-hi"


def test_cross_language_model_alignment_does_not_infer_missing_certainty():
    source = extract_claims(["The company may announce a new product."])[0]
    target = extract_claims(["कंपनी निश्चित रूप से एक नया उत्पाद घोषित करेगी।"])[0]
    mocked = {
        "similarity": 0.9,
        "method": "transformer_embedding",
        "limitations": [],
        "comparison_status": "RELATED",
    }
    aligned = align_claims(source["normalized_text"], target["normalized_text"], mocked)
    assert aligned["alignment_status"] == "ALIGNED"
    result = compare_claim_versions(source, target)
    assert result["mutation_types"] == []


def test_unsupported_language_is_explicitly_abstained():
    result = align_claims(
        "The product costs 500 rupees.",
        "Le produit coûte 500 roupies.",
        {"similarity": 0.8, "method": "transformer_embedding", "limitations": []},
    )
    assert result["alignment_status"] == "ABSTAIN"


def test_mocked_model_can_attempt_english_spanish_alignment_without_structured_mutation():
    result = align_claims(
        "The product costs 500 rupees.",
        "El producto cuesta 500 rupias.",
        {"similarity": 0.9, "method": "transformer_embedding", "limitations": []},
    )
    assert result["alignment_status"] == "ALIGNED"
    assert result["language_pair"] == "en-es"


def test_similarity_does_not_directly_create_mutation():
    source = extract_claims(["The company may announce a new product."])[0]
    target = extract_claims(["The company might announce a new product."])[0]
    result = compare_claim_versions(source, target)
    assert "NUMERICAL_MUTATION" not in result["mutation_types"]
    assert result["alignment_status"] in {"ALIGNED", "RELATED_BUT_UNALIGNED"}


def test_mocked_cross_language_certainty_and_numeric_mutations_are_positive():
    semantic = {"similarity": 0.9, "method": "transformer_embedding", "limitations": [], "comparison_status": "RELATED"}
    certainty = compare_claim_versions(
        extract_claims(["The company may announce a product."])[0],
        extract_claims(["कंपनी निश्चित रूप से एक उत्पाद घोषित करेगी।"])[0],
        semantic,
    )
    numeric = compare_claim_versions(
        extract_claims(["The product costs 500 rupees."])[0],
        extract_claims(["El producto cuesta 600 rupias."])[0],
        semantic,
    )
    assert "CERTAINTY_ESCALATION" in certainty["mutation_types"]
    assert "NUMERICAL_MUTATION" in numeric["mutation_types"]


def test_mocked_cross_language_negation_and_date_mutations_are_positive():
    semantic = {"similarity": 0.9, "method": "transformer_embedding", "limitations": [], "comparison_status": "RELATED"}
    negation = compare_claim_versions(
        extract_claims(["The market rose today."])[0],
        extract_claims(["El mercado no subio."])[0],
        semantic,
    )
    dates = compare_claim_versions(
        extract_claims(["The launch is on 01/06/2025."])[0],
        extract_claims(["लॉन्च 02/06/2025 को है।"])[0],
        semantic,
    )
    assert "NEGATION_MUTATION" in negation["mutation_types"]
    assert "TEMPORAL_MUTATION" in dates["mutation_types"]


def test_mocked_alignment_does_not_create_mutation_when_attributes_are_missing():
    result = compare_claim_versions(
        extract_claims(["The company may expand."])[0],
        extract_claims(["कंपनी विस्तार कर सकती है।"])[0],
        {"similarity": 0.9, "method": "transformer_embedding", "limitations": [], "comparison_status": "RELATED"},
    )
    assert result["mutation_types"] == []
