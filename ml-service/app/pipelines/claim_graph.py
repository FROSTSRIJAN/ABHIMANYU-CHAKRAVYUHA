from app.core.config import EVIDENCE_PATH
from app.pipelines.claim_normalizer import extract_claims
from app.pipelines.evidence_retriever import load_evidence
from app.pipelines.mutation_detector import compare_claim_versions
from app.pipelines.verifier import verify_claim

def _node(claim: dict, verification: dict) -> dict:
    return {
        **claim,
        "timestamp": None,
        "verification_status": verification["label"],
        "evidence_references": [item.document_id for item in verification["evidence"]],
        "evidence_sufficiency": bool(verification["evidence"]),
        "contradiction_indicators": [item.document_id for item in verification["evidence"] if item.stance == "REFUTES"],
        "retrieval_methods": sorted({item.retrieval_method for item in verification["evidence"]}),
        "verification_limitations": verification["limitations"],
    }

def build_claim_graph(messages: list[str], evidence=None) -> dict:
    claims = extract_claims(messages)
    records = (
        load_evidence(EVIDENCE_PATH)
        if evidence is None
        else [item.model_copy(update={"provenance_verified": False}) for item in evidence]
    )
    nodes = []
    for claim in claims:
        verification = verify_claim(claim["normalized_text"], records)
        nodes.append(_node(claim, verification))
    edges = []
    mutations = []
    for source, target in zip(claims, claims[1:]):
        mutation = compare_claim_versions(source, target)
        mutations.append(mutation)
        relationships = mutation["relationship"]
        if mutation["mutation_types"] == ["CLAIM_ADDITION"]:
            relationships = "CLAIM_ADDITION"
        elif mutation["mutation_types"] == ["CLAIM_REMOVAL"]:
            relationships = "CLAIM_REMOVAL"
        edges.append({
            "source_claim_id": source["claim_id"],
            "target_claim_id": target["claim_id"],
            "relationship": relationships,
            "mutation_types": mutation["mutation_types"],
            "semantic_similarity": mutation["semantic_similarity"],
            "explanation": mutation["explanation"],
            "detection_method": mutation["detection_method"],
            "changed_attributes": mutation.get("changed_attributes", []),
            "supporting_spans": mutation.get("supporting_spans", []),
            "confidence": mutation.get("confidence", "unknown"),
            "confidence_type": mutation.get("confidence_type", "heuristic"),
            "comparison_status": mutation.get("comparison_status", "UNKNOWN"),
            "abstention_reason": mutation.get("abstention_reason"),
            "language_original": mutation.get("language_original"),
            "language_modified": mutation.get("language_modified"),
            "language_pair": mutation.get("language_pair"),
            "alignment_status": mutation.get("alignment_status", "UNKNOWN"),
            "alignment_method": mutation.get("alignment_method"),
        })
    summary = {
        "certainty_escalations": sum("CERTAINTY_ESCALATION" in item["mutation_types"] for item in mutations),
        "urgency_escalations": sum("URGENCY_ESCALATION" in item["mutation_types"] for item in mutations),
        "qualifier_removals": sum("QUALIFIER_REMOVAL" in item["mutation_types"] for item in mutations),
        "numerical_mutations": sum("NUMERICAL_MUTATION" in item["mutation_types"] for item in mutations),
        "entity_mutations": sum("ENTITY_MUTATION" in item["mutation_types"] for item in mutations),
    }
    limitations = ["Chronological order represents sequence, not causation."]
    limitations.extend(
        limitation
        for node in nodes
        for limitation in node["verification_limitations"]
        if limitation not in limitations
    )
    return {
        "nodes": nodes,
        "edges": edges,
        "mutation_summary": summary,
        "overall_observations": [item["explanation"] for item in mutations if item["mutation_types"]],
        "verification_limitations": limitations,
        "human_review_recommended": bool(mutations) or any(node["verification_status"] in {"CONFLICTING", "INSUFFICIENT_EVIDENCE"} for node in nodes),
    }
