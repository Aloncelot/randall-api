"""Llamada al modelo de lenguaje (cualquier proveedor compatible con la API de OpenAI)."""

from __future__ import annotations

import re

from openai import AsyncOpenAI

from app.config import Settings
from app.knowledge import system_prompt
from app.schemas import ChatMessage

VALID_MOODS = {"idle", "happy", "surprised", "wink", "sad", "thinking"}
_MOOD_TAG = re.compile(r"^\s*\[(\w+)\]\s*")

_client: AsyncOpenAI | None = None


def _get_client(settings: Settings) -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url,
            timeout=settings.llm_timeout,
            max_retries=1,
        )
    return _client


def split_mood(text: str) -> tuple[str, str]:
    """Separa la etiqueta de ánimo "[happy]" del texto. Si falta o no es válida, usa "happy"."""
    match = _MOOD_TAG.match(text)
    mood = "happy"
    if match:
        if match.group(1).lower() in VALID_MOODS:
            mood = match.group(1).lower()
        text = text[match.end():]
    # Quita etiquetas sueltas que el modelo repita a mitad del texto
    text = re.sub(r"\[(?:%s)\]\s*" % "|".join(VALID_MOODS), "", text, flags=re.I)
    return text.strip(), mood


async def ask_llm(messages: list[ChatMessage], lang: str, settings: Settings) -> tuple[str, str]:
    client = _get_client(settings)
    completion = await client.chat.completions.create(
        model=settings.llm_model,
        messages=[
            {"role": "system", "content": system_prompt(lang)},
            *({"role": m.role, "content": m.content} for m in messages),
        ],
        temperature=0.4,
        max_tokens=settings.llm_max_tokens,
        # Los modelos gpt-oss razonan antes de responder: "low" = respuestas rápidas y baratas
        **({"extra_body": {"reasoning_effort": "low"}} if "gpt-oss" in settings.llm_model else {}),
    )
    content = (completion.choices[0].message.content or "").strip()
    if not content:
        raise RuntimeError("Respuesta vacía del modelo")
    return split_mood(content)
