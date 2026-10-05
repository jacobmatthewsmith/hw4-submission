"""Password hashing, user accounts, and session cookies.

Passwords are never stored or logged in plain text. They are hashed with
PBKDF2-HMAC-SHA256 and a random per-user salt, using the same format as the seed
database: ``pbkdf2_sha256$<salt>$<hex digest>``. Hashes are one-way: login works by
re-hashing the attempt with the stored salt and comparing in constant time.

Sessions are a signed, expiring token (itsdangerous) holding only the user id, kept
in an HttpOnly cookie. The signing key comes from SESSION_SECRET in the git-ignored
.env file one level above the project.
"""

import hashlib
import hmac
import os
import secrets
import sqlite3
import warnings

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

import db

db.load_env()

ALGORITHM = "pbkdf2_sha256"
ITERATIONS = 120_000  # matches the seed database's hashes
SESSION_COOKIE = "cc_session"
SESSION_MAX_AGE = 60 * 60 * 24 * 7  # one week

_secret = os.getenv("SESSION_SECRET")
if not _secret:
    warnings.warn("SESSION_SECRET not set; using a temporary key (logins reset on restart).")
    _secret = secrets.token_urlsafe(32)
_serializer = URLSafeTimedSerializer(_secret, salt="cc-session")


# --- Passwords ---------------------------------------------------------------

def _digest(password: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), ITERATIONS).hex()


def hash_password(password: str) -> str:
    salt = secrets.token_hex(8)
    return f"{ALGORITHM}${salt}${_digest(password, salt)}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algorithm, salt, expected = stored.split("$")
    except ValueError:
        return False
    if algorithm != ALGORITHM:
        return False
    return hmac.compare_digest(_digest(password, salt), expected)


# Hashed when an email isn't found, so unknown and known emails take the same time.
_DUMMY_HASH = hash_password(secrets.token_urlsafe(16))


# --- Users -------------------------------------------------------------------

class EmailTaken(Exception):
    pass


def public_user(row: sqlite3.Row) -> dict:
    """The user fields that are safe to send to the browser (never the hash)."""
    return {
        "id": row["id"],
        "email": row["email"],
        "first_name": row["first_name"],
        "last_name": row["last_name"],
        "name": row["name"],
    }


def normalize_email(email: str) -> str:
    return email.strip().lower()


def create_user(first_name: str, last_name: str, email: str, password: str) -> dict:
    first, last = first_name.strip(), last_name.strip()
    with db.connect() as conn:
        try:
            cur = conn.execute(
                "INSERT INTO users (name, email, password_hash, first_name, last_name) VALUES (?, ?, ?, ?, ?)",
                [f"{first} {last}", normalize_email(email), hash_password(password), first, last],
            )
        except sqlite3.IntegrityError as e:
            raise EmailTaken() from e
        row = conn.execute("SELECT * FROM users WHERE id = ?", [cur.lastrowid]).fetchone()
        return public_user(row)


def authenticate(email: str, password: str) -> dict | None:
    with db.connect() as conn:
        row = conn.execute("SELECT * FROM users WHERE email = ?", [normalize_email(email)]).fetchone()
    if row is None:
        verify_password(password, _DUMMY_HASH)
        return None
    return public_user(row) if verify_password(password, row["password_hash"]) else None


def get_user(user_id: int) -> dict | None:
    with db.connect() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", [user_id]).fetchone()
    return public_user(row) if row else None


# --- Sessions ----------------------------------------------------------------

def make_session_token(user_id: int) -> str:
    return _serializer.dumps({"uid": user_id})


def user_from_token(token: str | None) -> dict | None:
    if not token:
        return None
    try:
        data = _serializer.loads(token, max_age=SESSION_MAX_AGE)
    except (BadSignature, SignatureExpired):
        return None
    return get_user(data.get("uid"))
