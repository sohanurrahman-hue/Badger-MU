"""
Badge Engine FastAPI Application
Main entry point for the API
"""
import sys
from pathlib import Path

# Add parent directory to Python path to allow imports when running from api/ directory
# This allows 'from backend.db import ...' to work when running from api/ or backend/ directory
backend_dir = Path(__file__).parent.parent  # migration/backend/
parent_dir = backend_dir.parent  # migration/
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.security import OAuth2PasswordBearer
from contextlib import asynccontextmanager
import logging
import os

from backend.db import init_db
from backend.api.routers import achievements, issuers, awards, sign, scim_users, scim_groups
from backend.api.routers import credentials, profile_ob, discovery
from backend.auth.middleware import AuthMiddleware
from backend.utils.logger import setup_logging
from backend.schemas.open_badges.status import map_http_status_to_imsx

from backend.api.routers import auth


# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Environment
ENV = os.getenv("ENV", "development")
DEBUG = ENV == "development"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager - runs on startup and shutdown
    """
    # Startup
    logger.info("Starting Badge Engine API...")
    init_db()  # Initialize database tables
    logger.info("Database initialized")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Badge Engine API...")


# Create FastAPI application
app = FastAPI(
    title="Badge Engine API",
    description="Open Badge v3.0 compliant badge issuing platform",
    version="2.0.0",
    docs_url="/api/docs" if DEBUG else None,
    redoc_url="/api/redoc" if DEBUG else None,
    lifespan=lifespan
)


# CORS configuration
origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:3001").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add authentication middleware
app.add_middleware(AuthMiddleware)


# ============================================================================
# Exception Handlers
# ============================================================================

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with Imsx_StatusInfo format"""
    logger.error(f"Validation error: {exc.errors()}")
    error = map_http_status_to_imsx(
        400,
        f"Validation error: {', '.join([str(e) for e in exc.errors()])}"
    )
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=error.model_dump()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions with Imsx_StatusInfo format"""
    logger.exception(f"Unhandled exception: {str(exc)}")
    error = map_http_status_to_imsx(
        500,
        str(exc) if DEBUG else "An internal server error occurred"
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error.model_dump()
    )


# ============================================================================
# Routes
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Badge Engine API",
        "version": "2.0.0",
        "spec": "Open Badge v3.0"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


# Include routers
# Open Badges v3.0 spec-compliant endpoints (root level, no prefix)
app.include_router(credentials.router, tags=["OpenBadgeCredentials"])
app.include_router(profile_ob.router, tags=["OpenBadgeCredentials"])
app.include_router(discovery.router, tags=["Discovery"])

# Custom application endpoints
app.include_router(achievements.router, prefix="/api/achievements", tags=["Achievements"])
app.include_router(issuers.router, prefix="/api/issuers", tags=["Issuers"])
app.include_router(awards.router, prefix="/api/award", tags=["Awards"])
app.include_router(sign.router, prefix="/api/sign", tags=["Signing"])
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
# SCIM endpoints
app.include_router(scim_users.router, prefix="/scim/v2", tags=["SCIM"])
app.include_router(scim_groups.router, prefix="/scim/v2", tags=["SCIM"])


# ============================================================================
# Main execution (for development)
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "backend.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=DEBUG,
        log_level="info"
    )

