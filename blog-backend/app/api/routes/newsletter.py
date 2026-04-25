import secrets
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List

from app.core.dependencies import get_current_user, require_admin
from app.db.database import get_db
from app.models.models import NewsletterSubscriber, NewsletterCampaign, NewsletterStatus, CampaignStatus, User
from app.schemas.schemas import (
    NewsletterSubscribeRequest, NewsletterSubscriberOut,
    CampaignCreate, CampaignOut, MessageOut,
)

router = APIRouter(prefix="/newsletter", tags=["Newsletter"])


# ── Public: Subscribe / Unsubscribe ──────────────────────────────────────────

@router.post("/subscribe", response_model=NewsletterSubscriberOut, status_code=201)
def subscribe(payload: NewsletterSubscribeRequest, db: Session = Depends(get_db)):
    existing = db.query(NewsletterSubscriber).filter(
        NewsletterSubscriber.email == payload.email
    ).first()

    if existing:
        if existing.status == NewsletterStatus.unsubscribed:
            existing.status        = NewsletterStatus.subscribed
            existing.confirm_token = secrets.token_urlsafe(32)
            existing.confirmed     = False
            db.commit()
            db.refresh(existing)
            return existing
        raise HTTPException(400, "Email already subscribed")

    subscriber = NewsletterSubscriber(
        email=payload.email,
        full_name=payload.full_name,
        confirm_token=secrets.token_urlsafe(32),
    )
    db.add(subscriber)
    db.commit()
    db.refresh(subscriber)
    # TODO: send confirmation email with confirm_token
    return subscriber


@router.get("/confirm/{token}", response_model=MessageOut)
def confirm_subscription(token: str, db: Session = Depends(get_db)):
    sub = db.query(NewsletterSubscriber).filter(
        NewsletterSubscriber.confirm_token == token
    ).first()
    if not sub:
        raise HTTPException(404, "Invalid confirmation token")
    sub.confirmed     = True
    sub.confirm_token = None
    db.commit()
    return MessageOut(message="Subscription confirmed! Welcome aboard.")


@router.delete("/unsubscribe/{token}", response_model=MessageOut)
def unsubscribe(token: str, db: Session = Depends(get_db)):
    sub = db.query(NewsletterSubscriber).filter(
        NewsletterSubscriber.confirm_token == token
    ).first()
    if not sub:
        raise HTTPException(404, "Invalid token")
    sub.status = NewsletterStatus.unsubscribed
    db.commit()
    return MessageOut(message="You have been unsubscribed.")


# ── Admin: Subscribers ────────────────────────────────────────────────────────

@router.get("/subscribers", response_model=List[NewsletterSubscriberOut])
def list_subscribers(
    page:     int = Query(1,  ge=1),
    per_page: int = Query(50, ge=1, le=200),
    db:       Session = Depends(get_db),
    _:        User    = Depends(require_admin),
):
    return db.query(NewsletterSubscriber)\
             .filter(NewsletterSubscriber.status == NewsletterStatus.subscribed,
                     NewsletterSubscriber.confirmed == True)\
             .offset((page - 1) * per_page).limit(per_page).all()


# ── Admin: Campaigns ──────────────────────────────────────────────────────────

@router.get("/campaigns", response_model=List[CampaignOut])
def list_campaigns(
    db: Session = Depends(get_db),
    _:  User    = Depends(require_admin),
):
    return db.query(NewsletterCampaign).order_by(NewsletterCampaign.created_at.desc()).all()


@router.post("/campaigns", response_model=CampaignOut, status_code=201)
def create_campaign(
    payload:      CampaignCreate,
    current_user: User    = Depends(require_admin),
    db:           Session = Depends(get_db),
):
    campaign = NewsletterCampaign(
        subject=payload.subject,
        content=payload.content,
        author_id=current_user.id,
    )
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    return campaign


@router.post("/campaigns/{campaign_id}/send", response_model=CampaignOut)
def send_campaign(
    campaign_id: int,
    db:  Session = Depends(get_db),
    _:   User    = Depends(require_admin),
):
    campaign = db.query(NewsletterCampaign).filter(NewsletterCampaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(404, "Campaign not found")
    if campaign.status == CampaignStatus.sent:
        raise HTTPException(400, "Campaign already sent")

    confirmed_count = db.query(NewsletterSubscriber).filter(
        NewsletterSubscriber.status   == NewsletterStatus.subscribed,
        NewsletterSubscriber.confirmed== True,
    ).count()

    from datetime import datetime, timezone
    campaign.status     = CampaignStatus.sent
    campaign.sent_count = confirmed_count
    campaign.sent_at    = datetime.now(timezone.utc)
    db.commit()
    db.refresh(campaign)
    # TODO: queue actual email sending via Celery / background task
    return campaign