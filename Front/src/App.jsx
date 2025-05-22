import React, { useState, useEffect } from 'react';
import './App.css';
import ResponseCard from './components/ResponseCard';
import ScanListModal from './components/ScanListModal';
import * as XLSX from 'xlsx';

function App() {
  const [domain, setDomain] = useState('');
  const [responses, setResponses] = useState([]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [allScans, setAllScans] = useState([]);

  const isValidDomain = (d) => {
    const domainRegex = /^(?!-)([a-zA-Z0-9-]{1,63}\.)+[a-zA-Z]{2,}$/;
    return domainRegex.test(d);
  };

  const handleSubmit = async () => {
    setError('');
    if (!domain) return;

    if (!isValidDomain(domain)) {
      setError('Invalid domain format. Please enter a valid domain like example.com');
      setDomain('');
      return;
    }

    setLoading(true);
    try {
      const res = await fetch('http://localhost:8010/scan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ domain })
      });

      if (!res.ok) throw new Error('Server error');

      const data = await res.json();
      setResponses(prev => [data, ...prev]);
      setDomain('');
    } catch (err) {
      console.error('Error:', err);
      setError('Something went wrong. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const exportToExcel = async () => {
    await updateResponses();
    const worksheet = XLSX.utils.json_to_sheet(allScans.map(r => ({
      Domain: r.domain,
      Status: r.status,
      CreatedAt: r.created_at,
      CompletedAt: r.completed_at,
      Result: JSON.stringify(r.result || {})
    })));

    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, worksheet, 'Scans');

    XLSX.writeFile(workbook, 'osint_scans.xlsx');
  };

  const updateResponses = async () => {
    try {
      const res = await fetch('http://localhost:8010/scan/all');
      if (!res.ok) throw new Error('Failed to fetch scans');
      const data = await res.json();
      setAllScans(data.reverse());
    } catch (err) {
      console.error('Error fetching scans:', err);
    }
  };

  useEffect(() => {
    const fetchAllScans = async () => {
      try {
        const res = await fetch('http://localhost:8010/scan/all');
        if (!res.ok) throw new Error('Failed to fetch scans');
        const data = await res.json();
        setAllScans(data.reverse());
      } catch (err) {
        console.error('Error fetching scans:', err);
      }
    };

    fetchAllScans();
  }, []);

  useEffect(() => {
    const pollIncompleteScans = async () => {
      const interval = setInterval(async () => {
        const incomplete = responses.filter(r => r.status !== 'completed' && r.status !== 'error');
        for (let item of incomplete) {
          try {
            const res = await fetch(`http://localhost:8010/scan/${item.scan_id}`);
            if (!res.ok) continue;
            const data = await res.json();
            if (data.status === 'completed' || data.status === 'error') {
              setResponses(prev =>
                prev.map(r => (r.scan_id === item.scan_id ? { ...r, ...data } : r))
              );
            }
          } catch (err) {
            console.error('Polling error:', err);
          }
        }
      }, 15000);

      return () => clearInterval(interval);
    };

    pollIncompleteScans();
  }, [responses]);

  return (
    <div className="App">
      <h1 className="title">🔎 OSINT Scanner</h1>
      <div className="input-group">
        <input
          type="text"
          value={domain}
          onChange={(e) => setDomain(e.target.value)}
          placeholder="Enter domain name..."
        />
        <button onClick={handleSubmit} disabled={loading}>{loading ? 'Scanning...' : 'Scan'}</button>
        <button onClick={() => setShowModal(true)}>📂 Show All</button>
        <button onClick={exportToExcel}>📥 Export to Excel</button>
      </div>

      {error && <p className="error">{error}</p>}

      <div className="results">
        {Array.isArray(responses) && responses.map((r, idx) =>
          r && typeof r === 'object' && r.domain ? (
            <ResponseCard
              key={idx}
              domain={r.domain}
              response={r.result}
              status={r.status}
              createdAt={r.created_at}
              completedAt={r.completed_at}
            />
          ) : (
            <div key={idx} className="response-error">Invalid response format</div>
          )
        )}
      </div>

      {showModal && (
        <ScanListModal responses={responses} onClose={() => setShowModal(false)} show={showModal} />
      )}
    </div>
  );
}

export default App;
