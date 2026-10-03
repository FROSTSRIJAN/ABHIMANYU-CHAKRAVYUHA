from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import CORS_ORIGINS, MAX_INPUT_CHARS, MAX_SEQUENCE_LENGTH
from app.core.schemas import AnalyzeRequest, CompareRequest, GraphRequest, SequenceRequest, VerifyRequest
from app.pipelines.claim_graph import build_claim_graph
from app.pipelines.mutation_detector import analyze_mutation
from app.pipelines.semantic_analyzer import analyze_similarity, compare_claims
from app.services.analysis_service import analyze
from app.services.model_manager import ModelManager

app = FastAPI(title="Abhimanyu Chakravyuha NLP Intelligence API", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=CORS_ORIGINS, allow_methods=["GET", "POST"], allow_headers=["*"])

def _check_size(texts: list[str]) -> None:
    if any(len(text) > MAX_INPUT_CHARS for text in texts):
        raise HTTPException(status_code=413, detail=f"Input exceeds {MAX_INPUT_CHARS} characters.")

@app.get("/health")
def health():
    return {"status": "ok", "service": "ml-service"}

@app.get("/models")
def models():
    return {"models": ModelManager().models()}

@app.post("/compare")
def compare(request: CompareRequest):
    _check_size([request.first, request.second])
    semantic = analyze_similarity(request.first, request.second)
    return {
        "semantic_similarity": semantic["similarity"],
        "interpretation": "Relatedness only; not truth probability.",
        "semantic_analysis": semantic,
    }

@app.post("/verify")
def verify(request: VerifyRequest):
    _check_size([request.claim])
    result = analyze([request.claim], request.evidence)
    return result.verification

@app.post("/analyze")
def analyze_endpoint(request: AnalyzeRequest):
    _check_size(request.messages)
    return analyze(request.messages, request.evidence)

@app.post("/analyze/sequence")
def analyze_sequence(request: SequenceRequest):
    if len(request.messages) > MAX_SEQUENCE_LENGTH:
        raise HTTPException(status_code=413, detail=f"Sequence exceeds {MAX_SEQUENCE_LENGTH} messages.")
    _check_size(request.messages)
    pairs = []
    for index in range(1, len(request.messages)):
        pair = analyze_mutation(request.messages[index - 1:index + 1])
        pairs.append({
            "message_index": index,
            "semantic_similarity": compare_claims(request.messages[index - 1], request.messages[index]),
            "certainty_change": pair["certainty_change"],
            "urgency_change": pair["urgency_change"],
            "added_claims": pair["added_claims"],
            "removed_qualifiers": pair["removed_qualifiers"],
            "persuasion_indicators": pair["persuasion_indicators"],
            "explanation": pair["explanation"],
        })
    return {"status": "success", "pairs": pairs, "limitations": ["Mutation indicators are heuristic unless model-backed components are enabled."]}

@app.post("/analyze/graph")
def analyze_graph(request: GraphRequest):
    if len(request.messages) > MAX_SEQUENCE_LENGTH:
        raise HTTPException(status_code=413, detail=f"Sequence exceeds {MAX_SEQUENCE_LENGTH} messages.")
    _check_size(request.messages)
    return build_claim_graph(request.messages, request.evidence)
