from app.pipelines.claim_normalizer import extract_claims
from app.pipelines.mutation_detector import compare_claim_versions

def test_normalizer_preserves_qualifier_negation_and_metadata():
    claim = extract_claims(["Acme may grow 5% next quarter if demand improves."])[0]
    assert claim["qualifiers"] == ["may", "conditional"]
    assert claim["numbers"] == ["5%"]
    assert claim["dates"] == ["next quarter"]
    assert claim["conditional"] is True

def test_numerical_entity_temporal_and_negation_mutations():
    source = extract_claims(["Acme has not confirmed 5% growth next quarter."])[0]
    target = extract_claims(["Globex confirmed 25% growth tomorrow."])[0]
    result = compare_claim_versions(source, target)
    assert "NUMERICAL_MUTATION" in result["mutation_types"]
    assert "ENTITY_MUTATION" in result["mutation_types"]
    assert "TEMPORAL_MUTATION" in result["mutation_types"]
    assert "NEGATION_MUTATION" in result["mutation_types"]

def test_identical_claims_are_same_claim():
    claims = extract_claims(["The company may announce tomorrow.", "The company may announce tomorrow."])
    result = compare_claim_versions(claims[0], claims[1])
    assert result["relationship"] == "SAME_CLAIM"

def test_certainty_reduction_and_qualifier_removal():
    claims = extract_claims(["The company will announce.", "The company may announce."])
    result = compare_claim_versions(claims[0], claims[1])
    assert "CERTAINTY_REDUCTION" in result["mutation_types"]

def test_claim_graph_is_evidence_annotated():
    from app.pipelines.claim_graph import build_claim_graph
    graph = build_claim_graph(["The company may announce.", "The company will definitely announce."])
    assert len(graph["nodes"]) == 2
    assert len(graph["edges"]) == 1
    assert "verification_status" in graph["nodes"][0]
    assert graph["edges"][0]["source_claim_id"] != graph["edges"][0]["target_claim_id"]

def test_numeric_changes_do_not_become_temporal_mutations():
    for original, modified in [
        ("The product costs ₹500.", "The product costs ₹5000."),
        ("There are 10 users.", "There are 100 users."),
        ("The product costs 5000 rupees.", "The product costs 6000 rupees."),
    ]:
        result = compare_claim_versions(extract_claims([original])[0], extract_claims([modified])[0])
        assert "NUMERICAL_MUTATION" in result["mutation_types"]
        assert "TEMPORAL_MUTATION" not in result["mutation_types"]

def test_contextual_years_and_months_are_temporal():
    for original, modified in [
        ("The launch is scheduled for June.", "The launch is scheduled for December."),
        ("The launch is scheduled for Jan.", "The launch is scheduled for March."),
        ("The launch is scheduled for June 2026.", "The launch is scheduled for June 2027."),
        ("The launch is next week.", "The launch is next month."),
        ("The launch is tomorrow.", "The launch is next Friday."),
    ]:
        result = compare_claim_versions(extract_claims([original])[0], extract_claims([modified])[0])
        assert "TEMPORAL_MUTATION" in result["mutation_types"]
    year_claims = extract_claims(["Revenue increased in 2025.", "Revenue increased in 2026."])
    assert "TEMPORAL_MUTATION" in compare_claim_versions(*year_claims)["mutation_types"]

def test_equivalent_certainty_terms_do_not_create_directional_mutation():
    claims = extract_claims([
        "The regulator is likely to approve the filing.",
        "The regulator is expected to approve the filing.",
    ])
    assert not any(
        label in compare_claim_versions(*claims)["mutation_types"]
        for label in ("CERTAINTY_ESCALATION", "CERTAINTY_REDUCTION")
    )

def test_removed_qualifier_is_certainty_escalation_when_claim_is_comparable():
    claims = extract_claims([
        "The report may indicate a decline.",
        "The report indicates a decline.",
    ])
    result = compare_claim_versions(*claims)
    assert "CERTAINTY_ESCALATION" in result["mutation_types"]
    assert "QUALIFIER_REMOVAL" in result["mutation_types"]

def test_missing_certainty_term_is_not_directional_when_claim_changes():
    claims = extract_claims([
        "Investors may review the announcement.",
        "Investors should buy immediately after the announcement.",
    ])
    result = compare_claim_versions(*claims)
    assert "CERTAINTY_REDUCTION" not in result["mutation_types"]
    assert "QUALIFIER_REMOVAL" not in result["mutation_types"]

