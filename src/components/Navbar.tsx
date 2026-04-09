import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import { Menu, X, Atom } from 'lucide-react';
import { useState } from 'react';

export default function Navbar() {
  const { isAuthenticated, logout } = useAuth();
  const location = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);

  const links = [
    { to: '/', label: 'Home' },
    { to: '/blog', label: 'Articles' },
  ];

  const isActive = (path: string) => location.pathname === path;

  return (
    <nav className="sticky top-0 z-50 border-b border-border bg-background/90 backdrop-blur-md">
      <div className="container mx-auto flex items-center justify-between px-4 py-4">
        <Link to="/" className="flex items-center gap-2 group">
          <Atom className="h-6 w-6 text-primary transition-transform group-hover:rotate-90" />
          <span className="font-heading text-xl font-bold text-primary">
            Physics Blog
          </span>
        </Link>

        {/* Desktop */}
        <div className="hidden md:flex items-center gap-8">
          {links.map((l) => (
            <Link
              key={l.to}
              to={l.to}
              className={`text-sm tracking-wide transition-colors ${
                isActive(l.to) ? 'text-primary font-medium' : 'text-chalk hover:text-primary'
              }`}
            >
              {l.label}
            </Link>
          ))}
          {isAuthenticated ? (
            <>
              <Link
                to="/admin"
                className={`text-sm tracking-wide transition-colors ${
                  location.pathname.startsWith('/admin') ? 'text-primary font-medium' : 'text-chalk hover:text-primary'
                }`}
              >
                Admin
              </Link>
              <button
                onClick={logout}
                className="text-sm text-muted-foreground hover:text-destructive transition-colors"
              >
                Logout
              </button>
            </>
          ) : (
            <Link
              to="/login"
              className="text-sm text-chalk hover:text-primary transition-colors"
            >
              Login
            </Link>
          )}
        </div>

        {/* Mobile toggle */}
        <button
          className="md:hidden text-chalk"
          onClick={() => setMobileOpen(!mobileOpen)}
        >
          {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
      </div>

      {/* Mobile menu */}
      {mobileOpen && (
        <div className="md:hidden border-t border-border bg-background px-4 pb-4 space-y-3">
          {links.map((l) => (
            <Link
              key={l.to}
              to={l.to}
              onClick={() => setMobileOpen(false)}
              className={`block py-2 text-sm ${isActive(l.to) ? 'text-primary' : 'text-chalk'}`}
            >
              {l.label}
            </Link>
          ))}
          {isAuthenticated ? (
            <>
              <Link to="/admin" onClick={() => setMobileOpen(false)} className="block py-2 text-sm text-chalk">
                Admin
              </Link>
              <button onClick={() => { logout(); setMobileOpen(false); }} className="block py-2 text-sm text-muted-foreground">
                Logout
              </button>
            </>
          ) : (
            <Link to="/login" onClick={() => setMobileOpen(false)} className="block py-2 text-sm text-chalk">
              Login
            </Link>
          )}
        </div>
      )}
    </nav>
  );
}
