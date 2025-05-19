import React, { useState } from 'react';
import './App.css';

function App() {
  const [domain, setDomain] = useState('');
  const [responses, setResponses] = useState([]);

  const handleSubmit = async () => {
    if (!domain) return;
    const res = await fetch('http://localhost:8000/scan', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ domain })
    });
    const data = await res.json();
    setResponses([{ domain, response: data.message }, ...responses]);
    setDomain('');
  };

  return (
    <div className="App">
      <h1>OSINT Scanner</h1>
      <input
        type="text"
        value={domain}
        onChange={(e) => setDomain(e.target.value)}
        placeholder="Enter domain name"
      />
      <button onClick={handleSubmit}>Scan</button>
      <div className="results">
        {responses.map((r, idx) => (
          <div key={idx} className="card">
            <strong>Domain:</strong> {r.domain}<br/>
            <strong>Response:</strong> {r.response}
          </div>
        ))}
      </div>
    </div>
  );
}

export default App;
