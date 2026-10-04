from pathlib import Path
import os
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")
load_dotenv(ROOT / "ml-service" / ".env")
MAX_INPUT_CHARS = int(os.getenv("ABHIMANYU_MAX_INPUT_CHARS", "10000"))
MAX_SEQUENCE_LENGTH = int(os.getenv("ABHIMANYU_MAX_SEQUENCE_LENGTH", "20"))
EVIDENCE_RELEVANCE_THRESHOLD = float(os.getenv("ABHIMANYU_EVIDENCE_RELEVANCE_THRESHOLD", "0.3"))
EVIDENCE_MAX_CANDIDATES = int(os.getenv("ABHIMANYU_EVIDENCE_MAX_CANDIDATES", "5"))
EVIDENCE_PATH = Path(os.getenv("ABHIMANYU_EVIDENCE_PATH", str(ROOT / "app" / "data" / "sample_evidence.json")))
ENABLE_TRANSFORMERS = os.getenv("ENABLE_TRANSFORMERS", "false").lower() == "true"
ENABLE_NLI = os.getenv("ENABLE_NLI", "false").lower() == "true"
ENABLE_FAISS = os.getenv("ENABLE_FAISS", "false").lower() == "true"
MODEL_DEVICE = os.getenv("MODEL_DEVICE", "cpu")
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
EMBEDDING_MODEL_PATH = os.getenv("EMBEDDING_MODEL_PATH", "").strip()
NLI_MODEL_NAME = os.getenv("NLI_MODEL_NAME", "MoritzLaurer/mDeBERTa-v3-base-mnli-xnli")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
GROQ_ENABLED = os.getenv("GROQ_ENABLED", "false").lower() == "true"
GROQ_TIMEOUT = float(os.getenv("GROQ_TIMEOUT", "20"))
GROQ_MAX_RETRIES = min(max(int(os.getenv("GROQ_MAX_RETRIES", "1")), 0), 3)
CORS_ORIGINS = [origin.strip() for origin in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",") if origin.strip()]
