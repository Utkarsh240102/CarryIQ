"""
HTTP Fallback Scraper (Layer 2)
--------------------------------
Activated when: Playwright (Layer 1) hits a CAPTCHA.
Method: Direct HTTP requests using httpx + BeautifulSoup (no browser).
Limitation: Cannot execute JavaScript, so only basic HTML content is extracted.
If this also fails -> Mock Data (Layer 3) takes over automatically.
"""

import csv
import random
import re
import time
from datetime import datetime
from pathlib import Path

import httpx
from bs4 import BeautifulSoup

# ─── Config ──────────────────────────────────────────────────────────────────

AMAZON_BASE = "https://www.amazon.in"

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"
DATA_DIR.mkdir(parents=True, exist_ok=True)

PRODUCTS_CSV = DATA_DIR / "products_raw.csv"
REVIEWS_CSV  = DATA_DIR / "reviews_raw.csv"

PRODUCT_FIELDNAMES = [
    "brand", "asin", "title", "price", "mrp",
    "discount_pct", "rating", "review_count", "url", "scraped_at",
]

REVIEW_FIELDNAMES = [
    "brand", "asin", "product_title", "reviewer_name",
    "review_date", "review_rating", "review_title", "review_body",
    "verified_purchase", "scraped_at",
]

# ─── Rotating headers ─────────────────────────────────────────────────────────
# Different from Playwright headers — these mimic a simple browser GET request.

HEADERS_POOL = [
    {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-IN,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
    },
    {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.8",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
    },
]


# ─── Utility helpers ──────────────────────────────────────────────────────────

def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _delay(min_s: float = 2.0, max_s: float = 5.0):
    """Simple blocking delay (no async needed here)."""
    time.sleep(random.uniform(min_s, max_s))


def _is_blocked(html: str) -> bool:
    """Detect if Amazon returned a CAPTCHA or blocked page."""
    blocked_signals = ["captcha", "robot check", "enter the characters", "api-services-support"]
    return any(signal in html.lower() for signal in blocked_signals)


def _extract_asin(url: str) -> str:
    match = re.search(r"/dp/([A-Z0-9]{10})", url)
    return match.group(1) if match else "UNKNOWN"


def _clean_price(raw: str) -> float | None:
    if not raw:
        return None
    cleaned = re.sub(r"[^\d.]", "", raw)
    try:
        return float(cleaned)
    except ValueError:
        return None


def _clean_rating(raw: str) -> float | None:
    if not raw:
        return None
    match = re.search(r"(\d+\.?\d*)", raw)
    return float(match.group(1)) if match else None


def _clean_review_count(raw: str) -> int | None:
    if not raw:
        return None
    cleaned = re.sub(r"[^\d]", "", raw)
    return int(cleaned) if cleaned else None


def _append_product(row: dict):
    file_exists = PRODUCTS_CSV.exists()
    with open(PRODUCTS_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=PRODUCT_FIELDNAMES)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


def _append_review(row: dict):
    file_exists = REVIEWS_CSV.exists()
    with open(REVIEWS_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=REVIEW_FIELDNAMES)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


# ─── Core scraping ────────────────────────────────────────────────────────────

def _fetch(client: httpx.Client, url: str) -> str | None:
    """
    Fetch a URL and return HTML string.
    Returns None if blocked or request fails.
    """
    headers = random.choice(HEADERS_POOL)
    try:
        response = client.get(url, headers=headers, timeout=15, follow_redirects=True)
        if response.status_code != 200:
            print(f"  [FALLBACK] HTTP {response.status_code} for {url}")
            return None
        html = response.text
        if _is_blocked(html):
            print("  [FALLBACK] Blocked page detected (CAPTCHA signal).")
            return None
        return html
    except (httpx.RequestError, httpx.TimeoutException) as e:
        print(f"  [FALLBACK] Request error: {e}")
        return None


def scrape_brand_fallback(brand: str, max_products: int = 10) -> bool:
    """
    Attempt to scrape basic product data for a single brand via HTTP.
    Returns True if any products were collected, False if blocked.
    """
    search_query = f"{brand} luggage trolley bag"
    search_url = f"{AMAZON_BASE}/s?k={search_query.replace(' ', '+')}"

    print(f"\n  [FALLBACK] Trying HTTP scrape for: {brand}")
    print(f"  [FALLBACK] URL: {search_url}")

    products_saved = 0

    with httpx.Client(
        headers=random.choice(HEADERS_POOL),
        follow_redirects=True,
        timeout=15,
    ) as client:

        # Step 1: Fetch search results page
        html = _fetch(client, search_url)
        if not html:
            print(f"  [FALLBACK] Could not fetch search page for '{brand}'. Giving up.")
            return False

        soup = BeautifulSoup(html, "lxml")

        # Step 2: Parse product cards from search results
        results = soup.select('[data-component-type="s-search-result"]')
        print(f"  [FALLBACK] Found {len(results)} product cards in HTML.")

        for item in results[:max_products]:
            try:
                # Title
                title_el = item.select_one("h2 a span")
                title = title_el.get_text(strip=True) if title_el else None

                # Product URL
                link_el = item.select_one("h2 a")
                href = link_el.get("href") if link_el else None
                full_url = AMAZON_BASE + href if href and href.startswith("/") else href

                # Price
                price_el = item.select_one(".a-price .a-offscreen")
                price_raw = price_el.get_text(strip=True) if price_el else None

                # MRP
                mrp_els = item.select(".a-text-price .a-offscreen")
                mrp_raw = mrp_els[0].get_text(strip=True) if mrp_els else None

                # Rating
                rating_el = item.select_one(".a-icon-alt")
                rating_raw = rating_el.get_text(strip=True) if rating_el else None

                # Review count
                rc_el = item.select_one('[aria-label*="ratings"]')
                if not rc_el:
                    rc_el = item.select_one(".a-size-base.s-underline-text")
                rc_raw = rc_el.get_text(strip=True) if rc_el else None

                if title and full_url:
                    price = _clean_price(price_raw)
                    mrp = _clean_price(mrp_raw)
                    discount_pct = None
                    if price and mrp and mrp > price:
                        discount_pct = round(((mrp - price) / mrp) * 100, 1)

                    asin = _extract_asin(full_url)

                    _append_product({
                        "brand": brand,
                        "asin": asin,
                        "title": title,
                        "price": price,
                        "mrp": mrp,
                        "discount_pct": discount_pct,
                        "rating": _clean_rating(rating_raw),
                        "review_count": _clean_review_count(rc_raw),
                        "url": full_url,
                        "scraped_at": _now(),
                    })
                    products_saved += 1
                    print(f"  [FALLBACK] Saved: {title[:55]}...")

            except Exception as e:
                print(f"  [FALLBACK] Parse error on item: {e}")
                continue

            _delay(1.5, 3.0)

    print(f"  [FALLBACK] {brand}: {products_saved} products saved via HTTP fallback.")
    return products_saved > 0


def run_fallback(brands: list[str]) -> dict[str, bool]:
    """
    Run the HTTP fallback scraper for a list of brands.
    Returns a dict mapping brand -> success (True/False).
    """
    results = {}
    for brand in brands:
        success = scrape_brand_fallback(brand)
        results[brand] = success
        if not success:
            print(f"  [FALLBACK] '{brand}' fully blocked. Will use mock data.")
        _delay(3.0, 6.0)
    return results


# ─── CLI ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    brands = sys.argv[1:] if len(sys.argv) > 1 else ["Safari", "Skybags"]
    print(f"Running HTTP fallback scraper for: {brands}")
    results = run_fallback(brands)
    print("\nResults:", results)
