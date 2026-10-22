"""Unit tests for feature use cases, isolated from infrastructure adapters."""
import pytest
from fastapi import HTTPException

from app.modules.auth.service import AuthService
from app.modules.books.service import BookService
from app.modules.ratings.service import RatingService


class BookRepositoryStub:
    def create_book(self, payload: dict) -> dict:
        return {"bookId": "book-1", **payload}

    def update_book(self, book_id: str, payload: dict) -> dict:
        return {"bookId": book_id, **payload}

    def delete_book(self, book_id: str) -> dict:
        return {"bookId": book_id, "title": "Deleted"}


class AuthRepositoryStub:
    def __init__(self, existing_user: dict | None = None) -> None:
        self.existing_user = existing_user
        self.created_payload: dict | None = None
        self.refresh_tokens: dict = {}

    def find_user_by_email(self, email: str) -> dict | None:
        return self.existing_user

    def create_user(self, payload: dict) -> dict:
        self.created_payload = payload
        return {"userId": "user-1", **payload}

    def store_refresh_token(self, jti: str, user_id: str, expires_at) -> None:
        self.refresh_tokens[jti] = {"jti": jti, "userId": user_id, "revoked": False}

    def find_refresh_token(self, jti: str) -> dict | None:
        return self.refresh_tokens.get(jti)

    def revoke_refresh_token(self, jti: str) -> None:
        if jti in self.refresh_tokens:
            self.refresh_tokens[jti]["revoked"] = True


class RatingRepositoryStub:
    def add_rating(self, user_id: str, book_id: str, rating: int, review: str | None) -> dict:
        return {"book": {"bookId": book_id}, "rating": rating, "review": review}


def test_book_service_mutations() -> None:
    service = BookService(BookRepositoryStub())

    created = service.create({"title": "Clean Architecture", "author": "Martin"})
    updated = service.update("book-1", {"title": "Updated"})
    service.delete("book-1")

    assert created["bookId"] == "book-1"
    assert updated["title"] == "Updated"


def test_auth_service_registers_hashed_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    repository = AuthRepositoryStub()
    monkeypatch.setattr("app.modules.auth.service.hash_password", lambda password: f"hash:{password}")

    user = AuthService(repository).register("Ada", "ada@example.com", 30, "secret-password")

    assert user["userId"] == "user-1"
    assert repository.created_payload == {
        "name": "Ada", "email": "ada@example.com", "age": 30, "passwordHash": "hash:secret-password"
    }


def test_auth_service_rejects_duplicate_registration() -> None:
    service = AuthService(AuthRepositoryStub(existing_user={"userId": "user-1"}))

    with pytest.raises(HTTPException, match="already exists") as exc_info:
        service.register("Ada", "ada@example.com", 30, "secret-password")

    assert exc_info.value.status_code == 409


def test_auth_service_returns_token_for_valid_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    repository = AuthRepositoryStub(existing_user={"userId": "user-1", "passwordHash": "stored-hash"})
    monkeypatch.setattr("app.modules.auth.service.verify_password", lambda password, stored: password == "correct")
    monkeypatch.setattr("app.modules.auth.service.create_access_token", lambda subject: f"token:{subject}")
    monkeypatch.setattr("app.modules.auth.service.create_refresh_token", lambda subject: ("refresh:stub", "jti-stub"))

    token = AuthService(repository).login("ada@example.com", "correct")

    assert token["access_token"] == "token:user-1"
    assert token["refresh_token"] == "refresh:stub"
    assert token["token_type"] == "bearer"


def test_rating_service_adds_review() -> None:

    rating = RatingService(RatingRepositoryStub()).add("user-1", "book-1", 5, "Excellent")

    assert rating["rating"] == 5
    assert rating["review"] == "Excellent"
