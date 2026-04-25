from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.database import get_db
from app.models.models import Follow, User
from app.schemas.schemas import FollowOut, FollowStatus, MessageOut

router = APIRouter(prefix="/users", tags=["Follows"])


@router.get("/{username}/follow-status", response_model=FollowStatus)
def follow_status(
    username:     str,
    current_user: User    = Depends(get_current_user),
    db:           Session = Depends(get_db),
):
    target = db.query(User).filter(User.username == username).first()
    if not target:
        raise HTTPException(404, "User not found")

    is_following    = db.query(Follow).filter(
        Follow.follower_id  == current_user.id,
        Follow.following_id == target.id,
    ).first() is not None
    follower_count  = db.query(Follow).filter(Follow.following_id == target.id).count()
    following_count = db.query(Follow).filter(Follow.follower_id  == target.id).count()

    return FollowStatus(
        is_following=is_following,
        follower_count=follower_count,
        following_count=following_count,
    )


@router.post("/{username}/follow", response_model=FollowOut, status_code=201)
def follow_user(
    username:     str,
    current_user: User    = Depends(get_current_user),
    db:           Session = Depends(get_db),
):
    target = db.query(User).filter(User.username == username).first()
    if not target:
        raise HTTPException(404, "User not found")
    if target.id == current_user.id:
        raise HTTPException(400, "Cannot follow yourself")

    existing = db.query(Follow).filter(
        Follow.follower_id  == current_user.id,
        Follow.following_id == target.id,
    ).first()
    if existing:
        raise HTTPException(400, "Already following this user")

    follow = Follow(follower_id=current_user.id, following_id=target.id)
    db.add(follow)
    db.commit()
    db.refresh(follow)
    return follow


@router.delete("/{username}/follow", status_code=204)
def unfollow_user(
    username:     str,
    current_user: User    = Depends(get_current_user),
    db:           Session = Depends(get_db),
):
    target = db.query(User).filter(User.username == username).first()
    if not target:
        raise HTTPException(404, "User not found")

    follow = db.query(Follow).filter(
        Follow.follower_id  == current_user.id,
        Follow.following_id == target.id,
    ).first()
    if not follow:
        raise HTTPException(404, "Not following this user")

    db.delete(follow)
    db.commit()