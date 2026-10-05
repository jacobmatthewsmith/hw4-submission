"""Saved carts and orders (Problem 9).

New tables (created on startup if missing; the provided tables are not altered):
  cart_items(user_id, product_id, size, quantity, updated_at)   one row per cart line, logged-in users only
  orders(id, user_id, items_key, total, created_at)
  order_items(order_id, product_id, size, quantity, unit_price)

Guest carts live in the browser (localStorage); see frontend/src/cart.tsx.
"""

import hashlib
import json
import sqlite3
from datetime import datetime, timedelta, timezone

import db

MAX_LINE_QUANTITY = 10
MAX_CART_LINES = 50
DUPLICATE_WINDOW = timedelta(minutes=5)

SCHEMA = """
CREATE TABLE IF NOT EXISTS cart_items (
    user_id INTEGER NOT NULL,
    product_id TEXT NOT NULL,
    size TEXT NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (user_id, product_id, size),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (product_id) REFERENCES catalogue(product_id)
);
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    items_key TEXT NOT NULL,
    total REAL NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(id)
);
CREATE INDEX IF NOT EXISTS idx_orders_user_time ON orders (user_id, created_at);
CREATE TABLE IF NOT EXISTS order_items (
    order_id INTEGER NOT NULL,
    product_id TEXT NOT NULL,
    size TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price REAL NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id),
    FOREIGN KEY (product_id) REFERENCES catalogue(product_id)
);
"""


def ensure_tables() -> None:
    with db.connect() as conn:
        conn.executescript(SCHEMA)


class CartError(Exception):
    pass


class OutOfStock(Exception):
    def __init__(self, problems: list[str]):
        super().__init__("; ".join(problems))
        self.problems = problems


class DuplicateOrder(Exception):
    def __init__(self, order_id: int, created_at: str):
        super().__init__("duplicate order")
        self.order_id = order_id
        self.created_at = created_at


def _clean(items: list[dict]) -> list[dict]:
    """Validate cart lines against the catalogue and merge duplicates. Unknown products/sizes are dropped."""
    merged: dict[tuple[str, str], int] = {}
    with db.connect() as conn:
        valid = {(r["product_id"], r["size"]) for r in conn.execute("SELECT product_id, size FROM inventory")}
    for item in items:
        key = (item["product_id"], item["size"])
        if key in valid and item["quantity"] > 0:
            merged[key] = min(merged.get(key, 0) + item["quantity"], MAX_LINE_QUANTITY)
    lines = [{"product_id": p, "size": s, "quantity": q} for (p, s), q in merged.items()]
    return lines[:MAX_CART_LINES]


# --- Carts (logged-in users) ----------------------------------------------------

def get_cart(user_id: int) -> list[dict]:
    with db.connect() as conn:
        rows = conn.execute(
            "SELECT product_id, size, quantity FROM cart_items WHERE user_id = ? ORDER BY rowid", [user_id]
        ).fetchall()
    return [dict(r) for r in rows]


def set_cart(user_id: int, items: list[dict]) -> list[dict]:
    """Replace the user's saved cart with these lines."""
    lines = _clean(items)
    with db.connect() as conn:
        conn.execute("DELETE FROM cart_items WHERE user_id = ?", [user_id])
        conn.executemany(
            "INSERT INTO cart_items (user_id, product_id, size, quantity) VALUES (?, ?, ?, ?)",
            [(user_id, l["product_id"], l["size"], l["quantity"]) for l in lines],
        )
    return lines


def merge_cart(user_id: int, items: list[dict]) -> list[dict]:
    """Add a guest's cart to the user's saved cart (used right after logging in)."""
    return set_cart(user_id, get_cart(user_id) + items)


# --- Orders ---------------------------------------------------------------------

def items_key(lines: list[dict]) -> str:
    """Order-independent fingerprint of the items, used to spot identical repeat orders."""
    canonical = sorted((l["product_id"], l["size"], l["quantity"]) for l in lines)
    return hashlib.sha256(json.dumps(canonical).encode()).hexdigest()


def _recent_duplicate(conn: sqlite3.Connection, user_id: int, key: str) -> sqlite3.Row | None:
    since = (datetime.now(timezone.utc) - DUPLICATE_WINDOW).strftime("%Y-%m-%d %H:%M:%S")
    return conn.execute(
        "SELECT id, created_at FROM orders WHERE user_id = ? AND items_key = ? AND created_at >= ?"
        " ORDER BY id DESC LIMIT 1",
        [user_id, key, since],
    ).fetchone()


def place_order(user_id: int, items: list[dict], confirm_duplicate: bool = False) -> dict:
    """Place an order: check for an identical order in the last 5 minutes, check stock, charge
    catalogue prices, decrement inventory, and clear the saved cart, all in one transaction."""
    lines = _clean(items)
    if not lines:
        raise CartError("Your cart is empty.")
    key = items_key(lines)
    conn = db.connect()
    try:
        conn.execute("BEGIN IMMEDIATE")  # serialize orders so two clicks can't both pass the checks
        if not confirm_duplicate:
            dup = _recent_duplicate(conn, user_id, key)
            if dup is not None:
                raise DuplicateOrder(dup["id"], dup["created_at"])

        problems, priced = [], []
        for l in lines:
            row = conn.execute(
                "SELECT c.name, c.price, i.quantity AS stock FROM catalogue c JOIN inventory i USING (product_id)"
                " WHERE c.product_id = ? AND i.size = ?",
                [l["product_id"], l["size"]],
            ).fetchone()
            if row["stock"] < l["quantity"]:
                problems.append(
                    f"{row['name']} ({l['size']}): only {row['stock']} left" if row["stock"] else f"{row['name']} ({l['size']}) is sold out"
                )
            priced.append({**l, "name": row["name"], "unit_price": row["price"]})
        if problems:
            raise OutOfStock(problems)

        total = round(sum(p["unit_price"] * p["quantity"] for p in priced), 2)
        cur = conn.execute("INSERT INTO orders (user_id, items_key, total) VALUES (?, ?, ?)", [user_id, key, total])
        order_id = cur.lastrowid
        for p in priced:
            conn.execute(
                "INSERT INTO order_items (order_id, product_id, size, quantity, unit_price) VALUES (?, ?, ?, ?, ?)",
                [order_id, p["product_id"], p["size"], p["quantity"], p["unit_price"]],
            )
            conn.execute(
                "UPDATE inventory SET quantity = quantity - ? WHERE product_id = ? AND size = ?",
                [p["quantity"], p["product_id"], p["size"]],
            )
        conn.execute("DELETE FROM cart_items WHERE user_id = ?", [user_id])
        created_at = conn.execute("SELECT created_at FROM orders WHERE id = ?", [order_id]).fetchone()[0]
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
    return {"order_id": order_id, "total": total, "created_at": created_at, "items": priced}
