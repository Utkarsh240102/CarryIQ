"""
Amazon India Playwright Scraper
--------------------------------
Layer 1: Primary scraper using Playwright (async Chromium).
- Realistic headers and random delays to avoid detection.
- Incremental checkpoint saves after every product.
- CAPTCHA detection with graceful fallback trigger.
- Targets: Safari, Skybags, American Tourister, VIP, Aristocrat, Nasher Miles
- Minimum: 15 products/brand, 60+ reviews/brand
"""

import asyncio
import csv
import os
import random
import re
import sys
from datetime import datetime
from pathlib import Path

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

# ─── Config ─────────────────────────────────────────────────────────────────

BRANDS = [
    "Safari",
    "Skybags",
    "American Tourister",
    "VIP",
    "Aristocrat",
    "Nasher Miles",
]

MAX_PRODUCTS_PER_BRAND = 15
MIN_REVIEWS_PER_BRAND = 60
MAX_REVIEWS_PER_PRODUCT = 15

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"
DATA_DIR.mkdir(parents=True, exist_ok=True)

PRODUCTS_CSV = DATA_DIR / "products_raw.csv"
REVIEWS_CSV = DATA_DIR / "reviews_raw.csv"

AMAZON_BASE = "https://www.amazon.in"

PRODUCT_FIELDNAMES = [
    "brand", "asin", "title", "price", "mrp",
    "discount_pct", "rating", "review_count", "url", "scraped_at",
]

REVIEW_FIELDNAMES = [
    "brand", "asin", "product_title", "reviewer_name",
    "review_date", "review_rating", "review_title", "review_body",
    "verified_purchase", "scraped_at",
]

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
]


# ─── Utility Helpers ─────────────────────────────────────────────────────────

def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _write_product(row: dict):
    """Append a single product row to the CSV (checkpoint save)."""
    file_exists = PRODUCTS_CSV.exists()
    with open(PRODUCTS_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=PRODUCT_FIELDNAMES)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


def _write_review(row: dict):
    """Append a single review row to the CSV (checkpoint save)."""
    file_exists = REVIEWS_CSV.exists()
    with open(REVIEWS_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=REVIEW_FIELDNAMES)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


def _is_captcha(url: str) -> bool:
    return "captcha" in url.lower() or "ap/signin" in url.lower()


async def _random_delay(min_s: float = 3.0, max_s: float = 7.0):
    delay = random.uniform(min_s, max_s)
    await asyncio.sleep(delay)


def _clean_price(raw: str) -> float | None:
    """Extract numeric price from strings like '₹3,499' or '3,499.00'."""
    if not raw:
        return None
    cleaned = re.sub(r"[^\d.]", "", raw)
    try:
        return float(cleaned)
    except ValueError:
        return None


def _clean_rating(raw: str) -> float | None:
    """Extract float from '4.2 out of 5 stars'."""
    if not raw:
        return None
    match = re.search(r"(\d+\.?\d*)", raw)
    return float(match.group(1)) if match else None


def _clean_review_count(raw: str) -> int | None:
    """Extract int from '1,234 ratings'."""
    if not raw:
        return None
    cleaned = re.sub(r"[^\d]", "", raw)
    return int(cleaned) if cleaned else None


def _extract_asin(url: str) -> str:
    """Pull the ASIN from an Amazon product URL."""
    match = re.search(r"/dp/([A-Z0-9]{10})", url)
    return match.group(1) if match else "UNKNOWN"


# ─── Core Scraping Functions ─────────────────────────────────────────────────

