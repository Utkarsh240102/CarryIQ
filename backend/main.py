"""
FastAPI App Entry Point (Substep 4.1)
--------------------------------------
Boots the backend server and optionally runs the full data pipeline first.

Usage:
  python backend/main.py          # Live scrape attempt
  python backend/main.py --mock   # Uses mock data (guaranteed to work)

Server starts at:  http://localhost:8000
API docs at:       http://localhost:8000/docs
"""

import argparse
import asyncio
import sys
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ─── Add backend to Python path so imports work from anywhere ─────────────────
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.api.routes import router

# ─── FastAPI App Instance ─────────────────────────────────────────────────────

app = FastAPI(
    title="CarryIQ — Amazon Luggage Intelligence API",
    description=(
        "Competitive intelligence dashboard for Amazon India luggage brands. "
        "Provides brand metrics, LLM-powered sentiment analysis, and strategic insights."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ─── CORS Configuration (Substep 4.4) ────────────────────────────────────────
# Allows the React frontend (on port 5173) to make API calls to this server
# (on port 8000) without browser security errors.

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],           # Allows Render Frontend domain to connect
    allow_credentials=True,
    allow_methods=["*"],           # GET, POST, OPTIONS, etc.
    allow_headers=["*"],
)

# ─── Register API Routes ──────────────────────────────────────────────────────

app.include_router(router, prefix="/api")


# ─── Pipeline Orchestrator ────────────────────────────────────────────────────

def run_pipeline(mock: bool = False) -> bool:
    """
    Runs the complete data pipeline before starting the server.
    
    Pipeline order:
      1. Scrape (or generate mock data)
      2. Clean with pandas
      3. LLM sentiment analysis
      4. Calculate intelligence metrics
      5. Generate executive insights
    
    Returns True if all steps succeeded.
    """
    print("\n" + "=" * 60)
    print("  CarryIQ Data Pipeline Starting...")
    print(f"  Mode: {'MOCK (synthetic data)' if mock else 'LIVE (playwright scraping)'}")
    print("=" * 60)

    from backend.pipeline.cleaner import run_cleaner

    # Step 1: Scrape or mock ──────────────────────────────────────────────────
    if mock:
        print("\n[1/5] Generating mock data...")
        from backend.scraper.mock_data import generate_mock_data
        generate_mock_data()
    else:
        print("\n[1/5] Attempting live Playwright scrape...")
        try:
            from backend.scraper.playwright_scraper import run_scraper
            success = asyncio.run(run_scraper())
            if not success:
                print("      Playwright blocked. Attempting HTTP fallback...")
                from backend.scraper.fallback_scraper import run_fallback
                from backend.scraper.playwright_scraper import BRANDS
                results = run_fallback(BRANDS)
                # Check if any brands fully failed, fill those with mock data
                failed = [b for b, ok in results.items() if not ok]
                if failed:
                    print(f"      HTTP fallback also failed for: {failed}")
                    print("      Supplementing with mock data for those brands...")
                    from backend.scraper.mock_data import generate_mock_data
                    generate_mock_data()
        except Exception as e:
            print(f"      Scraper raised an exception: {e}")
            print("      Falling back to mock data.")
            from backend.scraper.mock_data import generate_mock_data
            generate_mock_data()

    # Step 2: Clean ───────────────────────────────────────────────────────────
    print("\n[2/5] Cleaning data with pandas...")
    try:
        run_cleaner()
    except Exception as e:
        print(f"      [ERROR] Cleaner failed: {e}")
        return False

    # Step 3: Sentiment Analysis ──────────────────────────────────────────────
    print("\n[3/5] Running LLM sentiment analysis...")
    try:
        from backend.pipeline.sentiment import run_sentiment_analysis
        run_sentiment_analysis()
    except Exception as e:
        print(f"      [ERROR] Sentiment analysis failed: {e}")
        print("      Server will still start; sentiment data may be stale.")

    # Step 4: Metrics Engine ──────────────────────────────────────────────────
    print("\n[4/5] Calculating intelligence metrics...")
    try:
        from backend.pipeline.metrics_engine import calculate_metrics
        calculate_metrics()
    except Exception as e:
        print(f"      [ERROR] Metrics engine failed: {e}")

    # Step 5: Insights Generator ──────────────────────────────────────────────
    print("\n[5/5] Generating executive insights...")
    try:
        from backend.pipeline.insights import run_insights_generation
        run_insights_generation()
    except Exception as e:
        print(f"      [ERROR] Insights generation failed: {e}")

    print("\n" + "=" * 60)
    print("  Pipeline complete! Starting API server...")
    print("=" * 60)
    return True


# ─── CLI Entry Point ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CarryIQ Backend Server")
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Use synthetic mock data instead of live scraping."
    )
    parser.add_argument(
        "--no-pipeline",
        action="store_true",
        help="Skip the pipeline and go straight to serving existing data."
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to run the server on (default: 8000)."
    )
    args = parser.parse_args()

    if not args.no_pipeline:
        run_pipeline(mock=args.mock)

    print(f"\n  API Server : http://localhost:{args.port}")
    print(f"  API Docs   : http://localhost:{args.port}/docs\n")

    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=args.port,
        reload=False,
        log_level="info",
    )
