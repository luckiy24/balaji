import os
from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
SAMPLE_DOCS_DIR = BASE_DIR / "sample_documents"
SAMPLE_DOCS_DIR.mkdir(parents=True, exist_ok=True)

class Settings(BaseSettings):
    BASE_DIR: Path = BASE_DIR
    APP_NAME: str = "StatSkill AI"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = "AI-enabled Competency Development Platform for India's Official Statistical System"
    DATABASE_URL: str = f"sqlite:///{BASE_DIR / 'statskill.db'}"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "statskill-mospi-karmayogi-secret-key-2026")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 # 24 hours
    UPLOAD_DIR: Path = UPLOAD_DIR
    MAX_FILE_SIZE_MB: int = 25
    ALLOWED_EXTENSIONS: set = {".pdf", ".docx", ".pptx", ".txt"}
    
    # Pluggable AI backend configuration
    AI_PROVIDER: str = os.getenv("AI_PROVIDER", "heuristic") # "heuristic", "gemini", "openai", "ollama"
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OLLAMA_URL: str = os.getenv("OLLAMA_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3")
    
    # iGOT Adapter mode
    IGOT_MODE: str = "adapter_mock" # adapter_mock, live_authorized (future)
    IGOT_API_ENDPOINT: str = os.getenv("IGOT_API_ENDPOINT", "https://igot-mock.karmayogi.gov.in/api/v1")
    
    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
