import json

from app.services import groq_provider


class FakeCompletions:
    def __init__(self, content):
        self.content = content
        self.calls = 0

    def create(self, **kwargs):
        self.calls += 1
        return type(
            "Response",
            (),
            {"choices": [type("Choice", (), {"message": type("Message", (), {"content": self.content})()})()]},
        )()


class FakeClient:
    def __init__(self, content):
        self.chat = type("Chat", (), {"completions": FakeCompletions(content)})()


def test_groq_is_disabled_without_configuration(monkeypatch):
    monkeypatch.setattr(groq_provider, "GROQ_ENABLED", False)
    result = groq_provider.interpret_claim_pair("A claim.", "A claim.")
    assert result["status"] == "disabled"
    assert result["abstain"] is True
    assert result["evidence"] == []


def test_groq_response_is_strictly_validated(monkeypatch):
    monkeypatch.setattr(groq_provider, "provider_status", lambda: {
        "provider": "groq", "enabled": True, "available": True, "status": "ready",
    })
    client = FakeClient(json.dumps({
        "relationship": "ALIGNED",
        "mutation_types": [],
        "abstain": False,
        "explanation": "The claims appear equivalent.",
    }))
    result = groq_provider.interpret_claim_pair("A claim.", "A claim.", client=client)
    assert result["relationship"] == "ALIGNED"
    assert result["provider_role"] == "semantic_interpretation_only"
    assert result["factual_verification"] == "not_performed"
    assert result["evidence"] == []


def test_malformed_groq_response_abstains(monkeypatch):
    monkeypatch.setattr(groq_provider, "provider_status", lambda: {
        "provider": "groq", "enabled": True, "available": True, "status": "ready",
    })
    result = groq_provider.interpret_claim_pair("A claim.", "A claim.", client=FakeClient("not-json"))
    assert result["status"] == "failed"
    assert result["relationship"] == "ABSTAIN"
    assert result["abstain"] is True


def test_provider_does_not_override_cross_language_local_abstention(monkeypatch):
    monkeypatch.setattr(groq_provider, "GROQ_ENABLED", False)
    from app.pipelines.semantic_analyzer import analyze_similarity
    result = analyze_similarity("The company may announce news.", "कंपनी समाचार घोषित कर सकती है।")
    assert result["comparison_status"] == "ABSTAIN"
    assert result["provider_metadata"] is None
