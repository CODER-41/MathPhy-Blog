"""
Pydantic schemas — request validation and response serialisation.

Design rules:
  - *Create schemas validate incoming data (strict)
  - *Update schemas are fully optional (PATCH semantics)
  - *Out schemas are what the API returns — never expose hashed_password
  - *Summary schemas are lightweight versions for list endpoints (omit heavy fields)
  - Nested schemas use *Out so foreign key objects are fully hydrated in responses
"""
from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, field_validator, model_validator

from app.models.models import (
    UserRole, PostStatus, DifficultyLevel,
    ReactionType, NewsletterStatus, CampaignStatus,
)


# ── User ──────────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    username:  str
    email:     EmailStr
    password:  str
    full_name: Optional[str] = None

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v

    @field_validator("username")
    @classmethod
    def username_valid(cls, v: str) -> str:
        if not v.isalnum() and "_" not in v:
            raise ValueError("Username must be alphanumeric (underscores allowed)")
        if len(v) < 3:
            raise ValueError("Username must be at least 3 characters")
        return v.lower()


class UserUpdate(BaseModel):
    full_name:        Optional[str] = None
    bio:              Optional[str] = None
    avatar_url:       Optional[str] = None
    cover_image_url:  Optional[str] = None
    institution:      Optional[str] = None
    specialization:   Optional[str] = None
    website_url:      Optional[str] = None
    twitter_url:      Optional[str] = None
    github_url:       Optional[str] = None
    linkedin_url:     Optional[str] = None
    orcid_id:         Optional[str] = None
    email_on_comment: Optional[bool] = None
    email_on_follow:  Optional[bool] = None


class UserRoleUpdate(BaseModel):
    role: UserRole


class UserOut(BaseModel):
    id:               int
    username:         str
    email:            EmailStr
    full_name:        Optional[str] = None
    bio:              Optional[str] = None
    avatar_url:       Optional[str] = None
    cover_image_url:  Optional[str] = None
    institution:      Optional[str] = None
    specialization:   Optional[str] = None
    website_url:      Optional[str] = None
    twitter_url:      Optional[str] = None
    github_url:       Optional[str] = None
    linkedin_url:     Optional[str] = None
    orcid_id:         Optional[str] = None
    role:             UserRole
    is_active:        bool
    email_on_comment: bool
    email_on_follow:  bool
    created_at:       datetime

    class Config:
        from_attributes = True


class UserPublic(BaseModel):
    """Minimal public profile — shown on post cards and author pages."""
    id:            int
    username:      str
    full_name:     Optional[str] = None
    avatar_url:    Optional[str] = None
    institution:   Optional[str] = None
    specialization:Optional[str] = None
    role:          UserRole

    class Config:
        from_attributes = True


# ── Auth ──────────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email:    EmailStr
    password: str


class TokenOut(BaseModel):
    access_token:  str
    refresh_token: str
    token_type:    str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


# ── Category ──────────────────────────────────────────────────────────────────

class CategoryCreate(BaseModel):
    name:        str
    description: Optional[str] = None
    icon:        Optional[str] = None
    color:       Optional[str] = None
    parent_id:   Optional[int] = None
    sort_order:  int = 0


class CategoryUpdate(BaseModel):
    name:        Optional[str] = None
    description: Optional[str] = None
    icon:        Optional[str] = None
    color:       Optional[str] = None
    parent_id:   Optional[int] = None
    sort_order:  Optional[int] = None


class CategoryOut(BaseModel):
    id:          int
    name:        str
    slug:        str
    description: Optional[str] = None
    icon:        Optional[str] = None
    color:       Optional[str] = None
    parent_id:   Optional[int] = None
    sort_order:  int
    created_at:  datetime
    children:    List["CategoryOut"] = []

    class Config:
        from_attributes = True


CategoryOut.model_rebuild()


# ── Tag ───────────────────────────────────────────────────────────────────────

class TagCreate(BaseModel):
    name: str


class TagOut(BaseModel):
    id:   int
    slug: str
    name: str

    class Config:
        from_attributes = True


# ── Series ────────────────────────────────────────────────────────────────────

