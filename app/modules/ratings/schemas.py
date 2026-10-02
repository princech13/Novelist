"""Rating request and response models."""
from datetime import datetime
from pydantic import Field

from app.modules.books.schemas import BookOut
from app.modules.shared.schemas import APIModel


class RatingCreate(APIModel):
    rating: int = Field(ge=1, le=5)
    review: str | None = Field(default=None, max_length=1000)


class RatingOut(APIModel):
    book: BookOut | None
    rating: int
    review: str | None = None
    timestamp: datetime | None = None
    helpful_count: int | None = None


class BookReviewOut(APIModel):
    user_id: str
    user_name: str
    rating: int
    review: str | None = None
    timestamp: datetime | None = None
