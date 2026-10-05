"""Tools the Campus Customs agent can call. Every answer about price or stock comes from here,
read live from the SQLite database, never from the model's memory."""

import re

from pydantic_ai import RunContext

import db
from audit import audited
from models import (
    ChatDeps,
    CurrentPage,
    CustomerProfile,
    ProductInfo,
    ProductMatch,
    SizeStockStatus,
    StockReport,
    stock_status,
)

# Shopper words -> words that appear in the catalogue.
SYNONYMS = {
    "tee": "t-shirt",
    "tees": "t-shirt",
    "tshirt": "t-shirt",
    "shirt": "t-shirt",
    "hoody": "hoodie",
    "hoodies": "hoodie",
    "sweatshirt": "sweatshirt",
    "crew": "crewneck",
    "quarterzip": "quarter-zip",
    "1/4": "quarter-zip",
    "grey": "gray",
    "coat": "jacket",
    "fleece": "fleece",
}
STOPWORDS = {
    "a", "an", "and", "any", "do", "for", "have", "i", "in", "is", "me", "my", "of", "on", "or",
    "show", "some", "the", "to", "with", "you", "your", "what", "which", "something", "want",
    "looking", "need", "got", "size", "sizes", "stock", "available", "campus", "customs",
}
SIZES = ["XS", "S", "M", "L", "XL", "XXL"]
SIZE_ALIASES = {
    "extra small": "XS", "x-small": "XS", "xsmall": "XS", "small": "S", "sm": "S",
    "medium": "M", "med": "M", "large": "L", "lg": "L",
    "extra large": "XL", "x-large": "XL", "xlarge": "XL",
    "2xl": "XXL", "xx-large": "XXL", "xxlarge": "XXL", "extra extra large": "XXL",
}
MAX_CANDIDATES = 6


def _normalize_size(size: str | None) -> str | None:
    if not size or not size.strip():
        return None
    s = size.strip().lower()
    return SIZE_ALIASES.get(s, s.upper())


def _terms(text: str) -> list[str]:
    words = re.findall(r"[a-z0-9/'-]+", text.lower())
    terms = []
    for w in words:
        if w in STOPWORDS:
            continue
        w = SYNONYMS.get(w, w)
        if len(w) > 3 and w.endswith("s") and not w.endswith("ss"):
            w = w[:-1]  # crude plural -> singular ("crewnecks" -> "crewneck")
        terms.append(w)
    return terms


def _match(p: dict) -> ProductMatch:
    return ProductMatch(
        product_id=p["product_id"],
        name=p["name"],
        garment_type=p["garment_type"],
        colors=p["colors"],
        price=p["price"],
        sizes_in_stock=[s["size"] for s in p["inventory"] if s["quantity"] > 0],
        sizes_sold_out=[s["size"] for s in p["inventory"] if s["quantity"] <= 0],
        total_stock=p["total_stock"],
    )


def _strong_text(p: dict) -> str:
    return " ".join([p["name"], p["garment_type"], *p["search_tags"], *p["colors"]]).lower()


def _resolve(product: str) -> tuple[str, dict | None, list[dict]]:
    """Turn a product_id or a shopper's wording into exactly one product, or say why not.

    Returns (status, product, candidates) where status is "found", "ambiguous", or "not_found".
    Never guesses: if several products fit equally well, the caller must ask the shopper.
    """
    text = product.strip()
    if not text:
        return "not_found", None, []
    exact = db.get_product(text)
    if exact is not None:
        return "found", exact, []

    products = db.list_products()
    norm = lambda x: re.sub(r"[^a-z0-9]+", " ", x.lower()).strip()
    by_name = [p for p in products if norm(p["name"]) == norm(text) or norm(p["product_id"]) == norm(text)]
    if len(by_name) == 1:
        return "found", by_name[0], []

    terms = _terms(text)
    if not terms:
        return "not_found", None, []
    # Candidates must match every meaningful word the shopper used.
    candidates = [p for p in products if all(t in _strong_text(p) for t in terms)]
    if len(candidates) == 1:
        return "found", candidates[0], []
    in_name = [p for p in candidates if all(t in p["name"].lower() for t in terms)]
    if len(in_name) == 1:
        return "found", in_name[0], []
    if candidates:
        return "ambiguous", None, candidates[:MAX_CANDIDATES]
    return "not_found", None, []


def search_products(
    query: str = "",
    garment_type: str | None = None,
    color: str | None = None,
    max_price: float | None = None,
    in_stock_size: str | None = None,
    limit: int = 8,
) -> list[ProductMatch]:
    """Search the Campus Customs catalogue to find products. Returns candidates with live price and which sizes
    are in stock vs sold out. Use get_product_info / check_stock for full details on one item.

    Args:
        query: Free-text keywords, e.g. "hockey", "vintage bulldog", "Berkeley college", "Harvard Yale game".
            Leave empty to browse using only the filters.
        garment_type: Optional loose type filter, e.g. "hoodie", "crewneck", "quarter-zip", "t-shirt", "jacket".
        color: Optional color filter, e.g. "navy", "gray", "white".
        max_price: Optional highest price in dollars.
        in_stock_size: Optional size (XS, S, M, L, XL, XXL); only return products with that size in stock.
        limit: Max results to return (1-30). Use a higher limit (e.g. 30) when the shopper wants to browse a whole category.
    """
    limit = max(1, min(limit, 30))
    terms = _terms(query)
    type_terms = _terms(garment_type or "")
    color_l = (color or "").lower().strip()
    size = _normalize_size(in_stock_size)

    scored: list[tuple[float, dict]] = []
    for p in db.list_products():
        gtype = p["garment_type"].lower()
        if type_terms and not all(t.replace("-", "") in gtype.replace("-", "") for t in type_terms):
            continue
        if color_l and not any(color_l in c.lower() for c in p["colors"]):
            continue
        if max_price is not None and p["price"] > max_price:
            continue
        if size and not any(s["size"] == size and s["quantity"] > 0 for s in p["inventory"]):
            continue

        score = 0.0
        if terms:
            strong = _strong_text(p)
            weak = p["description"].lower()
            for t in terms:
                if t in strong:
                    score += 2
                elif t in weak:
                    score += 1
            if score == 0:
                continue
        scored.append((score, p))

    scored.sort(key=lambda sp: (-sp[0], sp[1]["name"]))
    return [_match(p) for _, p in scored[:limit]]


