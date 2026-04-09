# CarryIQ — Amazon India Luggage Competitive Intelligence

A full-stack, AI-driven competitive intelligence dashboard designed to extract, analyze, and present structured market data from Amazon India luggage brands. Built specifically as a submission for the **Moonshot AI Agent Internship Assignment**.

This project transforms messy marketplace signals—specifically customer reviews and dynamic pricing—into a highly visual, decision-ready dashboard for business leaders.

---

## 🎯 Project Objective & Core Workflow
The goal of CarryIQ is to dynamically answer critical market questions:
* Which brands are positioned as premium vs. value-focused?
* Which brands rely on heavy discounting?
* What do customers consistently praise or complain about?
* Which brands win on sentiment relative to their price?

To accomplish this, CarryIQ implements a strictly automated 4-stage pipeline: **Scrape → Analyze → Compare → Present**.

---

## 🏗️ Technical Architecture & Features

This project utilizes a decoupled architecture with a Python/FastAPI backend and a React/Vite frontend. 

### 1. The 3-Layer Fault-Tolerant Data Pipeline (Backend)
Amazon employs aggressive anti-bot technology. To ensure the dashboard is never down and always has rich data for evaluation, the data pipeline (`backend/pipeline/`) utilizes a resilient 3-layer fallback system:
* **Layer 1 (The Primary Scraper):** An asynchronous Playwright (Chromium) script (`playwright_scraper.py`) that acts human, parses the DOM, and extracts live Amazon search results and product review URLs.
* **Layer 2 (The Fast HTTP Fallback):** If Playwright triggers a hard CAPTCHA, the orchestrator instantly switches to `fallback_scraper.py`, which uses `httpx` and `BeautifulSoup` to parse raw HTML and bypass complex JavaScript blocks.
* **Layer 3 (The Synthetic Failsafe):** If Amazon fully IP-blocks the host machine, the system falls back to `mock_data.py`. This injects a mathematically consistent, high-fidelity synthetic dataset mimicking 6 major luggage brands (Safari, Skybags, American Tourister, VIP, Aristocrat, Nasher Miles) so the dashboard remains fully functional for presentation.

### 2. The AI Synthesis & Metrics Engine
* **Pandas Cleaning:** Raw CSV data is scrubbed, type-coerced, ASINs are de-duplicated, and hidden discount percentages are calculated (`cleaner.py`).
* **LLM Sentiment Analysis:** Reviews are batched and sent to an LLM (configurable via OpenRouter or Groq). The LLM extracts a strict JSON schema containing a 0.0-1.0 sentiment score, top complaints, top strengths, and notable quotes. This fulfills the **Aspect-level sentiment analysis** requirement.
* **Competitive Intelligence Score:** Instead of relying solely on Amazon's easily manipulated star ratings, `metrics_engine.py` calculates a weighted score (from 0 to 100) taking into account: Volume of reviews, True AI sentiment, Amazon Rating, and the Price Premium.
* **Executive Insights Generator:** An additional LLM pass looks at the newly calculated metrics and writes strategic, qualitative takeaways for the dashboard. 

### 3. The Interactive Dashboard (Frontend)
The frontend (`frontend/src/`) is built using React and styled with a custom, framework-free "Dark Glassmorphism" CSS system. 
* **Dynamic Recharts Scatter Plot:** Automatically plots Star Ratings vs. LLM Sentiment to visually expose anomalies (e.g. repeated durability complaints hiding behind fake 4.5-star ratings).
* **Interactive Leaderboard:** Ranks brands based on their true Intelligence Score.
* **Live Pipeline Controls:** Users can trigger live scraping or generate new mock data directly from the UI, updating the charts in real-time.

---

## 🏅 Fulfilling the Evaluation Rubric & Bonuses

CarryIQ was built strictly to the Moonshot evaluation rubric and successfully implements the requested Bonus Points:
1. **Agent Insights:** The top panel of the dashboard features a glowing "AI Agent Analysis" module that automatically writes a market summary, identifies key anomalies, and gives strategic recommendations based purely on the processed data.
2. **Anomaly Detection:** The Recharts visualization is explicitly designed to catch brands with skewed Trust Signals (high ratings but low sentiment).
3. **Value-for-Money Analysis:** The backend intelligence score generation algorithm mathematically adjusts a brand's score based on whether it is priced as a mass-market or premium brand.
4. **Aspect-level sentiment:** The Sentiment Cards at the bottom of the dashboard highlight specific recurring complaints (e.g., zip breaking, wheel issues).

---

## 🚀 Setup & Execution Instructions

### Prerequisites
- Python 3.13+
- Node.js 18+

### 1. API Key Configuration
Create a `.env` file in the root directory (you can copy `.env.example`).
```properties
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=your_key_here
```

### 2. Backend Initialization
Open a terminal and set up the Python environment:
```powershell
python -m venv venv
.\venv\Scripts\activate

pip install -r backend/requirements.txt
playwright install chromium

# Start the Backend Server (Port 8000)
python backend/main.py
```
*(Tip: If you have already scraped data and just want the server to start instantly, use `python backend/main.py --no-pipeline`)*

### 3. Frontend Initialization
Open a second terminal window for the React dashboard:
```powershell
cd frontend
npm install

# Start the Frontend Dashboard (Port 5173)
npm run dev
```

Navigate to `http://localhost:5173` in your browser. Click either the **Generate Mock Data** or **Run Live Playwright Scrape** button at the top to kick off the pipeline and watch the dashboard come to life!
