import { useEffect, useState } from 'react';
import '../styles/HistoryPage.css';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://127.0.0.1:8000';

function HistoryPage({ onBack }) {
  const [reports, setReports] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetch(`${API_BASE_URL}/api/bugs?limit=50`)
      .then((response) => {
        if (!response.ok) throw new Error('Could not load bug history.');
        return response.json();
      })
      .then((data) => setReports(data.reports || []))
      .catch((reason) => setError(reason.message))
      .finally(() => setIsLoading(false));
  }, []);

  return (
    <main className="history-page">
      <div className="history-header">
        <div>
          <span className="history-kicker">Workspace</span>
          <h1>Bug History</h1>
          <p>Review submitted reports and reopen a diagnosis from your workspace.</p>
        </div>
        <button className="history-back-btn" type="button" onClick={onBack}>Back to diagnoses</button>
      </div>
      {isLoading && <div className="history-state">Loading submitted bugs...</div>}
      {error && <div className="history-state history-error">{error}</div>}
      {!isLoading && !error && reports.length === 0 && (
        <div className="history-state">No submitted bugs yet.</div>
      )}
      <div className="history-list">
        {reports.map((report) => (
          <article className="history-item" key={report.id}>
            <div className="history-item-top">
              <h2>{report.title}</h2>
              <span className="history-status">{report.status}</span>
            </div>
            <p>{report.description || report.error_log || 'No description provided.'}</p>
            <div className="history-meta">
              <span>{report.id}</span>
              <span>{new Date(report.created_at).toLocaleString()}</span>
              <span>{report.source_type}</span>
            </div>
          </article>
        ))}
      </div>
    </main>
  );
}

export default HistoryPage;