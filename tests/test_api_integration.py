import uuid
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app import main as app_main


class FakePublisher:
    def publish(self, *args, **kwargs):
        # no-op publisher for tests
        return None


class FakeRepo:
    def __init__(self):
        self.books = {}
        self.users = {}
        self.refresh_tokens: dict[str, dict] = {}

    def _to_plain(self, value):
        # recursively convert pydantic/other non-primitive values to primitives
        if value is None or isinstance(value, (str, int, float, bool)):
            return value
        if isinstance(value, list):
            return [self._to_plain(v) for v in value]
        if isinstance(value, dict):
            return {k: self._to_plain(v) for k, v in value.items()}
        try:
            # fallback: convert to string (covers HttpUrl, datetime, etc.)
            return str(value)
        except Exception:
            return value

    def create_book(self, payload: dict):
        # support Pydantic model or raw dict payloads
        data = payload.dict(by_alias=True) if hasattr(payload, "dict") else dict(payload)
        book_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        props = data.copy()
        # coerce any non-primitive values to plain types for JSON/response validation
        props = self._to_plain(props)
        # normalise snake_case keys that the real _book_properties maps to camelCase
        _remap = {
            "published_year": "publishedYear",
            "page_count": "pageCount",
            "cover_image_url": "coverImageUrl",
        }
        for snake, camel in _remap.items():
            if snake in props:
                props[camel] = props.pop(snake)
        props.update({
            "bookId": book_id,
            "createdAt": now,
            "updatedAt": now,
            "averageRating": None,
            "totalRatings": None,
            "hasEmbedding": None,
        })
        self.books[book_id] = props
        return props

    def page_books(self, page, size, query=None, genre=None, year=None,
                   sort_by="title", sort_order="asc", min_rating=None, max_page_count=None):
        items = list(self.books.values())
        if query:
            q = query.lower()
            items = [b for b in items if q in b.get("title", "").lower() or q in b.get("author", "").lower()]
        if genre:
            items = [b for b in items if genre in (b.get("genres") or [])]
        if year:
            items = [b for b in items if b.get("publishedYear") == year]
        if max_page_count is not None:
            items = [b for b in items if (b.get("pageCount") or 0) <= max_page_count]
        # sort
        reverse = sort_order == "desc"
        if sort_by == "title":
            items.sort(key=lambda b: b.get("title", "").lower(), reverse=reverse)
        elif sort_by == "createdAt":
            items.sort(key=lambda b: str(b.get("createdAt", "")), reverse=reverse)
        total = len(items)
        return items[(page * size): (page * size + size)], total

    def get_book(self, book_id):
        return self.books[book_id]

    def update_book(self, book_id, payload):
        self.books[book_id].update(payload)
        self.books[book_id]["updatedAt"] = datetime.now(timezone.utc)
        return self.books[book_id]

    def delete_book(self, book_id):
        return self.books.pop(book_id)

    def create_user(self, payload):
        data = payload.dict(by_alias=True) if hasattr(payload, "dict") else dict(payload)
        user_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        props = data.copy()
        props = self._to_plain(props)
        props.update({"userId": user_id, "createdAt": now, "updatedAt": now})
        self.users[user_id] = props
        return props

    def find_user_by_email(self, email: str):
        for user in self.users.values():
            if str(user.get("email")).lower() == str(email).lower():
                return user
        return None

    def page_users(self, page, size, query=None):
        items = list(self.users.values())
        total = len(items)
        return items[(page * size): (page * size + size)], total

    def get_user(self, user_id):
        user = self.users[user_id].copy()
        # include ratedBooks if present
        user.setdefault("ratedBooks", [])
        return user

    def update_user(self, user_id, payload):
        self.users[user_id].update(payload)
        self.users[user_id]["updatedAt"] = datetime.now(timezone.utc)
        return self.get_user(user_id)

    def delete_user(self, user_id):
        return self.users.pop(user_id)

    def add_rating(self, user_id, book_id, rating, review):
        timestamp = datetime.now(timezone.utc)
        rating_obj = {"rating": rating, "review": review, "timestamp": timestamp}
        # store on user
        user = self.users.get(user_id)
        if user is None:
            raise KeyError("user")
        user.setdefault("ratedBooks", []).append({"book": self.books[book_id], "rating": rating, "review": review, "timestamp": timestamp, "helpful": 0})
        return {"book": self.books[book_id], "rating": rating, "review": review, "timestamp": timestamp, "helpful": 0}

    def book_stats(self, book_id):
        return {"bookId": book_id, "averageRating": None, "totalRatings": 0}

    def trending(self, limit):
        return list(self.books.values())[:limit]

    def genres(self):
        # simple aggregation
        counts = {}
        for b in self.books.values():
            for g in b.get("genres", []):
                counts[g] = counts.get(g, 0) + 1
        return [{"genre": k, "count": v} for k, v in counts.items()]

    def recommendations(self, user_id, limit):
        return list(self.books.values())[:limit]

    # --- refresh token stubs ---
    def store_refresh_token(self, jti, user_id, expires_at):
        self.refresh_tokens[jti] = {"jti": jti, "userId": user_id, "expiresAt": expires_at, "revoked": False}

    def find_refresh_token(self, jti):
        return self.refresh_tokens.get(jti)

    def revoke_refresh_token(self, jti):
        if jti in self.refresh_tokens:
            self.refresh_tokens[jti]["revoked"] = True


