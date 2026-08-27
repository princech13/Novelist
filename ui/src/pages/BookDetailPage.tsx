import React, { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { booksApi } from "../api/books";
import { analyticsApi } from "../api/analytics";
import type { Book, BookStats } from "../api/types";
import { Star, ArrowLeft, BookOpen, Calendar, Hash, FileText, Tag, Trash2 } from "lucide-react";
import { RateReviewModal } from "../components/RateReviewModal";
import { useAuth } from "../context/AuthContext";

export function BookDetailPage() {
  const { bookId } = useParams<{ bookId: string }>();
  const navigate = useNavigate();
  const { userId } = useAuth();
  const queryClient = useQueryClient();
  const [showRate, setShowRate] = useState(false);

  const { data: book, isLoading } = useQuery<Book>({
    queryKey: ["book", bookId],
    queryFn: () => booksApi.get(bookId!),
    enabled: !!bookId,
  });

  const { data: stats } = useQuery<BookStats>({
    queryKey: ["bookStats", bookId],
    queryFn: () => analyticsApi.bookStats(bookId!),
    enabled: !!bookId,
  });

  const deleteMutation = useMutation({
    mutationFn: () => booksApi.delete(bookId!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["books"] });
      navigate("/books");
    },
  });

  if (isLoading) return <div style={styles.loading}>Loading…</div>;
  if (!book) return <div style={styles.loading}>Book not found.</div>;

  const avgRating =
    stats?.averageRating != null
      ? stats.averageRating
      : book.averageRating ?? null;
  const totalRatings = stats?.totalRatings ?? book.totalRatings ?? 0;

  // Placeholder gradient
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
    <div style={styles.page}>
      {/* Back */}
      <button style={styles.back} onClick={() => navigate(-1)}>
        <ArrowLeft size={15} />
        Back to library
      </button>

      {/* Hero layout */}
      <div style={styles.hero}>
        {/* Cover */}
        <div style={styles.coverWrap}>
          {book.coverImageUrl ? (
            <img src={book.coverImageUrl} alt={book.title} style={styles.coverImg} />
          ) : (
            <div
              style={{
                ...styles.coverPlaceholder,
                background: `linear-gradient(145deg, ${c1}, ${c2})`,
              }}
            >
              <span style={styles.coverInitial}>{book.title[0]}</span>
            </div>
          )}
        </div>

        {/* Details panel */}
        <div style={styles.details}>
          {book.genres && book.genres.length > 0 && (
            <div style={styles.genreRow}>
              <Tag size={11} color="#6366f1" />
              {book.genres.map((g) => (
                <span key={g} style={styles.genrePill}>{g}</span>
              ))}
            </div>
          )}

          <h1 style={styles.title}>{book.title}</h1>
          <p style={styles.author}>by <span style={styles.authorName}>{book.author}</span></p>

          {/* Rating */}
          <div style={styles.ratingRow}>
            <div style={styles.starsWrap}>
              {[1, 2, 3, 4, 5].map((s) => (
                <Star
                  key={s}
                  size={16}
                  color="#f59e0b"
                  fill={avgRating != null && s <= Math.round(avgRating) ? "#f59e0b" : "none"}
                />
              ))}
            </div>
            <span style={styles.ratingNum}>
              {avgRating != null ? avgRating.toFixed(1) : "—"}
            </span>
            <span style={styles.ratingCount}>· {totalRatings} ratings</span>
          </div>

          {/* Divider */}
          <div style={styles.divider} />

          {/* Meta chips */}
          <div style={styles.metaRow}>
            {book.publishedYear && (
              <MetaChip icon={<Calendar size={13} />} label={String(book.publishedYear)} />
            )}
            {book.pageCount && (
              <MetaChip icon={<BookOpen size={13} />} label={`${book.pageCount} pages`} />
            )}
            {book.isbn && (
              <MetaChip icon={<Hash size={13} />} label={book.isbn} />
            )}
            {book.language && (
              <MetaChip icon={<FileText size={13} />} label={book.language.toUpperCase()} />
            )}
          </div>

          {/* Description */}
          {book.description && (
            <p style={styles.description}>{book.description}</p>
          )}

          {/* Actions */}
          <div style={styles.actions}>
            <button style={styles.rateBtn} onClick={() => setShowRate(true)}>
              <Star size={15} />
              Rate &amp; Review
            </button>
            <button
              style={styles.deleteBtn}
              onClick={() => {
                if (confirm(`Delete "${book.title}"?`)) deleteMutation.mutate();
              }}
            >
              <Trash2 size={14} />
              Delete
            </button>
          </div>
        </div>
      </div>

      {showRate && userId && (
        <RateReviewModal
          book={book}
          userId={userId}
          onClose={() => setShowRate(false)}
          onSubmitted={() => {
            setShowRate(false);
            queryClient.invalidateQueries({ queryKey: ["bookStats", bookId] });
          }}
        />
      )}
    </div>
  );
}

