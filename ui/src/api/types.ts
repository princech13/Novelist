// ── Auth ────────────────────────────────────────────────────────────────────
export interface TokenOut {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

// ── Books ────────────────────────────────────────────────────────────────────
export interface Book {
  bookId: string;
  title: string;
  author: string;
  isbn?: string;
  publishedYear?: number;
  description?: string;
  content?: string;
  language?: string;
  pageCount?: number;
  coverImageUrl?: string;
  genres?: string[];
  createdAt?: string;
  updatedAt?: string;
  averageRating?: number;
  totalRatings?: number;
  hasEmbedding?: boolean;
}

export interface BookCreate {
  title: string;
  author: string;
  isbn?: string;
  publishedYear?: number;
  description?: string;
  content?: string;
  language?: string;
  pageCount?: number;
  coverImageUrl?: string;
  genres?: string[];
}

export interface PageOut<T> {
  content: T[];
  page: number;
  size: number;
  totalElements: number;
  totalPages: number;
  first: boolean;
  last: boolean;
  hasNext: boolean;
  hasPrevious: boolean;
}

// ── Ratings ──────────────────────────────────────────────────────────────────
export interface RatingOut {
  book: Book | null;
  rating: number;
  review?: string;
  timestamp?: string;
  helpfulCount?: number;
}

export interface BookReview {
  userId: string;
  userName: string;
  rating: number;
  review?: string;
  timestamp?: string;
}

// ── Users ────────────────────────────────────────────────────────────────────
export interface Preferences {
  favoriteGenres?: string[];
  favoriteAuthors?: string[];
  annualReadingGoal?: number;
  emailNotifications?: boolean;
  recommendationNotifications?: boolean;
}

export interface UserOut {
  userId: string;
  name: string;
  email?: string;
  age: number;
  preferences?: Preferences;
  ratedBooks: RatingOut[];
  createdAt?: string;
  updatedAt?: string;
}

// ── Analytics ────────────────────────────────────────────────────────────────
export interface BookStats {
  bookId: string;
  averageRating?: number;
  totalRatings: number;
}

export interface GenreCount {
  genre: string;
  count: number;
}

// ── RAG ──────────────────────────────────────────────────────────────────────
export interface RagChunk {
  bookId: string;
  title: string;
  author: string;
  chunkIndex: number;
  text: string;
  score: number;
}

export interface RagSearchOut {
  query: string;
  results: RagChunk[];
}
