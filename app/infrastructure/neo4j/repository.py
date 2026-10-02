"""Application-facing repository composed from feature persistence modules."""
from app.modules.articles.repository import ArticleRepositoryMixin
from .base import Neo4jRepository
from app.modules.analytics.repository import AnalyticsRepositoryMixin
from app.modules.auth.repository import AuthRepositoryMixin
from app.modules.books.repository import BookRepositoryMixin
from app.modules.rag.repository import RagRepositoryMixin
from app.modules.ratings.repository import RatingRepositoryMixin
from app.modules.recommendations.repository import RecommendationRepositoryMixin
from app.modules.users.repository import UserRepositoryMixin


class NovelistRepository(
    ArticleRepositoryMixin,
    AuthRepositoryMixin,
    BookRepositoryMixin,
    UserRepositoryMixin,
    RatingRepositoryMixin,
    AnalyticsRepositoryMixin,
    RecommendationRepositoryMixin,
    RagRepositoryMixin,
    Neo4jRepository,
):
    """Single request-scoped Neo4j adapter composed from feature repositories."""
