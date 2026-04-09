"""
Mock Data Generator
--------------------
Layer 3: Generates realistic synthetic Amazon India luggage data.
Produces identical CSV schemas to the live Playwright scraper.
Run via: python backend/main.py --mock

Brand Patterns (intentional for insightful analysis):
- Safari:            Value-priced, strong wheel/handle sentiment
- Skybags:           Mid-range, anomaly: high ratings but zipper failures
- American Tourister: Premium-priced, brand premium over product quality
- VIP:               Budget-friendly, mid-tier reliability
- Aristocrat:        Very budget, recurring material complaints
- Nasher Miles:      Newer entrant, mixed reviews, competitive pricing
"""

import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

# ─── Output paths ─────────────────────────────────────────────────────────────

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"
DATA_DIR.mkdir(parents=True, exist_ok=True)

PRODUCTS_CSV = DATA_DIR / "products_raw.csv"
REVIEWS_CSV = DATA_DIR / "reviews_raw.csv"

# ─── Brand definitions ────────────────────────────────────────────────────────

BRAND_PROFILES = {
    "Safari": {
        "price_range": (2999, 6999),
        "mrp_multiplier": (1.15, 1.35),
        "avg_rating": 4.3,
        "rating_std": 0.4,
        "positive_bias": 0.72,   # 72% positive reviews
        "aspect_strengths": ["wheels", "handle"],
        "aspect_weaknesses": ["material"],
    },
    "Skybags": {
        "price_range": (3499, 7999),
        "mrp_multiplier": (1.20, 1.45),
        "avg_rating": 4.2,      # ANOMALY: high rating but zipper complaints
        "rating_std": 0.5,
        "positive_bias": 0.68,
        "aspect_strengths": ["size", "design"],
        "aspect_weaknesses": ["zipper", "durability"],  # KEY ANOMALY
    },
    "American Tourister": {
        "price_range": (5499, 14999),
        "mrp_multiplier": (1.25, 1.50),
        "avg_rating": 4.4,
        "rating_std": 0.3,
        "positive_bias": 0.75,
        "aspect_strengths": ["material", "durability", "brand"],
        "aspect_weaknesses": ["price_value"],
    },
    "VIP": {
        "price_range": (2499, 5999),
        "mrp_multiplier": (1.18, 1.40),
        "avg_rating": 4.0,
        "rating_std": 0.5,
        "positive_bias": 0.64,
        "aspect_strengths": ["handle", "size"],
        "aspect_weaknesses": ["wheels", "finish"],
    },
    "Aristocrat": {
        "price_range": (1799, 4499),
        "mrp_multiplier": (1.10, 1.30),
        "avg_rating": 3.8,
        "rating_std": 0.6,
        "positive_bias": 0.58,
        "aspect_strengths": ["price", "size"],
        "aspect_weaknesses": ["material", "handle", "durability"],
    },
    "Nasher Miles": {
        "price_range": (2999, 6499),
        "mrp_multiplier": (1.22, 1.48),
        "avg_rating": 4.1,
        "rating_std": 0.5,
        "positive_bias": 0.66,
        "aspect_strengths": ["wheels", "design"],
        "aspect_weaknesses": ["zipper", "customer_service"],
    },
}

# ─── Product templates ─────────────────────────────────────────────────────────

