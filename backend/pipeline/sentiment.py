"""
LLM Sentiment Analyser (Substep 3.2)
-------------------------------------
Reads clean reviews, groups them by brand, and sends them to the LLM.
Forces the LLM to return structured JSON containing:
 - sentiment_score (0.0 to 1.0)
 - top_positives (list of strings)
 - top_complaints (list of strings)
 - notable_quotes (list of strings)

Output is stored in: data/processed/sentiment_results.json
"""

import json
from pathlib import Path

import pandas as pd

from .llm_client import chat

# ─── Paths ────────────────────────────────────────────────────────────────────

BASE_DIR      = Path(__file__).resolve().parents[2]
PROCESSED_DIR = BASE_DIR / "data" / "processed"
REVIEWS_CLEAN = PROCESSED_DIR / "reviews_clean.csv"
OUTPUT_JSON   = PROCESSED_DIR / "sentiment_results.json"


# ─── LLM prompts ──────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """
You are an expert e-commerce data analyst analyzing customer reviews for luggage brands.
You must return your analysis strictly as a valid, pure JSON object.
Do NOT wrap the JSON in Markdown code blocks (like ```json). Just return the raw JSON braces.

The JSON must exactly follow this schema:
{
  "brand": "BrandName",
  "sentiment_score": 0.85,  // Float between 0.0 (entirely negative) and 1.0 (entirely positive)
  "top_positives": ["keyword1", "keyword2", "keyword3"], // Max 3 concise phrases
  "top_complaints": ["keyword1", "keyword2", "keyword3"], // Max 3 concise phrases
  "notable_quotes": [
    "A direct, impactful quote from the reviews showing positive sentiment.",
    "A direct, impactful quote from the reviews showing negative sentiment."
  ]
}
"""

def build_user_prompt(brand: str, reviews: list[str]) -> str:
    """Combines the brand name and list of reviews into a single text block."""
    numbered_reviews = "\n".join(f"{i+1}. {r}" for i, r in enumerate(reviews))
    return f"Brand: {brand}\n\nHere are the latest customer reviews:\n\n{numbered_reviews}\n\nAnalyze these reviews and output the JSON."


# ─── Core logic ───────────────────────────────────────────────────────────────

def analyze_brand(brand: str, reviews: list[str]) -> dict:
    """
    Send a block of reviews to the LLM and safely parse the JSON response.
    Limits input to ~30 reviews to avoid context limit overflow and save cost.
    """
    # Truncate to maximum 30 reviews to keep the prompt size reasonable
    sample_reviews = reviews[:30]
    
    prompt = build_user_prompt(brand, sample_reviews)
    
    print(f"  [Sentiment] Analyzing '{brand}' ({len(sample_reviews)} reviews)...")
    
    raw_response = chat(
        prompt=prompt,
        system=SYSTEM_PROMPT,
        temperature=0.1,  # Low temperature = highly deterministic, JSON-friendly output
        max_tokens=600
    )

    # Sometimes LLMs ignore the system prompt and add Markdown anyway.
    # We strip ```json and ``` from the start and end just in case.
    cleaned_response = raw_response.strip()
    if cleaned_response.startswith("```json"):
        cleaned_response = cleaned_response[7:]
    if cleaned_response.startswith("```"):
        cleaned_response = cleaned_response[3:]
    if cleaned_response.endswith("```"):
        cleaned_response = cleaned_response[:-3]
    
    try:
        data = json.loads(cleaned_response.strip())
        return data
    except json.JSONDecodeError as e:
        print(f"  [ERROR] Failed to parse LLM JSON for {brand}: {e}")
        print(f"  [RAW STRING WAS]:\n{raw_response}")
        # Return a safe fallback rather than crashing the whole pipeline
        return {
            "brand": brand,
            "sentiment_score": 0.5,
            "top_positives": ["Data unparseable"],
            "top_complaints": ["Data unparseable"],
            "notable_quotes": []
        }


def run_sentiment_analysis() -> None:
    """
    Main orchestration function.
    Reads clean reviews, groups by brand, runs LLM analysis, and saves to JSON.
    """
    if not REVIEWS_CLEAN.exists():
        raise FileNotFoundError(f"Clean reviews not found at: {REVIEWS_CLEAN}")

    df = pd.read_csv(REVIEWS_CLEAN)
    
    # We only care about the brand and the text body
    if "brand" not in df.columns or "review_body" not in df.columns:
        raise ValueError("reviews_clean.csv is missing required columns.")

    results = {}

    for brand in df["brand"].dropna().unique():
        # Get all reviews for this brand, drop empty ones, convert to a standard string list
        brand_reviews = df[df["brand"] == brand]["review_body"].dropna().tolist()
        
        if not brand_reviews:
            print(f"  [Sentiment] Skipping '{brand}' (No valid reviews).")
            continue
            
        analysis_data = analyze_brand(brand, brand_reviews)
        results[brand] = analysis_data

    # Save final results map to JSON
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
        
    print(f"\n[Sentiment] Analysis complete! Results saved to: {OUTPUT_JSON}")


# ─── CLI ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Starting LLM Sentiment Analysis...")
    run_sentiment_analysis()
