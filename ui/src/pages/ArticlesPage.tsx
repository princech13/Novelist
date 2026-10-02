import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link, useParams } from 'react-router-dom';
import { ArrowLeft, ArrowRight, PenLine } from 'lucide-react';
import { articlesApi, type ArticleSummary } from '../api/articles';
import { PageHeading, PageNav, LoadState } from '../components/Editorial';
import { StoryBody } from '../components/StoryBody';
import { useAuth } from '../context/AuthContext';

export function ArticleRows({ articles }: { articles: ArticleSummary[] }) {
  return <div className="article-list">{articles.map((article, index) => <article className="article-row" key={article.articleId}><span className="article-number">{String(index+1).padStart(2,'0')}</span><div><p className="eyebrow">{article.kind}{article.book ? ` / ${article.book}` : ''}</p><Link to={`/articles/${article.articleId}`}><h2>{article.title}</h2><p className="article-deck">{article.subtitle || 'A new perspective from the Novelist community.'}</p></Link><p className="article-byline"><Link to={`/authors/${article.authorId}`}>{article.authorName}</Link><span>·</span>{new Date(article.publishedAt || article.updatedAt).toLocaleDateString(undefined,{month:'short',day:'numeric',year:'numeric'})}</p></div><Link className="icon-button" aria-label={`Read ${article.title}`} to={`/articles/${article.articleId}`}><ArrowRight size={21}/></Link></article>)}</div>;
}
export function ArticlesPage() {
  const [page,setPage] = useState(0);
  const query = useQuery({queryKey:['articles','public',page],queryFn:()=>articlesApi.list(page)});
  return <section><PageHeading eyebrow="The Novelist journal" title="Stories for the thoughtful reader.">Essays, reading notes, and fresh perspectives on the books that shape us.</PageHeading><div className="section-rule"><span>Latest stories</span><Link to="/write">Add your perspective ↗</Link></div>{query.isPending || query.isError ? <LoadState loading={query.isPending} error={query.isError} retry={()=>query.refetch()}/> : query.data.content.length ? <><ArticleRows articles={query.data.content}/><PageNav page={page} total={query.data.totalPages} onPage={setPage}/></> : <div className="journal-empty"><PenLine size={30}/><h2>The first story could be yours.</h2><p>Published articles and long-form book reviews will appear here.</p><Link className="ink-button" to="/write">Write a story <ArrowRight size={16}/></Link></div>}</section>;
}
export function ArticlePage() {
  const {articleId = ''} = useParams(); const {userId} = useAuth();
  const query = useQuery({queryKey:['articles','public',articleId],queryFn:()=>articlesApi.get(articleId)});
  if (query.isPending || query.isError) return <LoadState loading={query.isPending} error={query.isError} retry={()=>query.refetch()}/>;
  const article = query.data;
  return <section className="article-reading"><Link className="text-link" to="/articles"><ArrowLeft size={16}/>All stories</Link><header><p className="eyebrow">{article.kind}{article.book ? ` / ${article.book}` : ''}</p><h1>{article.title}</h1>{article.subtitle && <p className="reading-deck">{article.subtitle}</p>}<div className="article-byline"><Link to={`/authors/${article.authorId}`}>By {article.authorName}</Link><span>·</span><span>{Math.max(1,Math.ceil(article.body.trim().split(/\s+/).length/200))} min read</span><span>·</span><span>{new Date(article.publishedAt!).toLocaleDateString()}</span></div></header><StoryBody text={article.body}/><footer className="reading-footer"><Link className="text-link" to={`/authors/${article.authorId}`}>More by {article.authorName} <ArrowRight size={16}/></Link>{userId === article.authorId && <Link className="outline-button" to={`/write/${article.articleId}`}>Edit working draft</Link>}</footer></section>;
}
export function AuthorPage() {
  const {authorId = ''} = useParams(); const [page,setPage]=useState(0);
  const author = useQuery({queryKey:['author',authorId],queryFn:()=>articlesApi.author(authorId)});
  const articles = useQuery({queryKey:['articles','author',authorId,page],queryFn:()=>articlesApi.list(page,authorId)});
  if (author.isPending || author.isError) return <LoadState loading={author.isPending} error={author.isError} retry={()=>author.refetch()}/>;
  return <section><PageHeading eyebrow="Meet the writer" title={author.data.name}>{author.data.publishedCount} published {author.data.publishedCount === 1 ? 'story' : 'stories'} · A voice in the Novelist community.</PageHeading><div className="section-rule"><span>From this writer</span><Link to="/articles">All stories ↗</Link></div>{articles.isPending || articles.isError ? <LoadState loading={articles.isPending} error={articles.isError} retry={()=>articles.refetch()}/> : articles.data.content.length ? <><ArticleRows articles={articles.data.content}/><PageNav page={page} total={articles.data.totalPages} onPage={setPage}/></> : <div className="editorial-empty"><h2>A story is still taking shape.</h2><p>This author hasn’t published anything yet.</p></div>}</section>;
}
