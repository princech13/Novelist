import { api } from "./client";
import type { Book, BookCreate, PageOut } from "./types";

export interface BookSearchParams {
  query?: string;
  genre?: string;
  year?: number;
  sortBy?: "title" | "createdAt" | "rating";
  sortOrder?: "asc" | "desc";
  minRating?: number;
  maxPageCount?: number;
  page?: number;
  size?: number;
}

export const booksApi = {
  list: (page = 0, size = 20): Promise<PageOut<Book>> =>
    api.get("/api/v1/books", { params: { page, size } }).then((r) => r.data),

  search: (params: BookSearchParams): Promise<PageOut<Book>> =>
    api.get("/api/v1/books/search", { params }).then((r) => r.data),

  get: (bookId: string): Promise<Book> =>
    api.get(`/api/v1/books/${bookId}`).then((r) => r.data),

  create: (body: BookCreate): Promise<Book> =>
    api.post("/api/v1/books", body).then((r) => r.data),

  update: (bookId: string, body: Partial<BookCreate>): Promise<Book> =>
    api.put(`/api/v1/books/${bookId}`, body).then((r) => r.data),

  delete: (bookId: string): Promise<void> =>
    api.delete(`/api/v1/books/${bookId}`).then(() => undefined),

  myBooks: (page = 0, size = 20): Promise<PageOut<Book>> =>
    api.get("/api/v1/me/books", { params: { page, size } }).then((r) => r.data),
};
