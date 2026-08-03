"use client";
import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { supabase } from '@/lib/supabaseClient';

const CATEGORIES = [
  { name: 'Transport & Freight', code: 'TRA' },
  { name: 'Warehousing & Fulfillment', code: 'WHF' },
  { name: 'Tracking & Visibility', code: 'TRV' },
  { name: 'Labeling & Packaging', code: 'LAB' },
  { name: 'Digital Freight & Marketplaces', code: 'DFM' },
  { name: 'Supply Chain Software & Analytics', code: 'SCA' },
  { name: 'Customs, Compliance & Trade', code: 'CCT' },
  { name: 'Sustainability & Green Logistics', code: 'SGL' },
];
const CATEGORY_ORDER = CATEGORIES.map((c) => c.name);

function categoryClass(category) {
  const match = CATEGORIES.find((c) => c.name === category);
  return match ? `cat-${match.code.toLowerCase()}` : 'cat-other';
}

export default function CompaniesPage() {
  const router = useRouter();
  const [companies, setCompanies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [session, setSession] = useState(null);
  const [categoryFilter, setCategoryFilter] = useState('All');
  const [countryFilter, setCountryFilter] = useState('All');
  const [statusFilter, setStatusFilter] = useState('All');

  useEffect(() => {
    async function fetchCompanies() {
      try {
        const response = await fetch('/api/companies');
        const json = await response.json();
        if (!response.ok) throw new Error(json.error || 'Failed to load companies');
        setCompanies(json.companies || []);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }

    async function loadSession() {
      const { data } = await supabase.auth.getSession();
      setSession(data.session);
    }

    fetchCompanies();
    loadSession();

    const { data: authListener } = supabase.auth.onAuthStateChange((_event, currentSession) => {
      setSession(currentSession);
    });

    return () => {
      authListener.subscription.unsubscribe();
    };
  }, []);

  const isLoggedIn = Boolean(session?.user);

  const categories = useMemo(() => {
    const present = new Set(companies.map((c) => c.category || 'Other'));
    return CATEGORY_ORDER.filter((c) => present.has(c));
  }, [companies]);

  const countries = useMemo(() => {
    const present = new Set(companies.map((c) => c.country).filter(Boolean));
    return Array.from(present).sort();
  }, [companies]);

  const statuses = useMemo(() => {
    const present = new Set(companies.map((c) => (c.status || 'active').trim().toLowerCase()));
    return Array.from(present).sort();
  }, [companies]);

  const filteredCompanies = companies.filter((company) => {
    if (categoryFilter !== 'All' && (company.category || 'Other') !== categoryFilter) return false;
    if (countryFilter !== 'All' && company.country !== countryFilter) return false;
    if (statusFilter !== 'All' && (company.status || 'active').trim().toLowerCase() !== statusFilter) return false;
    return true;
  });

  return (
    <main className="page-shell">
      <section className="page-header">
        <div>
          <p className="eyebrow">Startup monitor</p>
          <h1>Logistics Startup Monitor</h1>
          <p className="section-text">
            The monitor pulls the latest logistics companies from the discovery pipeline.
          </p>
        </div>
      </section>

      {loading && <p>Loading startups…</p>}
      {error && <p className="error-text">{error}</p>}

      {!loading && !error && companies.length === 0 && (
        <div className="empty-state-card">
          <p>No interesting startups found yet. Run the pipeline or verify the discovery source.</p>
        </div>
      )}

      {!loading && companies.length > 0 && (
        <div className="companies-layout">
          <aside className="filter-sidebar">
            <div className="filter-group">
              <h3>Category</h3>
              <div className="filter-pills">
                <button
                  className={`filter-pill ${categoryFilter === 'All' ? 'active' : ''}`}
                  onClick={() => setCategoryFilter('All')}
                >
                  All
                </button>
                {categories.map((category) => (
                  <button
                    key={category}
                    className={`filter-pill ${categoryFilter === category ? 'active' : ''}`}
                    onClick={() => setCategoryFilter(category)}
                  >
                    {category}
                  </button>
                ))}
              </div>
            </div>

            <div className="filter-group">
              <h3>Country</h3>
              <div className="filter-pills">
                <button
                  className={`filter-pill ${countryFilter === 'All' ? 'active' : ''}`}
                  onClick={() => setCountryFilter('All')}
                >
                  All
                </button>
                {countries.map((country) => (
                  <button
                    key={country}
                    className={`filter-pill ${countryFilter === country ? 'active' : ''}`}
                    onClick={() => setCountryFilter(country)}
                  >
                    {country}
                  </button>
                ))}
              </div>
            </div>

            <div className="filter-group">
              <h3>Status</h3>
              <div className="filter-pills">
                <button
                  className={`filter-pill ${statusFilter === 'All' ? 'active' : ''}`}
                  onClick={() => setStatusFilter('All')}
                >
                  All
                </button>
                {statuses.map((status) => (
                  <button
                    key={status}
                    className={`filter-pill ${statusFilter === status ? 'active' : ''}`}
                    onClick={() => setStatusFilter(status)}
                  >
                    {status}
                  </button>
                ))}
              </div>
            </div>
          </aside>

          <div>
            {filteredCompanies.length === 0 ? (
              <div className="empty-state-card">
                <p>No startups match these filters.</p>
              </div>
            ) : (
              <div className="company-grid">
                {filteredCompanies.map((company) => {
                  const description = company.description || 'No description available.';
                  const preview = !isLoggedIn ? `${description.slice(0, 120)}${description.length > 120 ? '…' : ''}` : description;
                  const catClass = categoryClass(company.category);

                  return (
                    <article
                      key={company.id}
                      className={`company-card company-card-clickable ${catClass}`}
                      onClick={() => router.push(`/companies/${company.id}`)}
                    >
                      <span className={`category-badge ${catClass}`}>
                        {company.category || 'Other'}
                      </span>
                      <div className="company-card-header">
                        <h2>{company.name}</h2>
                      </div>
                      <p className="company-description">{preview}</p>
                      <div className="company-meta">
                        <span>{company.country || 'Global'}</span>
                        <span>{company.hq_city || 'HQ unknown'}</span>
                        <span>{company.funding_stage || 'Stage unknown'}</span>
                      </div>
                      {isLoggedIn ? (
                        <div className="company-footer">
                          {company.website ? (
                            <a
                              href={company.website}
                              target="_blank"
                              rel="noreferrer"
                              className="link-button"
                              onClick={(event) => event.stopPropagation()}
                            >
                              Visit website
                            </a>
                          ) : (
                            <span className="meta-text">No website provided</span>
                          )}
                        </div>
                      ) : (
                        <div className="company-footer">
                          <span className="meta-text">Click to view profile and <strong>register</strong> for full details.</span>
                        </div>
                      )}
                    </article>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      )}

      {!isLoggedIn && (
        <div className="alert-card">
          <p>
            Sign in or register for free to unlock full company descriptions, contacts, and market detail.
          </p>
          <Link href="/auth" className="button button-secondary">
            Register now
          </Link>
        </div>
      )}
    </main>
  );
}
