"""Rating use cases and event orchestration."""
from app.modules.shared.ports import EventPublisherPort
from .ports import RatingRepositoryPort


class RatingService:
    def __init__(self, repository: RatingRepositoryPort, publisher: EventPublisherPort):
        self.repository, self.publisher = repository, publisher

    def add(self, user_id: str, book_id: str, rating: int, review: str | None) -> dict:
        result = self.repository.add_rating(user_id, book_id, rating, review)
        self.publisher.publish("rating.added", {"userId": user_id, "bookId": book_id, "rating": rating, "review": review})
        return result

    def book_reviews(self, book_id: str) -> list[dict]:
        return self.repository.book_reviews(book_id)

    def my_books(self, user_id: str, page: int, size: int) -> tuple[list[dict], int]:
        return self.repository.user_rated_books(user_id, page, size)
