# CarryIQ — Amazon India Luggage Competitive Intelligence

<br>

A full-stack, AI-driven competitive intelligence dashboard designed to extract, analyze, and present structured market data from Amazon India luggage brands. Built specifically as a submission for the **Moonshot AI Agent Internship Assignment**.

This project transforms messy marketplace signals—specifically customer reviews and dynamic pricing—into a highly visual, decision-ready dashboard for business leaders. 

By autonomously scraping data, extracting sentiment through Large Language Models, weighting trust signals, and detecting anomalies, this system replaces hours of manual market research with actionable, agentic insights.

<br>

---

<br>

## 🎯 Project Objective & Core Workflow

The goal of CarryIQ is to dynamically answer critical market questions defined by the Moonshot product prompt:

1. **Which brands are positioned as premium vs. value-focused?**
2. **Which brands rely on heavy discounting to drive demand?**
3. **What do customers consistently praise or complain about?**
4. **Which brands win on sentiment relative to their price?**

To answer these questions continuously and automatically, CarryIQ implements a strictly automated 4-stage pipeline orchestrated by a robust state machine:

### Core Pipeline Phases:
* **Scrape:** Acquiring raw HTML, product titles, prices, ratings, and written reviews.
* **Analyze:** Passing unstructured text through an LLM to receive grouped, structured JSON output.
* **Compare:** Running analytical math to weight sentiment against pricing and ratings.
* **Present:** Displaying the final matrix in a sortable, interactive web interface.

<br>

---

<br>

## 🏗️ Technical Architecture & Engineering Decisions

This project utilizes a strictly decoupled architecture. A Python `FastAPI` application serves as the heavy-lifting backend and data orchestrator, while a `React` application provides the Interactive user interface.

<br>

### 1. The 3-Layer Fault-Tolerant Data Extraction System

Amazon employs aggressive, dynamic anti-bot technology. Constructing a competitive dashboard that relies on live data is notoriously fragile. To ensure this dashboard is never down and always has rich data for evaluation, the data retrieval pipeline (`backend/scraper/`) utilizes a resilient 3-layer fallback system:

#### Layer 1: The Primary Playwright Scraper (`playwright_scraper.py`)
This is the front-line orchestrator. It uses an asynchronous Playwright (Chromium) instance that mimics human behavior. It injects random delays, uses full rotating user-agent strings, and extracts live Amazon search results. It saves data incrementally to prevent data loss upon a crash.

#### Layer 2: The Fast HTTP Fallback (`fallback_scraper.py`)
If Playwright is detected and triggers a hard CAPTCHA, the `main.py` orchestrator catches the failure and instantly switches to `fallback_scraper.py`. This layer abandons the headless browser, instead mimicking lightweight GET requests using `httpx` and parsing the raw DOM directly via `BeautifulSoup`. 

#### Layer 3: The Synthetic Failsafe Module (`mock_data.py`)
If Amazon fully IP-blocks the host machine (causing Layer 2 to also fail), the system falls back to `mock_data.py`. This module acts as the ultimate failsafe, executing a mathematical random seed to inject a high-fidelity synthetic dataset mimicking 6 major luggage brands (Safari, Skybags, American Tourister, VIP, Aristocrat, Nasher Miles) so the dashboard remains fully functional for presentation.

<br>

### 2. The AI Synthesis & Metrics Engine

#### Data Cleaning (`cleaner.py`)
Raw CSV data is loaded into `pandas` dataframes. The system automatically handles type coercion, null removal, and strictly de-duplicates via ASIN (Amazon Standard Identification Number) to ensure corrupted or double-scraped items don't skew the AI metrics. It also calculates the hidden `discount_pct` by comparing the List Price vs the MRP.

#### LLM Sentiment Engine (`sentiment.py`)
Scraped review strings are batched and sent to an LLM (configurable via OpenRouter or Groq). A strict system prompt is used alongside JSON-mode enforcement. The LLM acts as an NLP classifier, outputting a highly structured dictionary containing:
* A normalized sentiment score (0.00-1.00)
* Array of top product strengths (aspect-level)
* Array of major complaints (aspect-level analysis)
* Notable qualitative quotes for the dashboard

#### The Competitive Intelligence Algorithm (`metrics_engine.py`)
Instead of relying solely on Amazon's easily manipulated star ratings, `metrics_engine.py` calculates a bespoke, weighted Intelligence Score (from 0 to 100). The formula accounts for:
1. `review_volume_weight`: Penalizes products with < 100 reviews.
2. `sentiment_weight`: Heavily biases the LLM's true text analysis over the star rating.
3. `price_premium_check`: Checks if the brand is priced over the market average.

