"""
Cache-Control header middleware.

Adds Cache-Control headers to public GET responses so Cloudflare
(or any CDN) can cache them at the edge — meaning 1000 users
hitting a popular post generates ~1 origin request, not 1000.

Rules:
  - Public GET /api/v1/posts*  → public, max-age=120, s-maxage=300
  - All other routes           → no-store (auth endpoints, writes, etc.)
"""
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

PUBLIC_PREFIXES = ("/api/v1/posts", "/api/v1/categories", "/api/v1/tags")


class CacheControlMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        path = request.url.path

        if (
            request.method == "GET"
            and any(path.startswith(p) for p in PUBLIC_PREFIXES)
            and response.status_code == 200
        ):
            # Browser caches 2 min, CDN (Cloudflare s-maxage) caches 5 min
            response.headers["Cache-Control"] = "public, max-age=120, s-maxage=300, stale-while-revalidate=60"
        else:
            response.headers["Cache-Control"] = "no-store"

        return response