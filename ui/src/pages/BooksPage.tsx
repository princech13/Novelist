import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { booksApi } from "../api/books";
import type { Book, PageOut } from "../api/types";
import { Search, Plus, Star, ChevronLeft, ChevronRight } from "lucide-react";
import { AddBookModal } from "../components/AddBookModal";

export function BooksPage() {
  const navigate = useNavigate();
  const [page, setPage] = useState(0);
  const [query, setQuery] = useState("");
  const [genre, setGenre] = useState("");
  const [sortBy, setSortBy] = useState<"title" | "rating" | "createdAt">("title");
  const [showAdd, setShowAdd] = useState(false);

  const isSearching = query.trim() !== "" || genre !== "";

  const { data, isLoading, refetch } = useQuery<PageOut<Book>>({
    queryKey: ["books", page, query, genre, sortBy],
    queryFn: () =>
      isSearching
        ? booksApi.search({
            query: query.trim() || undefined,
            genre: genre || undefined,
            sortBy,
            page,
            size: 20,
          })
        : booksApi.list(page, 20),
  });

  return (
    <div style={styles.page}>
      {/* Header */}
      <div style={styles.header}>
        <div>
          <p style={styles.eyebrow}>Your Library</p>
          <h1 style={styles.pageTitle}>Browse Books</h1>
          <p style={styles.pageSubtitle}>
            {data ? `${data.totalElements} books in collection` : "Loading…"}
          </p>
        </div>
        <button onClick={() => setShowAdd(true)} style={styles.addBtn}>
          <Plus size={15} />
          Add Book
        </button>
      </div>

      {/* Search & Filters */}
      <div style={styles.searchRow}>
        <div style={styles.searchBox}>
          <Search size={15} color="#6b7280" style={{ flexShrink: 0 }} />
          <input
            style={styles.searchInput}
            placeholder="Search by title or author…"
            value={query}
            onChange={(e) => { setQuery(e.target.value); setPage(0); }}
          />
        </div>
        <input
          style={styles.filterInput}
          placeholder="Genre"
          value={genre}
          onChange={(e) => { setGenre(e.target.value); setPage(0); }}
        />
        <select
          style={styles.filterInput}
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value as "title" | "rating" | "createdAt")}
        >
          <option value="title">Sort: Title</option>
          <option value="rating">Sort: Rating</option>
          <option value="createdAt">Sort: Newest</option>
        </select>
      </div>

      {/* Divider */}
      <div style={styles.divider} />

      {/* Book grid */}
      {isLoading ? (
        <div style={styles.empty}>Loading…</div>
      ) : !data || data.content.length === 0 ? (
        <div style={styles.empty}>No books found.</div>
      ) : (
        <div style={styles.grid}>
          {data.content.map((book) => (
            <BookCard
              key={book.bookId}
              book={book}
              onClick={() => navigate(`/books/${book.bookId}`)}
            />
          ))}
        </div>
      )}

      {/* Pagination */}
      {data && data.totalPages > 1 && (
        <div style={styles.pagination}>
          <button
            style={page === 0 ? styles.pageBtn : styles.pageBtnActive}
            disabled={page === 0}
            onClick={() => setPage((p) => p - 1)}
          >
            <ChevronLeft size={16} />
          </button>
          <span style={styles.pageInfo}>
            {page + 1} / {data.totalPages}
          </span>
          <button
            style={data.last ? styles.pageBtn : styles.pageBtnActive}
            disabled={data.last}
            onClick={() => setPage((p) => p + 1)}
          >
            <ChevronRight size={16} />
          </button>
        </div>
      )}

      {showAdd && (
        <AddBookModal
          onClose={() => setShowAdd(false)}
          onCreated={() => { setShowAdd(false); refetch(); }}
        />
      )}
    </div>
  );
}

