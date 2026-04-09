"""
Pandas Data Cleaning Pipeline (Step 2.4)
------------------------------------------
Reads raw CSVs from data/raw/ and outputs clean,
analysis-ready CSVs to data/processed/.

Input:  data/raw/products_raw.csv
        data/raw/reviews_raw.csv

Output: data/processed/products_clean.csv
        data/processed/reviews_clean.csv

Cleaning operations:
- De-duplicate by ASIN (products) and ASIN+reviewer_name (reviews)
- Ensure price/mrp/rating/discount_pct are float (not strings)
- Recalculate missing discount_pct from price and mrp
- Drop rows with missing critical fields (title, price, brand)
- Drop reviews with empty/too-short body text (< 20 chars)
- Normalise brand names (strip whitespace, title case)
- Add cleaned_at timestamp column
"""

import re
from datetime import datetime
from pathlib import Path

import pandas as pd

# ─── Paths ────────────────────────────────────────────────────────────────────

BASE_DIR      = Path(__file__).resolve().parents[2]
RAW_DIR       = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

PRODUCTS_RAW   = RAW_DIR / "products_raw.csv"
REVIEWS_RAW    = RAW_DIR / "reviews_raw.csv"

PRODUCTS_CLEAN = PROCESSED_DIR / "products_clean.csv"
REVIEWS_CLEAN  = PROCESSED_DIR / "reviews_clean.csv"

MIN_REVIEW_LENGTH = 20  # Characters — shorter reviews give no signal


# ─── Utility helpers ──────────────────────────────────────────────────────────

def _coerce_float(series: pd.Series) -> pd.Series:
    """
    Convert a Series to float, stripping common Amazon string artefacts.
    Handles: '₹3,499', '3,499.00', '4.2 out of 5 stars', None, NaN.
    """
    def _parse(val):
        if pd.isna(val):
            return None
        s = str(val)
        # Extract first numeric-looking substring
        match = re.search(r"(\d[\d,]*\.?\d*)", s)
        if match:
            return float(match.group(1).replace(",", ""))
        return None

    return series.apply(_parse).astype("float64")


def _coerce_int(series: pd.Series) -> pd.Series:
    """Convert a Series to nullable integer."""
    def _parse(val):
        if pd.isna(val):
            return None
        s = re.sub(r"[^\d]", "", str(val))
        return int(s) if s else None

    return series.apply(_parse).astype("Int64")  # Pandas nullable int


def _normalise_brand(series: pd.Series) -> pd.Series:
    return series.str.strip().str.title()


# ─── Products cleaner ─────────────────────────────────────────────────────────

def clean_products(df: pd.DataFrame) -> pd.DataFrame:
    """
    Full cleaning pass on the raw products DataFrame.
    Returns a clean DataFrame ready for analysis.
    """
    print(f"  [Products] Raw rows: {len(df)}")

    # 1. Normalise brand name
    df["brand"] = _normalise_brand(df["brand"])

    # 2. Coerce numeric columns
    df["price"]        = _coerce_float(df["price"])
    df["mrp"]          = _coerce_float(df["mrp"])
    df["rating"]       = _coerce_float(df["rating"])
    df["discount_pct"] = _coerce_float(df["discount_pct"])
    df["review_count"] = _coerce_int(df["review_count"])

    # 3. Recalculate missing discount_pct from price + mrp
    missing_discount = df["discount_pct"].isna() & df["price"].notna() & df["mrp"].notna()
    df.loc[missing_discount, "discount_pct"] = (
        ((df["mrp"] - df["price"]) / df["mrp"]) * 100
    ).round(1)

    # Clamp discount to 0-100 range (handle data oddities)
    df["discount_pct"] = df["discount_pct"].clip(lower=0, upper=100)

    # 4. Drop rows missing critical fields
    critical = ["brand", "title", "price"]
    before = len(df)
    df = df.dropna(subset=critical)
    print(f"  [Products] Dropped {before - len(df)} rows with missing critical fields.")

    # 5. Drop duplicates by ASIN (keep the first occurrence)
    if "asin" in df.columns:
        before = len(df)
        df = df.drop_duplicates(subset=["asin"], keep="first")
        print(f"  [Products] Dropped {before - len(df)} duplicate ASINs.")

    # 6. Filter out unrealistic ratings
    df = df[df["rating"].between(1.0, 5.0) | df["rating"].isna()]

    # 7. Filter out zero/negative prices
    df = df[df["price"] > 0]

    # 8. Add metadata
    df["cleaned_at"] = datetime.now().isoformat(timespec="seconds")

    # 9. Sort by brand then rating descending
    df = df.sort_values(["brand", "rating"], ascending=[True, False]).reset_index(drop=True)

    print(f"  [Products] Clean rows: {len(df)}")
    return df


