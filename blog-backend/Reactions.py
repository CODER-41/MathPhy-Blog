from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.core.cache import invalidate_post
from app.db.database import get_db
from app.models.models import Reaction, ReactionType, Post, PostStatus, User
from app.schemas.schemas import ReactionCreate, ReactionSummary, MessageOut

router = APIRouter(prefix="/posts", tags=["Reactions"])


def _reaction_summary(post: Post, user_id: int | None) -> ReactionSummary:
    likes     = sum(1 for r in post.reactions if r.type == ReactionType.like)
    bookmarks = sum(1 for r in post.reactions if r.type == ReactionType.bookmark)
    user_liked     = any(r.user_id == user_id and r.type == ReactionType.like     for r in post.reactions) if user_id else False
    user_bookmarked= any(r.user_id == user_id and r.type == ReactionType.bookmark for r in post.reactions) if user_id else False
    return ReactionSummary(likes=likes, bookmarks=bookmarks,
                           user_liked=user_liked, user_bookmarked=user_bookmarked)


@router.get("/{slug}/reactions", response_model=ReactionSummary)
async def get_reactions(
    slug:    str,
    request: Request,
    db:      Session = Depends(get_db),
):
    post = db.query(Post).filter(Post.slug == slug, Post.status == PostStatus.published).first()
    if not post:
        raise HTTPException(404, "Post not found")

    # Try to get user_id from optional token
    user_id = None
    try:
        from app.core.dependencies import bearer
        from app.core.security import decode_token
        auth = await bearer(request)
        if auth:
            data = decode_token(auth.credentials)
            if data:
                user_id = int(data.get("sub", 0))
    except Exception:
        pass

    return _reaction_summary(post, user_id)


@router.post("/{slug}/reactions", response_model=ReactionSummary, status_code=201)
async def toggle_reaction(
    slug:         str,
    payload:      ReactionCreate,
    current_user: User    = Depends(get_current_user),
    db:           Session = Depends(get_db),
):
    post = db.query(Post).filter(Post.slug == slug, Post.status == PostStatus.published).first()
    if not post:
        raise HTTPException(404, "Post not found")

    existing = db.query(Reaction).filter(
        Reaction.post_id == post.id,
        Reaction.user_id == current_user.id,
        Reaction.type    == payload.type,
    ).first()

    if existing:
        # Toggle off — remove reaction
        db.delete(existing)
        if payload.type == ReactionType.like:
            post.reaction_count = max(0, post.reaction_count - 1)
    else:
        # Toggle on — add reaction
        db.add(Reaction(post_id=post.id, user_id=current_user.id, type=payload.type))
        if payload.type == ReactionType.like:
            post.reaction_count += 1

    db.commit()
    db.refresh(post)
    await invalidate_post(slug)
    return _reaction_summary(post, current_user.id)