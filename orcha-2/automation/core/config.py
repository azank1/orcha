from __future__ import annotations

from functools import lru_cache
from pydantic import BaseModel, Field, AnyHttpUrl, ValidationError
import os


class LLMSettings(BaseModel):
    use_ollama: bool = Field(default=True)
    ollama_host: AnyHttpUrl = Field(default="http://127.0.0.1:11434")
    ollama_model: str = Field(default="llama3.2")
    use_openai: bool = Field(default=False)
    openai_api_key: str | None = None
    openai_model: str = Field(default="gpt-4-turbo")
    timeout_s: int = Field(default=15, ge=1, le=60)
    max_retries: int = Field(default=3, ge=0, le=8)


class AppSettings(BaseModel):
    env: str = Field(default=os.getenv("APP_ENV", "dev"))
    host: str = Field(default=os.getenv("HOST", "127.0.0.1"))
    port: int = Field(default=int(os.getenv("PORT", "5001")))
    llm: LLMSettings = LLMSettings()


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    try:
        # If needed: from dotenv import load_dotenv; load_dotenv()
        llm = LLMSettings(
            use_ollama=os.getenv("USE_OLLAMA", "true").lower() == "true",
            ollama_host=os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434"),
            ollama_model=os.getenv("OLLAMA_MODEL", "llama3.2"),
            use_openai=os.getenv("USE_OPENAI", "false").lower() == "true",
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            openai_model=os.getenv("OPENAI_MODEL", "gpt-4-turbo"),
            timeout_s=int(os.getenv("LLM_TIMEOUT", "15")),
            max_retries=int(os.getenv("LLM_MAX_RETRIES", "3")),
        )
        return AppSettings(
            env=os.getenv("APP_ENV", "dev"),
            host=os.getenv("HOST", "127.0.0.1"),
            port=int(os.getenv("PORT", "5001")),
            llm=llm,
        )
    except ValidationError as e:
        raise RuntimeError(f"Invalid configuration: {e}") from e
