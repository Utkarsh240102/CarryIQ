"""
Metrics Engine (Substep 3.3)
-----------------------------
Calculates the final "Competitive Intelligence Score" for each brand.
Merges numerical data (products_clean.csv) with AI data (sentiment_results.json).

Formula weights:
 - Sentiment Score : 35%
 - Avg Star Rating : 35%
 - Review Volume   : 20%
 - Price Premium   : 10% (rewards competitive pricing)

Output is stored in: data/processed/metrics.json
"""

import json
from pathlib import Path

import pandas as pd

# ─── Paths ────────────────────────────────────────────────────────────────────

BASE_DIR      = Path(__file__).resolve().parents[2]
PROCESSED_DIR = BASE_DIR / "data" / "processed"

PRODUCTS_CLEAN = PROCESSED_DIR / "products_clean.csv"
SENTIMENT_JSON = PROCESSED_DIR / "sentiment_results.json"
OUTPUT_JSON    = PROCESSED_DIR / "metrics.json"


# ─── Core Calculations ────────────────────────────────────────────────────────

def calculate_metrics() -> None:
    """
    Reads products and sentiment, merges them, calculates the final intelligence
    score, and saves the output to metrics.json.
    """
    if not PRODUCTS_CLEAN.exists() or not SENTIMENT_JSON.exists():
        raise FileNotFoundError(
            "Required input files are missing. "
            "Ensure you have run both the scraper/cleaner and the sentiment analyzer."
        )

    # 1. Load data
    products_df = pd.read_csv(PRODUCTS_CLEAN)
    
    with open(SENTIMENT_JSON, "r", encoding="utf-8") as f:
        sentiment_data = json.load(f)

    # 2. Calculate brand-level averages from the CSV
    # We group by 'brand' and calculate the mean of price/rating and sum of review counts
    metrics_df = products_df.groupby("brand").agg(
        avg_price=("price", "mean"),
        avg_mrp=("mrp", "mean"),
        avg_rating=("rating", "mean"),
        total_reviews=("review_count", "sum")
    ).reset_index()

    # Find the overall market averages (required for relational scoring)
    market_avg_price = metrics_df["avg_price"].mean()
    market_max_reviews = metrics_df["total_reviews"].max()

    results = []

    # 3. Calculate the intelligence score for each brand
    for _, row in metrics_df.iterrows():
        brand = row["brand"]
        
        # Pull sentiment from JSON (default to 0.5 if LLM failed on this brand)
        brand_sentiment = sentiment_data.get(brand, {}).get("sentiment_score", 0.5)

        avg_price = row["avg_price"]
        avg_rating = row["avg_rating"]
        total_reviews = row["total_reviews"]

        # --- Component 1: Sentiment (0 to 1 scale) ---
        # It's already 0-1 from the LLM, so we just use it directly.
        comp_sentiment = brand_sentiment
        
        # --- Component 2: Rating (scaled 0 to 1) ---
        # 5 stars = 1.0, 1 star = 0.2
        comp_rating = avg_rating / 5.0
        
        # --- Component 3: Review Volume (scaled 0 to 1) ---
        # Relative to the most popular brand in our dataset
        comp_volume = total_reviews / market_max_reviews if market_max_reviews > 0 else 0
        
        # --- Component 4: Price Premium (scaled 0 to 1) ---
        # Cheaper than market avg = higher score (value). Expensive = lower score.
        # Ratio = Market Avg / Brand Price
        price_ratio = market_avg_price / avg_price if avg_price > 0 else 1.0
        # Cap at 1.5 to prevent extreme budget brands from breaking the math
        comp_price = min(price_ratio, 1.5) / 1.5

        # 4. Apply Weights
        w_sentiment = 0.35
        w_rating = 0.35
        w_volume= 0.20
        w_price = 0.10

        final_score = (
            (comp_sentiment * w_sentiment) +
            (comp_rating * w_rating) +
            (comp_volume * w_volume) +
            (comp_price * w_price)
        )
        
        # Convert to 100-point scale
        final_score_100 = round(final_score * 100, 1)

        # 5. Determine "Confidence Badge" based on review volume
        # Helps users know if the score is trustworthy
        if total_reviews >= 5000:
            confidence = "High"
        elif total_reviews >= 1000:
            confidence = "Medium"
        else:
            confidence = "Low"

        # Build output record
        results.append({
            "brand": brand,
            "intelligence_score": final_score_100,
            "confidence_level": confidence,
            "metrics": {
                "avg_price": round(avg_price, 0),
                "avg_rating": round(avg_rating, 2),
                "total_reviews": int(total_reviews),
                "llm_sentiment_score": round(brand_sentiment, 2)
            }
        })

    # Sort results by highest intelligence score first
    results.sort(key=lambda x: x["intelligence_score"], reverse=True)

    # 6. Save final JSON
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"\n[Metrics] Successfully calculated Intelligence Scores for {len(results)} brands.")
    print(f"[Metrics] Saved to: {OUTPUT_JSON}")
    
    # Print a quick leaderboard
    print("\n   --- Leaderboard ---")
    for i, r in enumerate(results):
        print(f"   {i+1}. {r['brand']:<20} | Score: {r['intelligence_score']}/100")


# ─── CLI ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    calculate_metrics()
