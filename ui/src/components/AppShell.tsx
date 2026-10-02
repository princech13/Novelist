import { useEffect, type ReactNode } from "react";
import { NavLink, Link, useNavigate, useLocation } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";
import { useAuth } from "../context/AuthContext";
import { Feather, LogOut, PenLine } from "lucide-react";

export function AppShell({ children }: { children: ReactNode }) {
  const { logout, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const { pathname } = useLocation();
  useEffect(() => { window.scrollTo(0, 0); }, [pathname]);
  const cache = useQueryClient();
  const handleLogout = async () => {
    await logout();
    cache.clear();
    navigate("/login");
  };
  return (
    <div className="editorial-shell">
      <a className="skip-link" href="#main-content">Skip to content</a>
      <header className="site-header">
        <Link to="/books" className="wordmark"><Feather size={25} strokeWidth={1.4} />novelist<span className="wordmark-dot">.</span></Link>
        <nav className="site-nav" aria-label="Main navigation">
          <NavLink to="/books">The library</NavLink>
          <NavLink to="/articles">Stories</NavLink>
          <NavLink to="/journal">My journal</NavLink>
          <NavLink to="/trending">Discover</NavLink>
          <NavLink to="/profile">My reading</NavLink>
        </nav>
        <div className="header-actions">
          <Link to="/write" className="ink-button"><PenLine size={15} /> Write a story</Link>
          {isAuthenticated ? <button className="icon-button" onClick={handleLogout} aria-label="Sign out" title="Sign out"><LogOut size={17} /></button> : <Link className="text-link" to="/login">Sign in</Link>}
        </div>
      </header>
      <main id="main-content" className="editorial-main">{children}</main>
      <footer className="site-footer"><Link className="footer-brand" to="/books">novelist.</Link><span>A little space for books. A little room for thought.</span><Link to="/chat">Search inside books ↗</Link></footer>
    </div>
  );
}
