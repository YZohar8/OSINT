import React, { useEffect, useState } from 'react';
import './ScanListModal.css';

function ScanListModal({onClose, show }) {
  const [scans, setScans] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const getStatusClass = (status) => `status-${status.replace(/\s+/g, "_")}`;

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    try {
      return new Date(dateString).toLocaleString();
    } catch (err) {
      console.error('Invalid date format:', dateString);
      return 'Invalid Date';
    }
  };

  const updateResponses = async () => {
    setLoading(true);
    setError(null);
    try {
      // ייתכן שתצטרך לשנות את כתובת ה-API
      const res = await fetch('http://localhost:8010/scan/all');
      if (!res.ok) {
        throw new Error(`Failed to fetch: ${res.status} ${res.statusText}`);
      }
      const data = await res.json();
      setScans(data.reverse());
    } catch (err) {
      console.error('Error fetching scans:', err);
      setError(err.message || 'Error fetching scan data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (show) {
      updateResponses();
    }
  }, [show]);

  if (!show) return null;

  return (
    <div className="modal-backdrop">
      <div className="modal-content">
        <h2>📋 All Scans</h2>
        
        {loading && <p>Loading...</p>}
        {error && <p className="error-message">Error: {error}</p>}
        
        {!loading && !error && scans.length === 0 && (
          <p>No scans found.</p>
        )}
        
        {!loading && !error && scans.length > 0 && (
          <table className="scan-table">
            <thead>
              <tr>
                <th>Domain</th>
                <th>Status</th>
                <th>Created At</th>
                <th>Completed At</th>
                <th>Result</th>
              </tr>
            </thead>
            <tbody>
              {scans.map((r, idx) => (
                <tr key={idx}>
                  <td>{r.domain}</td>
                  <td className={getStatusClass(r.status || 'unknown')}>{r.status || 'Unknown'}</td>
                  <td>{formatDate(r.created_at)}</td>
                  <td>{formatDate(r.completed_at)}</td>
                  <td>{typeof r.result === 'object' ? JSON.stringify(r.result) : (r.result || 'Empty')}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        
        <button className="close-btn" onClick={onClose}>Close</button>
      </div>
    </div>
  );
}

export default ScanListModal;
