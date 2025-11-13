"""
Database connection and session management
Supports both PostgreSQL (production) and SQLite (local development/testing)
"""
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool, StaticPool
import os
from typing import Generator
from pathlib import Path
# Database URL from environment
# Default to SQLite for local development
# Store database in backend/data/ directory
backend_dir = Path(__file__).parent.parent  # backend/
data_dir = backend_dir / "data"
data_dir.mkdir(exist_ok=True)  # Create data directory if it doesn't exist
db_path = data_dir / "badge_engine.db"
sqlite_db = f"sqlite:///{db_path.absolute()}"

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    sqlite_db
)

# Detect database type
IS_SQLITE = DATABASE_URL.startswith("sqlite")
IS_POSTGRES = DATABASE_URL.startswith("postgresql")

# Configure engine based on database type
if IS_SQLITE:
    # SQLite configuration
    # Use StaticPool for SQLite to allow multiple threads
    # check_same_thread=False allows SQLite to work with FastAPI's async
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False} if "///" in DATABASE_URL else {},
        poolclass=StaticPool,
        echo=os.getenv("SQL_ECHO", "false").lower() == "true"
    )
    
    # Enable foreign key constraints for SQLite
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
else:
    # PostgreSQL configuration
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,  # Verify connections before using
        pool_size=10,
        max_overflow=20,
        echo=os.getenv("SQL_ECHO", "false").lower() == "true"
    )

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for declarative models
Base = declarative_base()


def get_db() -> Generator:
    """
    Dependency for getting database sessions.
    Yields a database session and ensures it's closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize database - create all tables.
    Should be called on application startup.
    """
    # Import all models here to ensure they're registered with Base
    from backend.db import models  # noqa: F401
    
    Base.metadata.create_all(bind=engine)


def drop_db():
    """
    Drop all database tables.
    WARNING: Use only in development/testing!
    """
    Base.metadata.drop_all(bind=engine)

