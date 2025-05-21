import React, { useState, useEffect } from 'react';
import './App.css';
import ResponseCard from './components/ResponseCard';
import ScanListModal from './components/ScanListModal';
import * as XLSX from 'xlsx';

function App() {
  const [domain, setDomain] = useState('');
  const [responses, setResponses] = useState([]);
  const [error, setError] = useState('');
  const [showModal, setShowModal] = useState(false);

  const isValidDomain = (d) => {
    const domainRegex = /^(?!\-)([a-zA-Z0-9\-]{1,63}\.)+[a-zA-Z]{2,}$/;
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

    try {
      const res = await fetch('http://localhost:8010/scan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ domain })
      });

      const data = await res.json();
      setResponses(prev => [data, ...prev]);
      setDomain('');
    } catch (err) {
      console.error('Error:', err);
      setError('Something went wrong. Please try again.');
    }
  };

  const exportToExcel = () => {
    const worksheet = XLSX.utils.json_to_sheet(responses.map(r => ({
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

  useEffect(() => {
    const fetchAllScans = async () => {
      try {
        const res = await fetch('http://localhost:8010/scan/all');
        const data = await res.json();
        setResponses(data.reverse());
      } catch (err) {
        console.error('Error fetching scans:', err);
      }
    };

    fetchAllScans();
  }, []);

  useEffect(() => {
    const interval = setInterval(async () => {
      const incomplete = responses.filter(r => r.status !== 'completed' && r.status !== 'error');

      for (let item of incomplete) {
        try {
          const res = await fetch(`http://localhost:8010/scan/${item.scan_id}`);
          const data = await res.json();

          if (data.status === 'completed' || data.status === 'error') {
            setResponses(prev =>
              prev.map(r =>
                r.scan_id === item.scan_id
                  ? { ...r, ...data }
                  : r
              )
            );
          }
        } catch (err) {
          console.error('Polling error:', err);
        }
      }
    }, 3000);

    return () => clearInterval(interval);
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
        <button onClick={handleSubmit}>Scan</button>
        <button onClick={() => setShowModal(true)}>📂 Show All</button>
        <button onClick={exportToExcel}>📥 Export to Excel</button>
      </div>

      {error && <p className="error">{error}</p>}

      <div className="results">
        {responses.map((r, idx) => (
          <ResponseCard
            key={idx}
            domain={r.domain}
            response={r.result}
            status={r.status}
            createdAt={r.created_at}
            completedAt={r.completed_at}
          />
        ))}
      </div>

      {showModal && (
        <ScanListModal responses={responses} onClose={() => setShowModal(false)} />
      )}
    </div>
  );
}

export default App;
