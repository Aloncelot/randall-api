"""Contratos de entrada y salida de la API."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

Mood = Literal["idle", "happy", "talking", "thinking", "surprised", "sad", "sleepy", "wink"]

MAX_MESSAGE_CHARS = 600
MAX_HISTORY = 12
# Solo los últimos mensajes y hasta este total de caracteres llegan a la IA (limita el gasto de tokens)
LLM_HISTORY_MESSAGES = 6
LLM_HISTORY_CHARS = 3_000


class ChatMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=MAX_MESSAGE_CHARS * 2)

    @field_validator("content")
    @classmethod
    def strip_control_chars(cls, value: str) -> str:
        cleaned = "".join(ch for ch in value if ch in "\n\t" or ch.isprintable()).strip()
        if not cleaned:
            raise ValueError("Mensaje vacío")
        return cleaned


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    messages: list[ChatMessage] = Field(min_length=1, max_length=MAX_HISTORY)
    lang: Literal["es", "en"] = "es"

    @field_validator("messages")
    @classmethod
    def last_is_user(cls, value: list[ChatMessage]) -> list[ChatMessage]:
        if value[-1].role != "user":
            raise ValueError("El último mensaje debe ser del usuario")
        if len(value[-1].content) > MAX_MESSAGE_CHARS:
            raise ValueError(f"Máximo {MAX_MESSAGE_CHARS} caracteres por mensaje")
        return value


class ChatResponse(BaseModel):
    reply: str
    mood: Mood
    source: Literal["llm", "faq"]


def trim_history(messages: list[ChatMessage]) -> list[ChatMessage]:
    """Recorta el historial: últimos mensajes y presupuesto total de caracteres, terminando en el del usuario."""
    kept: list[ChatMessage] = []
    total = 0
    for message in reversed(messages[-LLM_HISTORY_MESSAGES:]):
        total += len(message.content)
        if kept and total > LLM_HISTORY_CHARS:
            break
        kept.append(message)
    kept.reverse()
    while kept and kept[0].role != "user":  # que la conversación empiece con el usuario
        kept.pop(0)
    return kept or messages[-1:]
