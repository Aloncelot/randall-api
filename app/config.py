"""Configuración leída de variables de entorno (ver .env.example)."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


def _list(name: str, default: str) -> list[str]:
    return [item.strip().rstrip("/") for item in os.getenv(name, default).split(",") if item.strip()]


def _int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    # Proveedor de IA compatible con la API de OpenAI (Groq, Together, OpenAI, OpenRouter...)
    llm_api_key: str = field(default_factory=lambda: os.getenv("LLM_API_KEY", ""))
    llm_base_url: str = field(default_factory=lambda: os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1"))
    llm_model: str = field(default_factory=lambda: os.getenv("LLM_MODEL", "openai/gpt-oss-120b"))
    llm_timeout: int = field(default_factory=lambda: _int("LLM_TIMEOUT_SECONDS", 20))
    llm_max_tokens: int = field(default_factory=lambda: _int("LLM_MAX_TOKENS", 800))

    # Base de conocimiento generada por la landing (sin "/" final). Vacío = usar archivos locales.
    knowledge_url: str = field(
        default_factory=lambda: os.getenv("KNOWLEDGE_URL", "https://quasardevs.com/api/knowledge").rstrip("/")
    )
    knowledge_ttl: int = field(default_factory=lambda: _int("KNOWLEDGE_TTL_SECONDS", 600))

    # Solo estos orígenes pueden llamar a la API desde el navegador
    allowed_origins: list[str] = field(
        default_factory=lambda: _list(
            "ALLOWED_ORIGINS", "https://quasar-devs.vercel.app,http://localhost:3000"
        )
    )

    # Límite de peticiones por IP
    rate_per_minute: int = field(default_factory=lambda: _int("RATE_LIMIT_PER_MINUTE", 10))
    rate_per_day: int = field(default_factory=lambda: _int("RATE_LIMIT_PER_DAY", 150))
    # Activar solo si la API corre detrás de un proxy de confianza (Render, Railway, Fly, Nginx)
    trust_proxy: bool = field(default_factory=lambda: os.getenv("TRUST_PROXY", "false").lower() == "true")

    @property
    def llm_enabled(self) -> bool:
        return bool(self.llm_api_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()
