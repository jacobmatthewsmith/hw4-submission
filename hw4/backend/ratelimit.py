"""Server-side rate limiting (Problem 9).

Sliding-window counters kept in this process's memory. That's correct for the single uvicorn
process this app runs as. If it's ever deployed as multiple instances/workers, swap
SlidingWindow's storage for a shared store (e.g. Redis sorted sets) so limits apply across all of them.

Who a request belongs to (never taken from user-supplied headers or body fields):
  - logged in:   "user:<id>"     from the signed session cookie
  - anonymous:   "visitor:<id>"  from a random, HttpOnly cc_visitor cookie the server sets
  - no cookie:   "ip:<addr>"     the TCP peer address (request.client.host); X-Forwarded-For is ignored
                                  unless uvicorn is started with --proxy-headers behind a trusted proxy.

Every limit is configurable with an environment variable (see LIMITS below).
"""

import math
import os
import threading
import time
from collections import defaultdict, deque
from contextlib import contextmanager
from dataclasses import dataclass

from fastapi import HTTPException, Request


@dataclass(frozen=True)
class Limit:
    max_events: int
    window_seconds: int


def _limit(env: str, max_events: int, window_seconds: int) -> Limit:
    return Limit(int(os.getenv(env, max_events)), window_seconds)


LIMITS = {
    "login_account": _limit("RL_LOGIN_ACCOUNT_FAILS", 5, 15 * 60),  # failed logins per account
    "login_ip": _limit("RL_LOGIN_IP_FAILS", 20, 15 * 60),  # failed logins per IP, across accounts
    "search": _limit("RL_SEARCH_PER_MIN", 60, 60),
    "checkout": _limit("RL_CHECKOUT_PER_MIN", 10, 60),
    "chat_minute": _limit("RL_CHAT_PER_MIN", 5, 60),
    "chat_hour": _limit("RL_CHAT_PER_HOUR", 30, 60 * 60),
}
CHAT_MAX_CONCURRENT = int(os.getenv("RL_CHAT_CONCURRENT", 2))


class SlidingWindow:
    """Counts events per key over a rolling time window."""

    def __init__(self) -> None:
        self._events: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def _prune(self, key: str, limit: Limit, now: float) -> deque[float]:
        q = self._events[key]
        while q and q[0] <= now - limit.window_seconds:
            q.popleft()
        return q

    def retry_after(self, key: str, limit: Limit) -> int:
        """0 if another event is allowed now, else seconds until one is."""
        now = time.monotonic()
        with self._lock:
            q = self._prune(key, limit, now)
            if len(q) < limit.max_events:
                return 0
            return max(1, math.ceil(q[0] + limit.window_seconds - now))

    def add(self, key: str) -> None:
        with self._lock:
            self._events[key].append(time.monotonic())

    def hit(self, key: str, limit: Limit) -> int:
        """Check and record in one step. Returns 0 if allowed (and counted), else the wait in seconds."""
        now = time.monotonic()
        with self._lock:
            q = self._prune(key, limit, now)
            if len(q) >= limit.max_events:
                return max(1, math.ceil(q[0] + limit.window_seconds - now))
            q.append(now)
            return 0

    def clear(self, key: str) -> None:
        with self._lock:
            self._events.pop(key, None)

    def reset_all(self) -> None:
        with self._lock:
            self._events.clear()


windows = SlidingWindow()
_active_chats: dict[str, int] = defaultdict(int)
_active_lock = threading.Lock()


class RateLimited(HTTPException):
    def __init__(self, retry_after: int, message: str):
        super().__init__(status_code=429, detail=message, headers={"Retry-After": str(retry_after)})


def _wait_text(seconds: int) -> str:
    if seconds < 60:
        return f"{seconds} second{'s' if seconds != 1 else ''}"
    minutes = math.ceil(seconds / 60)
    return f"{minutes} minute{'s' if minutes != 1 else ''}"


def client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def identity(request: Request, user: dict | None) -> str:
    if user:
        return f"user:{user['id']}"
    visitor = request.cookies.get(VISITOR_COOKIE)
    if visitor and len(visitor) == 32 and visitor.isalnum():
        return f"visitor:{visitor}"
    return f"ip:{client_ip(request)}"


VISITOR_COOKIE = "cc_visitor"


# --- Checks used by the routes ---------------------------------------------------

def check(name: str, who: str, message: str) -> None:
    """Count one request against a limit; raise 429 if it's over."""
    wait = windows.hit(f"{name}:{who}", LIMITS[name])
    if wait:
        raise RateLimited(wait, f"{message} Please try again in {_wait_text(wait)}.")


def check_login_allowed(email: str, ip: str) -> None:
    """Before checking a password: block if this account or this IP has too many recent failures."""
    for name, key in (("login_account", email), ("login_ip", ip)):
        wait = windows.retry_after(f"{name}:{key}", LIMITS[name])
        if wait:
            raise RateLimited(wait, f"Too many failed login attempts. Please try again in {_wait_text(wait)}.")


def record_login_failure(email: str, ip: str) -> None:
    windows.add(f"login_account:{email}")
    windows.add(f"login_ip:{ip}")


def record_login_success(email: str) -> None:
    windows.clear(f"login_account:{email}")


@contextmanager
def chat_slot(who: str):
    """Rate-limit one AI request (per minute, per hour) and hold one of the caller's concurrent slots."""
    for name in ("chat_minute", "chat_hour"):
        wait = windows.retry_after(f"{name}:{who}", LIMITS[name])
        if wait:
            raise RateLimited(wait, f"You're chatting faster than our assistant can fold hoodies. Please try again in {_wait_text(wait)}.")
    with _active_lock:
        if _active_chats[who] >= CHAT_MAX_CONCURRENT:
            raise RateLimited(5, "Our assistant is still working on your last question. Please wait for it to finish.")
        _active_chats[who] += 1
    windows.add(f"chat_minute:{who}")
    windows.add(f"chat_hour:{who}")
    try:
        yield
    finally:
        with _active_lock:
            _active_chats[who] -= 1
            if _active_chats[who] <= 0:
                del _active_chats[who]
