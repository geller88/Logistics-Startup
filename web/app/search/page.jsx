"use client";
import { useEffect, useState } from 'react';
import Link from 'next/link';
import { supabase } from '@/lib/supabaseClient';

export default function SearchPage() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [session, setSession] = useState(null);

  useEffect(() => {
    async function loadSession() {
      const { data } = await supabase.auth.getSession();
      setSession(data.session);
    }

    loadSession();
    const { data: authListener } = supabase.auth.onAuthStateChange((_event, currentSession) => {
      setSession(currentSession);
    });

    return () => {
      authListener.subscription.unsubscribe();
    };
  }, []);

  const isLoggedIn = Boolean(session?.user);

  async function handleSearch(event) {
    event.preventDefault();
    setError('');
    setLoading(true);
    setResults([]);

    try {
      const response = await fetch('/api/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query }),
      });
      const json = await response.json();
      if (!response.ok) throw new Error(json.error || 'Search failed');
      setResults(json.results || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="page-shell">
      <section className="page-header">
        <div>
          <p className="eyebrow">Discovery search</p>
          <h1>Search logistics startups without paid LLM calls.</h1>
          <p className="section-text">
            Search company names, descriptions, websites, and headquarters data from pipeline discovery. Register to unlock full company profiles.
          </p>
        </div>
        {!isLoggedIn && (
          <div className="alert-card">
            <p>Free registration unlocks deeper startup detail, premium research, and more market context.</p>
            <Link href="/auth" className="button button-secondary">
              Register for free
            </Link>
          </div>
        )}
      </section>

      <form onSubmit={handleSearch} className="search-form">
        <input
          type="text"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Search logistics startups, freight, warehouse automation, or supply chain visibility"
          className="search-input"
        />
        <button type="submit" className="button button-primary">
          Search
        </button>
      </form>

      {loading && <p className="info-text">Searching…</p>}
      {error && <p className="error-text">{error}</p>}

      {!loading && results.length > 0 && (
        <div className="company-grid">
          {results.map((company) => {
            const description = company.description || 'No description available.';
            const preview = !isLoggedIn ? `${description.slice(0, 140)}${description.length > 140 ? '…' : ''}` : description;

            return (
              <article key={company.id} className="company-card">
                <div className="company-card-header">
                  <h2>{company.name}</h2>
                  <span className="badge">{company.status || 'Active'}</span>
                </div>
                <p className="company-description">{preview}</p>
                <div className="company-meta">
                  <span>{company.country || 'Global'}</span>
                  <span>{company.hq_city || 'HQ unknown'}</span>
                  <span>{company.funding_stage || 'Stage unknown'}</span>
                </div>
                {!isLoggedIn && (
                  <div className="company-footer">
                    <span className="meta-text">Sign in to read the full startup profile.</span>
                  </div>
                )}
              </article>
            );
          })}
        </div>
      )}

      {!loading && !error && results.length === 0 && query && (
        <p className="info-text">No search results found for that query.</p>
      )}
    </main>
  );
}
