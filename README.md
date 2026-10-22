# Novelist

Novelist is a full-stack article publishing and book review application. A **Python / FastAPI** backend handles articles, books, users, ratings, and recommendations; a **React / Vite** frontend provides a browser UI for all those features.

For the reviewed runtime structure, data flows, and known gaps, see [Architecture](spec/ARCHITECTURE.md). The [Architectural decision records](spec/ARCHITECTURAL_DECISIONS.md) explain the important choices, tradeoffs, and implementation evidence.

## Project structure

```
Novelist/
├── app/                            # FastAPI backend
│   ├── main.py                     # Bootstrap: lifespan, router registration, exception handlers
│   ├── core/                       # Config, dependencies, security, rate limiting, logging
│   ├── infrastructure/             # Concrete external-system adapters
│   │   └── neo4j/                  # Driver lifecycle and composed repository
│   └── modules/                    # Feature modules
│       ├── auth/                   # register, login, refresh, logout
│       ├── books/                  # CRUD + paginated search with filters
│       ├── users/                  # CRUD + preferences + search
│       ├── ratings/                # Per-user book ratings and reviews
│       ├── analytics/              # Stats, trending, genre breakdown
│       ├── recommendations/        # Graph-based recommendations
│       ├── profile/                # Current-user profile (/me)
│       └── shared/                 # Cross-feature API contracts
├── ui/                             # React + Vite + TypeScript frontend
│   └── src/
│       ├── api/                    # Typed API client (axios + all endpoints)
│       ├── context/                # AuthContext (JWT storage, login/logout)
│       ├── components/             # AppShell, modals (AddBook, RateReview)
│       └── pages/                  # BooksPage, BookDetailPage, ProfilePage,
│                                   # TrendingPage, ArticlesPage, JournalPage, AuthPages
├── tests/                          # pytest: unit + integration + coverage
├── spec/                           # Architecture, deployment, and design docs
└── docker-compose.yml              # Full stack: UI, API, Neo4j
```

Each backend module follows the same internal layout:
```
<module>/
├── ports.py       # Protocol interfaces (dependency-inversion boundary)
├── schemas.py     # Pydantic request/response models
├── service.py     # Use-case logic; depends on ports
├── repository.py  # Neo4j mixin; implements the port
└── router.py      # FastAPI router; calls service via DI
```

## Requirements

**Backend**
- Python 3.13+
- Neo4j 5+

**Frontend**
- Node.js 20.19+ or 22.12+ (container builds use Node.js 24)

## Run locally

### 1 — Backend

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8081
```

Interactive API docs: `http://localhost:8081/docs`


### 2 — Frontend

```bash
cd ui
npm install
npm run dev          # → http://localhost:5173
```

## Run with containers

```bash
docker compose up -d --build
```

If using Podman, start your Podman machine and run instead:

```bash
podman compose up -d --build
```

Open http://localhost:5173. The UI is built inside its container image and served
by Nginx, which forwards `/backend/` requests to the API. No local Node.js or
Python installation is needed. Page refreshes work through the React Router
fallback. The first build downloads application dependencies.

The stack runs three services: the UI, API, and Neo4j. Re-run the build command
after code changes to rebuild the images.
Stop with `docker compose stop` or `podman compose stop`; database volumes remain.
Port 5173 must be free, so stop any local UI dev server first.

### Service URLs

| Service | URL | Notes |
|---|---|---|
| **Novelist UI** | `http://localhost:5173` | Containerized static UI + API proxy |
| **API + Swagger** | `http://localhost:8081/docs` | — |
| **Neo4j Browser** | `http://localhost:7474` | neo4j / password |

## UI features

| Page | What it does |
|---|---|
| **Register / Login** | JWT-based auth; tokens stored in `localStorage` |
| **Browse Books** | Paginated grid, search by title/author, filter by genre, sort by title/rating/newest |
| **Book Detail** | Full metadata, live rating summary, Rate & Review modal (star picker + free-text) |
| **Add Book** | Modal form: title, author, year, pages, genres, ISBN, cover URL, description |
| **Trending** | Top-10 books by rating×count; genre popularity bar chart |
| **My Profile** | Identity card + complete reading history with stars and reviews |
| **Stories & Journal** | Public articles and author pages; private account drafts, Markdown preview, explicit publishing and unpublishing |

