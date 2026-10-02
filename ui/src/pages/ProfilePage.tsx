import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { ArrowRight, Star } from 'lucide-react';
import { profileApi } from '../api/profile';
import { useAuth } from '../context/AuthContext';
import { LoadState } from '../components/Editorial';
export function ProfilePage(){
  const{userId}=useAuth();const query=useQuery({queryKey:['profile',userId],queryFn:profileApi.me});
  if(query.isPending||query.isError)return <LoadState loading={query.isPending} error={query.isError} retry={()=>query.refetch()}/>;
  const user=query.data;const reviews=user.ratedBooks.filter(r=>r.review);
  return <section><header className="reader-profile"><div className="reader-avatar">{user.name.slice(0,1)}</div><div><p className="eyebrow">Your reading life</p><h1>{user.name}</h1><p className="intro-copy">{user.preferences?.favoriteGenres?.join(' · ') || 'A collection of books, thoughts, and things worth remembering.'}</p><Link className="text-link" to={`/authors/${user.userId}`}>Your public writer page <ArrowRight size={15}/></Link></div></header><div className="reading-stats"><div><strong>{user.ratedBooks.length}</strong><span>Books rated</span></div><div><strong>{reviews.length}</strong><span>Written reviews</span></div><div><strong>{user.preferences?.annualReadingGoal ?? '—'}</strong><span>Annual reading goal</span></div></div><div className="section-rule"><span>Notes from your bookshelf</span><Link to="/journal">Your writing notebook ↗</Link></div>{user.ratedBooks.length ? <div>{user.ratedBooks.map((entry,i)=><article className="reader-review" key={entry.book?.bookId||i}><div><p className="eyebrow">{entry.timestamp?new Date(entry.timestamp).toLocaleDateString(): 'From your reading life'}</p>{entry.book?<Link to={`/books/${entry.book.bookId}`}><h2>{entry.book.title}</h2></Link>:<h2>Unavailable book</h2>}<p className="article-byline">{entry.book?.author}</p></div><span className="rating-inline" aria-label={`${entry.rating} out of 5 stars`}><Star size={15} fill="currentColor"/>{entry.rating} / 5</span>{entry.review&&<p className="review-text">{entry.review}</p>}</article>)}</div>:<div className="journal-empty"><h2>The shelf is yours to fill.</h2><p>Rate a book or leave a review to start your reading history.</p><Link className="ink-button" to="/books">Find your next read <ArrowRight size={16}/></Link></div>}</section>;
}
