from contextlib import asynccontextmanager
from datetime import datetime, timezone

import structlog
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from .core.config import get_settings
from .core.dependencies import Repo
from .core.http import error
from .core.limiter import limiter
from .core.logging import configure_logging
from .infrastructure.messaging import EventPublisher
from .infrastructure.neo4j import NovelistRepository
from .infrastructure.neo4j.base import ConflictError, NotFoundError
from .modules.articles.router import router as articles_router
from .modules.analytics import router as analytics
from .modules.auth import router as auth
from .modules.books import router as books
from .modules.rag.router import router as rag_router
from .modules.ratings import router as ratings
from .modules.recommendations import router as recommendations
from .modules.profile import router as profile
from .modules.users import router as users

_settings = get_settings()
configure_logging(_settings.log_level)
logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    app.state.repository = NovelistRepository(settings)
    app.state.publisher = EventPublisher(settings)
    try:
        app.state.repository.verify()
    except Exception:
        logger.warning("Neo4j is not reachable at startup; requests will retry the connection.")
    yield
    app.state.repository.close()
    app.state.publisher.close()


app = FastAPI(title="Novelist API", version="1.0", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)
Instrumentator().instrument(app).expose(app, endpoint="/actuator/prometheus", include_in_schema=False)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(articles_router)
app.include_router(auth.router)
app.include_router(books.router)
app.include_router(users.router)
app.include_router(ratings.router)
app.include_router(analytics.router)
app.include_router(recommendations.router)
app.include_router(profile.router)
app.include_router(rag_router)

@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = {".".join(str(part) for part in item["loc"] if part != "body"): item["msg"] for item in exc.errors()}
    return JSONResponse(status_code=400, content={"status": 400, "message": "Validation failed", "errors": errors,
                                                   "timestamp": datetime.now(timezone.utc).isoformat()})


@app.exception_handler(NotFoundError)
async def not_found_handler(request: Request, exc: NotFoundError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"status": 404, "message": str(exc), "timestamp": datetime.now(timezone.utc).isoformat()})


@app.exception_handler(ConflictError)
async def conflict_handler(request: Request, exc: ConflictError) -> JSONResponse:
    return JSONResponse(status_code=409, content={"status": 409, "message": str(exc), "timestamp": datetime.now(timezone.utc).isoformat()})


@app.get("/actuator/health", include_in_schema=False)
def health(repo: Repo) -> dict[str, str]:
    try:
        repo.verify()
    except Exception as exc:
        raise error(503, "Neo4j is unavailable") from exc
    return {"status": "UP"}
