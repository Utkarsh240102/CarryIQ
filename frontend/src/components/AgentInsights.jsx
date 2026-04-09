/** AgentInsights.jsx — LLM Executive Analysis Panel */
export function AgentInsights({ data }) {
  if (!data) return null;
  return (
    <div className="insights-panel section-gap">
      <div className="insights-ai-badge">
        <span>⚡</span> AI Agent Analysis
      </div>

      <h2 className="insights-headline">{data.headline}</h2>

      <div className="insights-grid">
        <div className="insights-block">
          <div className="insights-block-label">Market Summary</div>
          <div className="insights-block-text">{data.market_summary}</div>
        </div>
        <div className="insights-block">
          <div className="insights-block-label">Key Anomaly</div>
          <div className="insights-block-text">{data.key_anomaly}</div>
        </div>
        <div className="insights-block">
          <div className="insights-block-label">Strategic Recommendation</div>
          <div className="insights-block-text">{data.strategic_recommendation}</div>
        </div>
      </div>

      {data.brand_highlights?.length > 0 && (
        <div className="insights-highlights">
          {data.brand_highlights.map((h) => (
            <div key={h.brand} className="highlight-pill">
              <strong>{h.brand}</strong>{h.insight}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