PRODUCT_TEMPLATES = {
    "Safari": [
        ("Safari Ray 55 cm Small Cabin Trolley Luggage", "55 cm", "Cabin"),
        ("Safari Pentagon 65 cm Medium Check-in Trolley", "65 cm", "Medium"),
        ("Safari Thorium 8 Wheels 75 cm Large Trolley Bag", "75 cm", "Large"),
        ("Safari Polycarbonate 360 Degree Wheels Cabin Bag", "55 cm", "Cabin"),
        ("Safari Tribe 4 Wheel Hard Luggage Set of 2", "Set", "Combo"),
        ("Safari Mint 65 cm Hard Trolley Blue", "65 cm", "Medium"),
        ("Safari Cosmo 75 cm Hardside Spinner Luggage", "75 cm", "Large"),
        ("Safari Regloss 55 cm Antiscratch Suitcase", "55 cm", "Cabin"),
        ("Safari Optima 69 cm Check-in Hard Trolley", "69 cm", "Medium"),
        ("Safari Snapper 8 Wheels Expandable Luggage", "79 cm", "Large"),
        ("Safari Hard Cabin Luggage 55 cm Pink Premium", "55 cm", "Cabin"),
        ("Safari Ozone 65 cm 4 Wheel Polycarbonate Trolley", "65 cm", "Medium"),
    ],
    "Skybags": [
        ("Skybags Teazy 55 cm Cabin Trolley Bag", "55 cm", "Cabin"),
        ("Skybags Stratos 4 Wheel 65 cm Trolley Bag", "65 cm", "Medium"),
        ("Skybags Turbo Plus 79 cm Large Trolley Hard Luggage", "79 cm", "Large"),
        ("Skybags Nimbus 2.0 21 Inch Cabin Bag", "55 cm", "Cabin"),
        ("Skybags Club 69 cm Medium Check-in Hardcase", "69 cm", "Medium"),
        ("Skybags Glide Plus 77 cm Hard Trolley Shell", "77 cm", "Large"),
        ("Skybags Carbon Hard Cabin Luggage Set", "Set", "Combo"),
        ("Skybags Rubik 55 cm Ultralight Trolley", "55 cm", "Cabin"),
        ("Skybags Reef 65 cm Polycarbonate Spinner", "65 cm", "Medium"),
        ("Skybags Optimus Plus 75 cm Expandable Trolley", "75 cm", "Large"),
        ("Skybags Edge 4 Wheel 55 cm Suitcase Red", "55 cm", "Cabin"),
        ("Skybags Citytrail 67 cm Hard Trolley Gray", "67 cm", "Medium"),
    ],
    "American Tourister": [
        ("American Tourister Ivy 55 cm Polycarbonate Cabin Bag", "55 cm", "Cabin"),
        ("American Tourister Linex 69 cm Medium Hard Luggage", "69 cm", "Medium"),
        ("American Tourister Magna Max 79 cm Large Trolley", "79 cm", "Large"),
        ("American Tourister Bon Air 4 Wheel 55 cm Suitcase", "55 cm", "Cabin"),
        ("American Tourister Curio 68 cm Medium Spinner", "68 cm", "Medium"),
        ("American Tourister Starvibe 77 cm Large Hardside", "77 cm", "Large"),
        ("American Tourister Instinction 55 cm Cabin Hard", "55 cm", "Cabin"),
        ("American Tourister Star Wars 65 cm Printed Trolley", "65 cm", "Medium"),
        ("American Tourister Crystal 75 cm Expandable Lock", "75 cm", "Large"),
        ("American Tourister Kamiliant Kam 55 cm Spin Luggage", "55 cm", "Cabin"),
        ("American Tourister Sky Bridge 4R 67 cm Trolley", "67 cm", "Medium"),
        ("American Tourister Trig 79 cm Large Hardside 8W", "79 cm", "Large"),
    ],
    "VIP": [
        ("VIP Skybag 55 cm Small Cabin Hard Trolley", "55 cm", "Cabin"),
        ("VIP Tropic 65 cm Polycarbonate Spinner Luggage", "65 cm", "Medium"),
        ("VIP Elanza 75 cm Large Hard Trolley Grey", "75 cm", "Large"),
        ("VIP Novo 55 cm 8 Wheel Spinner Cabin Bag", "55 cm", "Cabin"),
        ("VIP Odyssey 69 cm Medium Hardside Trolley", "69 cm", "Medium"),
        ("VIP Arcade 4 Wheels Large Trolley Black 79 cm", "79 cm", "Large"),
        ("VIP Verve 55 cm Hard Cabin Bag with TSA Lock", "55 cm", "Cabin"),
        ("VIP Spectra 67 cm Vertical Trolley Hard Luggage", "67 cm", "Medium"),
        ("VIP Swift Opal 75 cm Expendable Large Trolley", "75 cm", "Large"),
        ("VIP Tracks 55 cm Antiscratch Cabin Suitcase", "55 cm", "Cabin"),
        ("VIP Magnus 65 cm Combo Hard Trolley Set of 2", "Set", "Combo"),
        ("VIP Vega 4 Wheel 77 cm Large Hard Shell Trolley", "77 cm", "Large"),
    ],
    "Aristocrat": [
        ("Aristocrat Nile 55 cm Cabin Hard Trolley Bag", "55 cm", "Cabin"),
        ("Aristocrat Ozone 65 cm Hard Luggage Trolley", "65 cm", "Medium"),
        ("Aristocrat Regal 77 cm Large Hard Trolley Blue", "77 cm", "Large"),
        ("Aristocrat Witness 55 cm Polyester Cabin Bag", "55 cm", "Cabin"),
        ("Aristocrat Stario 65 cm 4 Wheel Hard Trolley Pink", "65 cm", "Medium"),
        ("Aristocrat Opus 75 cm Large Hard Luggage Black", "75 cm", "Large"),
        ("Aristocrat Spark 55 cm Spinner Hard Cabin Purple", "55 cm", "Cabin"),
        ("Aristocrat Volt Polycarbonate 69 cm Check-in", "69 cm", "Medium"),
        ("Aristocrat Hub 4 Wheel Small Cabin Trolley 55 cm", "55 cm", "Cabin"),
        ("Aristocrat Matrix 65 cm Medium Hard Trolley Red", "65 cm", "Medium"),
        ("Aristocrat Premier 79 cm XL Large Hard Trolley", "79 cm", "Large"),
        ("Aristocrat Pixel 55 cm 8 Wheel Cabin Hard Bag", "55 cm", "Cabin"),
    ],
    "Nasher Miles": [
        ("Nasher Miles Checked-In Hard Luggage Expandable 65 cm", "65 cm", "Medium"),
        ("Nasher Miles Florence Cabin Hard Luggage 55 cm", "55 cm", "Cabin"),
        ("Nasher Miles Rome 76 cm Large Hard Trolley", "76 cm", "Large"),
        ("Nasher Miles Berlin 55 cm Spinner Cabin Hard Bag", "55 cm", "Cabin"),
        ("Nasher Miles Paris 65 cm 4 Wheel Hard Luggage", "65 cm", "Medium"),
        ("Nasher Miles London 77 cm Large Polycarbonate", "77 cm", "Large"),
        ("Nasher Miles Edinburgh 55 cm Hard Trolley", "55 cm", "Cabin"),
        ("Nasher Miles Vienna 69 cm Medium Hard Spinner", "69 cm", "Medium"),
        ("Nasher Miles Oslo 75 cm Large Hardside Trolley", "75 cm", "Large"),
        ("Nasher Miles Dublin 55 cm TSA Lock Cabin Bag", "55 cm", "Cabin"),
        ("Nasher Miles Milan 65 cm Combo Set of 2 Luggage", "Set", "Combo"),
        ("Nasher Miles Tokyo 79 cm XL Expandable Hard Bag", "79 cm", "Large"),
    ],
}

