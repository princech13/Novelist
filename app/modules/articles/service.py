from .ports import ArticleRepositoryPort
from .schemas import ArticleSave

class ArticleService:
    def __init__(self, repository: ArticleRepositoryPort):
        self.repository = repository

    def save(self, article_id: str, user_id: str, payload: ArticleSave) -> dict:
        return self.repository.save_article(article_id, user_id, payload.model_dump())

    def get(self, article_id: str, owner_id: str | None = None) -> dict:
        return self.repository.get_article(article_id, owner_id)

    def page(self, page: int, size: int, owner_id: str | None = None, author_id: str | None = None):
        return self.repository.page_articles(page, size, owner_id, author_id)

    def author(self, user_id: str) -> dict:
        return self.repository.get_author(user_id)