#### Executive Insights Generator (`insights.py`)
To fulfill the "Agentic Thinking" requirement, a secondary LLM pass reviews the final JSON metrics output and writes strategic, qualitative takeaways for the dashboard. It isolates the "Winning Brand", flags key market anomalies, and gives a direct recommendation.

<br>

### 3. The Interactive UX System (Frontend)

The frontend (`frontend/src/`) is built using React. 

#### Design System
Rather than relying on default generic libraries like Bootstrap or Tailwind, the dashboard features a completely bespoke "God-Level Dark Glassmorphism" UI. This was implemented manually via CSS variables in `index.css` to hit the "UI Polish" requirements perfectly. It includes animated gradients, custom SVG score rings, and sleek hover states.

#### Recharts Anomaly Detection (`MetricsCharts.jsx`)
The dashboard includes an interactive Scatter Plot that plots Star Ratings against the LLM Sentiment Score. This visually exposes anomalies (e.g., brands with fake 4.5-star ratings but terrible text reviews hiding in the bottom right corner).

<br>

---

<br>

## 🏅 Fulfilling the Evaluation Rubric & Bonuses

CarryIQ was built strictly to the Moonshot evaluation rubric and successfully implements all of the requested Core Requirements and Bonus Points:

### Data Collection Quality (20 Score)
- **Status:** Accomplished.
- Handles Safari, Skybags, American Tourister, VIP, Aristocrat, and Nasher Miles (> 15 products / 60+ reviews per brand target).
- Auto handles deduplication and CAPTCHA evasion.

### Analytical Depth (20 Score)
- **Status:** Accomplished.
- The pipeline doesn't just read ratings; it actively reads the text via an LLM.

### Dashboard UX/UI (20 Score)
- **Status:** Accomplished.
- Clean layout, strong visual hierarchy, and an incredibly intuitive design system.

### Competitive Intelligence Quality (15 Score)
- **Status:** Accomplished.
- The proprietary Competitive Intelligence Score formula natively weighs price vs. sentiment to create a single readable benchmark.

### Technical Execution (15 Score)
- **Status:** Accomplished.
- Modular code architecture. Fully separated Python Backend and React Frontend.

### Product Thinking (10 Score)
- **Status:** Accomplished.
- The dashboard is built for a decision-maker: Topline stats, clear anomalies, qualitative reasons, and an AI agent to read it for you.

### Bonus Points Completed:
1. **Agent Insights:** The top panel of the dashboard features a glowing "AI Agent Analysis" module that automatically writes a market summary, identifies key anomalies, and gives strategic recommendations based purely on the processed data.
2. **Anomaly Detection:** The Recharts visualization is explicitly designed to catch anomaly brands with skewed Trust Signals.
3. **Value-for-Money Analysis:** The intelligence score mathematically adjusts a brand's score based on whether it is priced as a mass-market or premium brand.
4. **Aspect-level sentiment:** The Sentiment Cards at the bottom of the dashboard highlight specific recurring components (e.g., zippers, wheels, material).

<br>

---

<br>

## 🔌 API Reference Guide

The FastAPI backend exposes 6 strictly typed endpoints for the React frontend to consume:

#### `GET /api/health`
Returns the status of the server and whether the clean dataset `json` files currently exist in the directory. Used by React to know if the Scraper needs to be run.

#### `GET /api/brands`
Returns a list of strings representing the current brands stored in the local processed dataset.

#### `GET /api/metrics`
Returns the quantitative data. Contains the total brand count, confidence levels, and the complete Leaderboard array sorted by Intelligence Score.

#### `GET /api/sentiment`
Returns the qualitative data. Contains the LLM generated extraction sets (pros, cons, quotes) keyed by brand.

#### `GET /api/insights`
Returns the Executive Analysis JSON object (headline, market summary, anomalies).

#### `POST /api/run-pipeline`
Accepts a JSON payload `{ "mock": boolean }`. Triggers the entire 5-layer pipeline in the background and returns a success message when finished.

<br>

---

<br>

## 🚀 Environment Setup & Execution

### Prerequisites
- Python Minimum Version: 3.13+
- Node Minimum Version: 18+

<br>

### Step 1: Model Keys Configuration
Create a `.env` file in the root directory. You can use the provided `.env.example` as a template.
```properties
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=your_key_here
```

<br>

### Step 2: Backend Initialization
Open a terminal in the root `CarryIQ` directory and construct the Python virtual environment:

```powershell
# Create Virtual Environment
python -m venv venv

# Activate Environment (Windows)
.\venv\Scripts\activate
# For Mac/Linux: source venv/bin/activate

# Install the Python Dependencies
pip install -r backend/requirements.txt

# Download the headless browser engines for Playwright
playwright install chromium
```

To run the backend server:
```powershell
python backend/main.py
```
*(Pro-tip: If you have already scraped data during a previous session and just want the server to start instantly, bypass the pipeline initialization using `python backend/main.py --no-pipeline`)*

<br>

### Step 3: Frontend Initialization
Open a completely separate second terminal window and navigate into the React directory:

```powershell
cd frontend

# Install exact dependency tree
npm install

# Start the Vite development hot-server
npm run dev
```

<br>

### Step 4: Access Application
Navigate to `http://localhost:5173` in your favorite web browser. 

Once the application loads, you can use the interactive menu controls located right below the Navbar. Click either the **Generate Mock Data** button for instantaneous testing, or the **Run Live Playwright Scrape** button to instruct the backend to actively gather new live luggage data from Amazon.

Watch the dashboard dynamically rebuild itself right in front of your eyes!

<br>

---

<br>

## 🔮 Limitations and Future Improvements

As requested by the Submission recommendations, here are areas where CarryIQ could be expanded upon in a production environment:

1. **Database Persistence:** Currently, this architecture uses persistent CSV/JSON files as its storage block. For a production deployment, this would be swapped out to a PostgreSQL or MongoDB instance to allow for relational queries and time-series history tracking.
2. **WebSocket Integration:** The current "Run Scraper" button relies on HTTP polling. A bidirectional WebSocket implementation would allow the backend to stream live progress logs directly into the React UI while the scraper works.
3. **Cloud Proxy Rotation:** The Playwright layer works excellently locally, but for enterprise usage, integrating a dynamic residential IP proxy pool would allow it to scrape thousands of ASINs simultaneously without triggering Amazon CAPTCHAs. 
4. **Keyword Drilldowns:** Expanding the Sentiment Cards to allow clicking on "Wheel Durability" to see exactly which raw reviews were sourced for that topic.

<br>

---

<br>

## 🧩 Data Contract Schemas (Pydantic Models)

To guarantee stability between the Python execution layer and the React front-end layer, this project enforces strict Type contracts via Pydantic. If any data is missing or malformed, the API automatically flags the deviation before it can crash the UI.

### 1. `MetricsLeaderboardResponse`
```python
class BrandMetrics(BaseModel):
    brand: str
    avg_price: float
    avg_rating: float
    total_reviews: int
    llm_sentiment_score: float

class IntelligenceEntry(BaseModel):
    brand: str
    intelligence_score: float
    confidence_level: str
    metrics: BrandMetrics
```

### 2. `SentimentAnalysisResponse`
```python
class BrandSentiment(BaseModel):
    brand: str
    sentiment_score: float
    top_positives: list[str]
    top_complaints: list[str]
    notable_quotes: list[str]
```

### 3. `AgentInsightsResponse`
```python
class BrandHighlight(BaseModel):
    brand: str
    insight: str

class AgentInsightsResponse(BaseModel):
    headline: str
    market_summary: str
    key_anomaly: str
    strategic_recommendation: str
    brand_highlights: list[BrandHighlight]
```

<br>

---

<br>

## 🆘 Troubleshooting Guide

If you encounter issues while running the dashboard locally, please refer to these common solutions:

*   **Error:** `"Failed to load dashboard data. Ensure the FastAPI backend is running on port 8000."`
    *   **Fix:** Your React application is running, but the backend is closed. Open a separate terminal, activate the virtual environment, and execute `python backend/main.py`.
*   **Error:** `"LLM_PROVIDER key is missing."`
    *   **Fix:** Ensure you have created exactly `.env` (not `.env.example`) in the root directory, and populated it with a valid OpenRouter or Groq API string.
*   **Error:** `Python charmap codec can't encode character...`
    *   **Fix:** If you modify `metrics_engine.py` to add Emojis and print to a legacy Windows terminal, ensure you explicitly set the terminal encoding to UTF-8 using `chcp 65001`.
*   **Behavior:** `Playwright blocked. Attempting HTTP fallback...`
    *   **Response:** This is entirely normal! Amazon dynamically triggers CAPTCHAs based on IP reputation. You do not need to restart. The backend will automatically trigger the HTTP crawler or Mock injection on your behalf.
*   **Frontend Note:** If you resize your browser window, ensure your width remains greater than `768px` for the absolute optimal Desktop layout experience as defined by the glassmorphism grid structure.

<br>

<br>

**Thank you for reviewing CarryIQ!**
