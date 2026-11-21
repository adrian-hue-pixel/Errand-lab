"""SQLite storage for sessions, accounts and saved experiment reports."""
from contextlib import contextmanager
from pathlib import Path
import hashlib
import hmac
import json
import os
import re
import secrets
import sqlite3
import time

DATA = Path(os.environ.get("ERRANDLAB_DB", Path(__file__).parent / "data" / "errandlab.sqlite3"))
SESSION_LIFE = 86400 * 7
GUEST_LIFE = 86400
USER_PATTERN = re.compile(r"[a-z0-9][a-z0-9_.-]{2,29}", re.ASCII)
DUMMY_SALT = secrets.token_bytes(16)
SCHEMA = """
CREATE TABLE IF NOT EXISTS accounts (name TEXT PRIMARY KEY, salt BLOB, digest BLOB);
CREATE TABLE IF NOT EXISTS sessions (token TEXT PRIMARY KEY, username TEXT, csrf TEXT, expires INTEGER);
CREATE TABLE IF NOT EXISTS reports (
    id TEXT PRIMARY KEY, username TEXT, owner TEXT, title TEXT, payload TEXT,
    saved INTEGER DEFAULT 0, created INTEGER
);
CREATE INDEX IF NOT EXISTS report_username ON reports(username, saved, created);
CREATE TABLE IF NOT EXISTS profiles (username TEXT PRIMARY KEY, display TEXT, role TEXT, bio TEXT, avatar TEXT);
CREATE TABLE IF NOT EXISTS attempts (peer TEXT PRIMARY KEY, count INTEGER, expires INTEGER);
"""


@contextmanager
def connect():
    db = sqlite3.connect(DATA, timeout=8)
    db.row_factory = sqlite3.Row
    try:
        with db:
            yield db
    finally:
        db.close()


def initialize():
    DATA.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    DATA.touch(exist_ok=True, mode=0o600)
    with connect() as db:
        db.execute("PRAGMA journal_mode=WAL")
        db.executescript(SCHEMA)


def token_digest(token):
    return hashlib.sha256(token.encode()).hexdigest()


def get_session(token):
    if not token or not re.fullmatch(r"[a-zA-Z0-9_-]{43}", token):
        return None
    with connect() as db:
        return db.execute(
            "SELECT * FROM sessions WHERE token=? AND expires>?", (token_digest(token), int(time.time()))
        ).fetchone()


def new_session(username=None, previous=None):
    token, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(24)
    now = int(time.time())
    expires = now + (SESSION_LIFE if username else GUEST_LIFE)
    digest = token_digest(token)
    with connect() as db:
        # Demo workspaces are private, disposable sessions. Reclaim their saved
        # rows and personalization when the session expires or is signed out.
        for table in ("profiles","reports"):
            db.execute(f"DELETE FROM {table} WHERE username LIKE 'demo:%' AND username NOT LIKE '%@%' "
                       "AND username IN (SELECT username FROM sessions WHERE expires<=?)",(now,))
        db.execute("DELETE FROM sessions WHERE expires<=?", (now,))
        db.execute("DELETE FROM reports WHERE saved=0 AND created<=?", (now - GUEST_LIFE,))
        if previous:
            db.execute("DELETE FROM sessions WHERE token=?", (previous["token"],))
            if previous["username"] and previous["username"].startswith("demo:") and "@" not in previous["username"]:
                db.execute("DELETE FROM profiles WHERE username=?", (previous["username"],))
                db.execute("DELETE FROM reports WHERE username=?", (previous["username"],))
            # Preserve the current guest's recent work on sign-in.
            if username and not previous["username"]:
                db.execute("UPDATE reports SET username=?, owner=? WHERE owner=? AND username IS NULL",
                           (username, digest, previous["token"]))
        db.execute("INSERT INTO sessions VALUES (?,?,?,?)", (digest, username, csrf, expires))
    return token, get_session(token)


def throttle(peer):
    now = int(time.time())
    with connect() as db:
        db.execute("BEGIN IMMEDIATE")
        db.execute("DELETE FROM attempts WHERE expires<=?", (now,))
        db.execute("INSERT INTO attempts VALUES (?,1,?) ON CONFLICT(peer) DO UPDATE SET count=count+1",
                   (peer, now + 300))
        return db.execute("SELECT count FROM attempts WHERE peer=?", (peer,)).fetchone()[0] > 12


def digest_password(password, salt):
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 600_000)


def register(username, password):
    username = username.strip().lower()
    if len(username) > 254 or not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", username):
        raise ValueError("Enter a valid email address.")
    if not 12 <= len(password) <= 128:
        raise ValueError("Use a password of 12–128 characters.")
    salt = secrets.token_bytes(16)
    digest = digest_password(password, salt)
    try:
        with connect() as db:
            db.execute("INSERT INTO accounts VALUES (?,?,?)", (username, salt, digest))
    except sqlite3.IntegrityError:
        raise ValueError("Choose a different username.") from None
    return username


def authenticate(username, password):
    username = username.strip().lower()
    if not 1 <= len(password) <= 128 or len(username) > 254:
        return None
    with connect() as db:
        row = db.execute("SELECT salt,digest FROM accounts WHERE name=?", (username,)).fetchone()
    computed = digest_password(password, row["salt"] if row else DUMMY_SALT)
    matches = hmac.compare_digest(computed, row["digest"] if row else bytes(32))
    return username if row and matches else None


def create_report(session, title, payload):
    report_id = secrets.token_urlsafe(18)
    with connect() as db:
        db.execute("INSERT INTO reports VALUES (?,?,?,?,?,0,?)",
                   (report_id, session["username"], session["token"], title,
                    json.dumps(payload, ensure_ascii=False), int(time.time())))
    return report_id


def report(session, report_id):
    with connect() as db:
        return db.execute(
            "SELECT * FROM reports WHERE id=? AND (username=? OR (username IS NULL AND owner=?))",
            (report_id, session["username"], session["token"]),
        ).fetchone()


def save(session, report_id):
    if not session["username"]:
        return False
    with connect() as db:
        return bool(db.execute("UPDATE reports SET saved=1 WHERE id=? AND username=?",
                               (report_id, session["username"])).rowcount)


def saved_reports(session):
    with connect() as db:
        return db.execute(
            "SELECT id,title,created,payload FROM reports WHERE username=? AND saved=1 ORDER BY created DESC LIMIT 100",
            (session["username"],),
        ).fetchall()

def profile(username):
    with connect() as db:
        row = db.execute("SELECT * FROM profiles WHERE username=?", (username,)).fetchone()
    return dict(row) if row else {"display": "Demo explorer" if username.startswith("demo:") else username.split("@")[0],
                                  "role":"","bio":"","avatar":"Capi"}


def saved_count(username):
    with connect() as db:
        return db.execute("SELECT COUNT(*) FROM reports WHERE saved=1 AND username=?", (username,)).fetchone()[0]


def update_profile(username, form):
    values = [form.get(key, "").strip() for key in ("display","role","bio","avatar")]
    display, role, bio, avatar = values
    if not display or len(display)>48 or len(role)>64 or len(bio)>320 or avatar not in ("Capi","Leaf","Compass","Sun"):
        raise ValueError("Check the display name, avatar and field lengths.")
    with connect() as db:
        db.execute("INSERT OR REPLACE INTO profiles VALUES (?,?,?,?,?)", (username,*values))
