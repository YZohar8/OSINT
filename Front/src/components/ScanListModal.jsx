import React from 'react';
import './ScanListModal.css';

function ScanListModal({ responses, onClose }) {
  return (
    <div className="modal-backdrop">
      <div className="modal-content">
        <h2>📋 All Scans</h2>
        <select size="15" style={{ width: '100%' }}>
          {responses.map((r, idx) => (
            <option key={idx}>
              {r.domain} | {r.status} | {r.created_at}
            </option>
          ))}
        </select>
        <button onClick={onClose}>Close</button>
      </div>
    </div>
  );
}

export default ScanListModal;
