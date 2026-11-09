"""Contratos de entrada y salida de la API."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

Mood = Literal["idle", "happy", "talking", "thinking", "surprised", "sad", "sleepy", "wink"]

MAX_MESSAGE_CHARS = 600
MAX_HISTORY = 12


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
