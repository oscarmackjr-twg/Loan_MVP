"""FastAPI application main entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import logging.config
import yaml
from pathlib import Path

from config.settings import settings
from api.routes import router as api_router
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


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Loan Engine API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
