from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import func, or_
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.cache import cache
from app.core.config import settings
from app.core.dependencies import require_admin
from app.db.database import get_db
from app.models.models import Post, PostStatus, SearchLog, User
from app.schemas.schemas import PaginatedPosts, TopSearch

router = APIRouter(prefix="/search", tags=["Search"])


@router.get("", response_model=PaginatedPosts)
@cache(expire=60)   # short cache — search results change as new posts are published
async def search_posts(
    request:  Request,
    q:        str = Query(..., min_length=2, description="Search query"),
    page:     int = Query(1,  ge=1),
    per_page: int = Query(10, ge=1, le=50),
    difficulty: Optional[str] = None,
    category:   Optional[str] = None,
    db:       Session = Depends(get_db),
):
    query = db.query(Post).filter(
        Post.status == PostStatus.published,
        or_(
            Post.title.ilike(f"%{q}%"),
            Post.excerpt.ilike(f"%{q}%"),
            Post.content.ilike(f"%{q}%"),
        )
    )

    if difficulty:
        query = query.filter(Post.difficulty == difficulty)
    if category:
        query = query.join(Post.category).filter_by(slug=category)

    total   = query.count()
    results = query.order_by(Post.published_at.desc())\
                   .offset((page - 1) * per_page).limit(per_page).all()

    # Log the search (best-effort, don't block response)
    try:
        ip = request.client.host if request.client else None
        user_id = None
        log = SearchLog(query=q, results_count=total, ip_address=ip, user_id=user_id)
        db.add(log)
        db.commit()
    except Exception:
        pass

    return PaginatedPosts(
        items=results, total=total, page=page,
        per_page=per_page, pages=-(-total // per_page),
    )


@router.get("/top", response_model=List[TopSearch])
async def top_searches(
    request: Request,
    limit:   int     = Query(10, ge=1, le=50),
    db:      Session = Depends(get_db),
    _:       User    = Depends(require_admin),
):
    """Returns the most searched terms — useful for content strategy."""
    results = (
        db.query(SearchLog.query, func.count(SearchLog.id).label("count"))
        .group_by(SearchLog.query)
        .order_by(func.count(SearchLog.id).desc())
        .limit(limit)
        .all()
    )
    return [TopSearch(query=r.query, count=r.count) for r in results]