from typing import Annotated

from fastapi import Depends, Request

from app.core.config import Settings, get_settings
from app.infrastructure.messaging import EventPublisher
from app.infrastructure.neo4j import NovelistRepository
from app.modules.articles.service import ArticleService
from app.modules.auth.service import AuthService
from app.modules.analytics.service import AnalyticsService
from app.modules.books.service import BookService
from app.modules.rag.service import RagService
from app.modules.ratings.service import RatingService
from app.modules.recommendations.service import RecommendationService
from app.modules.profile.service import ProfileService
from app.modules.users.service import UserService


def get_settings_dependency() -> Settings:
    return get_settings()


def get_repository(request: Request) -> NovelistRepository:
    return request.app.state.repository


def get_publisher(request: Request) -> EventPublisher:
    return request.app.state.publisher


Repo = Annotated[NovelistRepository, Depends(get_repository)]
Publisher = Annotated[EventPublisher, Depends(get_publisher)]
SettingsDep = Annotated[Settings, Depends(get_settings_dependency)]


def get_auth_service(repository: Repo) -> AuthService:
    return AuthService(repository)


def get_analytics_service(repository: Repo) -> AnalyticsService:
    return AnalyticsService(repository)


def get_book_service(repository: Repo, publisher: Publisher) -> BookService:
    return BookService(repository, publisher)


def get_rating_service(repository: Repo, publisher: Publisher) -> RatingService:
    return RatingService(repository, publisher)


def get_recommendation_service(repository: Repo) -> RecommendationService:
    return RecommendationService(repository)


def get_profile_service(repository: Repo) -> ProfileService:
    return ProfileService(repository)


def get_user_service(repository: Repo) -> UserService:
    return UserService(repository)


def get_rag_service(repository: Repo, settings: SettingsDep) -> RagService:
    return RagService(repository, settings)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
AnalyticsServiceDep = Annotated[AnalyticsService, Depends(get_analytics_service)]
BookServiceDep = Annotated[BookService, Depends(get_book_service)]
RatingServiceDep = Annotated[RatingService, Depends(get_rating_service)]
RecommendationServiceDep = Annotated[RecommendationService, Depends(get_recommendation_service)]
ProfileServiceDep = Annotated[ProfileService, Depends(get_profile_service)]
UserServiceDep = Annotated[UserService, Depends(get_user_service)]
RagServiceDep = Annotated[RagService, Depends(get_rag_service)]


def get_article_service(repository: Repo) -> ArticleService:
    return ArticleService(repository)


ArticleServiceDep = Annotated[ArticleService, Depends(get_article_service)]
