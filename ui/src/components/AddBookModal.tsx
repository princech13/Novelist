import React, { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { booksApi } from "../api/books";
import type { BookCreate } from "../api/types";
import { X } from "lucide-react";

interface Props {
  onClose: () => void;
  onCreated: () => void;
}

export function AddBookModal({ onClose, onCreated }: Props) {
  const [form, setForm] = useState<BookCreate>({ title: "", author: "" });
  const [genresRaw, setGenresRaw] = useState("");
  const [error, setError] = useState("");

  const mutation = useMutation({
    mutationFn: (body: BookCreate) => booksApi.create(body),
    onSuccess: onCreated,
    onError: (err: unknown) => {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        "Failed to create book.";
      setError(msg);
    },
  });

  const set = (field: keyof BookCreate) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) =>
    setForm((f) => ({ ...f, [field]: e.target.value }));

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    const genres = genresRaw
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);
    mutation.mutate({ ...form, genres: genres.length ? genres : undefined });
  };

  return (
    <div style={overlay}>
      <div style={styles.modal}>
        <div style={styles.header}>
          <div>
            <h2 style={styles.title}>Add New Book</h2>
            <p style={styles.subtitle}>Fill in the details for your new book</p>
          </div>
          <button style={styles.closeBtn} onClick={onClose}>
            <X size={18} />
          </button>
        </div>

        {error && <div style={styles.errorBanner}>{error}</div>}

        <form onSubmit={submit} style={styles.form}>
          <Field label="Title *">
            <input style={styles.input} value={form.title} onChange={set("title")} required placeholder="e.g. Clean Code" />
          </Field>
          <Field label="Author *">
            <input style={styles.input} value={form.author} onChange={set("author")} required placeholder="e.g. Robert C. Martin" />
          </Field>
          <div style={styles.row}>
            <Field label="Published Year">
              <input
                style={styles.input}
                type="number"
                value={form.publishedYear ?? ""}
                onChange={(e) => setForm((f) => ({ ...f, publishedYear: e.target.value ? Number(e.target.value) : undefined }))}
                placeholder="2024"
              />
            </Field>
            <Field label="Pages">
              <input
                style={styles.input}
                type="number"
                value={form.pageCount ?? ""}
                onChange={(e) => setForm((f) => ({ ...f, pageCount: e.target.value ? Number(e.target.value) : undefined }))}
                placeholder="320"
              />
            </Field>
          </div>
          <Field label="Genres (comma-separated)">
            <input
              style={styles.input}
              value={genresRaw}
              onChange={(e) => setGenresRaw(e.target.value)}
              placeholder="Fiction, Thriller, Sci-Fi"
            />
          </Field>
          <Field label="ISBN">
            <input style={styles.input} value={form.isbn ?? ""} onChange={set("isbn")} placeholder="978-3-16-148410-0" />
          </Field>
          <Field label="Cover Image URL">
            <input style={styles.input} value={form.coverImageUrl ?? ""} onChange={set("coverImageUrl")} placeholder="https://…" />
          </Field>
          <Field label="Description">
            <textarea
              style={{ ...styles.input, height: 80, resize: "vertical" }}
              value={form.description ?? ""}
              onChange={set("description")}
              placeholder="Short description of the book"
            />
          </Field>
          <div style={styles.footer}>
            <button type="button" style={styles.cancelBtn} onClick={onClose}>Cancel</button>
            <button type="submit" style={styles.submitBtn} disabled={mutation.isPending}>
              {mutation.isPending ? "Saving…" : "Add Book"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 5, flex: 1 }}>
      <label style={{ fontSize: 11, fontWeight: 600, color: "#4B5155", letterSpacing: "0.04em", textTransform: "uppercase" as const }}>{label}</label>
      {children}
    </div>
  );
}

const overlay: React.CSSProperties = {
  position: "fixed",
  inset: 0,
  background: "rgba(31,36,33,0.3)",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  zIndex: 1000,
  padding: 16,
  backdropFilter: "blur(4px)",
};

const styles: Record<string, React.CSSProperties> = {
  modal: {
    background: "#FFFFFF",
    borderRadius: 16,
    border: "1px solid #EBEAE5",
    boxShadow: "0 16px 48px rgba(0,0,0,0.12)",
    width: "100%",
    maxWidth: 520,
    maxHeight: "90vh",
    overflowY: "auto",
    padding: 32,
  },
  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "flex-start",
    marginBottom: 20,
    paddingBottom: 16,
    borderBottom: "1px solid #F4F3F0",
  },
  title: {
    fontFamily: "'Playfair Display', Georgia, serif",
    fontSize: 18,
    fontWeight: 700,
    color: "#1F2421",
    margin: "0 0 3px",
  },
  subtitle: {
    fontSize: 12,
    color: "#9CA3A8",
    margin: 0,
  },
  closeBtn: {
    background: "#F8F7F4",
    border: "1px solid #EBEAE5",
    cursor: "pointer",
    color: "#9CA3A8",
    padding: 6,
    borderRadius: 7,
    display: "flex",
    alignItems: "center",
  },
  errorBanner: {
    background: "#FEF2F2",
    border: "1px solid #FECACA",
    color: "#B91C1C",
    borderRadius: 8,
    padding: "9px 12px",
    fontSize: 13,
    marginBottom: 14,
  },
  form: { display: "flex", flexDirection: "column", gap: 14 },
  row: { display: "flex", gap: 12 },
  input: {
    border: "1.5px solid #E5E3DC",
    borderRadius: 8,
    padding: "9px 11px",
    fontSize: 13,
    outline: "none",
    color: "#1F2421",
    background: "#FDFCF9",
    width: "100%",
    boxSizing: "border-box" as const,
    transition: "border-color 0.15s",
  },
  footer: { display: "flex", justifyContent: "flex-end", gap: 10, marginTop: 4 },
  cancelBtn: {
    background: "#F8F7F4",
    border: "1.5px solid #EBEAE5",
    borderRadius: 8,
    padding: "9px 18px",
    fontSize: 13,
    cursor: "pointer",
    color: "#6C757D",
    fontWeight: 500,
  },
  submitBtn: {
    background: "#E05347",
    color: "#fff",
    border: "none",
    borderRadius: 8,
    padding: "9px 20px",
    fontSize: 13,
    fontWeight: 600,
    cursor: "pointer",
  },
};
