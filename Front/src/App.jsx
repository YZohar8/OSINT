import React, { useState, useEffect } from 'react';
import './App.css';
import ResponseCard from './components/ResponseCard';

function App() {
  const [domain, setDomain] = useState('');
  const [responses, setResponses] = useState([]);
  const [error, setError] = useState('');

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

      setResponses(prev => [
        {
          scan_id: data.scan_id,
          domain,
          status: 'in_progress',
          created_at: data.start_time,
          result: null,
          completed_at: null,
        },
        ...prev
      ]);

      setDomain('');
    } catch (err) {
      console.error('Error:', err);
      setError('Something went wrong. Please try again.');
    }
  };

  useEffect(() => {
    const interval = setInterval(async () => {
      const incomplete = responses.filter(r => r.status !== 'completed');

      for (let item of incomplete) {
        try {
          const res = await fetch(`http://localhost:8010/scan/${item.scan_id}`);
          const data = await res.json();

          if (data.status === 'completed') {
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
    </div>
  );
}

export default App;
