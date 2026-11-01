import os
from pathlib import Path
try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    # Pure-stdlib policy simulation tests can run before optional app deps are installed.
    def load_dotenv():
        return False

load_dotenv()

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
LECTURES_DIR = DATA_DIR / "lectures"
CHROMA_DIR = DATA_DIR / "chroma_db"
DB_PATH = DATA_DIR / "sessions.db"

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 400))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 60))
TOP_K_RETRIEVAL = int(os.getenv("TOP_K_RETRIEVAL", 5))
VALIDATE_QUESTIONS = os.getenv("VALIDATE_QUESTIONS", "true").lower() == "true"
