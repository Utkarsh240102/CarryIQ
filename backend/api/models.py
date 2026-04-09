"""
Pydantic Response Models (Substep 4.3)
----------------------------------------
Defines the exact shape (schema) of every JSON response our API sends back.
FastAPI uses these to:
  1. Auto-validate every response before it leaves the server.
  2. Auto-generate the /docs interactive documentation.
  3. Give the frontend a guaranteed, stable data contract.
"""

from typing import Optional
from pydantic import BaseModel


# ─── Health Check ──────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    version: str
    data_available: bool


# ─── Metrics ──────────────────────────────────────────────────────────────────

class BrandRawMetrics(BaseModel):
    """The raw numerical breakdown that feeds the weighted formula."""
    avg_price: float
    avg_rating: float
    total_reviews: int
    llm_sentiment_score: float


class BrandMetric(BaseModel):
    """The final calculated score for a single brand."""
    brand: str
    intelligence_score: float        # 0 to 100 score
    confidence_level: str            # "High", "Medium", or "Low"
    metrics: BrandRawMetrics


class MetricsResponse(BaseModel):
    """The full leaderboard response — a list of all brand scores."""
    data: list[BrandMetric]
    total_brands: int


# ─── Sentiment ────────────────────────────────────────────────────────────────

class BrandSentiment(BaseModel):
    """Sentiment analysis result for a single brand."""
    brand: str
    sentiment_score: float           # 0.0 (negative) to 1.0 (positive)
    top_positives: list[str]
    top_complaints: list[str]
    notable_quotes: list[str]


class SentimentResponse(BaseModel):
    """Full sentiment data for all brands."""
    data: list[BrandSentiment]
    total_brands: int


# ─── Insights ─────────────────────────────────────────────────────────────────

class BrandHighlight(BaseModel):
    """A single brand-specific one-liner insight."""
    brand: str
    insight: str


class InsightsResponse(BaseModel):
    """The executive AI market summary."""
    headline: str
    market_summary: str
    key_anomaly: str
    strategic_recommendation: str
    brand_highlights: list[BrandHighlight]
    generated_at: Optional[str] = None
    total_brands_analyzed: Optional[int] = None


# ─── Pipeline Trigger ─────────────────────────────────────────────────────────

class PipelineRequest(BaseModel):
    """Request body for the POST /api/run-pipeline endpoint."""
    mock: bool = False              # True = use synthetic data


class PipelineResponse(BaseModel):
    """Result of triggering the data pipeline."""
    success: bool
    message: str
    mode: str                        # "mock" or "live"
