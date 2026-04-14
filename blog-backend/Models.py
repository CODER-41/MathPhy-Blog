"""
SQLAlchemy models.

Index strategy:
  - slug columns: unique + index (primary lookup key)
  - status + published_at: composite index for the most common list query
  - author_id, category_id: FK indexes for join performance
  - email, username on User: unique + index for auth lookups
"""
import enum
from sqlalchemy import (
    Column, Integer, String, Text, Boolean,
    DateTime, ForeignKey, Enum, Table, Index,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base


class UserRole(str, enum.Enum):
    admin  = "admin"
    author = "author"
    reader = "reader"


class PostStatus(str, enum.Enum):
    draft     = "draft"
    published = "published"
    archived  = "archived"


# ── Many-to-many: posts ↔ tags ────────────────────────────────────────────────
post_tags = Table(
    "post_tags", Base.metadata,
    Column("post_id", Integer, ForeignKey("posts.id",  ondelete="CASCADE"), primary_key=True),
    Column("tag_id",  Integer, ForeignKey("tags.id",   ondelete="CASCADE"), primary_key=True),
)


# ── User ──────────────────────────────────────────────────────────────────────
class User(Base):
    __tablename__ = "users"

    id              = Column(Integer, primary_key=True)
    username        = Column(String(50),  unique=True, nullable=False, index=True)
    email           = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name       = Column(String(100), nullable=True)
    bio             = Column(Text,        nullable=True)
    avatar_url      = Column(String(500), nullable=True)
    role            = Column(Enum(UserRole), default=UserRole.reader, nullable=False)
    is_active       = Column(Boolean, default=True)
    created_at      = Column(DateTime(timezone=True), server_default=func.now())
    updated_at      = Column(DateTime(timezone=True), onupdate=func.now())

    posts    = relationship("Post",    back_populates="author")
    comments = relationship("Comment", back_populates="author")


# ── Category ──────────────────────────────────────────────────────────────────
class Category(Base):
    __tablename__ = "categories"

    id          = Column(Integer, primary_key=True)
    name        = Column(String(100), unique=True, nullable=False)
    slug        = Column(String(120), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())

    posts = relationship("Post", back_populates="category")


# ── Tag ───────────────────────────────────────────────────────────────────────
class Tag(Base):
    __tablename__ = "tags"

    id   = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    slug = Column(String(60), unique=True, nullable=False, index=True)

    posts = relationship("Post", secondary=post_tags, back_populates="tags")


# ── Post ──────────────────────────────────────────────────────────────────────
class Post(Base):
    __tablename__ = "posts"

    id              = Column(Integer, primary_key=True)
    title           = Column(String(300), nullable=False)
    slug            = Column(String(350), unique=True, nullable=False, index=True)
    excerpt         = Column(Text,        nullable=True)
    content         = Column(Text,        nullable=False)
    cover_image_url = Column(String(500), nullable=True)
    status          = Column(Enum(PostStatus), default=PostStatus.draft, nullable=False, index=True)
    views           = Column(Integer, default=0)
    read_time       = Column(Integer, default=0)   # minutes

    author_id   = Column(Integer, ForeignKey("users.id"),      nullable=False, index=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True,  index=True)

    created_at   = Column(DateTime(timezone=True), server_default=func.now())
    updated_at   = Column(DateTime(timezone=True), onupdate=func.now())
    published_at = Column(DateTime(timezone=True), nullable=True, index=True)

    author   = relationship("User",     back_populates="posts")
    category = relationship("Category", back_populates="posts")
    tags     = relationship("Tag",      secondary=post_tags, back_populates="posts")
    comments = relationship("Comment",  back_populates="post", cascade="all, delete-orphan")

    # Composite index: the most common query is "published posts ordered by date"
    __table_args__ = (
        Index("ix_posts_status_published_at", "status", "published_at"),
    )


# ── Comment ───────────────────────────────────────────────────────────────────
class Comment(Base):
    __tablename__ = "comments"

    id          = Column(Integer, primary_key=True)
    content     = Column(Text, nullable=False)
    is_approved = Column(Boolean, default=False)

    post_id   = Column(Integer, ForeignKey("posts.id",    ondelete="CASCADE"), nullable=False, index=True)
    author_id = Column(Integer, ForeignKey("users.id",    ondelete="CASCADE"), nullable=False, index=True)
    parent_id = Column(Integer, ForeignKey("comments.id", ondelete="CASCADE"), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    post    = relationship("Post", back_populates="comments")
    author  = relationship("User", back_populates="comments")
    replies = relationship("Comment", backref="parent", remote_side=[id])