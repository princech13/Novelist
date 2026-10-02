"""Extended integration tests covering: 404s, 401s, analytics, recommendations,
user preferences, search filters, RAG endpoints, and CORS headers."""
import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app import main as app_main
from app.core.dependencies import get_publisher, get_repository
from app.infrastructure.neo4j.base import NotFoundError


# ---------------------------------------------------------------------------
# Shared fake infrastructure (mirrors test_api_integration.py FakeRepo)
# ---------------------------------------------------------------------------

class FakePublisher:
    def publish(self, *args, **kwargs):
        return None


class FakeRepo:
    def __init__(self):
        self.books = {}
        self.users = {}
        self.refresh_tokens: dict[str, dict] = {}

    def _to_plain(self, value):
        if value is None or isinstance(value, (str, int, float, bool)):
            return value
        if isinstance(value, list):
            return [self._to_plain(v) for v in value]
        if isinstance(value, dict):
            return {k: self._to_plain(v) for k, v in value.items()}
        return str(value)

    def create_book(self, payload: dict):
        data = dict(payload)
        book_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        props = self._to_plain(data)
        for snake, camel in [("published_year", "publishedYear"), ("page_count", "pageCount"), ("cover_image_url", "coverImageUrl")]:
            if snake in props:
                props[camel] = props.pop(snake)
        props.update({"bookId": book_id, "createdAt": now, "updatedAt": now,
                      "averageRating": None, "totalRatings": None, "hasEmbedding": None})
        self.books[book_id] = props
        return props

    def get_book(self, book_id):
        if book_id not in self.books:
            raise NotFoundError(f"Book not found with id: {book_id}")
        return self.books[book_id]

    def update_book(self, book_id, payload):
        self.get_book(book_id)
        self.books[book_id].update(payload)
        self.books[book_id]["updatedAt"] = datetime.now(timezone.utc)
        return self.books[book_id]

    def delete_book(self, book_id):
        self.get_book(book_id)
        return self.books.pop(book_id)

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
        reverse = sort_order == "desc"
        if sort_by == "title":
            items.sort(key=lambda b: b.get("title", "").lower(), reverse=reverse)
        total = len(items)
        return items[page * size: page * size + size], total

    def create_user(self, payload: dict):
        data = dict(payload)
        user_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        props = self._to_plain(data)
        props.update({"userId": user_id, "createdAt": now, "updatedAt": now})
        self.users[user_id] = props
        return props

    def find_user_by_email(self, email: str):
        for user in self.users.values():
            if str(user.get("email", "")).lower() == email.lower():
                return user
        return None

    def get_user(self, user_id):
        if user_id not in self.users:
            raise NotFoundError(f"User not found with id: {user_id}")
        user = self.users[user_id].copy()
        user.setdefault("ratedBooks", [])
        return user

    def update_user(self, user_id, payload):
        self.get_user(user_id)
        self.users[user_id].update(payload)
        self.users[user_id]["updatedAt"] = datetime.now(timezone.utc)
        return self.get_user(user_id)

    def delete_user(self, user_id):
        self.get_user(user_id)
        return self.users.pop(user_id)

    def page_users(self, page, size, query=None):
        items = list(self.users.values())
        if query:
            q = query.lower()
            items = [u for u in items if q in u.get("name", "").lower()]
        total = len(items)
        return items[page * size: page * size + size], total

    def add_rating(self, user_id, book_id, rating, review):
        self.get_user(user_id)
        self.get_book(book_id)
        timestamp = datetime.now(timezone.utc)
        entry = {"book": self.books[book_id], "rating": rating, "review": review,
                 "timestamp": timestamp, "helpful": 0}
        self.users[user_id].setdefault("ratedBooks", []).append(entry)
        return entry

    def book_stats(self, book_id):
        self.get_book(book_id)
        return {"bookId": book_id, "averageRating": 4.5, "totalRatings": 3}

    def trending(self, limit):
        return list(self.books.values())[:limit]

    def genres(self):
        counts = {}
        for b in self.books.values():
            for g in b.get("genres") or []:
                counts[g] = counts.get(g, 0) + 1
        return [{"genre": k, "count": v} for k, v in counts.items()]

    def recommendations(self, user_id, limit):
        return list(self.books.values())[:limit]

    def verify(self):
        pass

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
    app = app_main.app
    app.dependency_overrides[get_repository] = lambda: fake_repo
    app.dependency_overrides[get_publisher] = lambda: FakePublisher()
    yield TestClient(app)
    app.dependency_overrides.clear()


