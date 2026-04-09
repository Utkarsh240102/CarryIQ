# Detailed Implementation Plan: Moonshot Intelligence Dashboard
**Project:** Amazon India Luggage Competitive Intelligence Dashboard
**Stack:** Python · FastAPI · Playwright · Pandas · OpenRouter (`gpt-4o-mini`) / Groq · React (Vite) · Recharts · TailwindCSS
**Brands:** Safari, Skybags, American Tourister, VIP, Aristocrat, Nasher Miles (6 brands)

---

## Evaluation Rubric Mapping

| Rubric Criteria | How It Is Addressed |
|---|---|
| Data collection quality (20pts) | Playwright scraper + Mock Mode + Pandas cleaned CSVs |
| Analytical depth (20pts) | Aspect-level sentiment, confidence scoring, LLM synthesis |
| Dashboard UX/UI (20pts) | React + TailwindCSS + Recharts, animations, filters, drilldowns |
| Competitive intelligence (15pts) | Side-by-side brand benchmarking, PriceRatingScatter, win/loss analysis |
| Technical execution (15pts) | FastAPI backend, modular codebase, documented architecture |
| Product thinking (10pts) | Agent Insights layer, Strategic Recommendations, Decision Layer |
| Bonus Points | Aspect-level sentiment, anomaly detection, value-for-money, review trust signals |

---

## Step 1: Project & Environment Setup

### Substep 1.1 — Repository & Directory Structure
- Create the following exact directory tree in `d:\PROJECTS\CarryIQ`:
```
CarryIQ/
├── backend/
│   ├── scraper/
│   │   ├── playwright_scraper.py
│   │   ├── mock_data.py
│   │   └── fallback_scraper.py
│   ├── pipeline/
│   │   ├── cleaner.py
│   │   ├── llm_analyzer.py
│   │   ├── metrics_engine.py
│   │   └── insights.py
│   ├── api/
│   │   └── routes.py
│   ├── main.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── DashboardOverview.jsx
│   │   │   ├── BrandComparison.jsx
│   │   │   ├── ProductDrilldown.jsx
│   │   │   ├── PriceRatingScatter.jsx
│   │   │   ├── AgentInsights.jsx
│   │   │   ├── StrategicRecommendations.jsx
│   │   │   └── Sidebar.jsx
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── index.html
│   └── package.json
├── data/
│   ├── raw/
│   │   ├── products_raw.csv
│   │   └── reviews_raw.csv
│   └── processed/
│       ├── brand_metrics.csv
│       ├── products_clean.csv
│       ├── reviews_clean.csv
│       └── brand_analysis.json
├── .env
├── README.md
└── implementation_plan.md
```

### Substep 1.2 — Backend Python Environment
- Confirm Python 3.11+ is installed.
- Create a virtual environment: `python -m venv venv`
- Activate: `venv\Scripts\activate`
- Install dependencies via `requirements.txt`:
  ```
  fastapi==0.111.0
  uvicorn[standard]==0.29.0
  playwright==1.44.0
  pandas==2.2.2
  openai==1.30.0        # Works with OpenRouter & Groq APIs
  python-dotenv==1.0.1
  httpx==0.27.0
  pydantic==2.7.1
  beautifulsoup4==4.12.3
  lxml==5.2.2
  ```
- Install Playwright browsers: `playwright install chromium`

### Substep 1.3 — Frontend React/Vite Initialization
- Run: `npx create-vite@latest frontend --template react`
- `cd frontend && npm install`
- Install UI/charting/styling dependencies:
  ```
  npm install recharts axios react-router-dom
  npm install lucide-react clsx
  npm install -D tailwindcss postcss autoprefixer
  npx tailwindcss init -p
  ```

### Substep 1.4 — Environment Variables (`.env`)
- Create `.env` in the root directory:
  ```
  # Choose one provider:
  OPENROUTER_API_KEY=your_openrouter_key_here
  GROQ_API_KEY=your_groq_key_here

  # Active provider flag
  LLM_PROVIDER=openrouter   # or: groq

  # Model name
  LLM_MODEL=openai/gpt-4o-mini   # or: llama-3.1-70b-versatile (for Groq)

  BACKEND_PORT=8000
  ```

### Substep 1.5 — Create `.gitignore` File
- Create a `.gitignore` at the root of the project to ensure we never accidentally commit sensitive files (API keys, virtual envs, raw data, node_modules) to GitHub.
- Covers: Python venv, `.env`, `__pycache__`, IDE folders, Node modules, build outputs, raw scraped data CSVs.
- Git commands:
  ```bash
  git init                     # Initialize the repo (if not already done)
  git add .gitignore           # Stage only the .gitignore first
  git commit -m "chore: add .gitignore"
  ```

