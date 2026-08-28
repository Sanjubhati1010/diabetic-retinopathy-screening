"""
Database connection and session lifecycle management for MADOCS DR Screening System.
Provides connection pooling, engine initialization, session factory, and dependency injection.
"""

import os
import logging
from pathlib import Path
from typing import Generator
from dotenv import load_dotenv
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger("dr_backend.database")

# Explicitly load backend/.env if present
BACKEND_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"
if BACKEND_ENV_FILE.is_file():
    load_dotenv(dotenv_path=BACKEND_ENV_FILE)

# Environment-based Database URL
# Production MySQL: mysql+pymysql://<user>:<password>@<host>:<port>/<dbname>?charset=utf8mb4
# Development / Local Testing: sqlite:///./madocs_local.db
DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "madocs_local.db")
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH}")

# Engine Configuration
is_sqlite = DATABASE_URL.startswith("sqlite")

if is_sqlite:
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False,
    )
    # Enable foreign keys for SQLite
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
else:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=3600,
        pool_size=10,
        max_overflow=20,
        echo=False,
    )

# Session Factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declarative Base
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency injection provider for database sessions.
    Guarantees session closure and rollback on unhandled exceptions.
    """
    db: Session = SessionLocal()
    try:
        yield db
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database transaction error: {e}")
        raise
    finally:
        db.close()


def check_db_health() -> bool:
    """Verifies that the database engine can establish a working connection."""
    try:
        with engine.connect() as conn:
            conn.execute(Base.metadata.tables.get("doctors", None) is not None and "SELECT 1" or "SELECT 1")
        return True
    except Exception as e:
        logger.warning(f"Database health check failed: {e}")
        return False