def _register_and_login(client, email="user@test.com", password="SecurePass1!"):
    client.post("/auth/register", json={"name": "Test User", "email": email, "age": 25, "password": password})
    r = client.post("/auth/login", json={"email": email, "password": password})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def _make_book(client, headers, **kwargs):
    payload = {"title": "Test Book", "author": "Author", **kwargs}
    return client.post("/api/v1/books", json=payload, headers=headers).json()


def _make_user(client, headers, name="Bob", email="bob@test.com"):
    return client.post("/api/v1/users", json={"name": name, "email": email, "age": 30}, headers=headers).json()


# ===========================================================================
# Auth edge cases
# ===========================================================================

def test_login_wrong_password_returns_401(client):
    client.post("/auth/register", json={"name": "A", "email": "a@test.com", "age": 20, "password": "rightPass1!"})
    r = client.post("/auth/login", json={"email": "a@test.com", "password": "wrongPass1!"})
    assert r.status_code == 401


def test_login_unknown_email_returns_401(client):
    r = client.post("/auth/login", json={"email": "nobody@test.com", "password": "pass1234!"})
    assert r.status_code == 401


def test_request_with_invalid_token_returns_401(client):
    r = client.get("/api/v1/books", headers={"Authorization": "Bearer not.a.real.token"})
    assert r.status_code == 401


def test_request_with_missing_token_returns_401(client):
    r = client.get("/api/v1/me")
    assert r.status_code == 401


# ===========================================================================
# 404 — books
# ===========================================================================

def test_get_nonexistent_book_returns_404(client):
    h = _register_and_login(client)
    r = client.get(f"/api/v1/books/{uuid.uuid4()}", headers=h)
    assert r.status_code == 404


def test_update_nonexistent_book_returns_404(client):
    h = _register_and_login(client)
    r = client.put(f"/api/v1/books/{uuid.uuid4()}", json={"title": "X"}, headers=h)
    assert r.status_code == 404


def test_delete_nonexistent_book_returns_404(client):
    h = _register_and_login(client)
    r = client.delete(f"/api/v1/books/{uuid.uuid4()}", headers=h)
    assert r.status_code == 404


# ===========================================================================
# 404 — users
# ===========================================================================

def test_get_nonexistent_user_returns_404(client):
    h = _register_and_login(client)
    r = client.get(f"/api/v1/users/{uuid.uuid4()}", headers=h)
    assert r.status_code == 404


def test_rate_for_non_owner_returns_403(client):
    h = _register_and_login(client)
    book = _make_book(client, h)
    r = client.post(f"/api/v1/users/{uuid.uuid4()}/ratings/{book['bookId']}",
                    json={"rating": 4}, headers=h)
    assert r.status_code == 403


def test_rate_with_nonexistent_book_returns_404(client):
    h = _register_and_login(client)
    user = client.get("/api/v1/me", headers=h).json()
    r = client.post(f"/api/v1/users/{user['userId']}/ratings/{uuid.uuid4()}",
                    json={"rating": 4}, headers=h)
    assert r.status_code == 404


# ===========================================================================
# Book search filters
# ===========================================================================

def test_search_by_query_matches_title(client):
    h = _register_and_login(client)
    _make_book(client, h, title="Dune", author="Herbert")
    _make_book(client, h, title="Foundation", author="Asimov")

    r = client.get("/api/v1/books/search?query=dune", headers=h)
    assert r.status_code == 200
    assert r.json()["totalElements"] == 1
    assert r.json()["content"][0]["title"] == "Dune"


