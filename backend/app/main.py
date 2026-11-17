"""SupportPulse AI - Main FastAPI Application Entrypoint."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler

from backend.app.api.alerts import router as alerts_router
from backend.app.api.analyze import router as analyze_router
from backend.app.api.auth import router as auth_router
from backend.app.api.dashboard import router as dashboard_router
from backend.app.api.dev import router as dev_router
from backend.app.api.models import router as models_router
from backend.app.api.stream import router as stream_router
from backend.app.api.themes import router as themes_router
from backend.app.api.tickets import router as tickets_router
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.db.models import Base
from backend.app.db.session import engine
from backend.app.ml.registry import registry
from backend.app.scheduler.tasks import rescore_open_tickets

scheduler = BackgroundScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle: startup initialization and graceful shutdown."""
    logger.info("Initializing SupportPulse AI database tables...")
    Base.metadata.create_all(bind=engine)

    logger.info("Pre-loading active machine learning models into memory...")
    registry.load_active_models()

    if settings.ENABLE_SCHEDULER:
        logger.info(
            f"Starting background ticket rescoring scheduler (every {settings.SCHEDULER_INTERVAL_MINUTES} mins)..."
        )
        scheduler.add_job(
            rescore_open_tickets,
            "interval",
            minutes=settings.SCHEDULER_INTERVAL_MINUTES,
            id="ticket_rescoring_job",
            replace_existing=True,
        )
        scheduler.start()

    yield

    if scheduler.running:
        logger.info("Shutting down background scheduler...")
        scheduler.shutdown(wait=False)
    logger.info("SupportPulse AI backend stopped cleanly.")


app = FastAPI(
    title="SupportPulse AI",
    description="Locally deployable, ML-powered IT service-desk intelligence platform.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://localhost",
        "*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API Routers
app.include_router(auth_router, prefix="/api")
app.include_router(tickets_router, prefix="/api")
app.include_router(analyze_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")
app.include_router(alerts_router, prefix="/api")
app.include_router(themes_router, prefix="/api")
app.include_router(models_router, prefix="/api")
app.include_router(stream_router, prefix="/api")
app.include_router(dev_router, prefix="/api")


@app.get("/health", tags=["system"])
def root_health():
    """Root healthcheck probe for Docker Compose / Kubernetes."""
    return {"status": "ok", "app": settings.APP_NAME}
