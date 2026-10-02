import { useEffect, useRef, useState, type FormEvent } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { ratingsApi } from "../api/ratings";
import type { Book } from "../api/types";
import { Star, X, PenLine } from "lucide-react";

interface Props { book: Book; userId: string; onClose: () => void; onSubmitted: () => void; }
export function RateReviewModal({ book, userId, onClose, onSubmitted }: Props) {
  const dialog = useRef<HTMLDialogElement>(null);
  const [rating, setRating] = useState(0);
  const [review, setReview] = useState("");
  const [error, setError] = useState("");
  const cache = useQueryClient();
  useEffect(() => { const el = dialog.current; el?.showModal(); return () => el?.close(); }, []);
  const mutation = useMutation({
    mutationFn: () => ratingsApi.add(userId, book.bookId, rating, review.trim() || undefined),
    onSuccess: () => {
      for (const key of ["books", "myBooks", "profile", "bookStats", "bookReviews", "trending"]) void cache.invalidateQueries({ queryKey: [key] });
      onSubmitted();
    },
    onError: () => setError("Your review couldn’t be saved. Your words are still here — please try again."),
  });
  const submit = (event: FormEvent) => { event.preventDefault(); if (!rating) { setError("Choose a rating before posting your review."); return; } setError(""); mutation.mutate(); };
  return <dialog ref={dialog} className="review-dialog" aria-labelledby="review-title" onCancel={event => { event.preventDefault(); if (!mutation.isPending) onClose(); }}><div className="review-dialog-heading"><div><p className="eyebrow">A reader’s perspective</p><h2 id="review-title">Leave a little of your story.</h2><p>{book.title} <span>by {book.author}</span></p></div><button className="icon-button" aria-label="Close review" disabled={mutation.isPending} onClick={onClose}><X size={19} /></button></div><form onSubmit={submit}>{error && <p className="review-error" role="alert">{error}</p>}<fieldset className="review-rating"><legend>How did this book stay with you?</legend><div>{[1,2,3,4,5].map(n => <label key={n} className="star-choice"><input type="radio" name="rating" value={n} checked={rating === n} onChange={() => setRating(n)} aria-label={`${n} ${n === 1 ? "star" : "stars"}`} disabled={mutation.isPending} /><Star size={30} strokeWidth={1.3} fill={n <= rating ? "currentColor" : "none"} /></label>)}<span>{["Choose a rating", "Not for me", "An okay read", "Worth reading", "A wonderful read", "An unforgettable book"][rating]}</span></div></fieldset><label className="review-label" htmlFor="book-review">Your thoughts <span>Optional</span></label><textarea id="book-review" className="review-body" placeholder="What stayed with you after the last page? Share a thought on the writing, a character, or a feeling you couldn’t shake." value={review} onChange={e => setReview(e.target.value)} maxLength={1000} rows={7} disabled={mutation.isPending} /><div className="review-hint"><span>A thoughtful review helps the next reader. Mark any spoilers.</span><span>{review.length} / 1000</span></div><div className="review-dialog-footer"><button type="button" className="text-link" disabled={mutation.isPending} onClick={onClose}>Keep reading</button><button type="submit" className="ink-button" disabled={!rating || mutation.isPending}><PenLine size={15} />{mutation.isPending ? "Posting…" : "Post your review"}</button></div></form></dialog>;
}