---

## Step 2: Scraper & Cleaner Pipeline

### Substep 2.1 — Playwright Primary Scraper (`playwright_scraper.py`)
- Use `async playwright` to launch Chromium in headless mode.
- Set realistic browser headers:
  - `User-Agent`: Modern Chrome on Windows
  - `Accept-Language: en-IN,en;q=0.9`
  - `Viewport`: 1920x1080
- Add random delays between requests: `asyncio.sleep(random.uniform(3, 7))`
- **Per brand workflow:**
  1. Navigate to Amazon India search: `amazon.in/s?k={brand}+luggage`
  2. Collect up to 15 product URLs per brand (paginate if needed).
  3. For each product URL:
     - Extract: `title`, `price`, `MRP/list_price`, `discount_pct`, `star_rating`, `review_count`, `category`, `ASIN`.
     - Navigate to bottom review section and collect minimum 50 reviews total.
     - For each review: `reviewer_name`, `date`, `rating`, `title`, `body`, `verified_purchase`.
  4. Checkpoint save after every product using `append mode CSV` to avoid data loss.
- **CAPTCHA Detection:** If `'captcha' in page.url` → log warning and trigger Layer 2.
- Output: `data/raw/products_raw.csv` and `data/raw/reviews_raw.csv`

### Substep 2.2 — Mock Data Mode (`mock_data.py`) — CRITICAL FOR EVALUATION
- This is the most important fallback. It must work perfectly for a live demo.
- Generate realistic synthetic data for all 6 brands mimicking Amazon India's exact fields.
- Use realistic price ranges (₹2,000–₹15,000), realistic discount percentages (10%–50%).
- Generate at least 80+ reviews per brand with:
  - Mixed ratings (1–5 stars, weighted toward 4–5 for good brands).
  - Realistic review text touching on aspects: wheels, handle, material, zipper, size, durability.
  - Intentional anomalies: e.g., Skybags has 4.2 avg rating but 60% of negative reviews mention zipper failures.
- Invoked via CLI flag: `python backend/main.py --mock`

### Substep 2.3 — Fallback Scraper Layer (`fallback_scraper.py`)
- A simple stub that replaces Playwright network calls with a standard `httpx` GET to a public proxy/scraper endpoint (ScraperAPI or similar).
- Auto-triggered when the Playwright scraper detects a CAPTCHA loop.

### Substep 2.4 — Pandas Cleaner (`cleaner.py`)
- Load `products_raw.csv` and `reviews_raw.csv`.
- Products cleaning:
  - Strip `₹` and commas from price columns, cast to `float`.
  - Fill missing `discount_pct` by computing `((MRP - Price) / MRP) * 100`.
  - Normalize brand names to a canonical list.
  - Remove obvious duplicates by ASIN.
- Reviews cleaning:
  - Strip leading/trailing whitespace from review body.
  - Filter reviews where body length < 10 characters (likely empty).
  - Map star ratings (`"5.0 out of 5 stars"` → `5.0 float`).
- Output: `data/processed/products_clean.csv` and `data/processed/reviews_clean.csv`.

---

## Step 3: LLM Analysis & Metrics Engine

### Substep 3.1 — Aspect-Based Sentiment Analysis (`llm_analyzer.py`)
- **Model:** `openai/gpt-4o-mini` via OpenRouter **or** `llama-3.1-70b-versatile` via Groq.
- **Provider toggle:** Read `LLM_PROVIDER` from `.env`. Configure the client base URL accordingly:
  - OpenRouter: `base_url="https://openrouter.ai/api/v1"`
  - Groq: `base_url="https://api.groq.com/openai/v1"`
- For each brand, batch 20 reviews per LLM prompt call to minimize API costs.
- **Prompt structure (per batch):**
  ```
  You are a product analyst. For each review, return a JSON object with:
  - overall_sentiment: positive | neutral | negative
  - sentiment_score: float from -1.0 to 1.0
  - aspects: { wheels, handle, material, zipper, size, durability }
    Each aspect: { mentioned: bool, sentiment: positive|neutral|negative }
  - key_phrases: list of up to 3 key phrases (positive or negative)
  Reviews: [<review_1>, <review_2>, ...]
  ```
- Aggregate per-brand:
  - `avg_sentiment_score` (float)
  - `top_positive_themes` (top 5 recurring phrases from positives)
  - `top_negative_themes` (top 5 recurring phrases from negatives)
  - Per-aspect sentiment breakdown.
