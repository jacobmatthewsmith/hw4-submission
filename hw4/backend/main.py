"""Campus Customs API. Run from backend/:  uvicorn main:app --reload --port 8000

- Products: catalogue, inventory, and product images (Problem 3).
- Accounts: sign-up / login / logout with session cookies, see auth.py (Problem 4).
- Chat: the Pydantic AI shopping agent, see agent.py (Problem 5), with saved history for
  logged-in customers and page context, see chat_history.py (Problem 8).
- Saved carts, checkout with duplicate-order protection, similar items, and rate limits,
  see store.py and ratelimit.py (Problem 9).
"""

import logging
import secrets
from contextlib import asynccontextmanager

from fastapi import Cookie, FastAPI, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

import agent
import audit
import auth
import chat_history
import db
import ratelimit
import store
from models import (
    CartPayload,
    ChatRequest,
    ChatResponse,
    HistoryMessage,
    LoginRequest,
    OrderRequest,
    SignupRequest,
)

log = logging.getLogger("campus_customs")


@asynccontextmanager
async def lifespan(_: FastAPI):
    store.ensure_tables()  # cart/order tables; the provided tables are never altered
    yield


app = FastAPI(title="Campus Customs API", lifespan=lifespan)


@app.middleware("http")
async def visitor_cookie(request: Request, call_next):
    """Give anonymous visitors a random id cookie so rate limits apply per visitor, not per shared IP."""
    response = await call_next(request)
    if ratelimit.VISITOR_COOKIE not in request.cookies:
        response.set_cookie(
            ratelimit.VISITOR_COOKIE, secrets.token_hex(16), max_age=60 * 60 * 24 * 365, httponly=True, samesite="lax"
        )
    return response


def current_user(request: Request) -> dict | None:
    return auth.user_from_token(request.cookies.get(auth.SESSION_COOKIE))

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(RequestValidationError)
async def validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
    # FastAPI's default 422 echoes the request body back, which would include passwords.
    # Return only a readable message instead.
    messages = []
    for err in exc.errors():
        field = err["loc"][-1] if err["loc"] and err["loc"][-1] != "body" else None
        msg = err["msg"].removeprefix("Value error, ")
        messages.append(f"{str(field).replace('_', ' ').capitalize()}: {msg}" if field else msg)
    return JSONResponse(status_code=422, content={"detail": " ".join(messages)})


# Product images: catalogue.image_file_path "products/x.jpg" -> /media/products/x.jpg.
# Only the products folder is mounted so the database file is never served.
app.mount("/media/products", StaticFiles(directory=db.DATA_DIR / "products"), name="media")


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/api/products")
def products(request: Request, q: str | None = None) -> list[dict]:
    ratelimit.check("search", ratelimit.identity(request, current_user(request)), "That's a lot of searching!")
    return db.list_products(q)


@app.get("/api/products/{product_id}/similar")
def similar(product_id: str, limit: int = 8) -> list[dict]:
    found = db.similar_products(product_id, max(1, min(limit, 12)))
    if found is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return found


@app.get("/api/products/{product_id}")
def product(product_id: str) -> dict:
    found = db.get_product(product_id)
    if found is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return found


# --- Accounts ----------------------------------------------------------------

def _start_session(response: Response, user: dict) -> dict:
    response.set_cookie(
        auth.SESSION_COOKIE,
        auth.make_session_token(user["id"]),
        max_age=auth.SESSION_MAX_AGE,
        httponly=True,  # not readable from JavaScript
        samesite="lax",
        secure=False,  # localhost dev over http; set True when served over https
    )
    return user


@app.post("/api/auth/signup", status_code=201)
def signup(req: SignupRequest, response: Response) -> dict:
    try:
        user = auth.create_user(req.first_name, req.last_name, req.email, req.password)
    except auth.EmailTaken:
        raise HTTPException(status_code=409, detail="An account with that email already exists.")
    return _start_session(response, user)


@app.post("/api/auth/login")
def login(req: LoginRequest, request: Request, response: Response) -> dict:
    email, ip = auth.normalize_email(req.email), ratelimit.client_ip(request)
    ratelimit.check_login_allowed(email, ip)  # before any password hashing
    user = auth.authenticate(req.email, req.password)
    if user is None:
        ratelimit.record_login_failure(email, ip)
        raise HTTPException(status_code=401, detail="Incorrect email or password.")
    ratelimit.record_login_success(email)
    return _start_session(response, user)


