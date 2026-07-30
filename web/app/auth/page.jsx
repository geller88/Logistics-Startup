"use client";
import { useEffect, useState } from 'react';
import Link from 'next/link';
import { supabase } from '@/lib/supabaseClient';

export default function AuthPage() {
  const [mode, setMode] = useState('signIn');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
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
      authListener?.subscription?.unsubscribe();
    };
  }, []);

  async function handleSubmit(event) {
    event.preventDefault();
    setLoading(true);
    setError('');
    setMessage('');

    try {
      if (mode === 'signUp') {
        const { error } = await supabase.auth.signUp({ email, password });
        if (error) throw error;
        setMessage('Registration submitted. Please check your email for the confirmation link.');
      } else {
        const { error } = await supabase.auth.signInWithPassword({ email, password });
        if (error) throw error;
        setMessage('Signed in successfully.');
      }
    } catch (err) {
      setError(err.message || 'An unexpected error occurred.');
    } finally {
      setLoading(false);
    }
  }

  async function handleSignOut() {
    setLoading(true);
    await supabase.auth.signOut();
    setSession(null);
    setLoading(false);
  }

  return (
    <main className="page-shell">
      <section className="page-header">
        <div>
          <p className="eyebrow">Free registration</p>
          <h1>Register for startup access and market research.</h1>
          <p className="section-text">
            Create a free account to unlock full company profiles, contact signals, and premium research insights.
          </p>
        </div>
      </section>

      <div className="section-grid">
        <article className="card">
          {session ? (
            <div>
              <p>You are signed in as <strong>{session.user.email}</strong>.</p>
              <button className="button button-secondary" type="button" onClick={handleSignOut} disabled={loading}>
                Sign out
              </button>
              <p className="info-text">You can now return to the monitor or search pages.</p>
            </div>
          ) : (
            <form className="auth-form" onSubmit={handleSubmit}>
              <div className="toggle-row">
                <button
                  type="button"
                  className={mode === 'signIn' ? 'button button-primary' : 'button button-secondary'}
                  onClick={() => setMode('signIn')}
                >
                  Sign in
                </button>
                <button
                  type="button"
                  className={mode === 'signUp' ? 'button button-primary' : 'button button-secondary'}
                  onClick={() => setMode('signUp')}
                >
                  Register
                </button>
              </div>

              <div className="form-field">
                <label>Email</label>
                <input
                  type="email"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  placeholder="you@example.com"
                  required
                />
              </div>

              <div className="form-field">
                <label>Password</label>
                <input
                  type="password"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  placeholder="Enter a secure password"
                  required
                />
              </div>

              <button className="button button-primary" type="submit" disabled={loading}>
                {loading ? 'Processing…' : mode === 'signUp' ? 'Register' : 'Sign in'}
              </button>

              {error && <p className="error-text">{error}</p>}
              {message && <p className="info-text">{message}</p>}
            </form>
          )}
        </article>

        <article className="card">
          <h2>Why register?</h2>
          <ul className="feature-list">
            <li>Unlock full logistics startup descriptions.</li>
            <li>Reveal company contacts and website access.</li>
            <li>Get access to premium logistics market analysis.</li>
          </ul>
          <p className="section-text">
            Your registration keeps the discovery and search experience free, while enabling richer data for serious logistics teams.
          </p>
          <Link href="/premium" className="button button-secondary">
            Explore premium research
          </Link>
        </article>
      </div>
    </main>
  );
}
