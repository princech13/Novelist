"""Book use cases."""
from .ports import BookRepositoryPort


class BookService:
    def __init__(self, repository: BookRepositoryPort):
        self.repository = repository

    def create(self, payload: dict) -> dict:
        book = self.repository.create_book(payload)
        return book

    def update(self, book_id: str, payload: dict) -> dict:
        book = self.repository.update_book(book_id, payload)
        return book

    def delete(self, book_id: str) -> None:
        self.repository.delete_book(book_id)
