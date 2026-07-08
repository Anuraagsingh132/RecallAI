from fastapi import FastAPI, File, UploadFile, Request
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import asyncio
from core.security import MaxBodySizeMiddleware
from core.config import settings
from core.worker import worker_loop
from core.recovery import recover_zombie_jobs
import os
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
import structlog
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from api.routers.auth import limiter
import logging
from core.qdrant import init_qdrant

from core.database import engine

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)
logger = structlog.get_logger(__name__)

sentry_dsn = settings.SENTRY_DSN
if not sentry_dsn and os.environ.get("ENV") == "production":
    logger.warning("SENTRY_DSN is not set in production environment. Error tracking is disabled.")
if sentry_dsn:
    sentry_sdk.init(
        dsn=sentry_dsn,
        integrations=[FastApiIntegration()]
    )

worker_task = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global worker_task
    # Startup Sequence
    # 1. Recover any interrupted jobs
    recovered = await recover_zombie_jobs()
    print(f"Recovered {recovered} zombie jobs.")
    
    # 1.5 Init Qdrant
    await init_qdrant()
    print("Qdrant collection initialized.")
    
    # 2. Start the daemon worker loop
    worker_task = asyncio.create_task(worker_loop())
    yield
    
    # Shutdown Sequence
    if worker_task:
        worker_task.cancel()
        try:
            await worker_task
        except asyncio.CancelledError:
            pass
        print("Worker cleanly shut down.")

app = FastAPI(title="RecallAI", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_CORS_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add the streaming payload limit middleware
app.add_middleware(MaxBodySizeMiddleware, max_size=settings.MAX_UPLOAD_SIZE_BYTES)

from api.routers import documents, chat, auth

app.include_router(documents.router)
app.include_router(chat.router)
app.include_router(auth.router)

from fastapi.staticfiles import StaticFiles

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.get("/crash")
async def crash():
    raise ValueError("Intentional crash for testing")

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception caught", exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error"},
    )

# Mount frontend static files last, so it doesn't override API routes
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
