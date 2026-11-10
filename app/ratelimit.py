"""
Límites de uso de Randall.

- Por visitante (IP): por minuto y por día.
- Global para la IA: por minuto y por día, para no agotar la cuota del proveedor (Groq).
  Al llegar al tope global, Randall sigue respondiendo en modo FAQ (sin IA).

Los contadores viven en Upstash Redis (REST) para que funcionen en Vercel, donde cada
petición puede caer en una instancia distinta. Si Redis no está configurado o falla,
se usa memoria local (protege menos, pero nunca deja a Randall sin servicio).
"""

from __future__ import annotations

import logging
import os
import time
from collections import defaultdict
from threading import Lock

import httpx

logger = logging.getLogger("randall.ratelimit")


def _redis_config() -> tuple[str, str] | None:
    # Nombres de la integración de Vercel (KV_*) o de Upstash directo (UPSTASH_*)
    url = os.getenv("KV_REST_API_URL") or os.getenv("UPSTASH_REDIS_REST_URL")
    token = os.getenv("KV_REST_API_TOKEN") or os.getenv("UPSTASH_REDIS_REST_TOKEN")
    return (url.rstrip("/"), token) if url and token else None


class _MemoryCounter:
    """Contador de ventana fija en memoria (respaldo)."""

    def __init__(self) -> None:
        self._data: dict[str, tuple[int, float]] = defaultdict(lambda: (0, 0.0))
        self._lock = Lock()

    def incr(self, key: str, window: int) -> int:
        now = time.time()
        with self._lock:
            count, expires = self._data[key]
            if now >= expires:
                count, expires = 0, now + window
            count += 1
            self._data[key] = (count, expires)
            if len(self._data) > 20_000:  # limpieza ocasional
                for k in [k for k, (_, e) in self._data.items() if e <= now]:
                    del self._data[k]
            return count


class RateLimiter:
    def __init__(
        self,
        per_minute: int,
        per_day: int,
        llm_per_minute: int = 0,
        llm_per_day: int = 0,
        prefix: str = "randall",
    ) -> None:
        self.per_minute, self.per_day = per_minute, per_day
        self.llm_per_minute, self.llm_per_day = llm_per_minute, llm_per_day
        self.prefix = prefix
        self._memory = _MemoryCounter()
        self._redis = _redis_config()

    @property
    def backend(self) -> str:
        return "redis" if self._redis else "memory"

    async def _incr(self, key: str, window: int) -> int:
        """Incrementa un contador de ventana fija y devuelve el valor actual."""
        bucket = int(time.time() // window)
        full_key = f"{self.prefix}:{key}:{bucket}"
        if self._redis:
            url, token = self._redis
            try:
                async with httpx.AsyncClient(timeout=2.0) as client:
                    res = await client.post(
                        f"{url}/pipeline",
                        headers={"Authorization": f"Bearer {token}"},
                        json=[["INCR", full_key], ["EXPIRE", full_key, str(window + 5)]],
                    )
                res.raise_for_status()
                return int(res.json()[0]["result"])
            except Exception as exc:  # Redis caído: seguimos con memoria
                logger.warning("Redis no disponible para rate limit: %s", type(exc).__name__)
        return self._memory.incr(full_key, window)

    async def allow_visitor(self, ip: str) -> bool:
        """¿Este visitante puede hacer otra pregunta?"""
        minute = await self._incr(f"ip:{ip}:m", 60)
        if minute > self.per_minute:
            return False
        day = await self._incr(f"ip:{ip}:d", 86_400)
        return day <= self.per_day

    async def allow_llm(self) -> bool:
        """¿Queda presupuesto global para llamar a la IA? (si no, se responde en modo FAQ)"""
        if self.llm_per_minute and await self._incr("llm:m", 60) > self.llm_per_minute:
            return False
        if self.llm_per_day and await self._incr("llm:d", 86_400) > self.llm_per_day:
            return False
        return True
