from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from slugify import slugify
from sqlalchemy.orm import Session

from app.core.cache import cache, invalidate_lists
from app.core.config import settings
from app.core.dependencies import get_current_user, require_author
from app.db.database import get_db
from app.models.models import Series, Post, User, UserRole
from app.schemas.schemas import SeriesCreate, SeriesUpdate, SeriesOut, PaginatedSeries

router = APIRouter(prefix="/series", tags=["Series"])


def _unique_slug(title: str, db: Session, exclude_id: int | None = None) -> str:
    base = slugify(title)
    slug, n = base, 1
    while True:
        q = db.query(Series).filter(Series.slug == slug)
        if exclude_id:
            q = q.filter(Series.id != exclude_id)
        if not q.first():
            return slug
        slug, n = f"{base}-{n}", n + 1


@router.get("", response_model=PaginatedSeries)
@cache(expire=settings.CACHE_LIST_TTL)
async def list_series(
    request:  Request,
    page:     int = Query(1,  ge=1),
    per_page: int = Query(10, ge=1, le=50),
    db:       Session = Depends(get_db),
):
    total = db.query(Series).count()
    items = db.query(Series).order_by(Series.created_at.desc())\
              .offset((page - 1) * per_page).limit(per_page).all()
    return PaginatedSeries(items=items, total=total, page=page,
                           per_page=per_page, pages=-(-total // per_page))


@router.get("/{slug}", response_model=SeriesOut)
@cache(expire=settings.CACHE_POST_TTL)
async def get_series(request: Request, slug: str, db: Session = Depends(get_db)):
    s = db.query(Series).filter(Series.slug == slug).first()
    if not s:
        raise HTTPException(404, "Series not found")
    return s


@router.post("", response_model=SeriesOut, status_code=201)
async def create_series(
    payload:      SeriesCreate,
    current_user: User    = Depends(require_author),
    db:           Session = Depends(get_db),
):
    s = Series(
        title=payload.title,
        slug=_unique_slug(payload.title, db),
        description=payload.description,
        cover_image_url=payload.cover_image_url,
        category_id=payload.category_id,
        is_complete=payload.is_complete,
        author_id=current_user.id,
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    await invalidate_lists()
    return s


@router.put("/{series_id}", response_model=SeriesOut)
async def update_series(
    series_id:    int,
    payload:      SeriesUpdate,
    current_user: User    = Depends(require_author),
    db:           Session = Depends(get_db),
):
    s = db.query(Series).filter(Series.id == series_id).first()
    if not s:
        raise HTTPException(404, "Series not found")
    if s.author_id != current_user.id and current_user.role != UserRole.admin:
        raise HTTPException(403, "Not your series")

    if payload.title:
        s.title = payload.title
        s.slug  = _unique_slug(payload.title, db, exclude_id=series_id)
    if payload.description     is not None: s.description     = payload.description
    if payload.cover_image_url is not None: s.cover_image_url = payload.cover_image_url
    if payload.category_id     is not None: s.category_id     = payload.category_id
    if payload.is_complete     is not None: s.is_complete      = payload.is_complete

    db.commit()
    db.refresh(s)
    await invalidate_lists()
    return s


@router.delete("/{series_id}", status_code=204)
async def delete_series(
    series_id:    int,
    current_user: User    = Depends(require_author),
    db:           Session = Depends(get_db),
):
    s = db.query(Series).filter(Series.id == series_id).first()
    if not s:
        raise HTTPException(404, "Series not found")
    if s.author_id != current_user.id and current_user.role != UserRole.admin:
        raise HTTPException(403, "Not your series")
    db.delete(s)
    db.commit()
    await invalidate_lists()