"""
Physics Platform API — entry point.

Startup sequence:
  1. Create all DB tables (idempotent — Alembic handles migrations in prod)
  2. Seed first admin account if DB is empty
  3. Connect Redis and initialise FastAPICache
  4. Register middleware (outermost = logging, then CDN headers, then CORS)
  5. Mount all routers under /api/v1

Shutdown:
  1. Close Redis connection pool gracefully

Worker scaling (render.yaml startCommand):
  --workers 4 × pool_size(4) = 16 DB conns — well under Render's 97-conn limit
  Formula if you change workers: pool_size = floor(92 / num_workers)
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.auth            import router as auth_router
from app.api.routes.categories      import categories_router, tags_router
from app.api.routes.comments        import router as comments_router
from app.api.routes.follows         import router as follows_router
from app.api.routes.newsletter      import router as newsletter_router
from app.api.routes.posts           import router as posts_router
from app.api.routes.reactions       import router as reactions_router
from app.api.routes.reading_progress import router as progress_router
from app.api.routes.search          import router as search_router
from app.api.routes.series          import router as series_router
from app.api.routes.users           import router as users_router
from app.core.cache                 import close_cache, get_redis, init_cache
from app.core.config                import settings
from app.db.database                import Base, SessionLocal, engine
from app.middleware.cache_control   import CacheControlMiddleware
from app.middleware.logging         import RequestLoggingMiddleware
from app.models                     import models  # noqa: F401 — registers models with Base
from app.services.seed              import seed_admin


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_admin(db)
    finally:
        db.close()
    await init_cache()
    yield
    await close_cache()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Physics platform API — posts, series, reactions, reading progress, "
        "follows, newsletter, search analytics, and role-based auth."
    ),
    lifespan=lifespan,
    docs_url="/docs"  if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# ── Middleware ────────────────────────────────────────────────────────────────
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(CacheControlMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
V1 = "/api/v1"

app.include_router(auth_router,        prefix=V1)
app.include_router(posts_router,       prefix=V1)
app.include_router(series_router,      prefix=V1)
app.include_router(categories_router,  prefix=V1)
app.include_router(tags_router,        prefix=V1)
app.include_router(comments_router,    prefix=V1)
app.include_router(reactions_router,   prefix=V1)
app.include_router(progress_router,    prefix=V1)
app.include_router(follows_router,     prefix=V1)
app.include_router(newsletter_router,  prefix=V1)
app.include_router(search_router,      prefix=V1)
app.include_router(users_router,       prefix=V1)


# ── Health ────────────────────────────────────────────────────────────────────
@app.get("/health", include_in_schema=False)
async def health():
    redis_ok = False
    r = get_redis()
    if r:
        try:
            await r.ping()
            redis_ok = True
        except Exception:
            pass
    return {"status": "ok", "version": settings.APP_VERSION,
            "redis": "connected" if redis_ok else "unavailable"}


@app.get("/", include_in_schema=False)
def root():
    return {"name": settings.APP_NAME, "version": settings.APP_VERSION,
            "docs": "/docs" if settings.DEBUG else "disabled in production"}