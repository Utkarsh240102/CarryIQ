import {
  CartesianGrid,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
  ZAxis,
  Cell
} from 'recharts';

/**
 * Custom Tooltip component for Recharts
 * Ensures the popup matches our dark glassmorphism theme perfectly.
 */
const CustomTooltip = ({ active, payload }) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div style={{
        background: 'rgba(10, 22, 40, 0.9)',
        border: '1px solid rgba(59, 130, 246, 0.3)',
        borderRadius: '8px',
        padding: '12px 16px',
        boxShadow: '0 10px 25px rgba(0,0,0,0.5)',
        backdropFilter: 'blur(10px)'
      }}>
        <div style={{ fontWeight: 700, fontSize: '15px', color: '#fff', marginBottom: '6px' }}>
          {data.brand}
        </div>
        <div style={{ fontSize: '13px', color: '#94a3b8' }}>
          ⭐ Rating: <strong style={{ color: '#f1f5f9' }}>{data.rating}</strong>/5.0
        </div>
        <div style={{ fontSize: '13px', color: '#94a3b8' }}>
          💖 Sentiment: <strong style={{ color: '#f1f5f9' }}>{data.sentiment}</strong>/1.0
        </div>
      </div>
    );
  }
  return null;
};


/** 
 * MetricsCharts.jsx
 * Visualizes the difference between Star Ratings (X-axis) and LLM Sentiment (Y-axis). 
 */
export function MetricsCharts({ metrics }) {
  if (!metrics || metrics.length === 0) return null;

  // Transform backend leaderboard metrics into the flat shape Recharts needs
  const scatterData = metrics.map((m) => ({
    brand: m.brand,
    rating: m.metrics.avg_rating,
    sentiment: m.metrics.llm_sentiment_score,
    // Provide a random color for each brand dot based on its name length
    fill: m.brand.length % 2 === 0 ? '#3b82f6' : '#8b5cf6'
  }));

  return (
    <div className="charts-grid">
      
      {/* Chart Card */}
      <div className="chart-card" style={{ gridColumn: '1 / -1' }}>
        <h3 className="chart-title">Rating vs. True Sentiment Anomaly Plot</h3>
        <p className="chart-subtitle">
          Watch out for brands in the bottom-right: High star ratings but poor customer sentiment in the text.
        </p>

        <div style={{ width: '100%', height: 350 }}>
          <ResponsiveContainer>
            <ScatterChart margin={{ top: 20, right: 30, bottom: 20, left: 0 }}>
              
              <CartesianGrid 
                strokeDasharray="3 3" 
                stroke="rgba(255,255,255,0.05)" 
                vertical={false} 
              />
              
              <XAxis 
                type="number" 
                dataKey="rating" 
                name="Star Rating"
                domain={[3.0, 5.0]} 
                tick={{ fill: '#64748b', fontSize: 12 }}
                axisLine={{ stroke: 'rgba(255,255,255,0.1)' }}
                label={{ value: 'Amazon Star Rating (X)', position: 'insideBottom', offset: -10, fill: '#64748b', fontSize: 12 }}
              />
              
              <YAxis 
                type="number" 
                dataKey="sentiment" 
                name="Sentiment Score"
                domain={[0, 1.0]} 
                tick={{ fill: '#64748b', fontSize: 12 }}
                axisLine={{ stroke: 'rgba(255,255,255,0.1)' }}
                label={{ value: 'LLM Sentiment Score (Y)', angle: -90, position: 'insideLeft', fill: '#64748b', fontSize: 12 }}
              />
              
              {/* Z-Axis determines dot size. We use a static array here so they are all the same size */}
              <ZAxis type="category" dataKey="brand" range={[200, 200]} />
              
              <Tooltip 
                cursor={{ strokeDasharray: '3 3', stroke: 'rgba(255,255,255,0.1)' }} 
                content={<CustomTooltip />} 
              />
              
              <Scatter data={scatterData}>
                {scatterData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.fill} />
                ))}
              </Scatter>
              
            </ScatterChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
