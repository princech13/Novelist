from typing import Annotated

from fastapi import Depends, Request

from app.infrastructure.neo4j import NovelistRepository
from app.modules.articles.service import ArticleService
from app.modules.auth.service import AuthService
from app.modules.analytics.service import AnalyticsService
from app.modules.books.service import BookService
from app.modules.ratings.service import RatingService
from app.modules.recommendations.service import RecommendationService
from app.modules.profile.service import ProfileService
from app.modules.users.service import UserService


def get_repository(request: Request) -> NovelistRepository:
    return request.app.state.repository


Repo = Annotated[NovelistRepository, Depends(get_repository)]


def get_auth_service(repository: Repo) -> AuthService:
    return AuthService(repository)


def get_analytics_service(repository: Repo) -> AnalyticsService:
    return AnalyticsService(repository)


def get_book_service(repository: Repo) -> BookService:
    return BookService(repository)


def get_rating_service(repository: Repo) -> RatingService:
    return RatingService(repository)


def get_recommendation_service(repository: Repo) -> RecommendationService:
    return RecommendationService(repository)


def get_profile_service(repository: Repo) -> ProfileService:
    return ProfileService(repository)


def get_user_service(repository: Repo) -> UserService:
    return UserService(repository)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
AnalyticsServiceDep = Annotated[AnalyticsService, Depends(get_analytics_service)]
BookServiceDep = Annotated[BookService, Depends(get_book_service)]
RatingServiceDep = Annotated[RatingService, Depends(get_rating_service)]
RecommendationServiceDep = Annotated[RecommendationService, Depends(get_recommendation_service)]
ProfileServiceDep = Annotated[ProfileService, Depends(get_profile_service)]
UserServiceDep = Annotated[UserService, Depends(get_user_service)]


def get_article_service(repository: Repo) -> ArticleService:
    return ArticleService(repository)


ArticleServiceDep = Annotated[ArticleService, Depends(get_article_service)]
