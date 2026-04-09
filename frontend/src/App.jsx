import { useEffect, useState } from 'react';
import { AgentInsights } from './components/AgentInsights';
import { MetricsCharts } from './components/MetricsCharts';
import { SentimentCards } from './components/SentimentCards';
import { api } from './services/api';

export default function App() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [metrics, setMetrics] = useState(null);
  const [insights, setInsights] = useState(null);
  const [sentiment, setSentiment] = useState(null);

  // Global Pipeline Status State
  const [isScraping, setIsScraping] = useState(false);
  const [pipelineMsg, setPipelineMsg] = useState("");

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Check if data is available first
      const health = await api.health();
      if (!health.data_available) {
        setError('Data files not found. Please click "Run Data Pipeline" to generate data first.');
        setLoading(false);
        return;
      }

      // Fetch all three endpoints simultaneously
      const [mRes, iRes, sRes] = await Promise.all([
        api.metrics(),
        api.insights(),
        api.sentiment(),
      ]);

      setMetrics(mRes);
      setInsights(iRes);
      setSentiment(sRes);
      
    } catch (err) {
      console.error(err);
      setError(err.message || 'Failed to load dashboard data. Ensure the FastAPI backend is running on port 8000.');
    } finally {
      setLoading(false);
    }
  };

  const handleRunPipeline = async (mock = false) => {
    setIsScraping(true);
    setPipelineMsg(`Starting ${mock ? 'Mock' : 'Live Playwright'} Data Collection Pipeline...`);
    try {
      const res = await api.runPipeline(mock);
      setPipelineMsg(res.message);
      
      // We start polling to see when the backend finishes the pipeline
      const poll = setInterval(async () => {
        try {
          const h = await api.health();
          // We wait until the pipeline is NO LONGER running, and data is available
          if (h.data_available && !h.is_pipeline_running) {
            clearInterval(poll);
            setPipelineMsg("Pipeline complete! Reloading dashboard...");
            await fetchData();
            setIsScraping(false);
          }
        } catch {
          // Ignore polling errors while server is restarting/processing
        }
      }, 5000);

    } catch (err) {
      setPipelineMsg('');
      setError(`Pipeline initiation failed: ${err.message}`);
      setIsScraping(false);
    }
  };


  // ─── Render: Loading State ──────────────────────────────────────────────────
  if (loading) {
    return (
      <div className="fullscreen-center">
        <div className="loader-logo">CarryIQ</div>
        <div className="loader-spinner"></div>
        <div className="loader-text">Loading Intelligence Data...</div>
      </div>
    );
  }

  // ─── Render: Main Dashboard ────────────────────────────────────────────────
  return (
    <div className="app-bg">
      <div className="dashboard-container">
        
        {/* Navbar */}
        <nav className="navbar">
          <div className="navbar-brand">
            <div className="navbar-logo">👜</div>
            <div>
              <h1 className="navbar-title">CarryIQ</h1>
              <div className="navbar-subtitle">Amazon India Competitor Intelligence</div>
            </div>
          </div>
          <div className="navbar-actions">
            <div className="navbar-badge">
              <div className="navbar-badge-dot"></div>
              Live API Connection
            </div>
          </div>
        </nav>

        {/* Pipeline Controls Row */}
        <div className="pipeline-bar">
          <div className="pipeline-status">
            <span style={{ fontSize: '18px' }}>⚙️</span>
            <div className="pipeline-status-text">
              Status: <strong>{isScraping ? pipelineMsg : "Idle"}</strong>
            </div>
          </div>
          <div style={{ display: 'flex', gap: '12px' }}>
            <button 
              className="btn btn-ghost" 
              onClick={() => handleRunPipeline(true)}
              disabled={isScraping}
            >
              Generate Mock Data
            </button>
            <button 
              className="btn btn-primary" 
              onClick={() => handleRunPipeline(false)}
              disabled={isScraping}
            >
              Run Live Playwright Scrape
            </button>
          </div>
        </div>

        {/* Global Error Banner */}
        {error && (
          <div className="error-card" style={{ maxWidth: '100%', marginBottom: '40px' }}>
            <div className="error-icon">⚠️</div>
            <div className="error-title">System Error</div>
            <div className="error-desc">{error}</div>
          </div>
        )}

        {/* Rest of the dashboard only renders if we have data */}
        {metrics && insights && !error && (
          <>
            {/* 1. Market Headers */}
            <div className="stat-cards-row">
              <div className="stat-card">
                <div className="stat-label">Brands Tracked</div>
                <div className="stat-value">{metrics.total_brands}</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Market Leader</div>
                <div className="stat-value">{metrics.data[0].brand}</div>
                <div className="stat-sub">Score: {metrics.data[0].intelligence_score}/100</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Price Range Avg</div>
                <div className="stat-value">
                  ₹{Math.round(metrics.data.reduce((acc, m) => acc + m.metrics.avg_price, 0) / metrics.total_brands)}
                </div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Total Reviews Verified</div>
                <div className="stat-value">
                  {metrics.data.reduce((acc, m) => acc + m.metrics.total_reviews, 0).toLocaleString()}
                </div>
              </div>
            </div>

            {/* 2. Executive Agent Panel */}
            <AgentInsights data={insights} />

            {/* 3. Recharts Visualizations */}
            <div className="section-gap">
              <div className="section-header">
                <div className="section-label">Quantitative Data</div>
                <h2 className="section-title">Performance Metrics</h2>
                <p className="section-desc">Analysis of pricing, star ratings, and review volume against AI sentiment.</p>
              </div>
              <MetricsCharts metrics={metrics.data} />
            </div>

            {/* 4. Leaderboard Table */}
            <div className="section-gap">
              <table className="leaderboard">
                <thead>
                  <tr>
                    <th style={{ width: '60px', textAlign: 'center' }}>Rank</th>
                    <th>Brand Name</th>
                    <th>Intelligence Score (0-100)</th>
                    <th>Amazon Avg Rating</th>
                    <th>Avg Market Price</th>
                    <th>Confidence</th>
                  </tr>
                </thead>
                <tbody>
                  {metrics.data.map((m, idx) => (
                    <tr key={m.brand} className="leaderboard-row">
                      <td style={{ textAlign: 'center' }}>
                        <div className={`rank-badge ${idx < 3 ? `rank-${idx+1}` : 'rank-n'}`}>
                          {idx + 1}
                        </div>
                      </td>
                      <td className="brand-name-cell">{m.brand}</td>
                      <td>
                        <div className="score-bar-wrap">
                          <div className="score-value">{m.intelligence_score}</div>
                          <div className="score-bar-bg">
                            <div className="score-bar-fill" style={{ width: `${m.intelligence_score}%` }}></div>
                          </div>
                        </div>
                      </td>
                      <td className="mono">⭐ {m.metrics.avg_rating.toFixed(2)}</td>
                      <td className="mono">₹{m.metrics.avg_price.toLocaleString()}</td>
                      <td>
                        <div className={`confidence-badge conf-${m.confidence_level.toLowerCase()}`}>
                          {m.confidence_level}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* 5. Qualitative Sentiment Cards */}
            {sentiment && <SentimentCards sentimentData={sentiment.data} />}
          </>
        )}
      </div>
    </div>
  );
}
