"""Database setup and session management."""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool

# Use SQLite in app root
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./stripe_demo.db")

is_sqlite = DATABASE_URL.startswith("sqlite")
is_sqlite_memory = ":memory:" in DATABASE_URL

engine_kwargs = {
    "connect_args": {"check_same_thread": False} if is_sqlite else {},
    "echo": os.getenv("SQL_ECHO", "false").lower() == "true",
}

# In-memory SQLite creates a new, empty database per connection unless we
# force a single shared connection (required for tests using multiple sessions).
if is_sqlite and is_sqlite_memory:
    engine_kwargs["poolclass"] = StaticPool

engine = create_engine(DATABASE_URL, **engine_kwargs)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)