class SeriesCreate(BaseModel):
    title:           str
    description:     Optional[str] = None
    cover_image_url: Optional[str] = None
    category_id:     Optional[int] = None
    is_complete:     bool = False


class SeriesUpdate(BaseModel):
    title:           Optional[str]  = None
    description:     Optional[str]  = None
    cover_image_url: Optional[str]  = None
    category_id:     Optional[int]  = None
    is_complete:     Optional[bool] = None


class SeriesOut(BaseModel):
    id:              int
    title:           str
    slug:            str
    description:     Optional[str] = None
    cover_image_url: Optional[str] = None
    is_complete:     bool
    author:          UserPublic
    category:        Optional[CategoryOut] = None
    created_at:      datetime
    updated_at:      Optional[datetime] = None

    class Config:
        from_attributes = True


class SeriesSummary(BaseModel):
    """Used in PostOut — shows which series a post belongs to."""
    id:    int
    title: str
    slug:  str

    class Config:
        from_attributes = True


# ── Post ──────────────────────────────────────────────────────────────────────

class PostCreate(BaseModel):
    title:            str
    excerpt:          Optional[str]            = None
    content:          str
    cover_image_url:  Optional[str]            = None
    cover_image_alt:  Optional[str]            = None
    meta_description: Optional[str]            = None
    difficulty:       Optional[DifficultyLevel]= None
    latex_macros:     Optional[str]            = None
    prerequisites:    Optional[str]            = None
    status:           PostStatus               = PostStatus.draft
    is_featured:      bool                     = False
    is_premium:       bool                     = False
    allow_comments:   bool                     = True
    category_id:      Optional[int]            = None
    series_id:        Optional[int]            = None
    series_order:     Optional[int]            = None
    tag_ids:          List[int]                = []

    @field_validator("meta_description")
    @classmethod
    def meta_max_length(cls, v: Optional[str]) -> Optional[str]:
        if v and len(v) > 160:
            raise ValueError("meta_description must be 160 characters or less")
        return v


class PostUpdate(BaseModel):
    title:            Optional[str]             = None
    excerpt:          Optional[str]             = None
    content:          Optional[str]             = None
    cover_image_url:  Optional[str]             = None
    cover_image_alt:  Optional[str]             = None
    meta_description: Optional[str]             = None
    difficulty:       Optional[DifficultyLevel] = None
    latex_macros:     Optional[str]             = None
    prerequisites:    Optional[str]             = None
    status:           Optional[PostStatus]      = None
    is_featured:      Optional[bool]            = None
    is_premium:       Optional[bool]            = None
    allow_comments:   Optional[bool]            = None
    category_id:      Optional[int]             = None
    series_id:        Optional[int]             = None
    series_order:     Optional[int]             = None
    tag_ids:          Optional[List[int]]       = None


class PostOut(BaseModel):
    id:               int
    title:            str
    slug:             str
    excerpt:          Optional[str]             = None
    content:          str
    cover_image_url:  Optional[str]             = None
    cover_image_alt:  Optional[str]             = None
    meta_description: Optional[str]             = None
    difficulty:       Optional[DifficultyLevel] = None
    latex_macros:     Optional[str]             = None
    prerequisites:    Optional[str]             = None
    status:           PostStatus
    is_featured:      bool
    is_premium:       bool
    allow_comments:   bool
    views:            int
    read_time:        int
    reaction_count:   int
    comment_count:    int
    series_order:     Optional[int]             = None
    author:           UserPublic
    category:         Optional[CategoryOut]     = None
    series:           Optional[SeriesSummary]   = None
    tags:             List[TagOut]              = []
    created_at:       datetime
    updated_at:       Optional[datetime]        = None
    published_at:     Optional[datetime]        = None

    class Config:
        from_attributes = True


