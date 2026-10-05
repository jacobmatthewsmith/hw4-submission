"""Campus Customs shopping agent: model + system prompt + tools, wired with Pydantic AI.

The model is OpenAI gpt-5.6-sol, reached through Portkey's OpenAI-compatible gateway.
The system prompt is read from prompts/prompt.md at startup. Per-request context (who is chatting and which
page they're on) travels in ChatDeps and is added to the instructions by session_context() below.
"""

import asyncio
import logging
import os
import re
from pathlib import Path
from urllib.parse import unquote

from pydantic_ai import Agent, RunContext, UsageLimits
from pydantic_ai.exceptions import ModelHTTPError, UnexpectedModelBehavior, UsageLimitExceeded
from pydantic_ai.messages import ModelMessage, ModelRequest, ModelResponse, TextPart, UserPromptPart
from pydantic_ai.models.openai import OpenAIResponsesModel, OpenAIResponsesModelSettings
from pydantic_ai.providers.openai import OpenAIProvider

import audit
import db
from models import (
    AgentReply,
    ChatDeps,
    ChatResponse,
    ChatTurn,
    Customer,
    PageContext,
    PageProduct,
    PageResults,
    ProductCard,
)
from tools import TOOLS

HERE = Path(__file__).resolve().parent
PROMPT_PATH = HERE / "prompts" / "prompt.md"
MODEL_NAME = "gpt-5.6-sol"
PORTKEY_BASE_URL = "https://api.portkey.ai/v1"

MAX_HISTORY_TURNS = 12  # earlier chat turns sent back to the model for context
MAX_PAGE_RESULTS = 30  # product cards sent to the page per turn

# --- Budget per chat turn (Problem 9): stop the agent if it works harder than a normal answer needs ---
# A normal turn is 2-3 model requests (look something up, then answer) and 1-3 tool calls.
MAX_ATTEMPTS = 3  # tries at producing a valid structured answer (1 + 2 retries)
USAGE_LIMITS = UsageLimits(
    request_limit=6,  # model round-trips per turn
    tool_calls_limit=6,  # tool calls per turn
    total_tokens_limit=60_000,  # input + output tokens per turn
)
TURN_TIMEOUT_SECONDS = 45
MODEL_SETTINGS = OpenAIResponsesModelSettings(openai_reasoning_effort="low", timeout=30)
# Sent when the model provider's own safety filter blocks a message (e.g. prompt-injection attempts).
FILTERED_REPLY = "That one's outside my lane. I only help with Campus Customs merch! Want help finding a hoodie instead?"
REPHRASE_REPLY = (
    "Sorry, I got a little tangled up on that one. Could you ask it a different way? "
    "For example, name the item and the size you're interested in."
)

log = logging.getLogger("campus_customs.agent")

# The key lives in a .env outside the repo (see db.load_env and .env.example); never committed.
db.load_env()
_api_key = os.getenv("PORTKEY_API_KEY")
if not _api_key:
    raise RuntimeError("PORTKEY_API_KEY is missing. Copy .env.example to hw4/.env (or a folder above it) and fill it in.")

model = OpenAIResponsesModel(MODEL_NAME, provider=OpenAIProvider(api_key=_api_key, base_url=PORTKEY_BASE_URL))

agent = Agent(
    model,
    name="campus-customs-shopping-assistant",
    instructions=PROMPT_PATH.read_text(encoding="utf-8"),
    deps_type=ChatDeps,
    output_type=AgentReply,
    tools=TOOLS,
    retries=MAX_ATTEMPTS - 1,
    model_settings=MODEL_SETTINGS,
)

PRODUCT_PAGE = re.compile(r"/products/([^/?#]+)/?")


@agent.instructions
def session_context(ctx: RunContext[ChatDeps]) -> str:
    """Appended to prompt.md on every run: who is chatting and what page they're on."""
    deps = ctx.deps
    lines = ["## This session"]
    if deps.customer:
        first = deps.customer.name.split()[0] if deps.customer.name.strip() else deps.customer.name
        lines.append(
            f"- Customer: logged in as {deps.customer.name} ({deps.customer.email}). "
            f"Their first name is {first}."
        )
    else:
        lines.append("- Customer: a guest (not logged in). You don't know their name; don't guess or ask for it.")
    if deps.page_product:
        lines.append(
            f'- Page: the shopper is viewing the product page for "{deps.page_product.name}" '
            f"(product_id {deps.page_product.product_id}). \"This\", \"it\", or \"this one\" means this item."
        )
    else:
        lines.append(f"- Page: {deps.page_path or 'unknown'} (not a single-product page).")
    return "\n".join(lines)


