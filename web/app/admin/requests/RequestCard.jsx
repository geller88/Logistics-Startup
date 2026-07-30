"use client";
import { useState } from 'react';

export default function RequestCard({ request }) {
  const [status, setStatus] = useState(request.status);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  async function updateStatus(newStatus) {
    setSaving(true);
    setError('');

    try {
      const response = await fetch('/api/premium/status', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id: request.id, status: newStatus }),
      });

      const json = await response.json();
      if (!response.ok) {
        throw new Error(json.error || 'Unable to update status');
      }

      setStatus(newStatus);
    } catch (err) {
      setError(err.message || 'Update failed');
    } finally {
      setSaving(false);
    }
  }

  return (
    <article className="card request-card">
      <div className="company-card-header">
        <div>
          <h2>{request.plan}</h2>
          <p className="section-text">Requested by user: {request.user_id}</p>
        </div>
        <span className="badge">{status}</span>
      </div>
      <p className="company-description">{request.message}</p>
      <div className="company-meta">
        <span>{new Date(request.created_at).toLocaleString()}</span>
      </div>
      <div className="request-actions">
        <button className="button button-primary" type="button" onClick={() => updateStatus('approved')} disabled={saving || status === 'approved'}>
          Approve
        </button>
        <button className="button button-secondary" type="button" onClick={() => updateStatus('rejected')} disabled={saving || status === 'rejected'}>
          Reject
        </button>
        <button className="button button-secondary" type="button" onClick={() => updateStatus('in review')} disabled={saving || status === 'in review'}>
          In review
        </button>
      </div>
      {error && <p className="error-text">{error}</p>}
    </article>
  );
}
