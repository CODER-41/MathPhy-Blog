"""
Physics Blog API — entry point.

Startup sequence:
  1. Create all DB tables (idempotent — safe on every deploy)
  2. Seed first admin account if DB is empty
  3. Connect to Redis and initialise FastAPICache
  4. Register all middleware (order matters — logging outermost)
  5. Mount all routers under /api/v1

Shutdown sequence:
  1. Close Redis connection pool gracefully

Worker scaling (set in Procfile):
  --workers 4   → 4 × DB pool_size(5) = 20 conns ← under Railway's 25-conn limit
  Adjust DB_POOL_SIZE in .env if you change worker count.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes.auth import router as auth_router
from app.api.routes.categories import categories_router, tags_router
from app.api.routes.comments import router as comments_router
from app.api.routes.posts import router as posts_router
from app.api.routes.users import router as users_router
from app.core.cache import close_cache, get_redis, init_cache
from app.core.config import settings
from app.db.database import Base, SessionLocal, engine
from app.middleware.cache_control import CacheControlMiddleware
from app.middleware.logging import RequestLoggingMiddleware
from app.models import models  # noqa: F401 — ensures models are registered with Base
from app.services.seed import seed_admin


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ───────────────────────────────────────────────────────────────
    # Create tables (Alembic handles migrations in prod; this is a safety net)
    Base.metadata.create_all(bind=engine)

    # Seed first admin if DB is empty
    db = SessionLocal()
    try:
        seed_admin(db)
    finally:
        db.close()

    # Connect Redis + initialise FastAPICache
    await init_cache()

    yield

    # ── Shutdown ──────────────────────────────────────────────────────────────
    await close_cache()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Backend API for a physics blog. "
        "Supports Markdown + LaTeX posts, role-based auth, "
        "Redis caching, and CDN-friendly Cache-Control headers."
    ),
    lifespan=lifespan,
    # Hide docs in production
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# ── Middleware (outermost registered = outermost executed) ────────────────────
# 1. Request logging — wraps everything, catches unhandled exceptions
app.add_middleware(RequestLoggingMiddleware)

# 2. Cache-Control — adds CDN headers to public GET responses
app.add_middleware(CacheControlMiddleware)

# 3. CORS — must be after logging so preflight requests are also logged
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],   # so the frontend can read the trace ID
)

# ── Routers ───────────────────────────────────────────────────────────────────
PREFIX = "/api/v1"

app.include_router(auth_router,       prefix=PREFIX)
app.include_router(posts_router,      prefix=PREFIX)
app.include_router(categories_router, prefix=PREFIX)
app.include_router(tags_router,       prefix=PREFIX)
app.include_router(comments_router,   prefix=PREFIX)
app.include_router(users_router,      prefix=PREFIX)


# ── Health endpoint ───────────────────────────────────────────────────────────
@app.get("/health", tags=["Health"], include_in_schema=False)
async def health():
    """
    Used by:
      - Railway/Render health checks
      - UptimeRobot pinger (prevents cold starts on free tier)
      - Kubernetes / load-balancer liveness probes if you ever migrate

    Returns Redis status so monitoring can alert on cache layer failure.
    """
    redis_ok = False
    r = get_redis()
    if r:
        try:
            await r.ping()
            redis_ok = True
        except Exception:
            pass

    return {
        "status": "ok",
        "version": settings.APP_VERSION,
        "redis": "connected" if redis_ok else "unavailable",
    }


@app.get("/", include_in_schema=False)
def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs" if settings.DEBUG else "disabled in production",
    }