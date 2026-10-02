from uuid import UUID
from fastapi import APIRouter, Depends, Query
from app.core.dependencies import ArticleServiceDep
from app.core.pagination import make_page
from app.core.security import get_current_user_id
from .schemas import ArticleOut, ArticlePage, ArticleSave, AuthorOut

router = APIRouter(prefix="/api/v1", tags=["articles"])

@router.get("/articles", response_model=ArticlePage)
def published_articles(service: ArticleServiceDep, page: int = Query(0, ge=0), size: int = Query(12, ge=1, le=100), author_id: str | None = Query(None, alias="authorId")):
    items, total = service.page(page, size, author_id=author_id)
    return make_page(items, total, page, size)

@router.get("/articles/{article_id}", response_model=ArticleOut)
def published_article(article_id: UUID, service: ArticleServiceDep):
    return service.get(str(article_id))

@router.get("/authors/{user_id}", response_model=AuthorOut)
def author(user_id: str, service: ArticleServiceDep):
    return service.author(user_id)

@router.get("/me/articles", response_model=ArticlePage)
def my_articles(service: ArticleServiceDep, page: int = Query(0, ge=0), size: int = Query(12, ge=1, le=100), user_id: str = Depends(get_current_user_id)):
    items, total = service.page(page, size, owner_id=user_id)
    return make_page(items, total, page, size)

@router.get("/me/articles/{article_id}", response_model=ArticleOut)
def my_article(article_id: UUID, service: ArticleServiceDep, user_id: str = Depends(get_current_user_id)):
    return service.get(str(article_id), owner_id=user_id)

@router.put("/articles/{article_id}", response_model=ArticleOut)
def save_article(article_id: UUID, body: ArticleSave, service: ArticleServiceDep, user_id: str = Depends(get_current_user_id)):
    return service.save(str(article_id), user_id, body)
