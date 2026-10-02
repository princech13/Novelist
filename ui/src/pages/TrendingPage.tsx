import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { ArrowRight } from 'lucide-react';
import { analyticsApi } from '../api/analytics';
import { PageHeading,LoadState } from '../components/Editorial';
export function TrendingPage(){
  const books=useQuery({queryKey:['trending'],queryFn:()=>analyticsApi.trending(10)});
  const genres=useQuery({queryKey:['genres'],queryFn:analyticsApi.genres});
  const max=Math.max(1,...(genres.data||[]).map(g=>g.count));
  return <section><PageHeading eyebrow="Follow your curiosity" title="Your next great read is out there.">Explore the books readers are responding to, and the corners of the library you haven’t visited.</PageHeading><div className="discovery-grid"><section><div className="section-rule"><span>Reader favourites</span><span>Across the library</span></div><p className="small-note">Ranked by the combined number and strength of ratings, across all time.</p>{books.isPending||books.isError?<LoadState loading={books.isPending} error={books.isError} retry={()=>books.refetch()}/>:books.data.length?books.data.map((book,i)=><Link className="ranked-book" key={book.bookId} to={`/books/${book.bookId}`}><span>{String(i+1).padStart(2,'0')}</span><div><h2>{book.title}</h2><p>{book.author}</p></div><ArrowRight size={18}/></Link>):<div className="editorial-empty"><h2>A favourite is waiting to be found.</h2><p>Book ratings will bring this list to life.</p></div>}</section><aside className="genre-guide"><p className="eyebrow">Choose your own adventure</p><h2>So many worlds.<br/>Where to next?</h2>{genres.isPending||genres.isError?<LoadState loading={genres.isPending} error={genres.isError} retry={()=>genres.refetch()}/>:genres.data.length?genres.data.map(g=><div className="genre-meter" key={g.genre}><div><span>{g.genre}</span><span>{g.count} books</span></div><meter min={0} max={max} value={g.count} aria-label={`${g.genre}: ${g.count} books`}/></div>):<p>No genres in the library yet.</p>}<Link className="text-link" to="/books">Explore every shelf <ArrowRight size={16}/></Link></aside></div></section>;
}