- Output: enriched `reviews_clean.csv` with LLM columns + `brand_analysis.json`.

### Substep 3.2 — Review Trust & Anomaly Detection
- Flag suspicious reviews: review body repeated > 3 times across products → mark as `suspicious: True`.
- Detect anomaly: if `avg_rating >= 4.0` but `negative_durability_pct >= 50%` → generate an anomaly alert.
- Add `suspicious_review_pct` and `anomaly_flags` fields to `brand_analysis.json`.
- This directly earns **Bonus Points** on the rubric.

### Substep 3.3 — Confidence Badge Generator
- Calculate confidence based on:
  - Review count per brand (normalized 0–1).
  - Variance of ratings (low variance = more polarized = lower confidence).
  - Percentage of verified purchase reviews.
- Output a badge level: `"Very High"`, `"High"`, `"Medium"`, `"Low"`.
- Store in `brand_analysis.json` as `confidence_badge`.

### Substep 3.4 — Weighted Composite Score (Metrics Engine) (`metrics_engine.py`)
- Implement the normalized + weighted formula (justified in README):
  ```
  Score = (Sentiment_Normalized × 0.35)
        + (Rating_Normalized × 0.35)
        + (ReviewVolume_Normalized × 0.20)
        + (PricePremiumAdjusted × 0.10)
  ```
- Value-for-money analysis: compute `VFM = Score / Price_Band` where `Price_Band = 1 (budget), 2 (mid), 3 (premium)`.
- This earns the **"Value-for-money analysis"** bonus point.
- Output: `brand_metrics.csv` with composite score, VFM score, and all raw inputs.

### Substep 3.5 — Agent Insights & Decision Layer (`insights.py`)
- Feed entire `brand_metrics.csv` + `brand_analysis.json` into a single structured LLM prompt.
- **Prompt instructs the LLM to output:**
  - `agent_insights`: array of exactly 5 non-obvious conclusions, each ending with an actionable implication.
  - `strategic_recommendations`: array of exactly 3 recommendations (market positioning, product improvement, pricing).
- Save output to `data/processed/insights.json`.
- **Example insight format:**
  ```json
  {
    "insight": "Safari achieves the highest sentiment-to-price ratio despite pricing 18% below category average.",
    "implication": "Brands targeting the value segment should benchmark against Safari's wheel quality."
  }
  ```

---

## Step 4: FastAPI Backend

### Substep 4.1 — App Bootstrapping (`main.py`)
- Initialize FastAPI app with title, version, and description metadata.
- Configure CORS middleware to allow `http://localhost:5173` (Vite dev server).
- On startup, load all processed JSON/CSV files into memory as module-level data objects.
- Add `--mock` flag support via `argparse` or Typer CLI.

### Substep 4.2 — Core Data Endpoints (`routes.py`)
| Endpoint | Method | Description |
|---|---|---|
| `/api/overview` | GET | Total brands, products, reviews, avg sentiment |
| `/api/brands` | GET | All brand names and their composite scores |
| `/api/brands/{brand_name}` | GET | Full brand metrics, themes, confidence badge, anomalies |
| `/api/products` | GET | All products with optional `?brand=` and `?min_rating=` filters |
| `/api/products/{asin}` | GET | Single product drilldown with review synthesis |
| `/api/insights` | GET | Agent Insights + Strategic Recommendations from `insights.json` |
| `/api/metrics/comparison` | GET | Side-by-side comparison table data for all brands |

### Substep 4.3 — API Data Models (Pydantic)
- Define Pydantic `BaseModel` schemas for every endpoint response to ensure type safety.
- Example: `BrandResponse`, `ProductResponse`, `InsightResponse`.

---

## Step 5: React Frontend

### Substep 5.1 — Global Layout & Routing (`App.jsx`)
- Set up `react-router-dom` with routes for:
  - `/` → Dashboard Overview
  - `/brands` → Brand Comparison
  - `/products` → Product Drilldown
  - `/insights` → Agent Insights
- Use a persistent `Sidebar.jsx` component shared across all pages.

### Substep 5.2 — Sidebar with Filters (`Sidebar.jsx`)
- **Brand multi-select checkboxes** (all 6 brands, default all checked).
- **Price range slider** (₹0 – ₹20,000).
- **Minimum rating filter** (star rating 1–5).
- **Sentiment filter** (All / Positive / Neutral / Negative).
- **Confidence filter** (Minimum badge level: Very High / High / Medium / Low).
- All filter changes trigger a global state update that all components listen to.