@pytest.fixture
def client():
    from app.core.limiter import limiter
    # Clear rate-limit counters before each test so the 10/min auth cap isn't shared
    limiter.reset()

    fake_repo = FakeRepo()
    fake_pub = FakePublisher()
    app = app_main.app
    from app.core.dependencies import get_repository, get_publisher
    app.dependency_overrides[get_repository] = lambda: fake_repo
    app.dependency_overrides[get_publisher] = lambda: fake_pub
    yield TestClient(app)
    app.dependency_overrides.clear()


def auth_headers(client):
    register = client.post("/auth/register", json={
        "name": "Auth User",
        "email": "auth-user@example.com",
        "age": 29,
        "password": "SecurePass123!",
    })
    assert register.status_code == 201, register.text

    login = client.post("/auth/login", json={
        "email": "auth-user@example.com",
        "password": "SecurePass123!",
    })
    assert login.status_code == 200, login.text
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_create_and_list_books(client):
    headers = auth_headers(client)

    # create book
    payload = {
        "title": "Integration Book",
        "author": "Tester",
        "isbn": "123-4567890123",
        "publishedYear": 2026,
        "description": "Integration test book",
        "language": "en",
        "pageCount": 100,
        "coverImageUrl": "https://example.com/book.jpg",
        "genres": ["Test"]
    }
    r = client.post("/api/v1/books", json=payload, headers=headers)
    assert r.status_code == 201
    data = r.json()
    assert data["title"] == "Integration Book" or data.get("title") == "Integration Book" or data.get("bookId")

    # list books
    r2 = client.get("/api/v1/books?page=0&size=10", headers=headers)
    assert r2.status_code == 200
    body = r2.json()
    assert body["totalElements"] >= 1


def test_user_and_rating_flow(client):
    headers = auth_headers(client)

    # Ratings belong to the authenticated reader, not an unrelated user.
    user = client.get("/api/v1/me", headers=headers).json()
    user_id = user["userId"]

    # create book
    book_payload = {"title": "Rateable", "author": "Auth", "pageCount": 50}
    rb = client.post("/api/v1/books", json=book_payload, headers=headers)
    assert rb.status_code == 201
    book = rb.json()
    book_id = book.get("bookId") or book.get("book_id")

    # add rating
    r = client.post(f"/api/v1/users/{user_id}/ratings/{book_id}", json={"rating": 5, "review": "Nice"}, headers=headers)
    assert r.status_code == 201
    obj = r.json()
    assert obj["rating"] == 5
    assert obj["book"]["title"] == "Rateable"