def test_search_by_query_matches_author(client):
    h = _register_and_login(client)
    _make_book(client, h, title="I Robot", author="Asimov")
    _make_book(client, h, title="Dune", author="Herbert")

    r = client.get("/api/v1/books/search?query=asimov", headers=h)
    assert r.status_code == 200
    assert r.json()["totalElements"] == 1


def test_search_by_genre(client):
    h = _register_and_login(client)
    _make_book(client, h, title="Sci-Fi Book", genres=["science fiction"])
    _make_book(client, h, title="Fantasy Book", genres=["fantasy"])

    r = client.get("/api/v1/books/search?genre=science+fiction", headers=h)
    assert r.status_code == 200
    assert r.json()["totalElements"] == 1
    assert r.json()["content"][0]["title"] == "Sci-Fi Book"


def test_search_by_year(client):
    h = _register_and_login(client)
    _make_book(client, h, title="Old Book", publishedYear=1990)
    _make_book(client, h, title="New Book", publishedYear=2024)

    r = client.get("/api/v1/books/search?year=2024", headers=h)
    assert r.status_code == 200
    assert r.json()["totalElements"] == 1
    assert r.json()["content"][0]["title"] == "New Book"


def test_search_returns_empty_when_no_match(client):
    h = _register_and_login(client)
    _make_book(client, h, title="Dune")

    r = client.get("/api/v1/books/search?query=hobbit", headers=h)
    assert r.status_code == 200
    assert r.json()["totalElements"] == 0
    assert r.json()["content"] == []


# ===========================================================================
# User preferences
# ===========================================================================

def test_update_user_preferences(client):
    h = _register_and_login(client)
    user = client.get("/api/v1/me", headers=h).json()
    uid = user["userId"]

    prefs = {"preferences": {"favoriteGenres": ["fantasy", "sci-fi"], "annualReadingGoal": 12}}
    r = client.put(f"/api/v1/users/{uid}/preferences", json=prefs, headers=h)
    assert r.status_code == 200
    stored = r.json()["preferences"]
    assert "fantasy" in stored["favoriteGenres"]
    assert stored["annualReadingGoal"] == 12


def test_update_preferences_for_non_owner_returns_403(client):
    h = _register_and_login(client)
    prefs = {"preferences": {"favoriteGenres": ["horror"]}}
    r = client.put(f"/api/v1/users/{uuid.uuid4()}/preferences", json=prefs, headers=h)
    assert r.status_code == 403


# ===========================================================================
# User search
# ===========================================================================

def test_search_users_by_name(client):
    h = _register_and_login(client)
    _make_user(client, h, name="Alice Wonder", email="alice@test.com")
    _make_user(client, h, name="Bob Builder", email="bob2@test.com")

    r = client.get("/api/v1/users/search?query=alice", headers=h)
    assert r.status_code == 200
    assert r.json()["totalElements"] == 1
    assert r.json()["content"][0]["name"] == "Alice Wonder"


# ===========================================================================
# Analytics
# ===========================================================================

def test_analytics_book_stats(client):
    h = _register_and_login(client)
    book = _make_book(client, h)

    r = client.get(f"/api/v1/analytics/books/{book['bookId']}/stats", headers=h)
    assert r.status_code == 200
    body = r.json()
    assert body["bookId"] == book["bookId"]
    assert "averageRating" in body
    assert "totalRatings" in body


def test_analytics_book_stats_nonexistent_returns_404(client):
    h = _register_and_login(client)
    r = client.get(f"/api/v1/analytics/books/{uuid.uuid4()}/stats", headers=h)
    assert r.status_code == 404


def test_analytics_trending_books(client):
    h = _register_and_login(client)
    _make_book(client, h, title="Popular")
    _make_book(client, h, title="Less Popular")

    r = client.get("/api/v1/analytics/books/trending?limit=5", headers=h)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_analytics_trending_limit_validation(client):
    h = _register_and_login(client)
    r = client.get("/api/v1/analytics/books/trending?limit=200", headers=h)
    assert r.status_code == 400


def test_analytics_genres(client):
    h = _register_and_login(client)
    _make_book(client, h, genres=["fantasy"])
    _make_book(client, h, genres=["fantasy", "adventure"])

    r = client.get("/api/v1/analytics/genres", headers=h)
    assert r.status_code == 200
    body = r.json()
    assert isinstance(body, list)
    fantasy = next((g for g in body if g["genre"] == "fantasy"), None)
    assert fantasy is not None
    assert fantasy["count"] == 2


