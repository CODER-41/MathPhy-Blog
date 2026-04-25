from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List

from app.core.cache import cache, invalidate_comments
from app.core.config import settings
from app.core.dependencies import get_current_user, require_admin
from app.db.database import get_db
from app.models.models import Comment, Post, PostStatus, User, UserRole
from app.schemas.schemas import CommentCreate, CommentUpdate, CommentOut

router = APIRouter(tags=["Comments"])


@router.get("/posts/{slug}/comments", response_model=List[CommentOut])
@cache(expire=settings.CACHE_COMMENTS_TTL)
async def get_comments(request: Request, slug: str, db: Session = Depends(get_db)):
    post = db.query(Post).filter(Post.slug == slug, Post.status == PostStatus.published).first()
    if not post:
        raise HTTPException(404, "Post not found")
    return db.query(Comment).filter(
        Comment.post_id == post.id,
        Comment.is_approved == True,
        Comment.parent_id == None,
    ).all()


@router.post("/posts/{slug}/comments", response_model=CommentOut, status_code=201)
async def add_comment(slug: str, payload: CommentCreate,
                      current_user: User = Depends(get_current_user),
                      db: Session = Depends(get_db)):
    post = db.query(Post).filter(Post.slug == slug, Post.status == PostStatus.published).first()
    if not post:
        raise HTTPException(404, "Post not found")
    if not post.allow_comments:
        raise HTTPException(403, "Comments are disabled for this post")
    comment = Comment(
        content=payload.content,
        post_id=post.id,
        author_id=current_user.id,
        parent_id=payload.parent_id,
        is_approved=current_user.role in (UserRole.admin, UserRole.author),
    )
    db.add(comment)
    post.comment_count += 1
    db.commit()
    db.refresh(comment)
    await invalidate_comments(slug)
    return comment


@router.put("/comments/{comment_id}", response_model=CommentOut)
async def update_comment(comment_id: int, payload: CommentUpdate,
                         current_user: User = Depends(get_current_user),
                         db: Session = Depends(get_db)):
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(404, "Comment not found")
    if comment.author_id != current_user.id:
        raise HTTPException(403, "Not your comment")
    comment.content   = payload.content
    comment.is_edited = True
    db.commit()
    db.refresh(comment)
    await invalidate_comments(comment.post.slug)
    return comment


@router.patch("/comments/{comment_id}/approve", response_model=CommentOut)
async def approve_comment(comment_id: int, db: Session = Depends(get_db),
                          _: User = Depends(require_admin)):
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(404, "Comment not found")
    comment.is_approved = True
    db.commit()
    db.refresh(comment)
    await invalidate_comments(comment.post.slug)
    return comment


@router.delete("/comments/{comment_id}", status_code=204)
async def delete_comment(comment_id: int, current_user: User = Depends(get_current_user),
                         db: Session = Depends(get_db)):
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(404, "Comment not found")
    if comment.author_id != current_user.id and current_user.role != UserRole.admin:
        raise HTTPException(403, "Not your comment")
    slug = comment.post.slug
    comment.post.comment_count = max(0, comment.post.comment_count - 1)
    db.delete(comment)
    db.commit()
    await invalidate_comments(slug)
