"""
Posts routes.

Caching strategy:
  - GET /posts        → cached CACHE_LIST_TTL (2 min), invalidated on any write
  - GET /posts/{slug} → cached CACHE_POST_TTL (5 min), invalidated on update/delete
  - POST/PUT/DELETE   → no cache, always invalidates relevant keys after commit

Cloudflare / CDN:
  - Cache-Control headers added by CacheControlMiddleware (see middleware/cache_control.py)
  - s-maxage=300 means Cloudflare holds a copy for 5 min at the edge

Scalability note:
  - fastapi-cache2 requires `request: Request` as first param — do not remove it
  - View counter is a best-effort increment; losing a count on Redis miss is acceptable
"""
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from python_slugify import slugify
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.cache import cache, invalidate_lists, invalidate_post
from app.core.config import settings
from app.core.dependencies import get_current_user, require_author
from app.db.database import get_db
from app.models.models import Post, PostStatus, Tag, User, UserRole
from app.schemas.schemas import (PaginatedPosts, PostCreate, PostOut,
                                  PostSummary, PostUpdate)

router = APIRouter(prefix="/posts", tags=["Posts"])


# ── Helpers ───────────────────────────────────────────────────────────────────

def _read_time(content: str) -> int:
    return max(1, round(len(content.split()) / 200))


def _unique_slug(title: str, db: Session, exclude_id: int | None = None) -> str:
    base = slugify(title)
    slug, n = base, 1
    while True:
        q = db.query(Post).filter(Post.slug == slug)
        if exclude_id:
            q = q.filter(Post.id != exclude_id)
        if not q.first():
            return slug
        slug, n = f"{base}-{n}", n + 1


def _paginate(query, page: int, per_page: int) -> dict:
    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    return dict(items=items, total=total, page=page,
                per_page=per_page, pages=-(-total // per_page))


# ── Public (cached) ───────────────────────────────────────────────────────────

@router.get("", response_model=PaginatedPosts)
@cache(expire=settings.CACHE_LIST_TTL)
async def list_posts(
    request: Request,
    page:     int            = Query(1,  ge=1),
    per_page: int            = Query(10, ge=1, le=50),
    category: Optional[str]  = None,
    tag:      Optional[str]  = None,
    search:   Optional[str]  = None,
    db:       Session        = Depends(get_db),
):
    q = db.query(Post).filter(Post.status == PostStatus.published)
    if category:
        q = q.join(Post.category).filter_by(slug=category)
    if tag:
        q = q.join(Post.tags).filter_by(slug=tag)
    if search:
        q = q.filter(or_(
            Post.title.ilike(f"%{search}%"),
            Post.excerpt.ilike(f"%{search}%"),
        ))
    return PaginatedPosts(**_paginate(q.order_by(Post.published_at.desc()), page, per_page))


@router.get("/{slug}", response_model=PostOut)
@cache(expire=settings.CACHE_POST_TTL)
async def get_post(request: Request, slug: str, db: Session = Depends(get_db)):
    post = db.query(Post).filter(
        Post.slug == slug, Post.status == PostStatus.published
    ).first()
    if not post:
        raise HTTPException(404, "Post not found")
    post.views += 1
    db.commit()
    db.refresh(post)
    return post


# ── Author / Admin ────────────────────────────────────────────────────────────

@router.get("/manage/all", response_model=PaginatedPosts)
async def list_all_posts(
    page:        int                   = Query(1,  ge=1),
    per_page:    int                   = Query(10, ge=1, le=50),
    post_status: Optional[PostStatus]  = Query(None, alias="status"),
    current_user: User                 = Depends(require_author),
    db:          Session               = Depends(get_db),
):
    q = db.query(Post)
    if current_user.role != UserRole.admin:
        q = q.filter(Post.author_id == current_user.id)
    if post_status:
        q = q.filter(Post.status == post_status)
    return PaginatedPosts(**_paginate(q.order_by(Post.created_at.desc()), page, per_page))


@router.post("", response_model=PostOut, status_code=201)
async def create_post(
    payload:      PostCreate = ...,
    current_user: User       = Depends(require_author),
    db:           Session    = Depends(get_db),
):
    tags = db.query(Tag).filter(Tag.id.in_(payload.tag_ids or [])).all()
    post = Post(
        title=payload.title,
        slug=_unique_slug(payload.title, db),
        excerpt=payload.excerpt,
        content=payload.content,
        cover_image_url=payload.cover_image_url,
        status=payload.status,
        category_id=payload.category_id,
        author_id=current_user.id,
        read_time=_read_time(payload.content),
        tags=tags,
        published_at=datetime.now(timezone.utc) if payload.status == PostStatus.published else None,
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    await invalidate_lists()
    return post


@router.put("/{post_id}", response_model=PostOut)
async def update_post(
    post_id:      int,
    payload:      PostUpdate,
    current_user: User    = Depends(require_author),
    db:           Session = Depends(get_db),
):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(404, "Post not found")
    if post.author_id != current_user.id and current_user.role != UserRole.admin:
        raise HTTPException(403, "Not your post")

    old_slug = post.slug
    if payload.title:
        post.title = payload.title
        post.slug  = _unique_slug(payload.title, db, exclude_id=post_id)
    if payload.excerpt      is not None: post.excerpt         = payload.excerpt
    if payload.content:
        post.content   = payload.content
        post.read_time = _read_time(payload.content)
    if payload.cover_image_url is not None: post.cover_image_url = payload.cover_image_url
    if payload.category_id     is not None: post.category_id     = payload.category_id
    if payload.status:
        if payload.status == PostStatus.published and post.status != PostStatus.published:
            post.published_at = datetime.now(timezone.utc)
        post.status = payload.status
    if payload.tag_ids is not None:
        post.tags = db.query(Tag).filter(Tag.id.in_(payload.tag_ids)).all()

    db.commit()
    db.refresh(post)
    await invalidate_post(old_slug)
    if post.slug != old_slug:
        await invalidate_post(post.slug)
    await invalidate_lists()
    return post


@router.delete("/{post_id}", status_code=204)
async def delete_post(
    post_id:      int,
    current_user: User    = Depends(require_author),
    db:           Session = Depends(get_db),
):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(404, "Post not found")
    if post.author_id != current_user.id and current_user.role != UserRole.admin:
        raise HTTPException(403, "Not your post")
    slug = post.slug
    db.delete(post)
    db.commit()
    await invalidate_post(slug)
    await invalidate_lists()