## API endpoints

| Resource | Endpoints |
|---|---|
| **Auth** | `POST /auth/register`, `POST /auth/login`, `POST /auth/refresh`, `POST /auth/logout` |
| **Books** | `POST /api/v1/books`, `GET /api/v1/books`, `GET /api/v1/books/{bookId}`, `PUT /api/v1/books/{bookId}`, `DELETE /api/v1/books/{bookId}`, `GET /api/v1/books/search` |
| **Users** | `POST /api/v1/users`, `GET /api/v1/users`, `GET /api/v1/users/{userId}`, `PUT /api/v1/users/{userId}`, `DELETE /api/v1/users/{userId}`, `GET /api/v1/users/search`, `PUT /api/v1/users/{userId}/preferences` |
| **Ratings** | `POST /api/v1/users/{userId}/ratings/{bookId}` |
| **Articles** | `GET /api/v1/articles`, `GET /api/v1/articles/{articleId}`, `PUT /api/v1/articles/{articleId}`, `GET /api/v1/me/articles`, `GET /api/v1/me/articles/{articleId}`, `GET /api/v1/authors/{userId}` |
| **Profile** | `GET /api/v1/me` |
| **Analytics** | `GET /api/v1/analytics/books/{bookId}/stats`, `GET /api/v1/analytics/books/trending`, `GET /api/v1/analytics/genres` |
| **Recommendations** | `GET /api/v1/recommendations/users/{userId}` |
| **Actuator** | `GET /actuator/health` |

### Book search filters

`GET /api/v1/books/search` accepts:

| Param | Type | Description |
|---|---|---|
| `query` | string | Full-text match on title or author |
| `genre` | string | Exact genre match |
| `year` | int | Published year |
| `sortBy` | `title` \| `rating` \| `createdAt` | Sort field (default `title`) |
| `sortOrder` | `asc` \| `desc` | Sort direction (default `asc`) |
| `minRating` | float | Minimum average rating (1–5) |
| `maxPageCount` | int | Maximum page count |

## Test

```bash
pytest
```

The suite includes article contracts in `tests/test_articles.py`. Infrastructure is mocked; live Neo4j adapter verification remains pending. See [article publishing](spec/ARTICLE_PUBLISHING.md) and [UI review](spec/UI_REVIEW.md) for this phase and its limits.

## Configuration

Copy `.env.example` to `.env`. Key variables:

| Variable | Default | Description |
|---|---|---|
| `NEO4J_URI` | `bolt://localhost:7687` | Neo4j connection |
| `JWT_SECRET_KEY` | — | **Change in production** |
| `JWT_EXPIRY_MINUTES` | `60` | Access token lifetime |
| `JWT_REFRESH_EXPIRY_DAYS` | `7` | Refresh token lifetime |
| `LOG_LEVEL` | `INFO` | `DEBUG` (pretty) or `INFO`/`WARNING`/`ERROR` (JSON) |
| `CORS_ORIGINS` | `*` | Plain string: `*` or comma-separated origins, e.g. `http://localhost:5173` |

See `.env.example` for the full list and `spec/` for architecture and deployment documentation.

## Simplified runtime

RabbitMQ event publishing, semantic passage search, local embedding models, and
Prometheus/Grafana monitoring have been removed. Article publishing, book reviews,
profiles, trending, graph recommendations, structured logging, rate limiting, and
the database health endpoint remain. No database migration is required. Existing
book content is preserved; old search vectors are unused.

For an existing container deployment, run `docker compose up -d --build --remove-orphans`
(or the equivalent `podman compose` command) to rebuild the app and remove containers
for the retired services. Existing named volumes are preserved. Stale `RABBITMQ_*`
and `RAG_*` entries in a local `.env` are ignored and can be removed.