# ─── Review templates ──────────────────────────────────────────────────────────

POSITIVE_REVIEWS = {
    "wheels": [
        "The wheels glide so smoothly on airport floors, absolutely love it!",
        "360 degree spinner wheels work perfectly even on uneven surfaces.",
        "Wheels are the highlight — silent and effortless on marble floors.",
        "Used it across 3 international trips and wheels still spin perfectly.",
        "No wobble at all, the wheel quality is surprisingly premium.",
    ],
    "handle": [
        "The telescopic handle is sturdy and ergonomic, perfect height for me.",
        "Handle locks at exactly the right position and doesn't collapse mid-walk.",
        "Very comfortable grip on the handle, no strain even after long walks.",
        "Build quality of the handle is excellent, feels like a premium product.",
        "Handle mechanism is smooth and stays locked properly.",
    ],
    "material": [
        "Hard shell polycarbonate is rock solid, no dents after check-in.",
        "Material feels premium and the finish hasn't scratched even after heavy use.",
        "Loved the build quality — much better than similar price range bags.",
        "The outer shell material is tough, survived rough baggage handling.",
        "Looks and feels more expensive than it actually is.",
    ],
    "zipper": [
        "Zipper runs smoothly without snagging even when the bag is fully packed.",
        "TSA lock and zipper quality is excellent, feels very secure.",
        "Zippers are heavy duty and feel like they'll last years.",
        "Zipper didn't jam even once during 4 international flights.",
        "Double zipper is a great feature, makes securing bag so easy.",
    ],
    "size": [
        "Fits perfectly in the overhead cabin bin on IndiGo and Air India.",
        "Spacious inside — packed 6 days worth of clothes and still had room.",
        "The compartments are well thought out and very practical.",
        "Exactly the size advertised, no surprises at the airport check-in.",
        "Large capacity despite being cabin approved size — very smart design.",
    ],
    "durability": [
        "Used this bag for 12+ flights and it still looks brand new.",
        "Survived 2 international trips as check-in and came back with zero damage.",
        "Feels built to last, no creaking sounds even when fully loaded.",
        "After 6 months of regular use, the bag looks as new as day one.",
        "Very durable product, well worth the investment.",
    ],
    "general": [
        "Excellent quality for the price, would highly recommend.",
        "Very happy with this purchase, delivery was also fast.",
        "Perfect travel companion, just as described in the listing.",
        "Great build, great quality. Bought two more for my family.",
        "This is my third bag from this brand — never disappointed.",
        "Value for money is outstanding! Better than bags twice the price.",
        "Looks exactly like the pictures and arrived in perfect condition.",
        "Would definitely buy again, no complaints at all.",
    ],
}

