"""
LLM Insights Generator (Substep 3.4)
-------------------------------------
Takes the final metrics and sentiment data, sends them to the LLM,
and generates a strategic executive-level market analysis.

This powers the "Agent Insights" section at the top of the dashboard.

Input:
 - data/processed/metrics.json         (intelligence scores)
 - data/processed/sentiment_results.json (brand sentiment details)

Output:
 - data/processed/insights.json
"""

import json
from datetime import datetime
from pathlib import Path

from .llm_client import chat

# ─── Paths ────────────────────────────────────────────────────────────────────

BASE_DIR      = Path(__file__).resolve().parents[2]
PROCESSED_DIR = BASE_DIR / "data" / "processed"

METRICS_JSON   = PROCESSED_DIR / "metrics.json"
SENTIMENT_JSON = PROCESSED_DIR / "sentiment_results.json"
OUTPUT_JSON    = PROCESSED_DIR / "insights.json"


# ─── LLM Prompts ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """
You are a Senior E-Commerce Intelligence Analyst specializing in Amazon India consumer markets.
You write clear, data-driven executive summaries for brand strategy teams.
Your output must be a single valid JSON object only — no Markdown, no extra commentary.

Return this exact JSON schema:
{
  "headline": "A single punchy 10-word headline summarizing the market.",
  "market_summary": "2-3 sentences on the overall market health and the clear winner.",
  "key_anomaly": "2-3 sentences highlighting the most surprising finding in the data (e.g., high ratings but hidden complaints).",
  "strategic_recommendation": "2-3 sentences with one actionable recommendation for any brand trying to gain market share.",
  "brand_highlights": [
    {"brand": "BrandName", "insight": "One specific 1-2 sentence insight for that brand."}
  ]
}
"""

def build_insight_prompt(metrics: list[dict], sentiment: dict) -> str:
    """
    Builds a richly detailed prompt that combines score data and sentiment
    keywords into a single compact context block for the LLM.
    """
    lines = ["Here is the full competitive intelligence data for Amazon India luggage brands:\n"]

    for m in metrics:
        brand = m["brand"]
        score = m["intelligence_score"]
        confidence = m["confidence_level"]
        raw = m["metrics"]
        
        s = sentiment.get(brand, {})
        positives  = ", ".join(s.get("top_positives", []))
        complaints = ", ".join(s.get("top_complaints", []))
        sentiment_score = s.get("sentiment_score", "N/A")

        lines.append(
            f"Brand: {brand}\n"
            f"  Intelligence Score : {score}/100 (Confidence: {confidence})\n"
            f"  Avg Price          : Rs.{raw.get('avg_price', 'N/A'):.0f}\n"
            f"  Avg Star Rating    : {raw.get('avg_rating', 'N/A')}/5.0\n"
            f"  Total Reviews      : {raw.get('total_reviews', 'N/A'):,}\n"
            f"  Sentiment Score    : {sentiment_score}/1.0\n"
            f"  Top Strengths      : {positives or 'N/A'}\n"
            f"  Top Complaints     : {complaints or 'N/A'}\n"
        )

    lines.append("\nBased on this data, generate your JSON strategic analysis.")
    return "\n".join(lines)


# ─── Core Function ────────────────────────────────────────────────────────────

def run_insights_generation() -> None:
    """
    Main function that reads metrics + sentiment, calls the LLM,
    and writes the final insights JSON.
    """
    if not METRICS_JSON.exists() or not SENTIMENT_JSON.exists():
        raise FileNotFoundError(
            "Required data files are missing.\n"
            "Make sure you have run the metrics engine and sentiment analyser first."
        )

    print("[Insights] Loading metrics and sentiment data...")

    with open(METRICS_JSON,   "r", encoding="utf-8") as f:
        metrics = json.load(f)

    with open(SENTIMENT_JSON, "r", encoding="utf-8") as f:
        sentiment = json.load(f)

    prompt = build_insight_prompt(metrics, sentiment)

    print("[Insights] Requesting strategic analysis from LLM...")
    raw_response = chat(
        prompt=prompt,
        system=SYSTEM_PROMPT,
        temperature=0.3,  # Slightly higher for more creative strategic language
        max_tokens=1000,
    )

    # Strip any accidental markdown fences from the LLM
    cleaned = raw_response.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    if cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]

    try:
        insight_data = json.loads(cleaned.strip())
    except json.JSONDecodeError as e:
        print(f"[ERROR] Could not parse LLM insights JSON: {e}")
        print(f"[RAW RESPONSE]:\n{raw_response}")
        # Save a clear error placeholder so the frontend doesn't crash
        insight_data = {
            "headline": "Analysis Unavailable",
            "market_summary": "The LLM returned an unparseable response.",
            "key_anomaly": "N/A",
            "strategic_recommendation": "Please check your API key and re-run the pipeline.",
            "brand_highlights": []
        }

    # Attach metadata (when this was generated)
    insight_data["generated_at"] = datetime.now().isoformat(timespec="seconds")
    insight_data["total_brands_analyzed"] = len(metrics)

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(insight_data, f, indent=2)

    print(f"[Insights] Analysis saved to: {OUTPUT_JSON}")
    print(f"\n  Headline: {insight_data.get('headline', '')}")


# ─── CLI ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    run_insights_generation()
