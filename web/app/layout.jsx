import './globals.css';
import Link from 'next/link';

export const metadata = {
  title: 'Logistics Startup Market',
  description: 'MVP for logistics startup discovery and user-gated research',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        <div className="app-shell">
          <header className="site-header">
            <Link href="/" className="site-brand">
              Logistics Startup Market
            </Link>
            <nav className="site-nav">
              <Link href="/companies">Monitor</Link>
              <Link href="/search">Discover</Link>
              <Link href="/premium">Premium</Link>
              <Link href="/auth" className="nav-cta">
                Register
              </Link>
            </nav>
          </header>
          <div className="content-wrapper">{children}</div>
          <footer className="site-footer">
            <p>Built for logistics startup discovery, registration gating, and premium research.</p>
          </footer>
        </div>
      </body>
    </html>
  );
}
