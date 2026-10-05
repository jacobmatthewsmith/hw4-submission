"""Saved chat history for logged-in customers, in the existing `chat_messages` table.

Every query is filtered by user_id, and the user_id always comes from the verified session cookie
(never from the request body), so a customer only ever reads or writes their own history.

products_json stores which products a reply showed, as {"title": ..., "product_ids": [...]}.
Cards are rebuilt from the database when history is loaded, so old messages show current price and stock.
The seed rows use an older format (a JSON array of full product objects); both are read.
"""

import json

import db
from agent import product_cards
from models import ChatResponse, ChatTurn, HistoryMessage, PageResults

HISTORY_LIMIT = 100  # most recent messages reloaded into the chat panel


def save_turn(user_id: int, user_message: str, response: ChatResponse) -> None:
    """Save the shopper's message and the assistant's reply together (one transaction)."""
    products_json = None
    if response.results:
        products_json = json.dumps(
            {"title": response.results.title, "product_ids": [p.product_id for p in response.results.products]}
        )
    with db.connect() as conn:
        conn.execute(
            "INSERT INTO chat_messages (user_id, role, content) VALUES (?, 'user', ?)", [user_id, user_message]
        )
        conn.execute(
            "INSERT INTO chat_messages (user_id, role, content, products_json) VALUES (?, 'assistant', ?, ?)",
            [user_id, response.reply, products_json],
        )


def _results(products_json: str | None) -> PageResults | None:
    if not products_json:
        return None
    try:
        data = json.loads(products_json)
    except json.JSONDecodeError:
        return None
    if isinstance(data, dict):  # current format
        title, ids = data.get("title") or "From your chat", data.get("product_ids") or []
    elif isinstance(data, list):  # seed format: list of product objects
        title, ids = "From your chat", [p.get("product_id") for p in data if isinstance(p, dict)]
    else:
        return None
    cards = product_cards([i for i in ids if isinstance(i, str)])
    return PageResults(title=title, products=cards) if cards else None


def _rows(user_id: int, limit: int) -> list:
    with db.connect() as conn:
        rows = conn.execute(
            "SELECT role, content, products_json, created_at FROM chat_messages"
            " WHERE user_id = ? AND role IN ('user', 'assistant') ORDER BY id DESC LIMIT ?",
            [user_id, limit],
        ).fetchall()
    return list(reversed(rows))  # oldest first


def load_history(user_id: int) -> list[HistoryMessage]:
    """The customer's recent messages, oldest first, for the chat panel."""
    return [
        HistoryMessage(
            role=r["role"], content=r["content"], results=_results(r["products_json"]), created_at=r["created_at"]
        )
        for r in _rows(user_id, HISTORY_LIMIT)
    ]


def recent_turns(user_id: int, limit: int) -> list[ChatTurn]:
    """The customer's last few turns, oldest first, as context for the agent."""
    return [ChatTurn(role=r["role"], content=r["content"]) for r in _rows(user_id, limit)]