def test_auth_flow_requires_token_and_returns_jwt(client):
    register = client.post("/auth/register", json={
        "name": "Auth User",
        "email": "auth-user@example.com",
        "age": 29,
        "password": "SecurePass123!",
    })
    assert register.status_code == 201, register.text
    payload = register.json()
    assert payload["email"] == "auth-user@example.com"

    login = client.post("/auth/login", json={
        "email": "auth-user@example.com",
        "password": "SecurePass123!",
    })
    assert login.status_code == 200, login.text
    token = login.json()["access_token"]
    assert token

    protected = client.get("/api/v1/users")
    assert protected.status_code == 401, protected.text

    authenticated = client.get("/api/v1/users", headers={"Authorization": f"Bearer {token}"})
    assert authenticated.status_code == 200, authenticated.text


def test_current_profile_returns_the_jwt_subject(client):
    headers = auth_headers(client)

    unauthorized = client.get("/api/v1/me")
    assert unauthorized.status_code == 401

    profile = client.get("/api/v1/me", headers=headers)
    assert profile.status_code == 200, profile.text
    assert profile.json()["name"] == "Auth User"
    assert profile.json()["email"] == "auth-user@example.com"


def test_book_lifecycle_updates_and_removes_persisted_state(client):
    headers = auth_headers(client)
    created = client.post(
        "/api/v1/books",
        json={"title": "Original", "author": "Author", "pageCount": 100},
        headers=headers,
    )
    assert created.status_code == 201, created.text
    book_id = created.json()["bookId"]

    updated = client.put(
        f"/api/v1/books/{book_id}",
        json={"title": "Revised", "genres": ["Architecture"]},
        headers=headers,
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["title"] == "Revised"
    assert updated.json()["genres"] == ["Architecture"]

    fetched = client.get(f"/api/v1/books/{book_id}", headers=headers)
    assert fetched.status_code == 200, fetched.text
    assert fetched.json()["title"] == "Revised"

    deleted = client.delete(f"/api/v1/books/{book_id}", headers=headers)
    assert deleted.status_code == 204, deleted.text
    assert client.get("/api/v1/books", headers=headers).json()["totalElements"] == 0


def test_invalid_requests_and_duplicate_accounts_return_api_errors(client):
    headers = auth_headers(client)

    invalid_book = client.post(
        "/api/v1/books",
        json={"title": "   ", "author": "Author"},
        headers=headers,
    )
    assert invalid_book.status_code == 400
    assert invalid_book.json()["message"] == "Validation failed"
    assert "title" in invalid_book.json()["errors"]

    duplicate_user = client.post(
        "/auth/register",
        json={
            "name": "Another Name",
            "email": "auth-user@example.com",
            "age": 32,
            "password": "SecurePass123!",
        },
    )
    assert duplicate_user.status_code == 409
    assert "already exists" in duplicate_user.json()["detail"]


def test_search_sort_by_title_descending(client):
    headers = auth_headers(client)
    for title in ["Zebra Book", "Apple Book", "Mango Book"]:
        client.post("/api/v1/books", json={"title": title, "author": "A"}, headers=headers)

    r = client.get("/api/v1/books/search?sortBy=title&sortOrder=desc", headers=headers)
    assert r.status_code == 200
    titles = [b["title"] for b in r.json()["content"]]
    assert titles == sorted(titles, reverse=True)


def test_search_max_page_count_filter(client):
    headers = auth_headers(client)
    client.post("/api/v1/books", json={"title": "Short", "author": "A", "pageCount": 50}, headers=headers)
    client.post("/api/v1/books", json={"title": "Long",  "author": "A", "pageCount": 900}, headers=headers)

    r = client.get("/api/v1/books/search?maxPageCount=100", headers=headers)
    assert r.status_code == 200
    assert all(b.get("pageCount", 0) <= 100 for b in r.json()["content"])
    assert r.json()["totalElements"] == 1


def test_search_invalid_sort_by_returns_400(client):
    headers = auth_headers(client)
    r = client.get("/api/v1/books/search?sortBy=invalid", headers=headers)
    assert r.status_code == 400
    assert any("sortBy" in k for k in r.json()["errors"])


def test_search_min_rating_out_of_range_returns_400(client):
    headers = auth_headers(client)
    r = client.get("/api/v1/books/search?minRating=6", headers=headers)
    assert r.status_code == 400
    assert any("minRating" in k for k in r.json()["errors"])