def test_analytics_genres_returns_empty_when_no_books(client):
    h = _register_and_login(client)
    r = client.get("/api/v1/analytics/genres", headers=h)
    assert r.status_code == 200
    assert r.json() == []


# ===========================================================================
# Recommendations
# ===========================================================================

def test_recommendations_returns_list(client):
    h = _register_and_login(client)
    user = _make_user(client, h)
    _make_book(client, h, title="Book A")
    _make_book(client, h, title="Book B")

    r = client.get(f"/api/v1/recommendations/users/{user['userId']}?limit=5", headers=h)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_recommendations_limit_validation(client):
    h = _register_and_login(client)
    user = _make_user(client, h)
    r = client.get(f"/api/v1/recommendations/users/{user['userId']}?limit=0", headers=h)
    assert r.status_code == 400


# ===========================================================================
# RAG endpoints
# ===========================================================================

def test_rag_index_returns_chunk_count(client):
    h = _register_and_login(client)
    book = _make_book(client, h, content="The spice must flow. " * 50)

    # Patch RagService so tests don't download the embedding model
    from app.core.dependencies import get_rag_service
    from app.modules.rag.service import RagService

    mock_svc = MagicMock(spec=RagService)
    mock_svc.index_book.return_value = {
        "book_id": book["bookId"],
        "chunks_indexed": 5,
        "model": "all-MiniLM-L6-v2",
    }
    app_main.app.dependency_overrides[get_rag_service] = lambda: mock_svc

    r = client.post("/api/v1/rag/index", json={"bookId": book["bookId"]}, headers=h)
    assert r.status_code == 201
    body = r.json()
    assert body["bookId"] == book["bookId"]
    assert body["chunksIndexed"] == 5
    assert body["model"] == "all-MiniLM-L6-v2"

    del app_main.app.dependency_overrides[get_rag_service]


def test_rag_index_book_without_content_returns_404(client):
    h = _register_and_login(client)
    book = _make_book(client, h)  # no content field

    from app.core.dependencies import get_rag_service
    from app.modules.rag.service import RagService

    mock_svc = MagicMock(spec=RagService)
    mock_svc.index_book.side_effect = NotFoundError("Book has no content")
    app_main.app.dependency_overrides[get_rag_service] = lambda: mock_svc

    r = client.post("/api/v1/rag/index", json={"bookId": book["bookId"]}, headers=h)
    assert r.status_code == 404

    del app_main.app.dependency_overrides[get_rag_service]


def test_rag_search_returns_results(client):
    h = _register_and_login(client)

    from app.core.dependencies import get_rag_service
    from app.modules.rag.service import RagService

    mock_svc = MagicMock(spec=RagService)
    mock_svc.search.return_value = [
        {"bookId": "b1", "title": "Dune", "author": "Herbert",
         "chunkIndex": 0, "text": "The spice must flow.", "score": 0.95}
    ]
    app_main.app.dependency_overrides[get_rag_service] = lambda: mock_svc

    r = client.post("/api/v1/rag/search", json={"query": "spice trade", "topK": 3}, headers=h)
    assert r.status_code == 200
    body = r.json()
    assert body["query"] == "spice trade"
    assert len(body["results"]) == 1
    assert body["results"][0]["title"] == "Dune"
    assert body["results"][0]["score"] == 0.95

    del app_main.app.dependency_overrides[get_rag_service]


def test_rag_search_empty_query_returns_400(client):
    h = _register_and_login(client)
    r = client.post("/api/v1/rag/search", json={"query": "", "topK": 5}, headers=h)
    assert r.status_code == 400


def test_rag_search_requires_auth(client):
    r = client.post("/api/v1/rag/search", json={"query": "dragons", "topK": 5})
    assert r.status_code == 401


# ===========================================================================
# CORS headers
# ===========================================================================

