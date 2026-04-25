import logging
from sqlalchemy.orm import Session
from app.models.models import User, UserRole
from app.core.security import hash_password
from app.core.config import settings

logger = logging.getLogger(__name__)


def seed_admin(db: Session) -> None:
    if db.query(User).count() > 0:
        return
    admin = User(
        username=settings.FIRST_ADMIN_USERNAME,
        email=settings.FIRST_ADMIN_EMAIL,
        hashed_password=hash_password(settings.FIRST_ADMIN_PASSWORD),
        role=UserRole.admin,
        is_active=True,
    )
    db.add(admin)
    db.commit()
    logger.info("Admin account seeded: %s", settings.FIRST_ADMIN_EMAIL)