# ─── Reviews cleaner ──────────────────────────────────────────────────────────

def clean_reviews(df: pd.DataFrame) -> pd.DataFrame:
    """
    Full cleaning pass on the raw reviews DataFrame.
    Returns a clean DataFrame ready for sentiment analysis.
    """
    print(f"  [Reviews]  Raw rows: {len(df)}")

    # 1. Normalise brand name
    df["brand"] = _normalise_brand(df["brand"])

    # 2. Coerce rating column
    df["review_rating"] = _coerce_float(df["review_rating"])

    # 3. Drop rows with empty/missing review_body
    before = len(df)
    df = df.dropna(subset=["review_body"])
    df = df[df["review_body"].str.strip().str.len() >= MIN_REVIEW_LENGTH]
    print(f"  [Reviews]  Dropped {before - len(df)} empty/short reviews.")

    # 4. Clean text: strip leading/trailing whitespace and extra newlines
    df["review_body"]  = df["review_body"].str.strip()
    df["review_title"] = df["review_title"].str.strip().fillna("")

    # 5. De-duplicate: same reviewer on same product keeps first review
    before = len(df)
    if "asin" in df.columns and "reviewer_name" in df.columns:
        df = df.drop_duplicates(subset=["asin", "reviewer_name"], keep="first")
        print(f"  [Reviews]  Dropped {before - len(df)} duplicate reviewer entries.")

    # 6. Normalise verified_purchase to boolean
    if "verified_purchase" in df.columns:
        df["verified_purchase"] = df["verified_purchase"].map(
            {"True": True, "False": False, True: True, False: False}
        ).fillna(False)

    # 7. Drop rows with unknown brand
    df = df[df["brand"].notna() & (df["brand"] != "")]

    # 8. Add metadata
    df["cleaned_at"] = datetime.now().isoformat(timespec="seconds")

    # 9. Sort by brand, then newest reviews first
    if "review_date" in df.columns:
        df = df.sort_values(["brand", "review_date"], ascending=[True, False]).reset_index(drop=True)
    else:
        df = df.sort_values("brand").reset_index(drop=True)

    print(f"  [Reviews]  Clean rows: {len(df)}")
    return df


# ─── Summary stats helper ─────────────────────────────────────────────────────

def print_summary(products_df: pd.DataFrame, reviews_df: pd.DataFrame):
    """Print a quick dataset summary after cleaning."""
    print("\n  === Dataset Summary ===")
    print(f"  {'Brand':<22} {'Products':>8} {'Avg Price':>10} {'Avg Rating':>11} {'Reviews':>8}")
    print("  " + "-" * 65)

    for brand in sorted(products_df["brand"].unique()):
        p = products_df[products_df["brand"] == brand]
        r = reviews_df[reviews_df["brand"] == brand]
        avg_price  = p["price"].mean()
        avg_rating = p["rating"].mean()
        print(
            f"  {brand:<22} {len(p):>8} "
            f"  Rs.{avg_price:>7.0f} {avg_rating:>11.2f} {len(r):>8}"
        )
    print()


# ─── Main entry point ─────────────────────────────────────────────────────────

def run_cleaner() -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Run the full cleaning pipeline.
    Returns (products_clean_df, reviews_clean_df).
    Raises FileNotFoundError if raw data doesn't exist.
    """
    if not PRODUCTS_RAW.exists():
        raise FileNotFoundError(
            f"Raw products file not found: {PRODUCTS_RAW}\n"
            "Run the scraper first: python backend/main.py [--mock]"
        )
    if not REVIEWS_RAW.exists():
        raise FileNotFoundError(
            f"Raw reviews file not found: {REVIEWS_RAW}\n"
            "Run the scraper first: python backend/main.py [--mock]"
        )

    print("\n[Cleaner] Loading raw data...")
    products_raw = pd.read_csv(PRODUCTS_RAW, dtype=str)
    reviews_raw  = pd.read_csv(REVIEWS_RAW,  dtype=str)

    print("[Cleaner] Cleaning products...")
    products_clean = clean_products(products_raw)

    print("[Cleaner] Cleaning reviews...")
    reviews_clean = clean_reviews(reviews_raw)

    # Save outputs
    products_clean.to_csv(PRODUCTS_CLEAN, index=False, encoding="utf-8")
    reviews_clean.to_csv(REVIEWS_CLEAN,   index=False, encoding="utf-8")

    print(f"\n[Cleaner] Saved: {PRODUCTS_CLEAN}")
    print(f"[Cleaner] Saved: {REVIEWS_CLEAN}")

    print_summary(products_clean, reviews_clean)
    return products_clean, reviews_clean


# ─── CLI ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    run_cleaner()
