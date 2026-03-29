from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.core.database import get_db
from app.models.article import Article
from app.services.fetcher import fetch_html
from app.services.parser import parse_medium_article
from app.services.searcher import search_medium
from pydantic import BaseModel, HttpUrl
from datetime import datetime
from typing import List, Optional
import os

from pathlib import Path

router = APIRouter()
BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# View Routes
@router.get("/", response_class=HTMLResponse)
async def read_root(request: Request, q: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    query = select(Article).order_by(desc(Article.created_at))
    if q:
        query = query.where(Article.title.ilike(f"%{q}%"))
    
    result = await db.execute(query)
    articles = result.scalars().all()
    return templates.TemplateResponse(
        request=request, name="index.html", context={"articles": articles, "q": q}
    )

@router.get("/v/{article_id}", response_class=HTMLResponse)
async def view_article(request: Request, article_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Article).where(Article.id == article_id))
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return templates.TemplateResponse(
        request=request, name="article.html", context={"article": article}
    )

@router.get("/admin", response_class=HTMLResponse)
async def admin_view(request: Request, db: AsyncSession = Depends(get_db)):
    query = select(Article).order_by(desc(Article.created_at))
    result = await db.execute(query)
    articles = result.scalars().all()
    return templates.TemplateResponse(
        request=request, name="admin.html", context={"articles": articles}
    )

@router.get("/search", response_class=HTMLResponse)
async def search_view(request: Request, q: str, depth: int = 5):
    results = await search_medium(q, depth=depth)
    return templates.TemplateResponse(
        request=request, name="search.html", context={"results": results, "q": q}
    )

# API Routes
api_router = APIRouter(prefix="/api/v1")

class BulkDeleteRequest(BaseModel):
    article_ids: List[int]

@api_router.post("/articles/bulk-delete")
async def bulk_delete_articles(
    request: BulkDeleteRequest,
    db: AsyncSession = Depends(get_db)
):
    if not request.article_ids:
        return {"message": "No articles selected"}
        
    for article_id in request.article_ids:
        result = await db.execute(select(Article).where(Article.id == article_id))
        article = result.scalar_one_or_none()
        if article:
            await db.delete(article)
    
    await db.commit()
    return {"message": f"Successfully deleted {len(request.article_ids)} articles"}

class ArticleCreate(BaseModel):
    url: HttpUrl

class ArticleResponse(BaseModel):
    id: int
    url: str
    title: str
    author: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class ArticleDetail(ArticleResponse):
    content_html: str

@api_router.post("/fetch", response_model=ArticleDetail)
async def fetch_and_save_article(
    article_in: ArticleCreate,
    db: AsyncSession = Depends(get_db)
):
    url_str = str(article_in.url)
    
    # Check if article already exists
    result = await db.execute(select(Article).where(Article.url == url_str))
    existing_article = result.scalar_one_or_none()
    if existing_article:
        return existing_article

    # Fetch and parse
    html = await fetch_html(url_str)
    if not html:
        raise HTTPException(status_code=400, detail="Could not fetch article content")

    parsed_data = parse_medium_article(html)
    if not parsed_data:
        # Debugging: see what we actually got
        print(f"DEBUG: HTML length: {len(html)}")
        print(f"DEBUG: HTML Snippet: {html[:500]}")
        raise HTTPException(status_code=400, detail="Could not parse article content. The page might be a bot-check or login wall.")

    new_article = Article(
        url=url_str,
        title=parsed_data["title"],
        author=parsed_data["author"],
        content_html=parsed_data["content_html"]
    )
    
    db.add(new_article)
    await db.commit()
    await db.refresh(new_article)
    
    return new_article

@api_router.get("/articles", response_model=List[ArticleResponse])
async def list_articles(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    result = await db.execute(select(Article).offset(skip).limit(limit))
    articles = result.scalars().all()
    return articles

@api_router.get("/articles/{article_id}", response_model=ArticleDetail)
async def get_article(
    article_id: int,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Article).where(Article.id == article_id))
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article

@api_router.delete("/articles/{article_id}")
async def delete_article(
    article_id: int,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Article).where(Article.id == article_id))
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    await db.delete(article)
    await db.commit()
    return {"message": "Article deleted successfully"}

router.include_router(api_router)
