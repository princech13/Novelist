# Novelist

Novelist is a full-stack book-management application. A **Python / FastAPI** backend handles books, users, ratings, recommendations, and semantic search; a **React / Vite** frontend provides a browser UI for all those features.

For the reviewed runtime structure, data flows, and known gaps, see [Architecture](spec/ARCHITECTURE.md). The [Architectural decision records](spec/ARCHITECTURAL_DECISIONS.md) explain the important choices, tradeoffs, and implementation evidence.

## Project structure

```
Novelist/
├── app/                            # FastAPI backend
│   ├── main.py                     # Bootstrap: lifespan, router registration, exception handlers
│   ├── core/                       # Config, dependencies, security, rate limiting, logging
│   ├── infrastructure/             # Concrete external-system adapters
│   │   ├── neo4j/                  # Driver lifecycle and composed repository
│   │   └── messaging/              # RabbitMQ persistent-connection publisher
│   └── modules/                    # Feature modules
│       ├── auth/                   # register, login, refresh, logout
│       ├── books/                  # CRUD + paginated search with filters
│       ├── users/                  # CRUD + preferences + search
│       ├── ratings/                # Per-user book ratings and reviews
│       ├── analytics/              # Stats, trending, genre breakdown
│       ├── recommendations/        # Graph-based recommendations
│       ├── profile/                # Current-user profile (/me)
│       ├── rag/                    # Semantic search: index + vector query
│       └── shared/                 # Cross-feature API contracts
├── ui/                             # React + Vite + TypeScript frontend
│   └── src/
│       ├── api/                    # Typed API client (axios + all endpoints)
│       ├── context/                # AuthContext (JWT storage, login/logout)
│       ├── components/             # AppShell, modals (AddBook, RateReview)
│       └── pages/                  # BooksPage, BookDetailPage, ProfilePage,
│                                   # TrendingPage, ChatPage, AuthPages
├── tests/                          # pytest: unit + integration + coverage
├── spec/                           # Architecture, deployment, and design docs
├── docker-compose.yml              # Full stack: API, Neo4j, RabbitMQ, Prometheus, Grafana
└── prometheus.yml                  # Prometheus scrape config
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
- RabbitMQ (optional — disable with `RABBITMQ_ENABLED=false`)

**Frontend**
- Node.js 18+

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

> Set `RABBITMQ_ENABLED=false` in `.env` if you don't have a broker running locally.

### 2 — Frontend

```bash
cd ui
npm install
npm run dev          # → http://localhost:5173
```

## Run with containers

```bash
cp .env.example .env
docker compose up --build
```

Start the UI separately (it is a dev server, not containerised):

```bash
cd ui && npm run dev
```

### Service URLs

| Service | URL | Notes |
|---|---|---|
| **Novelist UI** | `http://localhost:5173` | React dev server |
| **API + Swagger** | `http://localhost:8081/docs` | — |
| **Neo4j Browser** | `http://localhost:7474` | neo4j / password |
| **RabbitMQ Management** | `http://localhost:15672` | novelist / password |
| **Prometheus** | `http://localhost:9090` | — |
| **Grafana** | `http://localhost:3000` | admin / password |

## UI features

| Page | What it does |
|---|---|
| **Register / Login** | JWT-based auth; tokens stored in `localStorage` |
| **Browse Books** | Paginated grid, search by title/author, filter by genre, sort by title/rating/newest |
| **Book Detail** | Full metadata, live rating summary, Rate & Review modal (star picker + free-text) |
| **Add Book** | Modal form: title, author, year, pages, genres, ISBN, cover URL, description |
| **Trending** | Top-10 books by rating×count; genre popularity bar chart |
| **My Profile** | Identity card + complete reading history with stars and reviews |
| **Passage Search** | Semantic search over indexed book content |
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
| **RAG** | `POST /api/v1/rag/index`, `POST /api/v1/rag/search` |
| **Actuator** | `GET /actuator/health`, `GET /actuator/prometheus` |

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

71 tests pass, including article contracts in `tests/test_articles.py`. Infrastructure is mocked; live Neo4j adapter verification remains pending. See [article publishing](spec/ARTICLE_PUBLISHING.md) and [UI review](spec/UI_REVIEW.md) for this phase and its limits.

## Configuration

Copy `.env.example` to `.env`. Key variables:

| Variable | Default | Description |
|---|---|---|
| `NEO4J_URI` | `bolt://localhost:7687` | Neo4j connection |
| `RABBITMQ_ENABLED` | `true` | Set `false` to disable event publishing |
| `JWT_SECRET_KEY` | — | **Change in production** |
| `JWT_EXPIRY_MINUTES` | `60` | Access token lifetime |
| `JWT_REFRESH_EXPIRY_DAYS` | `7` | Refresh token lifetime |
| `LOG_LEVEL` | `INFO` | `DEBUG` (pretty) or `INFO`/`WARNING`/`ERROR` (JSON) |
| `CORS_ORIGINS` | `*` | Plain string: `*` or comma-separated origins, e.g. `http://localhost:5173` |
| `RAG_EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Local sentence-transformers model (~90 MB, downloaded once) |
| `RAG_TOP_K` | `5` | Default number of RAG search results |

See `.env.example` for the full list and `spec/` for architecture and deployment documentation.