NEGATIVE_REVIEWS = {
    "wheels": [
        "One of the four wheels started wobbling after just 3 uses.",
        "Wheels make a loud noise on smooth airport floors — very annoying.",
        "Two wheels cracked during baggage handling at the airport.",
        "Wheel quality disappointed me — expected better for this price.",
        "Wheels stopped spinning smoothly after the second trip.",
    ],
    "handle": [
        "Handle sometimes gets stuck and doesn't extend smoothly.",
        "Telescopic handle has a slight wobble which is concerning for a new bag.",
        "Handle collapsed on its own while walking through the terminal.",
        "The handle mechanism feels flimsy compared to the price point.",
        "Handle broke at the joint after just 3 months of use.",
    ],
    "material": [
        "The material scratches very easily — bag looks old after one trip.",
        "Hard shell cracked slightly when airline handlers dropped it.",
        "Material feels thin and cheap compared to the price they charge.",
        "The outer coating started peeling after 4-5 uses.",
        "Expected better build quality given the brand reputation and price.",
    ],
    "zipper": [
        "Zipper got stuck on the second use, very disappointing.",
        "One of the zipper pulls broke within a week — poor quality control.",
        "Zipper teeth started separating after just 2 trips.",
        "Zipper runs rough and gets snagged on the fabric constantly.",
        "Zipper lock is loose and doesn't secure the bag properly.",
    ],
    "durability": [
        "Not durable at all — shell cracked after airport handling.",
        "Expected much better durability from a reputed brand.",
        "Shell started showing stress cracks after just 2 international trips.",
        "The bag didn't even last 6 months before showing serious wear.",
        "A premium bag should not crack this easily — very disappointed.",
    ],
    "general": [
        "Overpriced for the quality you get. Many better alternatives available.",
        "Returned the product after one use — quality was not up to standards.",
        "Customer service didn't respond to my damage complaint.",
        "Packaging was poor and the bag arrived slightly bent.",
        "Not worth the price. Would not recommend to anyone.",
        "Expected better from a brand at this price range.",
        "Build quality has clearly gone down compared to older models.",
        "Very disappointed with the overall quality and finish.",
    ],
}

# ─── Data generation helpers ──────────────────────────────────────────────────

def _random_asin() -> str:
    chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    return "B0" + "".join(random.choices(chars, k=8))


def _random_date(days_back: int = 365) -> str:
    base = datetime.now() - timedelta(days=random.randint(1, days_back))
    return f"Reviewed in India on {base.strftime('%d %B %Y')}"


def _random_reviewer() -> str:
    first = ["Amit", "Priya", "Rahul", "Sneha", "Vikram", "Anjali", "Kunal",
             "Deepika", "Arjun", "Pooja", "Rohit", "Nisha", "Sanjay", "Meera",
             "Aakash", "Kavita", "Suresh", "Ritu", "Manish", "Divya"]
    last = ["S.", "K.", "M.", "R.", "G.", "P.", "T.", "B.", "A.", "N."]
    return f"{random.choice(first)} {random.choice(last)}"


def _pick_review(profile: dict, is_positive: bool) -> str:
    """Generate a review based on brand profile and sentiment."""
    if is_positive:
        aspects = profile["aspect_strengths"] + ["general"] * 3
        aspect = random.choice(aspects)
        pool = POSITIVE_REVIEWS.get(aspect, POSITIVE_REVIEWS["general"])

        # Add extra detail occasionally
        base = random.choice(pool)
        if random.random() < 0.4:
            bonus = random.choice(POSITIVE_REVIEWS["general"])
            return f"{base} {bonus}"
        return base
    else:
        aspects = profile["aspect_weaknesses"] + ["general"] * 2
        aspect = random.choice(aspects)
        pool = NEGATIVE_REVIEWS.get(aspect, NEGATIVE_REVIEWS["general"])

        base = random.choice(pool)
        if random.random() < 0.3:
            bonus = random.choice(NEGATIVE_REVIEWS["general"])
            return f"{base} {bonus}"
        return base


