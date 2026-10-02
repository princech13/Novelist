"""Book request and response models."""
from datetime import datetime

from pydantic import ConfigDict, Field, HttpUrl, field_validator

from app.modules.shared.schemas import APIModel, to_camel


class BookCreate(APIModel):
    title: str = Field(min_length=1, max_length=200)
    author: str = Field(min_length=1, max_length=100)
    isbn: str | None = Field(default=None, pattern=r"^[0-9X-]{10,17}$")
    published_year: int | None = Field(default=None, ge=1000, le=2100)
    description: str | None = Field(default=None, max_length=2000)
    content: str | None = Field(default=None, max_length=1_000_000)
    language: str | None = Field(default=None, pattern=r"^[a-z]{2}$")
    page_count: int | None = Field(default=None, ge=1)
    cover_image_url: HttpUrl | None = None
    genres: list[str] | None = None

    @field_validator("title", "author")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be blank")
        return value


class BookUpdate(APIModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, extra="forbid")
    title: str | None = Field(default=None, min_length=1, max_length=200)
    author: str | None = Field(default=None, min_length=1, max_length=100)
    isbn: str | None = Field(default=None, pattern=r"^[0-9X-]{10,17}$")
    published_year: int | None = Field(default=None, ge=1000, le=2100)
    description: str | None = Field(default=None, max_length=2000)
    content: str | None = Field(default=None, max_length=1_000_000)
    language: str | None = Field(default=None, pattern=r"^[a-z]{2}$")
    page_count: int | None = Field(default=None, ge=1)
    cover_image_url: HttpUrl | None = None
    genres: list[str] | None = None


class BookOut(APIModel):
    content: str | None = None
    book_id: str
    title: str
    author: str
    isbn: str | None = None
    published_year: int | None = None
    description: str | None = None
    language: str | None = None
    page_count: int | None = None
    cover_image_url: str | None = None
    genres: list[str] | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    average_rating: float | None = None
    total_ratings: int | None = None
    has_embedding: bool | None = None