def get_product_info(product: str) -> ProductInfo:
    """Get the description, colors, and price of ONE product. Use for "what is it like?", "what does it cost?",
    "what colors?" questions.

    Args:
        product: A product_id from search results (preferred), or the product name as the shopper said it.
    """
    status, p, candidates = _resolve(product)
    if status == "not_found":
        return ProductInfo(lookup="not_found", message=f"No product in the catalogue matches '{product}'.")
    if status == "ambiguous":
        return ProductInfo(
            lookup="ambiguous",
            message=f"'{product}' matches {len(candidates)} products. Ask the shopper which one they mean.",
            candidates=[_match(c) for c in candidates],
        )
    assert p is not None
    return ProductInfo(
        lookup="found",
        message="Found.",
        product_id=p["product_id"],
        name=p["name"],
        garment_type=p["garment_type"],
        description=p["description"],
        colors=p["colors"],
        price=p["price"],
    )


def check_stock(product: str, size: str | None = None) -> StockReport:
    """Check live inventory for ONE product, by size. Use for every "is it in stock?", "how many are left?",
    or "do you have it in a medium?" question.

    Args:
        product: A product_id from search results (preferred), or the product name as the shopper said it.
        size: Optional size the shopper asked about: XS, S, M, L, XL, XXL (words like "medium" also work).
    """
    status, p, candidates = _resolve(product)
    if status == "not_found":
        return StockReport(lookup="not_found", message=f"No product in the catalogue matches '{product}'.")
    if status == "ambiguous":
        return StockReport(
            lookup="ambiguous",
            message=f"'{product}' matches {len(candidates)} products. Ask the shopper which one they mean.",
            candidates=[_match(c) for c in candidates],
        )
    assert p is not None
    sizes = [SizeStockStatus(size=s["size"], quantity=s["quantity"], status=stock_status(s["quantity"])) for s in p["inventory"]]
    report = StockReport(
        lookup="found",
        message="Found.",
        product_id=p["product_id"],
        name=p["name"],
        price=p["price"],
        sizes=sizes,
        total_stock=p["total_stock"],
    )
    wanted = _normalize_size(size)
    if wanted:
        report.requested_size = wanted
        row = next((s for s in sizes if s.size == wanted), None)
        if row is None:
            report.requested_size_status = "size_not_offered"
            report.message = f"{p['name']} does not come in size {wanted}. Offered sizes: {', '.join(s.size for s in sizes)}."
        else:
            report.requested_size_status = row.status
            report.requested_size_quantity = row.quantity
            report.message = (
                f"{p['name']} is SOLD OUT in {wanted} (0 units)."
                if row.status == "sold_out"
                else f"{p['name']} has {row.quantity} in stock in {wanted}."
            )
    return report


def catalogue_overview() -> dict:
    """Summarize what Campus Customs carries: product types with counts and price ranges, and the sizes offered.
    Use for broad questions like "what do you sell?" or "what's your cheapest item?"."""
    products = db.list_products()
    by_type: dict[str, list[float]] = {}
    for p in products:
        by_type.setdefault(p["garment_type"].lower(), []).append(p["price"])
    return {
        "total_products": len(products),
        "sizes_offered": SIZES,
        "price_range": [min(p["price"] for p in products), max(p["price"] for p in products)],
        "types": {t: {"count": len(prices), "min_price": min(prices), "max_price": max(prices)} for t, prices in sorted(by_type.items())},
    }


def get_customer_profile(ctx: RunContext[ChatDeps]) -> CustomerProfile:
    """Who is chatting: the logged-in customer's name and email, or logged_in=false for a guest.
    Use when the shopper asks "who am I?", "what's my email?", or anything about their account details."""
    c = ctx.deps.customer
    if c is None:
        return CustomerProfile(logged_in=False)
    return CustomerProfile(logged_in=True, name=c.name, email=c.email)


def get_current_page(ctx: RunContext[ChatDeps]) -> CurrentPage:
    """What the shopper is looking at right now. On a product page, returns that exact item's description, price,
    colors, and live stock by size. Call this whenever the shopper says "this", "it", "this one", or asks about
    "the item I'm looking at" without naming a product."""
    deps = ctx.deps
    if deps.page_product is None:
        return CurrentPage(
            path=deps.page_path,
            on_product_page=False,
            message="The shopper is not on a product page, so 'this item' is unknown. Ask which item they mean.",
        )
    pid = deps.page_product.product_id
    return CurrentPage(
        path=deps.page_path,
        on_product_page=True,
        message=f"The shopper is viewing the product page for {deps.page_product.name} (product_id {pid}).",
        product=get_product_info(pid),
        stock=check_stock(pid),
    )


# Each tool is wrapped so its calls land in output/audit_trail.json (see audit.py).
TOOLS = [
    audited(t)
    for t in (
        search_products,
        get_product_info,
        check_stock,
        catalogue_overview,
        get_customer_profile,
        get_current_page,
    )
]
