/**
 * SentimentCards.jsx
 * Visualizes the raw qualitative AI data (pros, cons, quotes) from the LLM.
 */

export function SentimentCards({ sentimentData }) {
  if (!sentimentData || sentimentData.length === 0) return null;

  // Helper to determine the mood of the card from the sentiment score
  const getCardMood = (score) => {
    if (score >= 0.7) return 'positive';
    if (score <= 0.4) return 'negative';
    return 'neutral';
  };

  return (
    <div className="section-gap">
      <div className="section-header">
        <div className="section-label">Qualitative Data</div>
        <h2 className="section-title">Brand Sentiment Profiles</h2>
        <p className="section-desc">Extracted automatically from customer reviews via LLM.</p>
      </div>

      <div className="sentiment-grid">
        {sentimentData.map((item) => {
          const mood = getCardMood(item.sentiment_score);
          
          return (
            <div key={item.brand} className={`sentiment-card ${mood}`}>
              
              {/* Card Header: Brand + Score Ring */}
              <div className="sentiment-card-header">
                <div className="sentiment-brand-name">{item.brand}</div>
                <div className="sentiment-score-ring">
                  {/* SVG Circle for visual flair */}
                  <svg viewBox="0 0 36 36" style={{ width: '100%', height: '100%' }}>
                    <path
                      d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                      fill="none"
                      stroke="rgba(255,255,255,0.05)"
                      strokeWidth="4"
                    />
                    <path
                      d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                      fill="none"
                      stroke={mood === 'positive' ? '#10b981' : mood === 'negative' ? '#ef4444' : '#06b6d4'}
                      strokeWidth="4"
                      strokeDasharray={`${item.sentiment_score * 100}, 100`}
                    />
                  </svg>
                  <div className="sentiment-score-text">
                    {Math.round(item.sentiment_score * 100)}
                  </div>
                </div>
              </div>

              {/* Positives List (Green Pills) */}
              {item.top_positives?.length > 0 && (
                <div className="tags-section">
                  <div className="tags-label positive">Top Strengths</div>
                  <div className="tags-wrap">
                    {item.top_positives.map((kw, i) => (
                      <span key={i} className="tag positive">{kw}</span>
                    ))}
                  </div>
                </div>
              )}

              {/* Complaints List (Red Pills) */}
              {item.top_complaints?.length > 0 && (
                <div className="tags-section">
                  <div className="tags-label negative">Main Complaints</div>
                  <div className="tags-wrap">
                    {item.top_complaints.map((kw, i) => (
                      <span key={i} className="tag negative">{kw}</span>
                    ))}
                  </div>
                </div>
              )}

              {/* Notable Quote (Italicized text block) */}
              {item.notable_quotes?.length > 0 && (
                <div style={{ marginTop: '20px' }}>
                  <div className="tags-label">Notable Quote</div>
                  <div className="notable-quote">
                    "{item.notable_quotes[0]}"
                  </div>
                </div>
              )}

            </div>
          );
        })}
      </div>
    </div>
  );
}
