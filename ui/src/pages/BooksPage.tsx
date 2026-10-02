import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { ArrowDown, ArrowRight, Plus, Search, Star, ChevronLeft, ChevronRight, Feather } from "lucide-react";
import { booksApi } from "../api/books";
import type { Book } from "../api/types";
import { useAuth } from "../context/AuthContext";
import { AddBookModal } from "../components/AddBookModal";

const GENRES = ["Fiction", "Non-Fiction", "Sci-Fi", "History", "Mystery", "Romance"];
export function BooksPage() {
  const { userId } = useAuth();
  const [tab, setTab] = useState("all");
  const [page, setPage] = useState(0);
  const [query, setQuery] = useState("");
  const [genre, setGenre] = useState("");
  const [sortBy, setSortBy] = useState<"title" | "rating" | "createdAt">("title");
  const [showAdd, setShowAdd] = useState(false);
  const { data, isPending, isError, refetch } = useQuery({
    queryKey: ["books", tab, userId, page, query, genre, sortBy],
    queryFn: () => tab === "mine" ? booksApi.myBooks(page, 12) : booksApi.search({
      query: query.trim() || undefined, genre: genre || undefined, sortBy,
      sortOrder: sortBy === "title" ? "asc" : "desc", page, size: 12,
    }),
  });
  const featured = data?.content[0];
  const changeTab = (value: string) => { setTab(value); setPage(0); };
  return (
    <div className="library-page">
      <section className="library-intro">
        <div><p className="eyebrow">For the love of a good story</p><h1>A life between<br />the <em>lines.</em></h1><p className="intro-copy">Books that stay with you. Ideas worth sharing.<br />A home for your next chapter.</p><a className="text-link" href="#bookshelf">Find your next read <ArrowDown size={15} /></a></div>
        <div className="reading-art" aria-hidden="true"><div className="art-orbit" /><div className="art-caption">READ. REFLECT. WRITE.</div><div className="art-book book-back"><span>the art of<br /><i>noticing</i></span><small>A READER’S JOURNAL</small></div><div className="art-book book-front"><span>One more<br /><i>chapter.</i></span><div className="book-line" /><small>NOTES FROM A READING LIFE</small></div><span className="art-number">N° 01 / THE READING ROOM</span></div>
      </section>
      <div className="section-rule"><span>The reading room</span><span>Good books. Fresh perspectives.</span></div>
      <div className="library-layout">
        <section id="bookshelf" className="bookshelf">
          <div className="section-heading"><div><p className="eyebrow">On the bookshelf</p><h2>Find a story to get lost in.</h2></div><button className="text-link" onClick={() => setShowAdd(true)}><Plus size={15} /> Add a book</button></div>
          <div className="shelf-tabs" aria-label="Book collection"><button aria-pressed={tab === "all"} className={tab === "all" ? "selected" : ""} onClick={() => changeTab("all")}>All books</button><button aria-pressed={tab === "mine"} className={tab === "mine" ? "selected" : ""} onClick={() => changeTab("mine")}>Read & reviewed</button></div>
          {tab === "all" && <><div className="shelf-controls"><label className="search-field"><Search size={17} /><input aria-label="Search books" placeholder="A title, an author, a new beginning…" value={query} onChange={e => { setQuery(e.target.value); setPage(0); }} /></label><select aria-label="Sort books" value={sortBy} onChange={e => { setSortBy(e.target.value as typeof sortBy); setPage(0); }}><option value="title">Title A–Z</option><option value="rating">Top rated</option><option value="createdAt">Newest first</option></select></div><div className="genre-filters">{["", ...GENRES].map(g => <button key={g} aria-pressed={genre === g} className={genre === g ? "selected" : ""} onClick={() => { setGenre(g); setPage(0); }}>{g || "All stories"}</button>)}</div></>}
          <div className="shelf-count" aria-live="polite">{isPending ? "Opening the library…" : data ? `${data.totalElements} ${tab === "mine" ? "books you’ve rated or reviewed" : "books to explore"}` : "Library unavailable"}</div>
          {isError ? <div className="editorial-empty" role="alert"><h3>The library couldn’t load.</h3><p>Please check your connection and try again.</p><button className="outline-button" onClick={() => refetch()}>Try again</button></div> : isPending ? <div className="book-grid" aria-label="Loading books">{[0, 1, 2].map(i => <div key={i} className="book-skeleton" />)}</div> : !data?.content.length ? <div className="editorial-empty"><Feather size={28} /><h3>{tab === "mine" ? "Your reading story starts here." : "A little room for a new story."}</h3><p>{tab === "mine" ? "Leave a rating or review on a book to find it here." : query || genre ? "Try a different title, author, or genre." : "Add the first book to the library."}</p><button className="outline-button" onClick={() => tab === "mine" ? changeTab("all") : setShowAdd(true)}>{tab === "mine" ? "Explore the library" : "Add a book"}</button></div> : <div className="book-grid">{data.content.map(book => <BookCard key={book.bookId} book={book} />)}</div>}
          {data && data.totalPages > 1 && <nav className="pagination" aria-label="Book pages"><button className="icon-button" aria-label="Previous page" disabled={page === 0} onClick={() => setPage(page - 1)}><ChevronLeft size={18} /></button><span>Page {page + 1} of {data.totalPages}</span><button className="icon-button" aria-label="Next page" disabled={data.last} onClick={() => setPage(page + 1)}><ChevronRight size={18} /></button></nav>}
        </section>
        <aside className="editorial-aside"><div className="writing-invitation"><Feather size={25} strokeWidth={1.3} /><p className="eyebrow">Your words belong here</p><h2>Every reader<br />has a story.</h2><p>A passage you underlined.<br />A book you can’t forget.<br />Start with what stayed.</p><Link className="ink-button" to="/write">Open your notebook <ArrowRight size={15} /></Link><span className="small-note">A quiet space to put it into words.</span></div>{featured && <div className="shelf-note"><p className="eyebrow">From the current shelf</p><h3>{featured.title}</h3><p>by {featured.author}</p>{featured.description && <p className="book-excerpt">{featured.description.slice(0, 170)}{featured.description.length > 170 ? "…" : ""}</p>}<Link className="text-link" to={`/books/${featured.bookId}`}>Explore this book <ArrowRight size={15} /></Link></div>}<div className="margin-note"><span>In the margins</span><p>Not every thought needs to be a finished story. Some just need a place to begin.</p><Link className="text-link" to="/journal">Visit your journal <ArrowRight size={15} /></Link></div></aside>
      </div>
      {showAdd && <AddBookModal onClose={() => setShowAdd(false)} onCreated={() => { setShowAdd(false); refetch(); }} />}
    </div>
  );
}

function BookCard({ book }: { book: Book }) {
  const [failedCover, setFailedCover] = useState(false);
  const shade = [...book.title].reduce((sum, letter) => sum + letter.charCodeAt(0), 0) % 4;
  return <Link className="shelf-book" to={`/books/${book.bookId}`}><div className={`book-stage shade-${shade}`}>{book.coverImageUrl && !failedCover ? <img src={book.coverImageUrl} alt={`Cover of ${book.title}`} loading="lazy" onError={() => setFailedCover(true)} /> : <div className={`type-cover cover-${shade}`}><small>NOVELIST LIBRARY</small><strong>{book.title}</strong><span>{book.author}</span></div>}</div><div className="book-meta"><span>{book.genres?.[0] || "From the library"}</span>{book.averageRating != null && <span className="book-rating"><Star size={12} fill="currentColor" />{book.averageRating.toFixed(1)}</span>}</div><h3>{book.title}</h3><p>{book.author}</p><span className="book-card-link">Read & reflect <ArrowRight size={13} /></span></Link>;
}
