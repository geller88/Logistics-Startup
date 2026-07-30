"use client";

import { useEffect, useState } from 'react';
import Link from 'next/link';
import RequestCard from './RequestCard';
import { supabase } from '@/lib/supabaseClient';

export default function AdminRequestsPage() {
  const [session, setSession] = useState(null);
  const [requests, setRequests] = useState([]);
  const [status, setStatus] = useState('loading');
  const [error, setError] = useState('');

  useEffect(() => {
    async function init() {
      const { data } = await supabase.auth.getSession();
      setSession(data.session);
    }

    init();
    const { data: authListener } = supabase.auth.onAuthStateChange((_event, currentSession) => {
      setSession(currentSession);
    });

    return () => {
      authListener?.subscription?.unsubscribe();
    };
  }, []);

  useEffect(() => {
    async function loadRequests() {
      if (!session?.access_token) {
        setStatus('idle');
        return;
      }

      setStatus('loading');
      setError('');

      try {
        const response = await fetch('/api/admin/requests', {
          headers: {
            Authorization: `Bearer ${session.access_token}`,
          },
        });

        const json = await response.json();
        if (!response.ok) {
          throw new Error(json.error || 'Unable to load admin requests');
        }

        setRequests(json.requests || []);
        setStatus('loaded');
      } catch (err) {
        setError(err.message || 'Failed to fetch admin requests');
        setStatus('error');
      }
    }

    loadRequests();
  }, [session]);

  const isSignedIn = Boolean(session?.user);

  return (
    <main className="page-shell">
      <section className="page-header">
        <div>
          <p className="eyebrow">Premium requests</p>
          <h1>Review submitted premium research requests</h1>
          <p className="section-text">
            Only authorized admin users may view premium request data. Sign in with an admin account to continue.
          </p>
        </div>
        <Link href="/premium" className="button button-secondary">
          Back to premium page
        </Link>
      </section>

      {!isSignedIn && (
        <article className="card">
          <p className="section-text">You must be signed in as an admin to view this page.</p>
          <Link href="/auth" className="button button-primary">
            Sign in
          </Link>
        </article>
      )}

      {isSignedIn && status === 'loading' && <p>Loading admin requests…</p>}
      {isSignedIn && status === 'error' && <p className="error-text">{error}</p>}
      {isSignedIn && status === 'loaded' && requests.length === 0 && (
        <article className="card">
          <p className="section-text">No premium research requests have been submitted yet.</p>
        </article>
      )}

      {isSignedIn && status === 'loaded' && requests.length > 0 && (
        <section className="request-grid">
          {requests.map((request) => (
            <RequestCard key={request.id} request={request} />
          ))}
        </section>
      )}
    </main>
  );
}
