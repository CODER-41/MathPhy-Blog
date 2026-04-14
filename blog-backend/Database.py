"""
Database session management.

Pool sizing rationale:
  - Railway free tier allows ~25 total PostgreSQL connections
  - We run 4 uvicorn workers (set in Procfile)
  - 4 workers × pool_size(5) = 20 persistent conns  ← stays under 25
  - max_overflow(3) allows short bursts without exhausting the limit
  - pool_pre_ping=True detects stale connections (Railway recycles them)
  - pool_recycle=1800 proactively recycles connections every 30 min
"""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    pool_pre_ping=True,       # test connection health before use
    pool_recycle=1800,        # recycle connections every 30 min
    echo=settings.DEBUG,      # log SQL in debug mode only
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency — yields a DB session, always closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()