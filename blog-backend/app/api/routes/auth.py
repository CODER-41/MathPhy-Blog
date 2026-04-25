from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.models import User, UserRole
from app.schemas.schemas import UserCreate, UserOut, LoginRequest, TokenOut, RefreshRequest
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token
from app.core.dependencies import get_current_user
from app.core.cache import check_rate_limit
from app.core.config import settings

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=UserOut, status_code=201)
async def register(payload: UserCreate, request: Request, db: Session = Depends(get_db)):
    ip = request.client.host if request.client else "unknown"
    if not await check_rate_limit(f"rl:register:{ip}", settings.RATE_LIMIT_REGISTER, settings.RATE_LIMIT_REGISTER_WINDOW):
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Too many registration attempts.")
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(400, "Email already registered")
    if db.query(User).filter(User.username == payload.username).first():
        raise HTTPException(400, "Username already taken")
    user = User(
        username=payload.username,
        email=payload.email,
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
        role=UserRole.reader,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenOut)
async def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    ip = request.client.host if request.client else "unknown"
    if not await check_rate_limit(f"rl:login:{ip}", settings.RATE_LIMIT_LOGIN, settings.RATE_LIMIT_LOGIN_WINDOW):
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Too many login attempts.")
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(401, "Invalid email or password")
    if not user.is_active:
        raise HTTPException(403, "Account is deactivated")
    return TokenOut(
        access_token=create_access_token({"sub": str(user.id)}),
        refresh_token=create_refresh_token({"sub": str(user.id)}),
    )


@router.post("/refresh", response_model=TokenOut)
async def refresh(payload: RefreshRequest):
    data = decode_token(payload.refresh_token)
    if not data or data.get("type") != "refresh":
        raise HTTPException(401, "Invalid refresh token")
    return TokenOut(
        access_token=create_access_token({"sub": data["sub"]}),
        refresh_token=create_refresh_token({"sub": data["sub"]}),
    )


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user
