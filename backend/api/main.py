"""FastAPI application main entry point."""
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import logging
import logging.config
import yaml

from config.settings import settings
from api.routes import router as api_router
from api.files import router as files_router
from auth.routes import router as auth_router
from scheduler.job_scheduler import scheduler, schedule_daily_runs

# Configure logging
log_config_path = Path(__file__).parent.parent / "config" / "logging.yaml"
if log_config_path.exists():
    with open(log_config_path, 'r') as f:
        log_config = yaml.safe_load(f)
        
        # Ensure logs directory exists if file handler is configured
        if 'handlers' in log_config:
            for handler_name, handler_config in log_config['handlers'].items():
                if 'filename' in handler_config:
                    log_file_path = Path(handler_config['filename'])
                    # Convert relative path to absolute
                    if not log_file_path.is_absolute():
                        log_file_path = Path(__file__).parent.parent / log_file_path
                    # Create directory if it doesn't exist
                    log_file_path.parent.mkdir(parents=True, exist_ok=True)
                    # Update path to absolute
                    log_config['handlers'][handler_name]['filename'] = str(log_file_path)
        
        logging.config.dictConfig(log_config)
else:
    logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Loan Engine API...")
    
    if settings.ENABLE_SCHEDULER:
        scheduler.start()
        # Schedule jobs after scheduler starts
        schedule_daily_runs()
        logger.info(f"Scheduler started - Daily runs at {settings.DAILY_RUN_TIME}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Loan Engine API...")
    if settings.ENABLE_SCHEDULER:
        scheduler.shutdown()


app = FastAPI(
    title="Loan Engine API",
    description="API for processing loans for structured finance products",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(api_router)
app.include_router(files_router)
app.include_router(files_router)
app.include_router(files_router)

# Serve frontend static files when present (e.g. in Docker / production build)
_static_dir = Path(__file__).resolve().parent.parent / "static"
if _static_dir.is_dir():
    _assets = _static_dir / "assets"
    if _assets.is_dir():
        app.mount("/assets", StaticFiles(directory=str(_assets)), name="assets")


@app.get("/")
async def root():
    """Root endpoint; serves SPA index when static build present."""
    index_html = Path(__file__).resolve().parent.parent / "static" / "index.html"
    if index_html.exists():
        from fastapi.responses import FileResponse
        return FileResponse(str(index_html))
    return {
        "message": "Loan Engine API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint (API only)."""
    return {"status": "healthy"}


@app.get("/health/ready")
async def health_ready():
    """Readiness check: API + database connectivity. Use for demo verification."""
    from sqlalchemy import text
    from db.connection import SessionLocal
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        return {"status": "ready", "database": "connected"}
    except Exception as e:
        logger.exception("Database health check failed")
        return {"status": "degraded", "database": "disconnected", "error": str(e)}


# SPA fallback: serve index.html for non-API routes when static build is present
if _static_dir.is_dir():
    _index_html = _static_dir / "index.html"
    if _index_html.exists():
        from fastapi.responses import FileResponse
        from fastapi import Request

        @app.get("/{full_path:path}")
        async def spa_fallback(request: Request, full_path: str):
            if full_path.startswith(("api/", "auth/", "docs", "openapi.json", "health", "assets/")):
                from fastapi import HTTPException
                raise HTTPException(status_code=404, detail="Not found")
            return FileResponse(str(_index_html))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