class PostSummary(BaseModel):
    """Lightweight — used in list endpoints. No content or latex_macros."""
    id:               int
    title:            str
    slug:             str
    excerpt:          Optional[str]             = None
    cover_image_url:  Optional[str]             = None
    difficulty:       Optional[DifficultyLevel] = None
    status:           PostStatus
    is_featured:      bool
    is_premium:       bool
    views:            int
    read_time:        int
    reaction_count:   int
    comment_count:    int
    series_order:     Optional[int]             = None
    author:           UserPublic
    category:         Optional[CategoryOut]     = None
    series:           Optional[SeriesSummary]   = None
    tags:             List[TagOut]              = []
    published_at:     Optional[datetime]        = None
    created_at:       datetime

    class Config:
        from_attributes = True


class PaginatedPosts(BaseModel):
    items:    List[PostSummary]
    total:    int
    page:     int
    per_page: int
    pages:    int


# ── PostView ──────────────────────────────────────────────────────────────────

class PostViewOut(BaseModel):
    recorded: bool
    total_views: int


# ── Reaction ──────────────────────────────────────────────────────────────────

class ReactionCreate(BaseModel):
    type: ReactionType


class ReactionOut(BaseModel):
    id:           int
    type:         ReactionType
    post_id:      int
    user_id:      int
    created_at:   datetime

    class Config:
        from_attributes = True


class ReactionSummary(BaseModel):
    """Returned on post detail — shows counts + whether current user reacted."""
    likes:          int
    bookmarks:      int
    user_liked:     bool = False
    user_bookmarked:bool = False


# ── ReadingProgress ───────────────────────────────────────────────────────────

class ReadingProgressUpsert(BaseModel):
    progress_pct: int

    @field_validator("progress_pct")
    @classmethod
    def pct_range(cls, v: int) -> int:
        if not 0 <= v <= 100:
            raise ValueError("progress_pct must be between 0 and 100")
        return v


class ReadingProgressOut(BaseModel):
    post_id:      int
    progress_pct: int
    completed:    bool
    last_read_at: datetime

    class Config:
        from_attributes = True


# ── Comment ───────────────────────────────────────────────────────────────────

class CommentCreate(BaseModel):
    content:   str
    parent_id: Optional[int] = None


class CommentUpdate(BaseModel):
    content: str


class CommentOut(BaseModel):
    id:          int
    content:     str
    is_approved: bool
    is_edited:   bool
    like_count:  int
    author:      UserPublic
    parent_id:   Optional[int] = None
    created_at:  datetime
    updated_at:  Optional[datetime] = None
    replies:     List["CommentOut"] = []

    class Config:
        from_attributes = True


CommentOut.model_rebuild()


# ── Follow ────────────────────────────────────────────────────────────────────

class FollowOut(BaseModel):
    follower_id:  int
    following_id: int
    created_at:   datetime

    class Config:
        from_attributes = True


class FollowStatus(BaseModel):
    is_following:   bool
    follower_count: int
    following_count:int


# ── Series ────────────────────────────────────────────────────────────────────

class PaginatedSeries(BaseModel):
    items:    List[SeriesOut]
    total:    int
    page:     int
    per_page: int
    pages:    int


# ── Newsletter ────────────────────────────────────────────────────────────────

class NewsletterSubscribeRequest(BaseModel):
    email:     EmailStr
    full_name: Optional[str] = None


class NewsletterSubscriberOut(BaseModel):
    id:        int
    email:     EmailStr
    full_name: Optional[str] = None
    status:    NewsletterStatus
    confirmed: bool

    class Config:
        from_attributes = True


class CampaignCreate(BaseModel):
    subject: str
    content: str


class CampaignOut(BaseModel):
    id:          int
    subject:     str
    content:     str
    status:      CampaignStatus
    sent_count:  int
    author:      UserPublic
    created_at:  datetime
    sent_at:     Optional[datetime] = None

    class Config:
        from_attributes = True


# ── SearchLog ─────────────────────────────────────────────────────────────────

class SearchRequest(BaseModel):
    query: str


class SearchLogOut(BaseModel):
    query:         str
    results_count: int
    searched_at:   datetime

    class Config:
        from_attributes = True


class TopSearch(BaseModel):
    query: str
    count: int


# ── Generic ───────────────────────────────────────────────────────────────────

class ErrorOut(BaseModel):
    detail:     str
    request_id: Optional[str] = None


class MessageOut(BaseModel):
    message: str