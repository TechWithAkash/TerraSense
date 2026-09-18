from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # database
    database_url: str = f"sqlite:///{BACKEND_ROOT / 'terrasense.db'}"

    # knowledge base source files, loaded at startup
    knowledge_base_dir: Path = BACKEND_ROOT / "knowledge_base"

    # LLM provider, used for intake parsing, clarifying questions, and narration
    # if no key is set, the system falls back to rule-based logic so it still runs and demos cleanly
    # Groq speaks the OpenAI Chat Completions API, so we reuse the openai SDK pointed at Groq's base_url
    groq_api_key: str | None = None
    groq_model: str = "llama-3.3-70b-versatile"
    groq_base_url: str = "https://api.groq.com/openai/v1"

    # reasoning engine tuning
    max_propagation_depth: int = 3
    attenuation_per_hop: float = 0.85
    max_clarifying_questions: int = 3

    cors_origins: list[str] = ["http://localhost:3000"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
