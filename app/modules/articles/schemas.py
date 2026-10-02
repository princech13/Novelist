from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import ConfigDict, Field, model_validator
from app.modules.shared.schemas import APIModel, to_camel


class ArticleContent(APIModel):
    title: str = Field(default="", max_length=200)
    subtitle: str = Field(default="", max_length=500)
    body: str = Field(default="", max_length=100_000)
    kind: Literal["Article", "Book review"] = "Article"
    book: str = Field(default="", max_length=300)


class ArticleSave(ArticleContent):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, extra="forbid")
    revision: int = Field(ge=0)
    action: Literal["save", "publish", "unpublish"] = "save"

    @model_validator(mode="after")
    def require_publishable_content(self):
        if self.action == "publish" and (not self.title.strip() or not self.body.strip()):
            raise ValueError("A title and story are required to publish")
        return self


class ArticleOut(ArticleContent):
    article_id: UUID
    author_id: str
    author_name: str
    revision: int
    published: bool
    updated_at: datetime
    published_at: datetime | None = None


class ArticleSummary(APIModel):
    article_id: UUID
    author_id: str
    author_name: str
    title: str
    subtitle: str
    kind: Literal["Article", "Book review"]
    book: str
    published: bool
    updated_at: datetime
    published_at: datetime | None = None


class ArticlePage(APIModel):
    content: list[ArticleSummary]
    page: int
    size: int
    total_elements: int
    total_pages: int
    first: bool
    last: bool
    has_next: bool
    has_previous: bool


class AuthorOut(APIModel):
    user_id: str
    name: str
    published_count: int
