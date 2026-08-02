"use client";
import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { supabase } from '@/lib/supabaseClient';

function categoryClass(category) {
  const codes = {
    'Transport & Freight': 'tra',
    'Warehousing & Fulfillment': 'whf',
    'Tracking & Visibility': 'trv',
    'Labeling & Packaging': 'lab',
    'Digital Freight & Marketplaces': 'dfm',
    'Supply Chain Software & Analytics': 'sca',
    'Customs, Compliance & Trade': 'cct',
    'Sustainability & Green Logistics': 'sgl',
  };
  return `cat-${codes[category] || 'other'}`;
}

export default function CompanyDetailPage() {
  const { id } = useParams();
  const [company, setCompany] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [session, setSession] = useState(null);
  const [logoFailed, setLogoFailed] = useState(false);

  useEffect(() => {
    async function loadSession() {
      const { data } = await supabase.auth.getSession();
      setSession(data.session);
    }

    async function loadCompany() {
      try {
        const response = await fetch(`/api/companies/${id}`);
        const json = await response.json();
        if (!response.ok) throw new Error(json.error || 'Failed to load company');
        setCompany(json.company);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }

    loadSession();
    loadCompany();

    const { data: authListener } = supabase.auth.onAuthStateChange((_event, currentSession) => {
      setSession(currentSession);
    });

    return () => {
      authListener?.subscription?.unsubscribe();
    };
  }, [id]);

  const isLoggedIn = Boolean(session?.user);

  if (loading) {
    return (
      <main className="page-shell">
        <p>Loading company…</p>
      </main>
    );
  }

  if (error || !company) {
    return (
      <main className="page-shell">
        <p className="error-text">{error || 'Company not found.'}</p>
        <Link href="/companies" className="link-button">← Back to monitor</Link>
      </main>
    );
  }

  const catClass = categoryClass(company.category);
  const logoUrl = company.domain ? `https://www.google.com/s2/favicons?domain=${company.domain}&sz=128` : null;

  return (
    <main className="page-shell">
      <Link href="/companies" className="link-button">← Back to monitor</Link>

      <section className={`company-card company-card-detail ${catClass}`}>
        <span className={`category-badge ${catClass}`}>{company.category || 'Other'}</span>

        <div className="company-detail-header">
          {logoUrl && !logoFailed && (
            <img
              src={logoUrl}
              alt={`${company.name} logo`}
              className="company-logo"
              onError={() => setLogoFailed(true)}
            />
          )}
          <div>
            <h1>{company.name}</h1>
            <span className="badge">{company.status || 'Active'}</span>
          </div>
        </div>

        {!isLoggedIn ? (
          <div className="alert-card">
            <p>
              <Link href="/auth" className="link-button">Register for free</Link> to see this company&apos;s full
              profile, including address, phone, and website.
            </p>
          </div>
        ) : (
          <>
            <p className="company-description">{company.description || 'No description available.'}</p>

            <div className="detail-grid">
              <div>
                <h3>Address</h3>
                <p>{company.address || 'Not available'}</p>
              </div>
              <div>
                <h3>ZIP</h3>
                <p>{company.zip_code || 'Not available'}</p>
              </div>
              <div>
                <h3>City</h3>
                <p>{company.hq_city || 'Not available'}</p>
              </div>
              <div>
                <h3>Country</h3>
                <p>{company.country || 'Not available'}</p>
              </div>
              <div>
                <h3>Phone</h3>
                <p>{company.phone || 'Not available'}</p>
              </div>
              <div>
                <h3>Funding stage</h3>
                <p>{company.funding_stage || 'Not available'}</p>
              </div>
            </div>

            {company.website && (
              <a href={company.website} target="_blank" rel="noreferrer" className="button button-primary">
                Visit website
              </a>
            )}
          </>
        )}
      </section>
    </main>
  );
}
