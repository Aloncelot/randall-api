"""
API de Randall, el asistente de Quasar Devs.

Ejecutar en local:
    uvicorn app.main:app --reload --port 8000
"""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import fallback
from app.config import get_settings
from app.llm import ask_llm
from app.ratelimit import RateLimiter
from app.schemas import ChatRequest, ChatResponse

logger = logging.getLogger("randall")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

settings = get_settings()
limiter = RateLimiter(settings.rate_per_minute, settings.rate_per_day)

app = FastAPI(
    title="Randall API — Quasar Devs",
    version="1.0.0",
    docs_url=None,  # sin documentación pública en producción
    redoc_url=None,
    openapi_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
    allow_credentials=False,
    max_age=600,
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    # Rechaza cuerpos enormes antes de leerlos
    length = request.headers.get("content-length")
    if length and length.isdigit() and int(length) > 16_000:
        return JSONResponse({"detail": "Payload demasiado grande"}, status_code=413)
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Cache-Control"] = "no-store"
    response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
    return response


@app.exception_handler(RequestValidationError)
async def validation_error(_: Request, __: RequestValidationError):
    # No devolvemos el detalle interno de la validación
    return JSONResponse({"detail": "Solicitud inválida"}, status_code=422)


def client_ip(request: Request) -> str:
    if settings.trust_proxy:
        forwarded = request.headers.get("x-forwarded-for", "")
        if forwarded:
            return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@app.get("/health")
async def health():
    return {"status": "ok", "llm": settings.llm_enabled}


@app.post("/chat", response_model=ChatResponse)
async def chat(body: ChatRequest, request: Request):
    if not limiter.allow(client_ip(request)):
        msg = (
            "Voy muy rápido, dame unos segundos para recargar energía. ⚡"
            if body.lang == "es"
            else "I'm going too fast, give me a few seconds to recharge. ⚡"
        )
        return JSONResponse({"reply": msg, "mood": "sleepy", "source": "faq"}, status_code=429)

    question = body.messages[-1].content

    if settings.llm_enabled:
        try:
            reply, mood = await ask_llm(body.messages, body.lang, settings)
            return ChatResponse(reply=reply, mood=mood, source="llm")
        except Exception as exc:  # el proveedor falló: seguimos con el modo FAQ
            logger.warning("Fallo del LLM, usando FAQ: %s", type(exc).__name__)

    reply, mood = fallback.answer(question, body.lang)
    return ChatResponse(reply=reply, mood=mood, source="faq")
