"""Rating use cases."""
from .ports import RatingRepositoryPort


class RatingService:
    def __init__(self, repository: RatingRepositoryPort):
        self.repository = repository

    def add(self, user_id: str, book_id: str, rating: int, review: str | None) -> dict:
        result = self.repository.add_rating(user_id, book_id, rating, review)
        return result

    def book_reviews(self, book_id: str) -> list[dict]:
        return self.repository.book_reviews(book_id)

    def my_books(self, user_id: str, page: int, size: int) -> tuple[list[dict], int]:
        return self.repository.user_rated_books(user_id, page, size)