def _generate_rating(profile: dict, is_positive: bool) -> float:
    avg = profile["avg_rating"]
    if is_positive:
        raw = random.gauss(avg + 0.3, 0.3)
        return round(min(5.0, max(3.5, raw)), 1)
    else:
        raw = random.gauss(2.0, 0.5)
        return round(min(3.0, max(1.0, raw)), 1)


# ─── Main generator ───────────────────────────────────────────────────────────

def generate_mock_data(
    products_per_brand: int = 12,
    reviews_per_brand: int = 70,
) -> tuple[int, int]:
    """
    Generate mock products and reviews CSVs.
    Returns (total_products, total_reviews).
    """
    product_fieldnames = [
        "brand", "asin", "title", "price", "mrp",
        "discount_pct", "rating", "review_count", "url", "scraped_at",
    ]
    review_fieldnames = [
        "brand", "asin", "product_title", "reviewer_name",
        "review_date", "review_rating", "review_title", "review_body",
        "verified_purchase", "scraped_at",
    ]

    total_products = 0
    total_reviews = 0
    now_str = datetime.now().isoformat(timespec="seconds")

    with (
        open(PRODUCTS_CSV, "w", newline="", encoding="utf-8") as pf,
        open(REVIEWS_CSV, "w", newline="", encoding="utf-8") as rf,
    ):
        product_writer = csv.DictWriter(pf, fieldnames=product_fieldnames)
        review_writer = csv.DictWriter(rf, fieldnames=review_fieldnames)
        product_writer.writeheader()
        review_writer.writeheader()

        for brand, profile in BRAND_PROFILES.items():
            templates = PRODUCT_TEMPLATES[brand][:products_per_brand]
            asin_pool = [_random_asin() for _ in templates]

            reviews_written = 0

            for i, (title, size, category) in enumerate(templates):
                asin = asin_pool[i]
                price_low, price_high = profile["price_range"]
                price = round(random.uniform(price_low, price_high), -1)  # round to 10s
                mrp_mult = random.uniform(*profile["mrp_multiplier"])
                mrp = round(price * mrp_mult, -1)
                discount_pct = round(((mrp - price) / mrp) * 100, 1)

                avg_r = profile["avg_rating"]
                rating = round(min(5.0, max(1.0, random.gauss(avg_r, 0.2))), 1)
                review_count = random.randint(120, 4500)

                product_writer.writerow({
                    "brand": brand,
                    "asin": asin,
                    "title": title,
                    "price": price,
                    "mrp": mrp,
                    "discount_pct": discount_pct,
                    "rating": rating,
                    "review_count": review_count,
                    "url": f"https://www.amazon.in/dp/{asin}",
                    "scraped_at": now_str,
                })
                total_products += 1

                # Distribute reviews across products
                reviews_for_this = reviews_per_brand // products_per_brand
                if i < (reviews_per_brand % products_per_brand):
                    reviews_for_this += 1

                for _ in range(reviews_for_this):
                    is_positive = random.random() < profile["positive_bias"]

                    # Skybags anomaly: even positive reviewers mention zipper issues
                    review_body = _pick_review(profile, is_positive)
                    if brand == "Skybags" and not is_positive and random.random() < 0.6:
                        zipper_note = random.choice(NEGATIVE_REVIEWS["zipper"])
                        review_body = zipper_note  # Force zipper complaint

                    r_rating = _generate_rating(profile, is_positive)
                    r_title = "Great product!" if is_positive else "Disappointing experience"

                    review_writer.writerow({
                        "brand": brand,
                        "asin": asin,
                        "product_title": title,
                        "reviewer_name": _random_reviewer(),
                        "review_date": _random_date(),
                        "review_rating": r_rating,
                        "review_title": r_title,
                        "review_body": review_body,
                        "verified_purchase": random.random() < 0.75,
                        "scraped_at": now_str,
                    })
                    reviews_written += 1
                    total_reviews += 1

            print(f"  [OK] {brand}: {len(templates)} products, {reviews_written} reviews generated.")

    return total_products, total_reviews


# --- CLI -------------------------------------------------------------------

if __name__ == "__main__":
    print("Generating mock data...")
    products, reviews = generate_mock_data()
    print(f"\nDone! {products} products and {reviews} reviews saved to {DATA_DIR}")
