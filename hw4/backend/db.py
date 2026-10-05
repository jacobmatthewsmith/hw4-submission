"""Read-only helpers for the Campus Customs SQLite database."""

import json
import os
import sqlite3
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
DB_PATH = Path(os.getenv("CC_DB_PATH", DATA_DIR / "campus_customs.db"))  # override for tests

SIZE_ORDER = ["XS", "S", "M", "L", "XL", "XXL"]


def load_env() -> None:
    """Load secrets from the first .env found: hw4/.env, then up to two folders above it
    (so the real key can live outside the git repo). Existing environment variables win."""
    for folder in [ROOT, *ROOT.parents[:2]]:
        load_dotenv(folder / ".env")


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _product_from_row(row: sqlite3.Row) -> dict:
    return {
        "product_id": row["product_id"],
        "name": row["name"],
        "garment_type": row["garment_type"],
        "description": row["description"],
        "colors": json.loads(row["colors"]),
        "search_tags": json.loads(row["search_tags"]),
        "image_url": f"/media/{row['image_file_path']}",
        "price": row["price"],
    }


def _inventory(conn: sqlite3.Connection, product_ids: list[str]) -> dict[str, list[dict]]:
    if not product_ids:
        return {}
    placeholders = ",".join("?" * len(product_ids))
    rows = conn.execute(
        f"SELECT product_id, size, quantity FROM inventory WHERE product_id IN ({placeholders})",
        product_ids,
    ).fetchall()
    by_product: dict[str, list[dict]] = {pid: [] for pid in product_ids}
    for r in rows:
        by_product[r["product_id"]].append({"size": r["size"], "quantity": r["quantity"]})
    for sizes in by_product.values():
        sizes.sort(key=lambda s: SIZE_ORDER.index(s["size"]) if s["size"] in SIZE_ORDER else 99)
    return by_product


def _with_inventory(conn: sqlite3.Connection, products: list[dict]) -> list[dict]:
    inventory = _inventory(conn, [p["product_id"] for p in products])
    for p in products:
        p["inventory"] = inventory.get(p["product_id"], [])
        p["total_stock"] = sum(s["quantity"] for s in p["inventory"])
    return products


def list_products(query: str | None = None) -> list[dict]:
    sql = "SELECT * FROM catalogue"
    params: list[str] = []
    if query:
        like = f"%{query.lower()}%"
        sql += (
            " WHERE lower(name) LIKE ? OR lower(garment_type) LIKE ?"
            " OR lower(description) LIKE ? OR lower(colors) LIKE ? OR lower(search_tags) LIKE ?"
        )
        params = [like] * 5
    sql += " ORDER BY name"
    with connect() as conn:
        products = [_product_from_row(r) for r in conn.execute(sql, params)]
        return _with_inventory(conn, products)


def get_product(product_id: str) -> dict | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM catalogue WHERE product_id = ?", [product_id]).fetchone()
        if row is None:
            return None
        return _with_inventory(conn, [_product_from_row(row)])[0]


# Same loose categories as frontend/src/categories.ts (garment_type values are inconsistent).
CATEGORIES = [
    ("hoodie", ["hood"]),
    ("crewneck", ["crewneck", "crew-neck sweat", "mockneck", "raglan"]),
    ("quarter-zip", ["quarter-zip"]),
    ("t-shirt", ["t-shirt", "performance shirt"]),
    ("jacket", ["jacket"]),
]
GENERIC_TAGS = {"yale", "campus customs", "college apparel", "yale merch", "college merch"}


def category_of(product: dict) -> str | None:
    gtype = product["garment_type"].lower()
    return next((key for key, words in CATEGORIES if any(w in gtype for w in words)), None)


def similar_products(product_id: str, limit: int = 8) -> list[dict] | None:
    """Products most like this one: same category, shared tags/colors, similar price. In-stock items first.
    Returns None if the product doesn't exist."""
    products = list_products()
    target = next((p for p in products if p["product_id"] == product_id), None)
    if target is None:
        return None
    t_cat = category_of(target)
    t_tags = {t.lower() for t in target["search_tags"]} - GENERIC_TAGS
    t_colors = {c.lower() for c in target["colors"]}

    def score(p: dict) -> float:
        s = 0.0
        if category_of(p) == t_cat:
            s += 5
        s += 1.5 * len(t_tags & ({t.lower() for t in p["search_tags"]} - GENERIC_TAGS))
        s += 1.0 * len(t_colors & {c.lower() for c in p["colors"]})
        s -= abs(p["price"] - target["price"]) / 20  # $20 apart costs one point
        if p["total_stock"] == 0:
            s -= 10
        return s

    others = [p for p in products if p["product_id"] != product_id]
    others.sort(key=lambda p: (-score(p), p["name"]))
    return others[:limit]