@app.post("/api/auth/logout", status_code=204)
def logout(response: Response) -> None:
    response.delete_cookie(auth.SESSION_COOKIE)


@app.get("/api/auth/me")
def me(cc_session: str | None = Cookie(default=None)) -> dict | None:
    """The logged-in user, or null when there's no valid session."""
    return auth.user_from_token(cc_session)


# --- Chat --------------------------------------------------------------------

def _audit_who(identity: str) -> str:
    """Audit identity: user id for customers; anonymous visitors are just "guest" (no cookie ids in the file)."""
    return identity if identity.startswith("user:") else "guest"


@app.post("/api/chat")
async def chat(req: ChatRequest, request: Request) -> ChatResponse:
    # Who is chatting comes only from the signed session cookie. Logged-in customers get their
    # saved history from the database; guests use the history their browser sent.
    user = current_user(request)
    who = ratelimit.identity(request, user)
    try:
        # Rate limits are checked (on entering chat_slot) before any history loading or model call.
        with ratelimit.chat_slot(who):
            if user:
                history = chat_history.recent_turns(user["id"], agent.MAX_HISTORY_TURNS)
            else:
                history = req.history
            deps = agent.build_deps(user, req.page)
            try:
                response = await agent.chat(req.message, history, deps, who=_audit_who(who))
            except Exception as e:
                log.error("Agent run failed: %s", type(e).__name__)  # no conversation text in logs
                raise HTTPException(status_code=502, detail="The assistant hit a snag. Please try again in a moment.")
    except ratelimit.RateLimited:
        page = req.page.path if req.page else None
        audit.finish_run(audit.start_run(_audit_who(who), page, len(req.message)), "rate_limited")
        raise
    if user:
        chat_history.save_turn(user["id"], req.message, response)
    return response


@app.get("/api/chat/history")
def history(cc_session: str | None = Cookie(default=None)) -> list[HistoryMessage]:
    """The logged-in customer's saved chat. Guests get an empty list."""
    user = auth.user_from_token(cc_session)
    return chat_history.load_history(user["id"]) if user else []


# --- Cart and checkout (Problem 9) ---------------------------------------------------

def _require_user(request: Request) -> dict:
    user = current_user(request)
    if user is None:
        raise HTTPException(status_code=401, detail="Please log in first.")
    return user


@app.get("/api/cart")
def get_cart(request: Request) -> dict:
    """The logged-in customer's saved cart. Guests keep their cart in the browser."""
    user = current_user(request)
    return {"items": store.get_cart(user["id"]) if user else []}


@app.put("/api/cart")
def put_cart(payload: CartPayload, request: Request) -> dict:
    user = _require_user(request)
    return {"items": store.set_cart(user["id"], [i.model_dump() for i in payload.items])}


@app.post("/api/cart/merge")
def merge_cart(payload: CartPayload, request: Request) -> dict:
    """Right after login: add the guest cart from this browser to the account's saved cart."""
    user = _require_user(request)
    return {"items": store.merge_cart(user["id"], [i.model_dump() for i in payload.items])}


@app.post("/api/orders", status_code=201)
def place_order(req: OrderRequest, request: Request):
    user = current_user(request)
    ratelimit.check("checkout", ratelimit.identity(request, user), "Too many checkout attempts.")
    if user is None:
        raise HTTPException(status_code=401, detail="Please log in to place your order.")
    try:
        return store.place_order(user["id"], [i.model_dump() for i in req.items], req.confirm_duplicate)
    except store.DuplicateOrder as dup:
        return JSONResponse(
            status_code=409,
            content={
                "code": "duplicate_order",
                "detail": "You placed an identical order a few minutes ago. Did you mean to buy these items again?",
                "previous_order_id": dup.order_id,
                "previous_order_at": dup.created_at,
            },
        )
    except store.OutOfStock as e:
        raise HTTPException(status_code=409, detail="Some items no longer have enough stock: " + "; ".join(e.problems) + ".")
    except store.CartError as e:
        raise HTTPException(status_code=400, detail=str(e))
