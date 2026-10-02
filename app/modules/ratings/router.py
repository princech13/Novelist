"""Rating routes: add ratings and review books."""
from fastapi import APIRouter, Depends, Query

from app.core.dependencies import RatingServiceDep
from app.core.security import get_current_user_id, require_self
from app.core.http import check_paging
from app.core.pagination import make_page
from app.modules.books.schemas import BookOut
from app.modules.ratings.schemas import BookReviewOut, RatingCreate, RatingOut
from app.modules.shared.schemas import PageOut

router = APIRouter(prefix="/api/v1", tags=["ratings"])


@router.post("/users/{user_id}/ratings/{book_id}", status_code=201, response_model=RatingOut)
def add_rating(user_id: str, book_id: str, body: RatingCreate, service: RatingServiceDep, caller_id: str = Depends(get_current_user_id)):
    require_self(user_id, caller_id)
    return service.add(user_id, book_id, body.rating, body.review)


@router.get("/books/{book_id}/reviews", response_model=list[BookReviewOut])
def book_reviews(book_id: str, service: RatingServiceDep, _: str = Depends(get_current_user_id)):
    return service.book_reviews(book_id)


@router.get("/me/books", response_model=PageOut, summary="Books the current user has rated")
def my_books(
    service: RatingServiceDep,
    page: int = Query(default=0, ge=0),
    size: int = Query(default=20, ge=1, le=100),
    user_id: str = Depends(get_current_user_id),
):
    check_paging(page, size)
    books, total = service.my_books(user_id, page, size)
    return make_page(books, total, page, size)