async def _scrape_search_results(page, brand: str) -> list[dict]:
    """Search Amazon India for a brand and return raw product stubs."""
    search_query = f"{brand} luggage trolley bag"
    url = f"{AMAZON_BASE}/s?k={search_query.replace(' ', '+')}"
    print(f"  → Searching: {url}")

    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
    except PlaywrightTimeoutError:
        print("  ⚠ Page load timed out. Skipping brand.")
        return []

    await _random_delay(2, 4)

    if _is_captcha(page.url):
        print("  🚫 CAPTCHA detected! Triggering fallback.")
        return "CAPTCHA"

    products = []
    results = await page.query_selector_all('[data-component-type="s-search-result"]')
    print(f"  → Found {len(results)} results on search page.")

    for item in results[:MAX_PRODUCTS_PER_BRAND]:
        try:
            # Title
            title_el = await item.query_selector("h2")
            title = (await title_el.inner_text()).strip() if title_el else None

            # URL
            link_el = await item.query_selector("h2 a")
            if not link_el:
                link_el = await item.query_selector("a.a-link-normal")
            href = await link_el.get_attribute("href") if link_el else None
            full_url = AMAZON_BASE + href if href and href.startswith("/") else href

            # Price
            price_el = await item.query_selector(".a-price .a-offscreen")
            price_raw = (await price_el.inner_text()) if price_el else None

            # MRP
            mrp_el = await item.query_selector(".a-text-price .a-offscreen")
            mrp_raw = (await mrp_el.inner_text()) if mrp_el else None

            # Rating
            rating_el = await item.query_selector(".a-icon-alt")
            rating_raw = (await rating_el.inner_text()) if rating_el else None

            # Review count
            rc_el = await item.query_selector('[aria-label*="ratings"]')
            if not rc_el:
                rc_el = await item.query_selector(".a-size-base.s-underline-text")
            rc_raw = (await rc_el.inner_text()) if rc_el else None

            if title and full_url:
                price = _clean_price(price_raw)
                mrp = _clean_price(mrp_raw)

                discount_pct = None
                if price and mrp and mrp > price:
                    discount_pct = round(((mrp - price) / mrp) * 100, 1)

                asin = _extract_asin(full_url)

                products.append({
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
        except Exception as e:
            print(f"  ⚠ Error parsing product: {e}")
            continue

    return products


async def _scrape_reviews(page, product: dict, brand_review_count: int) -> list[dict]:
    """Navigate to a product's reviews page and extract reviews."""
    asin = product["asin"]
    reviews_url = f"{AMAZON_BASE}/product-reviews/{asin}/?pageNumber=1&sortBy=recent"

    if asin == "UNKNOWN":
        return []

    try:
        await page.goto(reviews_url, wait_until="domcontentloaded", timeout=30000)
    except PlaywrightTimeoutError:
        print(f"  ⚠ Timeout on reviews for ASIN {asin}")
        return []

    await _random_delay(2, 5)

    if _is_captcha(page.url):
        print("  🚫 CAPTCHA on reviews page!")
        return "CAPTCHA"

    reviews = []
    review_els = await page.query_selector_all('[data-hook="review"]')

    for el in review_els[:MAX_REVIEWS_PER_PRODUCT]:
        try:
            # reviewer
            name_el = await el.query_selector(".a-profile-name")
            name = (await name_el.inner_text()).strip() if name_el else "Anonymous"

            # date
            date_el = await el.query_selector('[data-hook="review-date"]')
            date_raw = (await date_el.inner_text()).strip() if date_el else ""

            # rating
            rating_el = await el.query_selector('[data-hook="review-star-rating"] .a-icon-alt')
            rating_raw = (await rating_el.inner_text()).strip() if rating_el else None
            rating = _clean_rating(rating_raw)

            # review title
            title_el = await el.query_selector('[data-hook="review-title"] span:last-child')
            review_title = (await title_el.inner_text()).strip() if title_el else ""

            # review body
            body_el = await el.query_selector('[data-hook="review-body"] span')
            review_body = (await body_el.inner_text()).strip() if body_el else ""

            # verified purchase
            vp_el = await el.query_selector('[data-hook="avp-badge"]')
            verified = vp_el is not None

            if review_body and len(review_body) > 10:
                reviews.append({
                    "brand": product["brand"],
                    "asin": asin,
                    "product_title": product["title"],
                    "reviewer_name": name,
                    "review_date": date_raw,
                    "review_rating": rating,
                    "review_title": review_title,
                    "review_body": review_body,
                    "verified_purchase": verified,
                    "scraped_at": _now(),
                })
        except Exception as e:
            print(f"  ⚠ Error parsing review: {e}")
            continue

    return reviews


# ─── Main Orchestrator ────────────────────────────────────────────────────────

async def run_scraper(brands: list[str] | None = None, headless: bool = True):
    """Main entry point for the Playwright scraper."""
    target_brands = brands or BRANDS
    captcha_triggered = False
    total_products = 0
    total_reviews = 0

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=headless)

        for brand in target_brands:
            if captcha_triggered:
                print(f"\n⚠ Skipping '{brand}' — CAPTCHA triggered earlier. Use --mock mode.")
                break

            print(f"\n{'='*55}")
            print(f"  Scraping brand: {brand}")
            print(f"{'='*55}")

            context = await browser.new_context(
                user_agent=random.choice(USER_AGENTS),
                viewport={"width": 1920, "height": 1080},
                locale="en-IN",
                extra_http_headers={
                    "Accept-Language": "en-IN,en;q=0.9",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                }
            )
            page = await context.new_page()

            # Step 1: Get product list
            products = await _scrape_search_results(page, brand)

            if products == "CAPTCHA":
                captcha_triggered = True
                await context.close()
                break

            if not products:
                print(f"  ⚠ No products found for {brand}. Skipping.")
                await context.close()
                continue

            brand_review_count = 0

            for i, product in enumerate(products):
                print(f"  [{i+1}/{len(products)}] {product['title'][:60]}...")

                # Checkpoint save: persist product immediately
                _write_product(product)
                total_products += 1

                # Step 2: Scrape reviews if we still need more for this brand
                if brand_review_count < MIN_REVIEWS_PER_BRAND:
                    await _random_delay(3, 6)
                    reviews = await _scrape_reviews(page, product, brand_review_count)

                    if reviews == "CAPTCHA":
                        captcha_triggered = True
                        break

                    for review in (reviews or []):
                        _write_review(review)
                        brand_review_count += 1
                        total_reviews += 1

                    print(f"     ✓ {len(reviews or [])} reviews collected "
                          f"(brand total: {brand_review_count})")

                await _random_delay(3, 7)

            await context.close()
            print(f"\n  ✅ {brand}: {len(products)} products, {brand_review_count} reviews saved.")

        await browser.close()

    print(f"\n{'='*55}")
    print(f"  Scraping complete: {total_products} products, {total_reviews} reviews")
    print(f"  Data saved to: {DATA_DIR}")
    print(f"{'='*55}")

    if captcha_triggered:
        print("\n  ⚠ CAPTCHA was hit. Run with --mock flag for full data.")
        return False
    if total_products == 0:
        print("\n  ⚠ No products were scraped (DOM mismatch or silent block). Triggering fallback.")
        return False
    return True


# ─── CLI Entry Point ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Amazon India Luggage Scraper")
    parser.add_argument("--brands", nargs="+", default=None,
                        help="Specific brands to scrape (default: all 6)")
    parser.add_argument("--no-headless", action="store_true",
                        help="Run browser in visible mode for debugging")
    args = parser.parse_args()

    success = asyncio.run(
        run_scraper(brands=args.brands, headless=not args.no_headless)
    )
    sys.exit(0 if success else 1)
