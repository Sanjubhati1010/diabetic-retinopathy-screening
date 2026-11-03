"""
Database connection and session lifecycle management
for MADOCS DR Screening System.

Provides:
- Database engine initialization
- Connection pooling
- Session factory
- SQLite foreign key support
- Database health check
- FastAPI dependency injection
"""

import os
import logging
from pathlib import Path
from typing import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from sqlalchemy.exc import SQLAlchemyError


# --------------------------------------------------
# Logging Configuration
# --------------------------------------------------

logger = logging.getLogger("dr_backend.database")


# --------------------------------------------------
# Environment Configuration
# --------------------------------------------------

BACKEND_DIR = Path(__file__).resolve().parent.parent
BACKEND_ENV_FILE = BACKEND_DIR / ".env"

if BACKEND_ENV_FILE.is_file():
    load_dotenv(dotenv_path=BACKEND_ENV_FILE)

DEFAULT_DB_PATH = BACKEND_DIR / "madocs_local.db"

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"sqlite:///{DEFAULT_DB_PATH.as_posix()}"
)


# --------------------------------------------------
# Database Engine Configuration
# --------------------------------------------------

is_sqlite = DATABASE_URL.startswith("sqlite")

if is_sqlite:

    engine = create_engine(
        DATABASE_URL,
        connect_args={
            "check_same_thread": False
        },
        pool_pre_ping=True,
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
        pool_size=5,
        max_overflow=5,
        echo=False,
    )


# --------------------------------------------------
# Session Factory
# --------------------------------------------------

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


# --------------------------------------------------
# Declarative Base
# --------------------------------------------------

Base = declarative_base()


# --------------------------------------------------
# Database Dependency
# --------------------------------------------------

def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency injection provider.

    Creates a database session and guarantees
    that it is closed after the request.
    """

    db = SessionLocal()

    try:
        yield db

    except SQLAlchemyError as error:

        db.rollback()

        logger.error(
            "Database transaction error: %s",
            error
        )

        raise

    finally:

        db.close()


# --------------------------------------------------
# Database Health Check
# --------------------------------------------------

def check_db_health() -> bool:
    """
    Checks whether the database connection is working.
    Compatible with SQLAlchemy 2.x.
    """

    try:

        with engine.connect() as connection:

            connection.execute(text("SELECT 1"))

        logger.info("Database health check successful.")

        return True

    except Exception as error:

        logger.warning(
            "Database health check failed: %s",
            error
        )

        return False


# --------------------------------------------------
# Database Initialization
# --------------------------------------------------

def init_db():

    try:

        Base.metadata.create_all(bind=engine)

        logger.info(
            "Database tables initialized successfully."
        )

        return True

    except Exception as error:

        logger.exception(
            "Database initialization failed: %s",
            error
        )

        raise
