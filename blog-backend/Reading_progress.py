from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.dependencies import get_current_user
from app.db.database import get_db
from app.models.models import ReadingProgress, Post, PostStatus, User
from app.schemas.schemas import ReadingProgressUpsert, ReadingProgressOut

router = APIRouter(prefix="/reading-progress", tags=["Reading Progress"])


@router.put("/{slug}", response_model=ReadingProgressOut)
async def upsert_progress(
    slug:         str,
    payload:      ReadingProgressUpsert,
    current_user: User    = Depends(get_current_user),
    db:           Session = Depends(get_db),
):
    """Create or update reading progress for the current user on a post."""
    post = db.query(Post).filter(Post.slug == slug).first()
    if not post:
        raise HTTPException(404, "Post not found")

    progress = db.query(ReadingProgress).filter(
        ReadingProgress.user_id == current_user.id,
        ReadingProgress.post_id == post.id,
    ).first()

    if progress:
        progress.progress_pct = max(progress.progress_pct, payload.progress_pct)
        progress.completed    = progress.progress_pct >= 100
    else:
        progress = ReadingProgress(
            user_id=current_user.id,
            post_id=post.id,
            progress_pct=payload.progress_pct,
            completed=payload.progress_pct >= 100,
        )
        db.add(progress)

    db.commit()
    db.refresh(progress)
    return progress


@router.get("", response_model=List[ReadingProgressOut])
def get_my_progress(
    current_user: User    = Depends(get_current_user),
    db:           Session = Depends(get_db),
):
    """Return all reading progress records for the current user."""
    return db.query(ReadingProgress)\
             .filter(ReadingProgress.user_id == current_user.id)\
             .order_by(ReadingProgress.last_read_at.desc())\
             .all()


@router.get("/{slug}", response_model=ReadingProgressOut)
def get_progress_for_post(
    slug:         str,
    current_user: User    = Depends(get_current_user),
    db:           Session = Depends(get_db),
):
    post = db.query(Post).filter(Post.slug == slug).first()
    if not post:
        raise HTTPException(404, "Post not found")
    progress = db.query(ReadingProgress).filter(
        ReadingProgress.user_id == current_user.id,
        ReadingProgress.post_id == post.id,
    ).first()
    if not progress:
        raise HTTPException(404, "No progress recorded yet")
    return progress