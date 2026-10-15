import { useState, useEffect } from 'react';
import {
  PieChart, Pie, Cell,
  BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer,
  LineChart, Line
} from 'recharts';
import '../styles/AnalyticsPage.css';

const COLORS = {
  Critical: '#ef4444',
  High: '#f97316',
  Medium: '#eab308',
  Low: '#22c55e',
  Unknown: '#6b7280'
};

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://127.0.0.1:8000';

function AnalyticsPage() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Filters
  const [component, setComponent] = useState('');
  const [severity, setSeverity] = useState('');

  const fetchAnalytics = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (component) params.append('component', component);
      if (severity) params.append('severity', severity);

      const response = await fetch(`${API_BASE_URL}/api/analytics/defects?${params.toString()}`);
      if (!response.ok) throw new Error('Failed to fetch analytics');
      const result = await response.json();
      setData(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleApplyFilters = (e) => {
    e.preventDefault();
    fetchAnalytics();
  };

  if (loading && !data) return <div className="analytics-loading">Loading analytics...</div>;
  if (error) return <div className="analytics-error">{error}</div>;
  if (!data) return null;

  // Formatting for Recharts
  const pieData = Object.entries(data.severity_distribution || {}).map(([name, value]) => ({ name, value }));
  const componentData = Object.entries(data.component_distribution || {}).map(([name, count]) => ({ name, count }));
  const exceptionData = Object.entries(data.exception_type_distribution || {}).map(([name, count]) => ({ name, count }));
  const timeData = data.bug_frequency_over_time || [];

  return (
    <div className="analytics-page">
      <header className="analytics-header">
        <h1>Defect Pattern Analytics</h1>
        <p>Insights from submitted bugs and historical knowledge base</p>
      </header>

      <form className="analytics-filters" onSubmit={handleApplyFilters}>
        <input 
          type="text" 
          placeholder="Filter by Component" 
          value={component} 
          onChange={e => setComponent(e.target.value)} 
        />
        <select value={severity} onChange={e => setSeverity(e.target.value)}>
          <option value="">All Severities</option>
          <option value="Critical">Critical</option>
          <option value="High">High</option>
          <option value="Medium">Medium</option>
          <option value="Low">Low</option>
        </select>
        <button type="submit">Apply Filters</button>
      </form>

      <div className="analytics-stats-grid">
        <div className="stat-card">
          <h3>Total Bugs</h3>
          <p>{data.total_bugs}</p>
        </div>
        <div className="stat-card">
          <h3>Knowledge Base Size</h3>
          <p>{data.knowledge_base_size} Chunks</p>
        </div>
        <div className="stat-card">
          <h3>Duplicate Rate</h3>
          <p>{data.duplicate_rate.toFixed(1)}%</p>
        </div>
        <div className="stat-card">
          <h3>Remediation Supported</h3>
          <p>{data.remediation_supported_rate.toFixed(1)}%</p>
        </div>
      </div>

      <div className="analytics-charts-grid">
        <div className="chart-box">
          <h3>Severity Distribution</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie data={pieData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} label>
                {pieData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[entry.name] || COLORS.Unknown} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="chart-box">
          <h3>Bug Frequency Over Time</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={timeData}>
              <XAxis dataKey="date" stroke="#888" />
              <YAxis stroke="#888" />
              <Tooltip wrapperStyle={{ backgroundColor: '#2d333b', color: '#fff' }} />
              <Line type="monotone" dataKey="count" stroke="#60a5fa" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="chart-box">
          <h3>Top Affected Components</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={componentData} layout="vertical" margin={{ left: 50 }}>
              <XAxis type="number" stroke="#888" />
              <YAxis type="category" dataKey="name" stroke="#888" width={100} />
              <Tooltip cursor={{fill: 'rgba(255,255,255,0.1)'}} />
              <Bar dataKey="count" fill="#8b5cf6" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="chart-box">
          <h3>Exception Types</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={exceptionData} margin={{ bottom: 20 }}>
              <XAxis dataKey="name" stroke="#888" tick={{ fontSize: 12 }} angle={-45} textAnchor="end" />
              <YAxis stroke="#888" />
              <Tooltip cursor={{fill: 'rgba(255,255,255,0.1)'}} />
              <Bar dataKey="count" fill="#10b981" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
      
      <div className="chart-box full-width">
        <h3>Common Root Causes</h3>
        {Object.keys(data.root_cause_distribution || {}).length > 0 ? (
          <ul className="root-cause-list">
            {Object.entries(data.root_cause_distribution)
              .sort((a, b) => b[1] - a[1])
              .map(([cause, count], i) => (
                <li key={i}>
                  <span className="cause-text">{cause}</span>
                  <span className="cause-count">{count} {count === 1 ? 'time' : 'times'}</span>
                </li>
            ))}
          </ul>
        ) : (
          <p className="no-data-msg">No root cause themes available.</p>
        )}
      </div>

    </div>
  );
}

export default AnalyticsPage;
