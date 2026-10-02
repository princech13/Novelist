import { api } from "./client";
import type { BookReview, RatingOut } from "./types";

export const ratingsApi = {
  add: (userId: string, bookId: string, rating: number, review?: string): Promise<RatingOut> =>
    api
      .post(`/api/v1/users/${userId}/ratings/${bookId}`, { rating, review })
      .then((r) => r.data),

  bookReviews: (bookId: string): Promise<BookReview[]> =>
    api.get(`/api/v1/books/${bookId}/reviews`).then((r) => r.data),
};
