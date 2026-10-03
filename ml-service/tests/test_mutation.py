from app.pipelines.mutation_detector import analyze_mutation

def test_certainty_and_urgency_escalate():
    result = analyze_mutation(["The company may announce news.", "The company will definitely announce news. Buy now."])
    assert result["certainty_escalation"]
    assert result["investment_persuasion"]

def test_qualifier_removal_is_reported():
    result = analyze_mutation(["The result may change.", "The result will change."])
    assert "may" in result["removed_qualifiers"]

def test_certainty_reduction_is_reported():
    result = analyze_mutation(["The result will happen.", "The result may happen."])
    assert result["certainty_change"] == "DECREASED"