### Substep 5.3 — Dashboard Overview (`DashboardOverview.jsx`)
- Stat cards at the top: Total Brands | Total Products | Total Reviews | Avg Sentiment.
- A `BarChart` (Recharts) showing composite scores for all brands side by side.
- A bar chart for average discount % per brand.
- A price distribution range chart per brand.

### Substep 5.4 — Brand Comparison View (`BrandComparison.jsx`)
- Sortable comparison table: Brand | Avg Price | Avg Discount % | Avg Rating | Review Count | Sentiment Score | Composite Score.
- Expandable rows showing Top 3 Pros and Top 3 Cons per brand.
- Confidence badge displayed next to each brand name.
- Anomaly flag icon for brands with detected review inconsistencies.

### Substep 5.5 — Price × Rating Scatter (`PriceRatingScatter.jsx`)
- Recharts `ScatterChart` with:
  - X-axis: Average Product Price (₹)
  - Y-axis: Star Rating (1.0–5.0)
  - Bubble size: total review count
  - Color: unique brand color
- Tooltips on hover showing product name + ASIN.
- Works as both an overview and within the Product Drilldown tab.

### Substep 5.6 — Product Drilldown (`ProductDrilldown.jsx`)
- Searchable/filterable product table.
- Click on a product to open a side panel showing:
  - Title, Price, MRP, Discount %, Rating, Review Count.
  - LLM-generated review synthesis paragraph.
  - Aspect sentiment breakdown (wheels, handle, durability, etc.) shown as colored progress bars.
  - Top Complaint Themes and Top Praise Themes as tag chips.

### Substep 5.7 — Agent Insights View (`AgentInsights.jsx` + `StrategicRecommendations.jsx`)
- **Agent Insights:** 5 numbered insight cards. Each card has:
  - Insight text (bold, larger font).
  - Implication text (muted, smaller).
  - A dynamic icon based on the topic (e.g., a trending icon for pricing insights).
- **Strategic Recommendations:** 3 cards below insights with icons:
  - 🎯 Market Positioning recommendation.
  - 🔧 Product Improvement recommendation.
  - 💰 Pricing Strategy recommendation.

---

## Step 6: Final Testing, Polish & Documentation

### Substep 6.1 — End-to-End Pipeline Test
- Run the full pipeline in `--mock` mode: `python backend/main.py --mock`
- Verify all processed files are generated correctly in `data/processed/`.
- Start the FastAPI server: `uvicorn backend.main:app --reload --port 8000`
- Start the React dev server: `cd frontend && npm run dev`
- Click through every tab, filter, and drilldown in the browser to verify with zero errors.

### Substep 6.2 — Live Scraping Validation
- Attempt a partial scrape of 2 brands (5 products each).
- Verify the CSV output matches the expected schema before committing mock data as a fallback.
- Document in README: "Live scraping attempted for X brands, Y products collected before rate limiting. Use `--mock` for reliable demo."

### Substep 6.3 — README Writing
Structured exactly per the blueprint:
1. Project Overview
2. Live Demo / Screenshots
3. Architecture Diagram
4. Setup Instructions (with `--mock` flag explained prominently)
5. LLM Methodology & Weights Justification
6. Data Limitations & Scraping Notes
7. Bonus Features Implemented
8. Future Improvements

### Substep 6.4 — Dataset Submission File
- Export a final `luggage_brands_dataset.csv` combining:
  - All products (cleaned)
  - All reviews (cleaned)
  - Sentiment scores
  - Composite scores
- This is the "Cleaned dataset" deliverable required by the rubric.

---

## LLM Provider Configuration Reference

| Feature | OpenRouter | Groq |
|---|---|---|
| Model | `openai/gpt-4o-mini` | `llama-3.1-70b-versatile` |
| Base URL | `https://openrouter.ai/api/v1` | `https://api.groq.com/openai/v1` |
| Auth Header | `Authorization: Bearer $OPENROUTER_API_KEY` | `Authorization: Bearer $GROQ_API_KEY` |
| Rate Limits | Moderate | Very fast, generous free tier |
| Cost | ~$0.15/1M tokens | Free tier available |

> Use **Groq** during development for speed. Switch to **OpenRouter (`gpt-4o-mini`)** for final submission to ensure quality.

---

## Bonus Points Checklist

- [ ] Aspect-level sentiment (wheels, handle, material, zipper, size, durability) — **Substep 3.1**
- [ ] Anomaly detection (high rating + durability complaints) — **Substep 3.2**
- [ ] Value-for-money analysis (sentiment adjusted by price band) — **Substep 3.4**
- [ ] Review trust signals (suspicious repetition detection) — **Substep 3.2**
- [ ] Agent Insights (5 non-obvious auto-generated conclusions) — **Substep 3.5**
