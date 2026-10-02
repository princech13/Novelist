import { api } from "./client";
import type { PageOut } from "./types";

export interface ArticleContent { title: string; subtitle: string; body: string; kind: "Article" | "Book review"; book: string }
export interface Article extends ArticleContent {
  articleId: string; authorId: string; authorName: string; revision: number;
  published: boolean; updatedAt: string; publishedAt: string | null;
}
export type ArticleSummary = Omit<Article, "body" | "revision">;
export type ArticleAction = "save" | "publish" | "unpublish";
export interface Author { userId: string; name: string; publishedCount: number }
export const articlesApi = {
  list: (page = 0, authorId?: string): Promise<PageOut<ArticleSummary>> => api.get('/api/v1/articles', { params: { page, size: 12, authorId } }).then(r => r.data),
  mine: (page = 0): Promise<PageOut<ArticleSummary>> => api.get('/api/v1/me/articles', { params: { page, size: 12 } }).then(r => r.data),
  get: (id: string): Promise<Article> => api.get(`/api/v1/articles/${id}`).then(r => r.data),
  draft: (id: string): Promise<Article> => api.get(`/api/v1/me/articles/${id}`).then(r => r.data),
  save: (id: string, content: ArticleContent, revision: number, action: ArticleAction): Promise<Article> => api.put(`/api/v1/articles/${id}`, { ...content, revision, action }).then(r => r.data),
  author: (id: string): Promise<Author> => api.get(`/api/v1/authors/${encodeURIComponent(id)}`).then(r => r.data),
};
export function errorMessage(error: unknown, fallback: string) {
  const response = (error as { response?: { data?: { detail?: unknown; message?: string }; status?: number } })?.response;
  return typeof response?.data?.detail === "string" ? response.data.detail : response?.data?.message || fallback;
}
