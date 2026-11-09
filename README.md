# Randall API — asistente de Quasar Devs

Backend en Python (FastAPI) del chatbot **Randall**, el avatar pixelado turquesa de la landing de Quasar Devs.

- Responde **solo** con la información de la landing (`knowledge/quasar_devs.es.md` y `.en.md`).
- Usa cualquier proveedor de IA compatible con la API de OpenAI (Groq, Together, OpenAI, OpenRouter…).
- **Modo FAQ sin IA**: si no hay `LLM_API_KEY` o el proveedor falla, responde con respuestas predefinidas (`app/fallback.py`). Randall nunca se queda mudo.
- Devuelve también el **ánimo** (`happy`, `wink`, `surprised`…) para que el avatar cambie de expresión.

## Correr en local

```bash
cd randall-api
python -m venv .venv
.venv\Scripts\activate            # Windows  (macOS/Linux: source .venv/bin/activate)
pip install -r requirements-dev.txt
copy .env.example .env            # y pega tu LLM_API_KEY (opcional)
uvicorn app.main:app --reload --port 8000
pytest -q
```

Prueba rápida:

```bash
curl -X POST http://localhost:8000/chat -H "Content-Type: application/json" -d "{\"lang\":\"es\",\"messages\":[{\"role\":\"user\",\"content\":\"¿Qué servicios ofrecen?\"}]}"
```

## API

| Método | Ruta      | Descripción |
|--------|-----------|-------------|
| GET    | `/health` | `{ "status": "ok", "llm": true/false }` |
| POST   | `/chat`   | Body: `{ "lang": "es"|"en", "messages": [{ "role": "user"|"assistant", "content": "..." }] }` → `{ "reply", "mood", "source": "llm"|"faq" }` |

## Desplegar (ej. Render, Railway o Fly.io)

1. Sube esta carpeta a su propio repo de GitHub.
2. Crea un servicio web con el `Dockerfile` (o comando `uvicorn app.main:app --host 0.0.0.0 --port $PORT`).
3. Variables de entorno: `LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL`, `ALLOWED_ORIGINS=https://quasar-devs.vercel.app`, `TRUST_PROXY=true`.
4. En Vercel (proyecto quasar-devs) agrega `NEXT_PUBLIC_RANDALL_API_URL=https://tu-api...` y vuelve a desplegar.

## Seguridad

- CORS restringido a `ALLOWED_ORIGINS`; sin cookies ni credenciales.
- Límite por IP (10/min y 150/día por defecto) y cuerpo máximo de 16 KB.
- Validación estricta: máx. 12 mensajes, 600 caracteres por pregunta, sin rol `system` desde el cliente, sin caracteres de control.
- El prompt impide inventar precios/datos y cambiar las reglas por instrucciones del usuario.
- La API key vive solo en el servidor (`.env`, ignorado por git). Sin docs públicas (`/docs` desactivado).
- El límite por IP vive en memoria: con varias instancias usa Redis o el rate limit del proveedor.

## Actualizar lo que sabe Randall

Edita `knowledge/quasar_devs.es.md` y `knowledge/quasar_devs.en.md` cuando cambie la landing (servicios, proyectos, contacto). Para el modo sin IA, ajusta `app/fallback.py`.