function MetaChip({ icon, label }: { icon: React.ReactNode; label: string }) {
  return (
    <div style={metaStyles.chip}>
      {icon}
      <span style={metaStyles.label}>{label}</span>
    </div>
  );
}

const metaStyles: Record<string, React.CSSProperties> = {
  chip: {
    display: "flex",
    alignItems: "center",
    gap: 6,
    background: "#1e2533",
    border: "1px solid #2d3748",
    borderRadius: 8,
    padding: "6px 12px",
    color: "#94a3b8",
  },
  label: { fontSize: 12, fontWeight: 500, color: "#94a3b8" },
};

const styles: Record<string, React.CSSProperties> = {
  page: {
    minHeight: "100vh",
  },
  loading: { color: "#4b5563", marginTop: 80, textAlign: "center" },
  back: {
    display: "flex",
    alignItems: "center",
    gap: 6,
    background: "none",
    border: "1px solid #2d3748",
    cursor: "pointer",
    color: "#64748b",
    fontSize: 13,
    padding: "7px 14px",
    marginBottom: 32,
    borderRadius: 8,
    transition: "color 0.15s",
  },
  hero: {
    display: "flex",
    gap: 48,
    alignItems: "flex-start",
    flexWrap: "wrap",
  },
  coverWrap: {
    flexShrink: 0,
    borderRadius: 14,
    overflow: "hidden",
    boxShadow: "0 24px 60px rgba(0,0,0,0.65)",
  },
  coverImg: {
    width: 220,
    height: 320,
    objectFit: "cover",
    display: "block",
  },
  coverPlaceholder: {
    width: 220,
    height: 320,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
  },
  coverInitial: {
    fontSize: 72,
    fontWeight: 800,
    color: "rgba(255,255,255,0.15)",
    userSelect: "none",
  },
  details: {
    flex: 1,
    minWidth: 260,
    paddingTop: 8,
  },
  genreRow: {
    display: "flex",
    alignItems: "center",
    gap: 6,
    flexWrap: "wrap",
    marginBottom: 14,
  },
  genrePill: {
    fontSize: 11,
    background: "#1a2340",
    color: "#6366f1",
    borderRadius: 4,
    padding: "3px 9px",
    fontWeight: 600,
    letterSpacing: "0.03em",
  },
  title: {
    fontSize: 30,
    fontWeight: 800,
    color: "#f1f5f9",
    margin: "0 0 8px",
    letterSpacing: "-0.025em",
    lineHeight: 1.2,
  },
  author: {
    fontSize: 15,
    color: "#64748b",
    margin: "0 0 18px",
  },
  authorName: {
    color: "#94a3b8",
    fontWeight: 500,
  },
  ratingRow: {
    display: "flex",
    alignItems: "center",
    gap: 8,
    marginBottom: 20,
  },
  starsWrap: {
    display: "flex",
    gap: 2,
  },
  ratingNum: {
    fontSize: 18,
    fontWeight: 800,
    color: "#fbbf24",
    letterSpacing: "-0.01em",
  },
  ratingCount: {
    fontSize: 13,
    color: "#64748b",
  },
  divider: {
    height: 1,
    background: "#1e2533",
    marginBottom: 20,
  },
  metaRow: {
    display: "flex",
    flexWrap: "wrap",
    gap: 8,
    marginBottom: 24,
  },
  description: {
    fontSize: 14,
    color: "#94a3b8",
    lineHeight: 1.75,
    marginBottom: 28,
    maxWidth: 540,
  },
  actions: {
    display: "flex",
    gap: 10,
    flexWrap: "wrap",
  },
  rateBtn: {
    display: "flex",
    alignItems: "center",
    gap: 7,
    background: "#6366f1",
    color: "#fff",
    border: "none",
    borderRadius: 9,
    padding: "11px 22px",
    fontSize: 14,
    fontWeight: 700,
    cursor: "pointer",
    letterSpacing: "0.01em",
  },
  deleteBtn: {
    display: "flex",
    alignItems: "center",
    gap: 7,
    background: "transparent",
    color: "#ef4444",
    border: "1px solid #3f1e1e",
    borderRadius: 9,
    padding: "11px 18px",
    fontSize: 14,
    fontWeight: 500,
    cursor: "pointer",
  },
};
