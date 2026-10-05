"""Pydantic types shared by the API, the agent, and its tools."""

from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, model_validator


# --- Products ----------------------------------------------------------------

class SizeStock(BaseModel):
    size: str
    quantity: int


class ProductCard(BaseModel):
    """A product as shown on the site and in chat. Always built from the database."""

    product_id: str
    name: str
    garment_type: str
    description: str
    colors: list[str]
    image_url: str
    price: float
    inventory: list[SizeStock]
    total_stock: int


# --- Tool results (what the agent sees) ---------------------------------------
# Status fields are explicit strings so the model never has to infer "sold out" from a 0.

LOW_STOCK_THRESHOLD = 5

StockStatus = Literal["in_stock", "low_stock", "sold_out"]
LookupStatus = Literal["found", "ambiguous", "not_found"]


def stock_status(quantity: int) -> StockStatus:
    if quantity <= 0:
        return "sold_out"
    return "low_stock" if quantity <= LOW_STOCK_THRESHOLD else "in_stock"


class ProductMatch(BaseModel):
    """A lightweight candidate, used for search results and to list options when a lookup is ambiguous."""

    product_id: str
    name: str
    garment_type: str
    colors: list[str]
    price: float
    sizes_in_stock: list[str] = Field(description="Sizes with at least 1 unit.")
    sizes_sold_out: list[str] = Field(description="Sizes the item comes in but with 0 units right now.")
    total_stock: int


class SizeStockStatus(BaseModel):
    size: str
    quantity: int
    status: StockStatus


class ProductInfo(BaseModel):
    """Description and price for one product (get_product_info)."""

    lookup: LookupStatus
    message: str = Field(description="Plain-language note on the lookup, e.g. why it was ambiguous.")
    product_id: str | None = None
    name: str | None = None
    garment_type: str | None = None
    description: str | None = None
    colors: list[str] = Field(default_factory=list)
    price: float | None = None
    candidates: list[ProductMatch] = Field(default_factory=list, description="Options to ask the shopper about when ambiguous.")


class StockReport(BaseModel):
    """Live per-size inventory for one product (check_stock)."""

    lookup: LookupStatus
    message: str
    product_id: str | None = None
    name: str | None = None
    price: float | None = None
    requested_size: str | None = None
    requested_size_status: StockStatus | Literal["size_not_offered"] | None = Field(
        default=None, description="Status of the size the shopper asked about, if any."
    )
    requested_size_quantity: int | None = None
    sizes: list[SizeStockStatus] = Field(default_factory=list, description="Every size, smallest to largest.")
    total_stock: int | None = None
    candidates: list[ProductMatch] = Field(default_factory=list)


# --- Chat --------------------------------------------------------------------

class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(max_length=4000)


class PageContext(BaseModel):
    """Where the shopper is on the site. Only the path is sent; the backend works out the product itself."""

    path: str = Field(max_length=300, description='Current URL path, e.g. "/products/basic-hoodie-big-yale".')


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=500)
    history: list[ChatTurn] = Field(
        default_factory=list,
        description="Earlier turns, oldest first. Only used for guests; logged-in history comes from the database.",
    )
    page: PageContext | None = None


class PageResults(BaseModel):
    """Product matches the website renders as cards on the page, as if the shopper had searched."""

    title: str = Field(description='Short heading for the results, e.g. "Navy hoodies under $70".')
    products: list[ProductCard]


class ChatResponse(BaseModel):
    """API contract for POST /api/chat. `results` is null when the turn has no products to show
    (greetings, follow-up questions, refusals), so the page keeps whatever it was showing."""

    reply: str
    results: PageResults | None = None
    stopped_early: bool = Field(default=False, description="True when the turn hit its budget and asks the shopper to rephrase.")


class HistoryMessage(BaseModel):
    """One saved chat message, as returned by GET /api/chat/history."""

    role: Literal["user", "assistant"]
    content: str
    results: PageResults | None = None
    created_at: str


class AgentReply(BaseModel):
    """The agent's structured output. The API turns product_ids into ProductCards from the
    database, so prices and stock shown to shoppers never come from the model's memory."""

    reply: str = Field(description="The message to show the shopper, in the Campus Customs voice. Plain text, no markdown.")
    product_ids: list[str] = Field(
        default_factory=list,
        description="product_id values (from tool results) of every item that matches the shopper's request, "
        "most relevant first, max 30. The website shows them as product cards on the page. "
        "Empty if no specific products are relevant.",
    )
    results_title: str = Field(
        default="",
        description='Short heading (2-6 words) describing product_ids for the page, e.g. "Navy hoodies in size L". '
        "Empty when product_ids is empty.",
    )
    on_topic: bool = Field(description="False if the shopper's message was not about Campus Customs or its merch.")


# --- Agent context (deps) ----------------------------------------------------

class Customer(BaseModel):
    """The customer fields the agent is allowed to see. Deliberately just name and email."""

    name: str
    email: str


class PageProduct(BaseModel):
    product_id: str
    name: str


@dataclass
class ChatDeps:
    """Per-request context handed to the agent (Pydantic AI `deps`).

    customer: the logged-in shopper, or None for guests.
    page_path: the path the shopper is on.
    page_product: the product on that page, looked up in the database from the path, or None.
    """

    customer: Customer | None
    page_path: str | None
    page_product: PageProduct | None


class CustomerProfile(BaseModel):
    logged_in: bool
    name: str | None = None
    email: str | None = None


class CurrentPage(BaseModel):
    """What the shopper is looking at (get_current_page). Product facts come from the database."""

    path: str | None
    on_product_page: bool
    message: str
    product: ProductInfo | None = None
    stock: StockReport | None = None


# --- Accounts ----------------------------------------------------------------

class SignupRequest(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    confirm_password: str

    @model_validator(mode="after")
    def passwords_match(self) -> "SignupRequest":
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
        if not self.first_name.strip() or not self.last_name.strip():
            raise ValueError("First and last name are required")
        return self


class LoginRequest(BaseModel):
    email: str
    password: str


# --- Cart and orders (Problem 9) ------------------------------------------------

class CartLine(BaseModel):
    product_id: str = Field(max_length=200)
    size: str = Field(max_length=10)
    quantity: int = Field(ge=1, le=10)


class CartPayload(BaseModel):
    items: list[CartLine] = Field(max_length=50)


class OrderRequest(BaseModel):
    items: list[CartLine] = Field(min_length=1, max_length=50)
    confirm_duplicate: bool = Field(
        default=False, description="Set true after the shopper confirms they really want to repeat a recent identical order."
    )
