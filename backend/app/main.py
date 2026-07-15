"""
FastAPI application entry point.
Registers middleware, routers, startup/shutdown events, and CORS.
"""
from __future__ import annotations

import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.monitoring.metrics import app_info, app_uptime_seconds
from app.monitoring.middleware import MetricsMiddleware
from app.routers import chat, escalation, health
from app.utils.logging import configure_logging, logger

# ── Lifespan (startup / shutdown) ─────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    settings = get_settings()
    configure_logging()
    logger.info(
        "Application starting",
        environment=settings.environment,
        mock_mode=settings.mock_mode,
        azure_configured=settings.azure_configured,
    )
    app_info.info({
        "version": "1.0.0",
        "environment": settings.environment,
        "mock_mode": str(settings.mock_mode),
    })

    # Background: update uptime gauge every 60s
    import asyncio

    async def _uptime_loop() -> None:
        start = time.time()
        while True:
            app_uptime_seconds.set(round(time.time() - start, 0))
            await asyncio.sleep(60)

    task = asyncio.create_task(_uptime_loop())

    yield  # App runs

    # Shutdown
    task.cancel()
    logger.info("Application shutting down")


# ── App factory ───────────────────────────────────────────────────────────────

def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="IT Helpdesk Deflection Agent",
        description=(
            "RAG-grounded IT support agent with confidence-based escalation, "
            "security guardrails, and full observability."
        ),
        version="1.0.0",
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        lifespan=lifespan,
    )

    # ── Security headers middleware ────────────────────────────────────────
    @app.middleware("http")
    async def add_security_headers(request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline';"
        )
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response

    # ── Prometheus metrics middleware ──────────────────────────────────────
    app.add_middleware(MetricsMiddleware)

    # ── CORS ──────────────────────────────────────────────────────────────
    origins = (
        ["*"] if not settings.is_production
        else ["https://<your-swa>.azurestaticapps.net"]
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PATCH"],
        allow_headers=["Content-Type", "Authorization"],
    )

    # ── Routers ───────────────────────────────────────────────────────────
    app.include_router(chat.router)
    app.include_router(escalation.router)
    app.include_router(health.router)

    return app


app = create_app()
