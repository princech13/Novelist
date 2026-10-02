"""Persistence operations for ratings."""
from typing import Any

from app.infrastructure.neo4j.base import node, now, to_native


class RatingRepositoryMixin:
    def add_rating(self, user_id: str, book_id: str, rating: int, review: str | None) -> dict[str, Any]:
        self.get_user(user_id)
        book = self.get_book(book_id)
        record = self._one(
            "MATCH (u:User {userId: $user_id}), (b:Book {bookId: $book_id}) MERGE (u)-[r:RATED]->(b) "
            "ON CREATE SET r.timestamp = $timestamp, r.helpful = 0 SET r.rating = $rating, r.review = $review RETURN r",
            user_id=user_id, book_id=book_id, rating=rating, review=review, timestamp=now(),
        )
        relation = to_native(dict(record["r"]))
        return {"book": book, "rating": relation["rating"], "review": relation.get("review"), "timestamp": relation.get("timestamp"), "helpfulCount": relation.get("helpful", 0)}

    def user_rated_books(self, user_id: str, page: int, size: int) -> tuple[list[dict[str, Any]], int]:
        """Return the books that a specific user has rated, with pagination."""
        params: dict[str, Any] = {"user_id": user_id, "skip": page * size, "size": size}
        total = self._one(
            "MATCH (u:User {userId: $user_id})-[:RATED]->(b:Book) RETURN count(b) AS total",
            **params,
        )["total"]
        rows = self._all(
            "MATCH (u:User {userId: $user_id})-[r:RATED]->(b:Book) "
            "RETURN b AS entity ORDER BY b.title SKIP $skip LIMIT $size",
            **params,
        )
        return [node(row) for row in rows], total

    def book_reviews(self, book_id: str) -> list[dict[str, Any]]:
        rows = self._all(
            "MATCH (u:User)-[r:RATED]->(b:Book {bookId: $book_id}) "
            "RETURN u.userId AS userId, u.name AS userName, r.rating AS rating, "
            "r.review AS review, r.timestamp AS timestamp ORDER BY r.timestamp DESC",
            book_id=book_id,
        )
        return [
            {
                "userId": row["userId"],
                "userName": row["userName"],
                "rating": row["rating"],
                "review": row["review"],
                "timestamp": to_native(row["timestamp"]),
            }
            for row in rows
        ]
