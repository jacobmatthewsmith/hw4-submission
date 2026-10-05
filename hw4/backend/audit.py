"""Append-only audit trail of agent activity (Problem 12): output/audit_trail.json.

One record per chat turn: when it ran, who asked (as an id, never a name or email), which page they were on,
every tool call (time, tool name, short args, short result), usage counts, and the stop reason.

The file is a JSON array that only ever grows. New records are written over the closing "]" at the end of the
file and nothing earlier is rewritten, so history is never wiped between runs or restarts. The shopper's
message text is not logged, only its length, so the trail doesn't store full conversations.
"""

import contextvars
import functools
import inspect
import json
import os
import secrets
import threading
import time
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel

ROOT = Path(__file__).resolve().parent.parent
AUDIT_PATH = Path(os.getenv("CC_AUDIT_PATH", ROOT / "output" / "audit_trail.json"))
MAX_ARGS_CHARS = 160
MAX_RESULT_CHARS = 220

_lock = threading.Lock()
_current: contextvars.ContextVar["RunRecord | None"] = contextvars.ContextVar("audit_run", default=None)


def _now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _clip(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[: limit - 1] + "…"


def summarize_result(value) -> str:
    """A short, human-readable summary of a tool result (no customer email)."""
    if isinstance(value, list):
        names = [getattr(v, "name", None) or (v.get("name") if isinstance(v, dict) else str(v)) for v in value]
        return f"{len(value)} match(es)" + (": " + ", ".join(names[:4]) + (" …" if len(names) > 4 else "") if names else "")
    if isinstance(value, BaseModel):
        data = value.model_dump(exclude_none=True)
        if "logged_in" in data:  # CustomerProfile: record only whether a customer was present
            return f"logged_in={data['logged_in']}"
        parts = [data.get("lookup"), data.get("message")]
        if data.get("price") is not None:
            parts.append(f"price=${data['price']:.2f}")
        if data.get("requested_size_status"):
            parts.append(f"{data.get('requested_size')}={data['requested_size_status']}")
        return " | ".join(str(p) for p in parts if p)
    if isinstance(value, dict):
        return json.dumps({k: value[k] for k in list(value)[:6]}, default=str)
    return str(value)


class RunRecord:
    def __init__(self, who: str, page: str | None, message_chars: int):
        self.started = time.monotonic()
        self.data: dict = {
            "time": _now(),
            "run_id": datetime.now().strftime("%Y%m%d-%H%M%S-") + secrets.token_hex(3),
            "who": who,
            "page": page,
            "message_chars": message_chars,
            "tool_calls": [],
        }

    def tool_call(self, tool: str, args: dict, result: str, ok: bool, ms: int) -> None:
        self.data["tool_calls"].append(
            {
                "time": _now(),
                "tool": tool,
                "args": _clip(json.dumps(args, default=str), MAX_ARGS_CHARS),
                "result": _clip(result, MAX_RESULT_CHARS),
                "ok": ok,
                "ms": ms,
            }
        )


def start_run(who: str, page: str | None, message_chars: int) -> RunRecord:
    record = RunRecord(who, page, message_chars)
    _current.set(record)
    return record


def finish_run(record: RunRecord, stop_reason: str, **extra) -> None:
    """Write the turn's record. stop_reason: completed | refused_off_topic | content_filtered | usage_limit |
    timeout | out_of_attempts | error | rate_limited."""
    record.data.update(extra)
    record.data["stop_reason"] = stop_reason
    record.data["duration_ms"] = int((time.monotonic() - record.started) * 1000)
    append(record.data)
    _current.set(None)


def append(entry: dict) -> None:
    """Append one record to the JSON array on disk without rewriting what's already there."""
    blob = json.dumps(entry, indent=2, ensure_ascii=False, default=str)
    with _lock:
        AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
        if not AUDIT_PATH.exists() or AUDIT_PATH.stat().st_size == 0:
            AUDIT_PATH.write_text("[\n" + blob + "\n]\n", encoding="utf-8")
            return
        with open(AUDIT_PATH, "r+b") as f:
            # Find the closing bracket at the end of the file and write the new record over it.
            f.seek(0, os.SEEK_END)
            pos = f.tell()
            while pos > 0:
                pos -= 1
                f.seek(pos)
                if f.read(1) == b"]":
                    break
            else:
                raise ValueError(f"{AUDIT_PATH} is not a JSON array; refusing to modify it.")
            f.seek(pos)
            f.write((",\n" + blob + "\n]\n").encode("utf-8"))


def audited(fn):
    """Wrap a tool so each call is recorded on the current run (signature and docstring are kept for the agent)."""
    sig = inspect.signature(fn)

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        record = _current.get()
        bound = sig.bind_partial(*args, **kwargs)
        shown = {k: v for k, v in bound.arguments.items() if k != "ctx"}
        start = time.monotonic()
        try:
            result = fn(*args, **kwargs)
        except Exception as e:
            if record:
                record.tool_call(fn.__name__, shown, f"error: {type(e).__name__}", False, int((time.monotonic() - start) * 1000))
            raise
        if record:
            record.tool_call(fn.__name__, shown, summarize_result(result), True, int((time.monotonic() - start) * 1000))
        return result

    return wrapper