def build_deps(user: dict | None, page: PageContext | None) -> ChatDeps:
    """Build the agent's context. The page's product is looked up in the database from the URL path,
    so the agent can only ever be told about a real item, and always the one actually on screen."""
    customer = Customer(name=user["name"], email=user["email"]) if user else None
    path = page.path if page else None
    page_product = None
    if path and (m := PRODUCT_PAGE.fullmatch(path)):
        product = db.get_product(unquote(m.group(1)))
        if product is not None:
            page_product = PageProduct(product_id=product["product_id"], name=product["name"])
    return ChatDeps(customer=customer, page_path=path, page_product=page_product)


def _history_to_messages(history: list[ChatTurn]) -> list[ModelMessage]:
    messages: list[ModelMessage] = []
    for turn in history[-MAX_HISTORY_TURNS:]:
        if turn.role == "user":
            messages.append(ModelRequest(parts=[UserPromptPart(content=turn.content)]))
        else:
            messages.append(ModelResponse(parts=[TextPart(content=turn.content)]))
    return messages


def product_cards(product_ids: list[str]) -> list[ProductCard]:
    """Look up each id in the database; unknown ids (model mistakes) are dropped."""
    cards: list[ProductCard] = []
    for pid in dict.fromkeys(product_ids):  # de-duplicate, keep order
        product = db.get_product(pid)
        if product is not None:
            cards.append(ProductCard.model_validate(product))
        if len(cards) == MAX_PAGE_RESULTS:
            break
    return cards


STOP_REASONS = {UsageLimitExceeded: "usage_limit", TimeoutError: "timeout", UnexpectedModelBehavior: "out_of_attempts"}


async def chat(message: str, history: list[ChatTurn], deps: ChatDeps, who: str = "guest") -> ChatResponse:
    record = audit.start_run(who, deps.page_path, len(message))
    try:
        result = await asyncio.wait_for(
            agent.run(message, message_history=_history_to_messages(history), deps=deps, usage_limits=USAGE_LIMITS),
            timeout=TURN_TIMEOUT_SECONDS,
        )
    except (UsageLimitExceeded, UnexpectedModelBehavior, TimeoutError) as e:
        # Over budget, stuck in a loop, out of answer attempts, or too slow: stop and ask to rephrase.
        # Only the error type is logged, never the conversation.
        log.warning("Chat turn stopped early: %s", type(e).__name__)
        reason = next(r for t, r in STOP_REASONS.items() if isinstance(e, t))
        audit.finish_run(record, reason, error=type(e).__name__, reply_kind="rephrase")
        return ChatResponse(reply=REPHRASE_REPLY, stopped_early=True)
    except ModelHTTPError as e:
        if "content_filter" in str(e.body):
            # The provider's safety filter rejected the request: answer with the standard refusal, not an error.
            audit.finish_run(record, "content_filtered", error="content_filter", reply_kind="refusal")
            return ChatResponse(reply=FILTERED_REPLY)
        audit.finish_run(record, "error", error=type(e).__name__)
        raise
    except Exception as e:
        audit.finish_run(record, "error", error=type(e).__name__)
        raise
    out = result.output
    usage = result.usage
    cards = product_cards(out.product_ids) if out.on_topic else []
    audit.finish_run(
        record,
        "completed" if out.on_topic else "refused_off_topic",
        model_requests=usage.requests,
        tokens={"input": usage.input_tokens, "output": usage.output_tokens},
        products_shown=len(cards),
        results_title=out.results_title or None,
    )
    if not cards:
        return ChatResponse(reply=out.reply)
    title = out.results_title.strip() or "From your chat"
    return ChatResponse(reply=out.reply, results=PageResults(title=title, products=cards))