function BookCard({ book, onClick }: { book: Book; onClick: () => void }) {
  const [hovered, setHovered] = useState(false);

  // Generate a deterministic gradient from the book title for placeholder covers
  const colors = [
    ["#1a1a2e", "#16213e"],
    ["#0f3460", "#533483"],
    ["#1b1b2f", "#2c2c54"],
    ["#162447", "#1f4068"],
    ["#2d132c", "#ee4540"],
    ["#0d0d0d", "#3a3a5c"],
  ];
  const idx = book.title.charCodeAt(0) % colors.length;
  const [c1, c2] = colors[idx];

  return (
    <div
      style={{
        ...cardStyles.wrap,
        transform: hovered ? "translateY(-6px)" : "translateY(0)",
        boxShadow: hovered
          ? "0 20px 40px rgba(0,0,0,0.6)"
          : "0 4px 16px rgba(0,0,0,0.35)",
      }}
      onClick={onClick}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      {/* Cover */}
      <div style={cardStyles.coverArea}>
        {book.coverImageUrl ? (
          <img
            src={book.coverImageUrl}
            alt={book.title}
            style={{
              ...cardStyles.coverImg,
              transform: hovered ? "scale(1.06)" : "scale(1)",
            }}
          />
        ) : (
          <div
            style={{
              ...cardStyles.coverPlaceholder,
              background: `linear-gradient(145deg, ${c1}, ${c2})`,
              transform: hovered ? "scale(1.06)" : "scale(1)",
            }}
          >
            <span style={cardStyles.coverInitial}>{book.title[0]}</span>
          </div>
        )}

        {/* Hover overlay */}
        <div
          style={{
            ...cardStyles.overlay,
            opacity: hovered ? 1 : 0,
          }}
        >
          <span style={cardStyles.overlayReadBtn}>View Details</span>
        </div>

        {/* Rating badge always visible */}
        {book.averageRating != null && (
          <div style={cardStyles.ratingBadge}>
            <Star size={10} color="#f59e0b" fill="#f59e0b" />
            <span style={cardStyles.ratingBadgeText}>
              {book.averageRating.toFixed(1)}
            </span>
          </div>
        )}
      </div>

      {/* Card body */}
      <div style={cardStyles.body}>
        <p style={cardStyles.title}>{book.title}</p>
        <p style={cardStyles.author}>{book.author}</p>
        {book.genres && book.genres.length > 0 && (
          <div style={cardStyles.genreRow}>
            {book.genres.slice(0, 2).map((g) => (
              <span key={g} style={cardStyles.genrePill}>{g}</span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  page: {
    minHeight: "100vh",
  },
  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "flex-end",
    marginBottom: 28,
  },
  eyebrow: {
    fontSize: 11,
    fontWeight: 600,
    letterSpacing: "0.12em",
    textTransform: "uppercase",
    color: "#6366f1",
    margin: "0 0 6px",
  },
  pageTitle: {
    fontSize: 28,
    fontWeight: 800,
    color: "#f1f5f9",
    margin: "0 0 4px",
    letterSpacing: "-0.02em",
  },
  pageSubtitle: { fontSize: 13, color: "#64748b", margin: 0 },
  addBtn: {
    display: "flex",
    alignItems: "center",
    gap: 7,
    background: "#6366f1",
    color: "#fff",
    border: "none",
    borderRadius: 8,
    padding: "9px 18px",
    fontSize: 13,
    fontWeight: 600,
    cursor: "pointer",
    letterSpacing: "0.01em",
    flexShrink: 0,
  },
  searchRow: {
    display: "flex",
    gap: 10,
    marginBottom: 24,
    flexWrap: "wrap",
  },
  searchBox: {
    display: "flex",
    alignItems: "center",
    gap: 8,
    background: "#1e2533",
    border: "1px solid #2d3748",
    borderRadius: 8,
    padding: "9px 14px",
    flex: 1,
    minWidth: 200,
  },
  searchInput: {
    border: "none",
    outline: "none",
    fontSize: 13,
    flex: 1,
    color: "#e2e8f0",
    background: "transparent",
  },
  filterInput: {
    border: "1px solid #2d3748",
    borderRadius: 8,
    padding: "9px 14px",
    fontSize: 13,
    color: "#e2e8f0",
    background: "#1e2533",
    outline: "none",
  },
  divider: {
    height: 1,
    background: "#1e2533",
    marginBottom: 28,
  },
  grid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fill, minmax(165px, 1fr))",
    gap: 20,
  },
  pagination: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    gap: 14,
    marginTop: 40,
  },
  pageBtn: {
    background: "#1e2533",
    border: "1px solid #2d3748",
    borderRadius: 6,
    padding: "7px 11px",
    cursor: "not-allowed",
    opacity: 0.4,
    display: "flex",
    alignItems: "center",
    color: "#94a3b8",
  },
  pageBtnActive: {
    background: "#1e2533",
    border: "1px solid #3f4a5c",
    borderRadius: 6,
    padding: "7px 11px",
    cursor: "pointer",
    display: "flex",
    alignItems: "center",
    color: "#e2e8f0",
  },
  pageInfo: { fontSize: 13, color: "#64748b", fontVariantNumeric: "tabular-nums" },
  empty: { textAlign: "center", color: "#4b5563", marginTop: 80, fontSize: 15 },
};

const cardStyles: Record<string, React.CSSProperties> = {
  wrap: {
    background: "#131b2e",
    borderRadius: 12,
    overflow: "hidden",
    cursor: "pointer",
    transition: "transform 0.22s ease, box-shadow 0.22s ease",
    border: "1px solid #1e2d45",
  },
  coverArea: {
    position: "relative",
    height: 220,
    overflow: "hidden",
  },
  coverImg: {
    width: "100%",
    height: "100%",
    objectFit: "cover",
    display: "block",
    transition: "transform 0.35s ease",
  },
  coverPlaceholder: {
    width: "100%",
    height: "100%",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    transition: "transform 0.35s ease",
  },
  coverInitial: {
    fontSize: 52,
    fontWeight: 800,
    color: "rgba(255,255,255,0.18)",
    userSelect: "none",
  },
  overlay: {
    position: "absolute",
    inset: 0,
    background: "linear-gradient(to top, rgba(6,11,25,0.92) 0%, rgba(6,11,25,0.45) 60%, transparent 100%)",
    display: "flex",
    alignItems: "flex-end",
    justifyContent: "center",
    paddingBottom: 18,
    transition: "opacity 0.25s ease",
  },
  overlayReadBtn: {
    fontSize: 12,
    fontWeight: 700,
    letterSpacing: "0.1em",
    textTransform: "uppercase",
    color: "#fff",
    background: "rgba(99,102,241,0.85)",
    borderRadius: 6,
    padding: "6px 14px",
    backdropFilter: "blur(4px)",
  },
  ratingBadge: {
    position: "absolute",
    top: 10,
    right: 10,
    background: "rgba(0,0,0,0.65)",
    borderRadius: 20,
    padding: "3px 8px",
    display: "flex",
    alignItems: "center",
    gap: 4,
    backdropFilter: "blur(6px)",
  },
  ratingBadgeText: {
    fontSize: 11,
    fontWeight: 700,
    color: "#fbbf24",
  },
  body: {
    padding: "12px 14px 14px",
  },
  title: {
    fontSize: 13,
    fontWeight: 700,
    color: "#e2e8f0",
    margin: "0 0 3px",
    display: "-webkit-box",
    WebkitLineClamp: 2,
    WebkitBoxOrient: "vertical",
    overflow: "hidden",
    lineHeight: 1.4,
  },
  author: {
    fontSize: 11,
    color: "#64748b",
    margin: "0 0 8px",
  },
  genreRow: {
    display: "flex",
    gap: 4,
    flexWrap: "wrap",
  },
  genrePill: {
    fontSize: 10,
    background: "#1e2d45",
    color: "#7c8fa8",
    borderRadius: 4,
    padding: "2px 7px",
    fontWeight: 500,
  },
};