def test_semantic_drift_does_not_infer_certainty_direction():
    claims = extract_claims([
        "The treasury will publish a quarterly liquidity report.",
        "A coastal research group may relocate its laboratory before winter.",
    ])
    result = compare_claim_versions(*claims)
    assert result["mutation_types"] == ["SEMANTIC_DRIFT"]

def test_paraphrase_canonicalizes_temporal_text_and_ignores_sentence_initial_word():
    claims = extract_claims([
        "The company may announce a new product next month.",
        "Next month, the company might reveal a new product.",
    ])
    result = compare_claim_versions(*claims)
    assert result["mutation_types"] == []

def test_numeric_formatting_and_percent_equivalence_are_not_mutations():
    for original, modified in [
        ("The product costs 1,000 rupees.", "The product costs 1000 rupees."),
        ("Growth was 5%.", "Growth was 5 percent."),
    ]:
        result = compare_claim_versions(extract_claims([original])[0], extract_claims([modified])[0])
        assert "NUMERICAL_MUTATION" not in result["mutation_types"]

def test_currency_representation_is_equivalent_and_value_change_is_detected():
    equivalent = compare_claim_versions(
        extract_claims(["The product costs ₹500."])[0],
        extract_claims(["The product costs Rs. 500."])[0],
    )
    changed = compare_claim_versions(
        extract_claims(["The product costs ₹500."])[0],
        extract_claims(["The product costs ₹5000."])[0],
    )
    assert "NUMERICAL_MUTATION" not in equivalent["mutation_types"]
    assert "NUMERICAL_MUTATION" in changed["mutation_types"]

def test_location_substitution_has_conservative_location_metadata():
    result = compare_claim_versions(
        extract_claims(["The company opened an office in Delhi."])[0],
        extract_claims(["The company opened an office in Mumbai."])[0],
    )
    attribute = next(item for item in result["changed_attributes"] if item["category"] == "ENTITY_MUTATION")
    assert result["mutation_types"] == ["ENTITY_MUTATION"]
    assert attribute["entity_type"] == "location"

def test_negation_scope_abstains_for_modal_or_unrelated_negation():
    ambiguous = compare_claim_versions(
        extract_claims(["The market rose today."])[0],
        extract_claims(["The market may not have risen today."])[0],
    )
    unrelated = compare_claim_versions(
        extract_claims(["The market rose today."])[0],
        extract_claims(["The market rose today, but the report does not establish tomorrow's trend."])[0],
    )
    assert "NEGATION_MUTATION" not in ambiguous["mutation_types"]
    assert "NEGATION_MUTATION" not in unrelated["mutation_types"]

def test_structured_mutation_output_and_graph_edge_are_additive():
    claims = extract_claims(["The product costs ₹500.", "The product costs ₹5000."])
    result = compare_claim_versions(*claims)
    assert result["confidence_type"] == "heuristic"
    assert result["changed_attributes"][0]["category"] == "NUMERICAL_MUTATION"
    from app.pipelines.claim_graph import build_claim_graph
    edge = build_claim_graph(["The product costs ₹500.", "The product costs ₹5000."])["edges"][0]
    assert "changed_attributes" in edge
    assert "supporting_spans" in edge

def test_non_english_claims_abstain_from_english_mutation_rules():
    from app.pipelines.language_detector import assess_language
    hindi = extract_claims(["कंपनी एक नया उत्पाद घोषित कर सकती है।"])[0]
    assert hindi["language"] == "hi"
    assert hindi["language_metadata"]["support_status"] == "LIMITED"
    result = compare_claim_versions(
        extract_claims(["The company may announce a new product."])[0],
        hindi,
    )
    assert result["mutation_types"] == []
    assert result["comparison_status"] == "ABSTAIN"
    assert assess_language("El producto cuesta 500 rupias.")["support_status"] == "UNSUPPORTED"

def test_spanish_article_is_not_an_entity():
    claim = extract_claims(["El producto cuesta 500 rupias."])[0]
    assert "El" not in claim["entities"]
    assert claim["numbers"] == ["500"]

def test_language_assessment_handles_scripts_and_ambiguous_inputs():
    from app.pipelines.language_detector import assess_language
    assert assess_language("বাংলা ভাষা।")["language_code"] == "bn"
    assert assess_language("ਪੰਜਾਬੀ ਭਾਸ਼ਾ।")["language_code"] == "pa"
    assert assess_language("தமிழ் மொழி।")["language_code"] == "ta"
    assert assess_language("తెలుగు భాష।")["language_code"] == "te"
    assert assess_language("")["support_status"] == "UNKNOWN"
    assert assess_language("12345")["support_status"] == "UNKNOWN"
    assert assess_language("English कंपनी")["support_status"] == "UNKNOWN"
