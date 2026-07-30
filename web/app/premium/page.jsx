"use client";
import { useEffect, useState } from 'react';
import Link from 'next/link';
import { supabase } from '@/lib/supabaseClient';

export default function PremiumPage() {
  const [session, setSession] = useState(null);
  const [message, setMessage] = useState('');
  const [plan, setPlan] = useState('Standard Research');
  const [status, setStatus] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

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
      authListener?.subscription?.unsubscribe();
    };
  }, []);

  const isLoggedIn = Boolean(session?.user);

  async function handleSubmit(event) {
    event.preventDefault();
    setError('');
    setStatus('');
    setLoading(true);

    if (!isLoggedIn) {
      setError('Please sign in to submit a premium research request.');
      setLoading(false);
      return;
    }

    try {
      const response = await fetch('/api/premium', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: session.user.id,
          plan,
          message,
        }),
      });

      const json = await response.json();
      if (!response.ok) {
        throw new Error(json.error || 'Request failed');
      }

      setStatus('Your premium research request has been submitted. We will follow up by email shortly.');
      setMessage('');
    } catch (err) {
      setError(err.message || 'Unable to submit request.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="page-shell">
      <section className="page-header">
        <div>
          <p className="eyebrow">Premium research</p>
          <h1>Deeper logistics analysis for power users.</h1>
          <p className="section-text">
            Reserve premium LLM-driven logistics research, portfolio-level trend insight, and startup intelligence.
          </p>
        </div>
      </section>

      <section className="section-grid">
        <article className="card">
          <h2>Submit a premium research request</h2>
          <p className="section-text">
            Logged-in users can request a premium analysis brief on logistics sectors, startup portfolios, or supply chain opportunities.
          </p>

          {!isLoggedIn ? (
            <div className="alert-card">
              <p>Please <Link href="/auth" className="link-button">sign in or register</Link> to submit a premium research request.</p>
            </div>
          ) : (
            <form className="auth-form" onSubmit={handleSubmit}>
              <label>Request type</label>
              <select value={plan} onChange={(event) => setPlan(event.target.value)}>
                <option>Standard Research</option>
                <option>Startup Portfolio Scan</option>
                <option>Market Trend Deep Dive</option>
              </select>

              <div className="form-field">
                <label>What would you like researched?</label>
                <textarea
                  value={message}
                  onChange={(event) => setMessage(event.target.value)}
                  placeholder="Provide a short summary of the logistics research you need."
                  rows="6"
                  required
                />
              </div>

              <button type="submit" className="button button-primary" disabled={loading}>
                {loading ? 'Submitting…' : 'Submit request'}
              </button>

              {status && <p className="info-text">{status}</p>}
              {error && <p className="error-text">{error}</p>}
            </form>
          )}
        </article>

        <article className="card">
          <h3>What you get</h3>
          <ul className="feature-list">
            <li>Custom logistics research briefs tailored to your use case.</li>
            <li>Startup and market trend insight for freight, warehousing, last mile, and visibility.</li>
            <li>Fast follow-up on premium requests from the operations or investor team.</li>
          </ul>
        </article>
      </section>
    </main>
  );
}
