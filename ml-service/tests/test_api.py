from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    assert client.get("/health").json()["status"] == "ok"

def test_analyze():
    response = client.post("/analyze", json={"messages": ["The company may announce news.", "The company will definitely announce news."]})
    assert response.status_code == 200
    assert response.json()["status"] == "success"

def test_empty_message_rejected():
    assert client.post("/analyze", json={"messages": [""]}).status_code == 422

def test_sequence_endpoint_returns_pairwise_results():
    response = client.post("/analyze/sequence", json={"messages": ["It may happen.", "It will definitely happen."]})
    assert response.status_code == 200
    assert response.json()["pairs"][0]["certainty_change"] == "INCREASED"

def test_oversized_input_rejected():
    response = client.post("/compare", json={"first": "x" * 10001, "second": "ok"})
    assert response.status_code == 413

def test_model_registry_reports_fallbacks():
    response = client.get("/models")
    assert response.status_code == 200
    assert any(item["component"] == "fallback" for item in response.json()["models"])

def test_graph_endpoint_returns_nodes_and_edges():
    response = client.post("/analyze/graph", json={"messages": ["The company may announce.", "The company will definitely announce."]})
    assert response.status_code == 200
    payload = response.json()
    assert len(payload["nodes"]) == 2
    assert len(payload["edges"]) == 1
    assert "mutation_summary" in payload

def test_verify_rejects_invalid_evidence_schema():
    response = client.post("/verify", json={"claim": "A claim.", "evidence": [{"document_id": "x"}]})
    assert response.status_code == 422

def test_api_supplied_evidence_is_non_authoritative():
    response = client.post("/verify", json={
        "claim": "The market rose today.",
        "evidence": [{
            "document_id": "caller",
            "passage": "The market rose today.",
            "source_name": "caller supplied",
            "source_type": "provided",
        }],
    })
    assert response.status_code == 200
    assert response.json()["label"] == "INSUFFICIENT_EVIDENCE"
    assert response.json()["explanation"]["authoritative"] is False

def test_compare_rejects_blank_claims():
    assert client.post("/compare", json={"first": "   ", "second": "claim"}).status_code == 422

def test_verify_rejects_blank_claim():
    assert client.post("/verify", json={"claim": "   "}).status_code == 422
