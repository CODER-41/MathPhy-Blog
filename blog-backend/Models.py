"""
Physics Platform — Database Models (Phase 1)

Models:
  User            — auth + rich author profile (institution, specialization, socials)
  Category        — nested (parent/child), with icon + color for UI
  Tag             — unchanged
  Series          — groups multi-part posts (e.g. "Quantum Mechanics 101")
  Post            — full physics blog post with all metadata
  PostView        — unique IP view tracking (prevents refresh inflation)
  Reaction        — likes + bookmarks per user per post
  ReadingProgress — tracks how far a user has read (per post)
  Comment         — nested comments with moderation + likes
  Follow          — user follows an author
  Newsletter      — email subscribers + campaign log
  SearchLog       — query analytics for discovery insights

Index strategy:
  - All slug columns: unique + index (primary lookup)
  - status + published_at: composite index (most common list query)
  - All FK columns: indexed for join performance
  - PostView: composite unique (post_id, ip_address, date) — prevents duplicate counts
  - Reaction: composite unique (user_id, post_id, type) — one reaction per type per user
"""

import enum
from sqlalchemy import (
    Boolean, Column, Date, DateTime, Enum, ForeignKey,
    Index, Integer, String, Text, Table, UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base


# ── Enums ─────────────────────────────────────────────────────────────────────

class UserRole(str, enum.Enum):
    admin  = "admin"
    author = "author"
    reader = "reader"


class PostStatus(str, enum.Enum):
    draft     = "draft"
    published = "published"
    archived  = "archived"


class DifficultyLevel(str, enum.Enum):
    beginner     = "beginner"
    intermediate = "intermediate"
    advanced     = "advanced"
    research     = "research"


class ReactionType(str, enum.Enum):
    like     = "like"
    bookmark = "bookmark"


class NewsletterStatus(str, enum.Enum):
    subscribed   = "subscribed"
    unsubscribed = "unsubscribed"


class CampaignStatus(str, enum.Enum):
    draft = "draft"
    sent  = "sent"


# ── Association tables ────────────────────────────────────────────────────────

post_tags = Table(
    "post_tags", Base.metadata,
    Column("post_id", Integer, ForeignKey("posts.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id",  Integer, ForeignKey("tags.id",  ondelete="CASCADE"), primary_key=True),
)


# ── User ──────────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id              = Column(Integer, primary_key=True)
    username        = Column(String(50),  unique=True, nullable=False, index=True)
    email           = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role            = Column(Enum(UserRole), default=UserRole.reader, nullable=False, index=True)
    is_active       = Column(Boolean, default=True)

    # Profile
    full_name       = Column(String(100), nullable=True)
    bio             = Column(Text,        nullable=True)
    avatar_url      = Column(String(500), nullable=True)
    cover_image_url = Column(String(500), nullable=True)  # profile banner

    # Author-specific fields
    institution     = Column(String(200), nullable=True)  # university / lab / company
    specialization  = Column(String(200), nullable=True)  # e.g. "Quantum Field Theory"
    website_url     = Column(String(500), nullable=True)
    twitter_url     = Column(String(500), nullable=True)
    github_url      = Column(String(500), nullable=True)
    linkedin_url    = Column(String(500), nullable=True)
    orcid_id        = Column(String(50),  nullable=True)  # researcher ORCID identifier

    # Preferences
    email_on_comment = Column(Boolean, default=True)   # notify on new comment
    email_on_follow  = Column(Boolean, default=True)   # notify on new follower

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    posts            = relationship("Post",            back_populates="author")
    comments         = relationship("Comment",         back_populates="author")
    reactions        = relationship("Reaction",        back_populates="user")
    reading_progress = relationship("ReadingProgress", back_populates="user")
    following        = relationship("Follow", foreign_keys="Follow.follower_id", back_populates="follower")
    followers        = relationship("Follow", foreign_keys="Follow.following_id", back_populates="following")


# ── Category ──────────────────────────────────────────────────────────────────

class Category(Base):
    __tablename__ = "categories"

    id          = Column(Integer, primary_key=True)
    name        = Column(String(100), unique=True, nullable=False)
    slug        = Column(String(120), unique=True, nullable=False, index=True)
    description = Column(Text,        nullable=True)
    icon        = Column(String(50),  nullable=True)   # e.g. "atom", "wave", "rocket"
    color       = Column(String(20),  nullable=True)   # e.g. "#5DCAA5" for badge styling
    parent_id   = Column(Integer, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True, index=True)
    sort_order  = Column(Integer, default=0)           # for custom ordering in nav
    created_at  = Column(DateTime(timezone=True), server_default=func.now())

    posts    = relationship("Post",     back_populates="category")
    parent   = relationship("Category", remote_side="Category.id", back_populates="children")
    children = relationship("Category", back_populates="parent")


# ── Tag ───────────────────────────────────────────────────────────────────────

class Tag(Base):
    __tablename__ = "tags"

    id   = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    slug = Column(String(60), unique=True, nullable=False, index=True)

    posts = relationship("Post", secondary=post_tags, back_populates="tags")


# ── Series ────────────────────────────────────────────────────────────────────

class Series(Base):
    """Groups related posts into ordered sequences, e.g. 'Quantum Mechanics 101 Parts 1–5'."""
    __tablename__ = "series"

    id              = Column(Integer, primary_key=True)
    title           = Column(String(300), nullable=False)
    slug            = Column(String(350), unique=True, nullable=False, index=True)
    description     = Column(Text,        nullable=True)
    cover_image_url = Column(String(500), nullable=True)
    is_complete     = Column(Boolean, default=False)  # marks series as finished
    author_id       = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    category_id     = Column(Integer, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True, index=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    author   = relationship("User",     foreign_keys=[author_id])
    category = relationship("Category", foreign_keys=[category_id])
    posts    = relationship("Post",     back_populates="series", order_by="Post.series_order")


# ── Post ──────────────────────────────────────────────────────────────────────

class Post(Base):
    __tablename__ = "posts"

    id              = Column(Integer, primary_key=True)
    title           = Column(String(300), nullable=False)
    slug            = Column(String(350), unique=True, nullable=False, index=True)
    excerpt         = Column(Text,        nullable=True)
    content         = Column(Text,        nullable=False)   # Markdown + LaTeX
    cover_image_url = Column(String(500), nullable=True)
    cover_image_alt = Column(String(300), nullable=True)    # accessibility
    meta_description= Column(String(160), nullable=True)    # SEO — max 160 chars

    # Physics-specific
    difficulty      = Column(Enum(DifficultyLevel), nullable=True, index=True)
    latex_macros    = Column(Text, nullable=True)           # custom \newcommand definitions
    prerequisites   = Column(Text, nullable=True)           # free-text or comma-sep slugs

    # Status + visibility
    status          = Column(Enum(PostStatus), default=PostStatus.draft, nullable=False, index=True)
    is_featured     = Column(Boolean, default=False, index=True)  # pinned to homepage
    is_premium      = Column(Boolean, default=False, index=True)  # paywalled content
    allow_comments  = Column(Boolean, default=True)

    # Metrics (denormalised for performance — no JOIN needed for list views)
    views           = Column(Integer, default=0)
    read_time       = Column(Integer, default=0)            # minutes
    reaction_count  = Column(Integer, default=0)            # cached like count
    comment_count   = Column(Integer, default=0)            # cached comment count

    # Series membership
    series_id       = Column(Integer, ForeignKey("series.id", ondelete="SET NULL"), nullable=True, index=True)
    series_order    = Column(Integer, nullable=True)        # position within series

    # Foreign keys
    author_id       = Column(Integer, ForeignKey("users.id"),      nullable=False, index=True)
    category_id     = Column(Integer, ForeignKey("categories.id"), nullable=True,  index=True)

    created_at   = Column(DateTime(timezone=True), server_default=func.now())
    updated_at   = Column(DateTime(timezone=True), onupdate=func.now())
    published_at = Column(DateTime(timezone=True), nullable=True, index=True)

    # Relationships
    author           = relationship("User",            back_populates="posts")
    category         = relationship("Category",        back_populates="posts")
    series           = relationship("Series",          back_populates="posts")
    tags             = relationship("Tag",             secondary=post_tags, back_populates="posts")
    comments         = relationship("Comment",         back_populates="post", cascade="all, delete-orphan")
    reactions        = relationship("Reaction",        back_populates="post", cascade="all, delete-orphan")
    views_log        = relationship("PostView",        back_populates="post", cascade="all, delete-orphan")
    reading_progress = relationship("ReadingProgress", back_populates="post", cascade="all, delete-orphan")

    __table_args__ = (
        # Most common query: published posts ordered by date
        Index("ix_posts_status_published_at", "status", "published_at"),
        # Featured published posts for homepage
        Index("ix_posts_featured_status", "is_featured", "status"),
    )


# ── PostView ──────────────────────────────────────────────────────────────────

class PostView(Base):
    """
    Tracks unique views per post per IP per day.
    Prevents view count inflation from page refreshes.
    A user refreshing 100 times still counts as 1 view per day.
    """
    __tablename__ = "post_views"

    id         = Column(Integer, primary_key=True)
    post_id    = Column(Integer, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False, index=True)
    ip_address = Column(String(45), nullable=False)   # supports IPv6
    user_id    = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    viewed_at  = Column(Date, server_default=func.current_date())

    post = relationship("Post", back_populates="views_log")

    __table_args__ = (
        # One view record per post per IP per day
        UniqueConstraint("post_id", "ip_address", "viewed_at", name="uq_post_view_daily"),
    )


# ── Reaction ──────────────────────────────────────────────────────────────────

class Reaction(Base):
    """Likes and bookmarks. One of each type per user per post."""
    __tablename__ = "reactions"

    id      = Column(Integer, primary_key=True)
    type    = Column(Enum(ReactionType), nullable=False)
    post_id = Column(Integer, ForeignKey("posts.id",  ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id",  ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    post = relationship("Post", back_populates="reactions")
    user = relationship("User", back_populates="reactions")

    __table_args__ = (
        # One reaction of each type per user per post
        UniqueConstraint("user_id", "post_id", "type", name="uq_reaction_user_post_type"),
    )


# ── ReadingProgress ───────────────────────────────────────────────────────────

class ReadingProgress(Base):
    """
    Tracks how far a logged-in user has scrolled through a post (0–100%).
    Used to show "continue reading" on the homepage and progress bars on posts.
    """
    __tablename__ = "reading_progress"

    id           = Column(Integer, primary_key=True)
    user_id      = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    post_id      = Column(Integer, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False, index=True)
    progress_pct = Column(Integer, default=0)       # 0–100
    completed    = Column(Boolean, default=False)   # true when progress_pct = 100
    last_read_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="reading_progress")
    post = relationship("Post", back_populates="reading_progress")

    __table_args__ = (
        UniqueConstraint("user_id", "post_id", name="uq_reading_progress_user_post"),
    )


# ── Comment ───────────────────────────────────────────────────────────────────

class Comment(Base):
    __tablename__ = "comments"

    id          = Column(Integer, primary_key=True)
    content     = Column(Text, nullable=False)
    is_approved = Column(Boolean, default=False)
    is_edited   = Column(Boolean, default=False)
    like_count  = Column(Integer, default=0)

    post_id   = Column(Integer, ForeignKey("posts.id",    ondelete="CASCADE"), nullable=False, index=True)
    author_id = Column(Integer, ForeignKey("users.id",    ondelete="CASCADE"), nullable=False, index=True)
    parent_id = Column(Integer, ForeignKey("comments.id", ondelete="CASCADE"), nullable=True,  index=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    post    = relationship("Post",    back_populates="comments")
    author  = relationship("User",    back_populates="comments")
    replies = relationship("Comment", backref="parent", remote_side=[id])


# ── Follow ────────────────────────────────────────────────────────────────────

class Follow(Base):
    """A reader follows an author to get notified of new posts."""
    __tablename__ = "follows"

    id           = Column(Integer, primary_key=True)
    follower_id  = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    following_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at   = Column(DateTime(timezone=True), server_default=func.now())

    follower  = relationship("User", foreign_keys=[follower_id],  back_populates="following")
    following = relationship("User", foreign_keys=[following_id], back_populates="followers")

    __table_args__ = (
        UniqueConstraint("follower_id", "following_id", name="uq_follow_pair"),
    )


# ── Newsletter ────────────────────────────────────────────────────────────────

class NewsletterSubscriber(Base):
    """Email subscribers — separate from users (anyone can subscribe without an account)."""
    __tablename__ = "newsletter_subscribers"

    id           = Column(Integer, primary_key=True)
    email        = Column(String(255), unique=True, nullable=False, index=True)
    full_name    = Column(String(100), nullable=True)
    status       = Column(Enum(NewsletterStatus), default=NewsletterStatus.subscribed, nullable=False)
    user_id      = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    confirm_token= Column(String(100), nullable=True)   # double opt-in token
    confirmed    = Column(Boolean, default=False)
    subscribed_at= Column(DateTime(timezone=True), server_default=func.now())
    unsubscribed_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User")


class NewsletterCampaign(Base):
    """A newsletter issue sent to all confirmed subscribers."""
    __tablename__ = "newsletter_campaigns"

    id           = Column(Integer, primary_key=True)
    subject      = Column(String(300), nullable=False)
    content      = Column(Text,        nullable=False)   # HTML or Markdown
    status       = Column(Enum(CampaignStatus), default=CampaignStatus.draft, nullable=False)
    sent_count   = Column(Integer, default=0)
    author_id    = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    created_at   = Column(DateTime(timezone=True), server_default=func.now())
    sent_at      = Column(DateTime(timezone=True), nullable=True)

    author = relationship("User")


# ── SearchLog ─────────────────────────────────────────────────────────────────

class SearchLog(Base):
    """
    Logs every search query made on the platform.
    Used for:
      - Discovering what topics readers want that don't have posts yet
      - Autocomplete improvements
      - Content strategy decisions
    """
    __tablename__ = "search_logs"

    id          = Column(Integer, primary_key=True)
    query       = Column(String(500), nullable=False)
    results_count = Column(Integer, default=0)         # how many results came back
    user_id     = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    ip_address  = Column(String(45), nullable=True)
    searched_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")

    __table_args__ = (
        Index("ix_search_logs_query", "query"),           # fast aggregation by query
        Index("ix_search_logs_searched_at", "searched_at"),
    )