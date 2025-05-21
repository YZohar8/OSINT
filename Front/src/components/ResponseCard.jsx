import React from 'react';
import './ResponseCard.css';

function ResponseCard({ domain, response, status, createdAt, completedAt }) {
  return (
    <div className="response-card">
      <h3>{domain}</h3>
      <p>Status: {status}</p>
      <p>Started: {new Date(createdAt).toLocaleString()}</p>
      {completedAt && <p>Completed: {new Date(completedAt).toLocaleString()}</p>}
      {(status === 'completed' || status === 'error') && (
        <pre>{JSON.stringify(response, null, 2)}</pre>
      )}
    </div>
  );
}

export default ResponseCard;