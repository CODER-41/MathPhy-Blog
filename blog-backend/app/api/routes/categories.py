from fastapi import APIRouter, Depends, HTTPException, Request
from python_slugify import slugify
from sqlalchemy.orm import Session
from typing import List

from app.core.cache import cache, invalidate_taxonomy
from app.core.config import settings
from app.core.dependencies import require_admin
from app.db.database import get_db
from app.models.models import Category, Tag
from app.schemas.schemas import CategoryCreate, CategoryUpdate, CategoryOut, TagCreate, TagOut

categories_router = APIRouter(prefix="/categories", tags=["Categories"])
tags_router       = APIRouter(prefix="/tags",       tags=["Tags"])


@categories_router.get("", response_model=List[CategoryOut])
@cache(expire=settings.CACHE_TAXONOMY_TTL)
async def list_categories(request: Request, db: Session = Depends(get_db)):
    return db.query(Category).filter(Category.parent_id == None).order_by(Category.sort_order, Category.name).all()


@categories_router.post("", response_model=CategoryOut, status_code=201)
async def create_category(payload: CategoryCreate, db: Session = Depends(get_db), _=Depends(require_admin)):
    slug = slugify(payload.name)
    if db.query(Category).filter(Category.slug == slug).first():
        raise HTTPException(400, "Category already exists")
    cat = Category(name=payload.name, slug=slug, description=payload.description,
                   icon=payload.icon, color=payload.color,
                   parent_id=payload.parent_id, sort_order=payload.sort_order)
    db.add(cat)
    db.commit()
    db.refresh(cat)
    await invalidate_taxonomy()
    return cat


@categories_router.put("/{category_id}", response_model=CategoryOut)
async def update_category(category_id: int, payload: CategoryUpdate,
                          db: Session = Depends(get_db), _=Depends(require_admin)):
    cat = db.query(Category).filter(Category.id == category_id).first()
    if not cat:
        raise HTTPException(404, "Category not found")
    if payload.name:
        cat.name = payload.name
        cat.slug = slugify(payload.name)
    if payload.description is not None: cat.description = payload.description
    if payload.icon        is not None: cat.icon        = payload.icon
    if payload.color       is not None: cat.color       = payload.color
    if payload.parent_id   is not None: cat.parent_id   = payload.parent_id
    if payload.sort_order  is not None: cat.sort_order  = payload.sort_order
    db.commit()
    db.refresh(cat)
    await invalidate_taxonomy()
    return cat


@categories_router.delete("/{category_id}", status_code=204)
async def delete_category(category_id: int, db: Session = Depends(get_db), _=Depends(require_admin)):
    cat = db.query(Category).filter(Category.id == category_id).first()
    if not cat:
        raise HTTPException(404, "Category not found")
    db.delete(cat)
    db.commit()
    await invalidate_taxonomy()


@tags_router.get("", response_model=List[TagOut])
@cache(expire=settings.CACHE_TAXONOMY_TTL)
async def list_tags(request: Request, db: Session = Depends(get_db)):
    return db.query(Tag).order_by(Tag.name).all()


@tags_router.post("", response_model=TagOut, status_code=201)
async def create_tag(payload: TagCreate, db: Session = Depends(get_db), _=Depends(require_admin)):
    slug = slugify(payload.name)
    if db.query(Tag).filter(Tag.slug == slug).first():
        raise HTTPException(400, "Tag already exists")
    tag = Tag(name=payload.name, slug=slug)
    db.add(tag)
    db.commit()
    db.refresh(tag)
    await invalidate_taxonomy()
    return tag


@tags_router.delete("/{tag_id}", status_code=204)
async def delete_tag(tag_id: int, db: Session = Depends(get_db), _=Depends(require_admin)):
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not tag:
        raise HTTPException(404, "Tag not found")
    db.delete(tag)
    db.commit()
    await invalidate_taxonomy()
