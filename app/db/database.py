"""Database engine and schema initialization."""

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from app.config import DATABASE_URL
from app.db.models import Base


def _connect_args(database_url: str) -> dict[str, object]:
    """Return engine connect args for the configured database."""
    if database_url.startswith("sqlite"):
        return {"check_same_thread": False}
    return {}


def _ensure_sqlite_parent(database_url: str) -> None:
    """Create the parent directory for file-based SQLite databases."""
    if not database_url.startswith("sqlite:///"):
        return

    db_path = database_url.removeprefix("sqlite:///")
    if db_path and db_path != ":memory:":
        Path(db_path).expanduser().parent.mkdir(parents=True, exist_ok=True)


def create_database_engine(database_url: str = DATABASE_URL) -> Engine:
    """Create a SQLAlchemy engine for the given database URL."""
    _ensure_sqlite_parent(database_url)
    return create_engine(database_url, connect_args=_connect_args(database_url))


engine = create_database_engine()
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


def init_db() -> None:
    """Create database tables if they do not already exist."""
    Base.metadata.create_all(bind=engine)