def test_cors_header_present_on_response(client):
    r = client.get("/actuator/health", headers={"Origin": "http://localhost:3000"})
    assert r.status_code == 200
    assert r.headers.get("access-control-allow-origin") is not None


def test_cors_preflight_returns_200(client):
    r = client.options(
        "/api/v1/books",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Authorization, Content-Type",
        },
    )
    assert r.status_code == 200
    assert r.headers.get("access-control-allow-origin") is not None


# ===========================================================================
# Refresh token & logout
# ===========================================================================

def _login_full(client, email="refresh@test.com", password="SecurePass1!"):
    """Register + login, return the full token response dict."""
    client.post("/auth/register", json={"name": "Refresh User", "email": email, "age": 25, "password": password})
    r = client.post("/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return r.json()


def test_login_returns_both_tokens(client):
    tokens = _login_full(client)
    assert "access_token" in tokens
    assert "refresh_token" in tokens
    assert tokens["token_type"] == "bearer"


def test_refresh_returns_new_access_token(client):
    tokens = _login_full(client, email="refresh2@test.com")
    r = client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert r.status_code == 200, r.text
    body = r.json()
    assert "access_token" in body
    # refresh endpoint returns access token only — no new refresh token
    assert "refresh_token" not in body or body.get("refresh_token") is None


def test_new_access_token_is_usable(client):
    tokens = _login_full(client, email="refresh3@test.com")
    r = client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    new_access = r.json()["access_token"]
    # use the new access token to hit a protected endpoint
    r2 = client.get("/api/v1/books", headers={"Authorization": f"Bearer {new_access}"})
    assert r2.status_code == 200


def test_logout_revokes_refresh_token(client):
    tokens = _login_full(client, email="logout@test.com")
    # logout
    r = client.post("/auth/logout", json={"refresh_token": tokens["refresh_token"]})
    assert r.status_code == 204
    # subsequent refresh attempt must fail
    r2 = client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert r2.status_code == 401


def test_refresh_with_invalid_token_returns_401(client):
    r = client.post("/auth/refresh", json={"refresh_token": "not.a.valid.token"})
    assert r.status_code == 401


def test_refresh_with_access_token_returns_401(client):
    """Supplying an access token where a refresh token is expected must be rejected."""
    tokens = _login_full(client, email="wrongtoken@test.com")
    r = client.post("/auth/refresh", json={"refresh_token": tokens["access_token"]})
    assert r.status_code == 401


def test_logout_with_invalid_token_returns_401(client):
    r = client.post("/auth/logout", json={"refresh_token": "garbage"})
    assert r.status_code == 401

# ===========================================================================
# Rate limiting
# ===========================================================================

def test_auth_login_rate_limit_returns_429(client):
    """11th login attempt from the same IP within one minute must return 429."""
    # Register once so the login credentials exist
    client.post("/auth/register", json={"name": "RL User", "email": "rl@test.com", "age": 25, "password": "SecurePass1!"})
    for _ in range(10):
        r = client.post("/auth/login", json={"email": "rl@test.com", "password": "SecurePass1!"})
        assert r.status_code == 200, f"Expected 200 on attempt, got {r.status_code}: {r.text}"
    # 11th attempt must be blocked
    r = client.post("/auth/login", json={"email": "rl@test.com", "password": "SecurePass1!"})
    assert r.status_code == 429


def test_auth_register_rate_limit_returns_429(client):
    """11th register attempt from the same IP within one minute must return 429."""
    for i in range(10):
        client.post("/auth/register", json={"name": f"U{i}", "email": f"u{i}@rl.com", "age": 20, "password": "SecurePass1!"})
    r = client.post("/auth/register", json={"name": "X", "email": "x@rl.com", "age": 20, "password": "SecurePass1!"})
    assert r.status_code == 429


def test_rate_limit_resets_between_tests(client):
    """Confirm the fixture reset works — first call after reset is always 200."""
    client.post("/auth/register", json={"name": "Reset User", "email": "reset@test.com", "age": 25, "password": "SecurePass1!"})
    r = client.post("/auth/login", json={"email": "reset@test.com", "password": "SecurePass1!"})
    assert r.status_code == 200
