import type { ReactNode } from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';
export function PageHeading({ eyebrow, title, children }: { eyebrow: string; title: string; children?: ReactNode }) {
  return <header className="editorial-heading"><p className="eyebrow">{eyebrow}</p><h1>{title}</h1>{children && <div className="intro-copy">{children}</div>}</header>;
}
export function LoadState({ loading, error, retry }: { loading?: boolean; error?: boolean; retry?: () => void }) {
  return <div className="editorial-empty" role={error ? 'alert' : 'status'}><h2>{loading ? 'Opening the next page…' : 'This page couldn’t load.'}</h2>{error && <><p>Your connection or the server may be unavailable.</p><button className="outline-button" onClick={retry}>Try again</button></>}</div>;
}
export function PageNav({ page, total, onPage }: { page: number; total: number; onPage: (page: number) => void }) {
  if (total <= 1) return null;
  return <nav className="pagination" aria-label="Pages"><button className="icon-button" aria-label="Previous page" disabled={!page} onClick={() => onPage(page-1)}><ChevronLeft size={18}/></button><span>Page {page+1} of {total}</span><button className="icon-button" aria-label="Next page" disabled={page+1 >= total} onClick={() => onPage(page+1)}><ChevronRight size={18}/></button></nav>;
}
