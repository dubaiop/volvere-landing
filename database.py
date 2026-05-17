import os, sqlite3
from datetime import datetime

DATABASE_URL = os.environ.get("DATABASE_URL", "")

if DATABASE_URL:
    import psycopg2, psycopg2.extras
    def _conn():
        return psycopg2.connect(DATABASE_URL, sslmode="require")
else:
    def _conn():
        c = sqlite3.connect("volvere.db")
        c.row_factory = sqlite3.Row
        return c


def init_db():
    if DATABASE_URL:
        with _conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
                        email TEXT UNIQUE NOT NULL,
                        password_hash TEXT NOT NULL,
                        name TEXT,
                        plan TEXT DEFAULT 'free',
                        is_admin BOOLEAN DEFAULT FALSE,
                        created_at TEXT
                    )
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS waitlist (
                        id SERIAL PRIMARY KEY,
                        email TEXT UNIQUE NOT NULL,
                        name TEXT,
                        company TEXT,
                        created_at TEXT,
                        notified BOOLEAN DEFAULT FALSE
                    )
                """)
            conn.commit()
    else:
        with _conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    name TEXT,
                    plan TEXT DEFAULT 'free',
                    is_admin INTEGER DEFAULT 0,
                    created_at TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS waitlist (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL,
                    name TEXT,
                    company TEXT,
                    created_at TEXT,
                    notified INTEGER DEFAULT 0
                )
            """)
            conn.commit()


def add_waitlist(email: str, name: str = "", company: str = "") -> bool:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        if DATABASE_URL:
            with _conn() as conn:
                with conn.cursor() as cur:
                    cur.execute("INSERT INTO waitlist (email, name, company, created_at) VALUES (%s,%s,%s,%s)",
                                (email.lower().strip(), name, company, now))
                conn.commit()
        else:
            with _conn() as conn:
                conn.execute("INSERT INTO waitlist (email, name, company, created_at) VALUES (?,?,?,?)",
                             (email.lower().strip(), name, company, now))
                conn.commit()
        return True
    except Exception:
        return False  # duplicate email


def get_waitlist_count() -> int:
    if DATABASE_URL:
        with _conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM waitlist")
                return cur.fetchone()[0]
    else:
        with _conn() as conn:
            return conn.execute("SELECT COUNT(*) FROM waitlist").fetchone()[0]


def create_user(email: str, password_hash: str, name: str = "", is_admin: bool = False) -> bool:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        if DATABASE_URL:
            with _conn() as conn:
                with conn.cursor() as cur:
                    cur.execute("INSERT INTO users (email, password_hash, name, is_admin, created_at) VALUES (%s,%s,%s,%s,%s)",
                                (email.lower().strip(), password_hash, name, is_admin, now))
                conn.commit()
        else:
            with _conn() as conn:
                conn.execute("INSERT INTO users (email, password_hash, name, is_admin, created_at) VALUES (?,?,?,?,?)",
                             (email.lower().strip(), password_hash, name, 1 if is_admin else 0, now))
                conn.commit()
        return True
    except Exception:
        return False


def get_user(email: str) -> dict | None:
    if DATABASE_URL:
        with _conn() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT * FROM users WHERE email=%s LIMIT 1", (email.lower().strip(),))
                row = cur.fetchone()
                return dict(row) if row else None
    else:
        with _conn() as conn:
            row = conn.execute("SELECT * FROM users WHERE email=? LIMIT 1", (email.lower().strip(),)).fetchone()
            return dict(row) if row else None


def get_users_count() -> int:
    if DATABASE_URL:
        with _conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM users")
                return cur.fetchone()[0]
    else:
        with _conn() as conn:
            return conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]


def get_all_waitlist() -> list[dict]:
    if DATABASE_URL:
        with _conn() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT * FROM waitlist ORDER BY created_at DESC")
                return [dict(r) for r in cur.fetchall()]
    else:
        with _conn() as conn:
            rows = conn.execute("SELECT * FROM waitlist ORDER BY created_at DESC").fetchall()
            return [dict(r) for r in rows]
