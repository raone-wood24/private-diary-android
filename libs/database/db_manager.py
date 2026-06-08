"""SQLite 数据库管理 — Android 适配版"""

import sqlite3
import json
from datetime import datetime, date
from contextlib import contextmanager
from libs.utils.config import DATABASE_PATH, ensure_data_dir

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    content_encrypted BLOB NOT NULL,
    iv BLOB NOT NULL,
    mood TEXT DEFAULT 'neutral',
    created_at TEXT DEFAULT (datetime('now','localtime')),
    updated_at TEXT DEFAULT (datetime('now','localtime')),
    word_count INTEGER DEFAULT 0,
    category TEXT DEFAULT '默认'
);

CREATE TABLE IF NOT EXISTS habits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT UNIQUE,
    entry_count INTEGER DEFAULT 0,
    first_write_time TEXT,
    last_write_time TEXT,
    total_words INTEGER DEFAULT 0,
    session_duration_sec INTEGER DEFAULT 0,
    moods TEXT DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS writing_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TEXT,
    ended_at TEXT,
    duration_sec INTEGER DEFAULT 0,
    entry_id INTEGER,
    word_count_delta INTEGER DEFAULT 0,
    day_of_week INTEGER,
    hour_of_day INTEGER,
    FOREIGN KEY (entry_id) REFERENCES entries(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS keyword_tracking (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    keyword TEXT NOT NULL,
    category TEXT,
    entry_id INTEGER,
    tracked_date TEXT,
    FOREIGN KEY (entry_id) REFERENCES entries(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS recommendation_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rec_type TEXT,
    rec_content TEXT,
    generated_at TEXT DEFAULT (datetime('now','localtime')),
    was_dismissed INTEGER DEFAULT 0,
    was_followed INTEGER DEFAULT 0,
    follow_up_note TEXT
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT
);
"""


def get_connection() -> sqlite3.Connection:
    ensure_data_dir()
    conn = sqlite3.connect(str(DATABASE_PATH))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    conn = get_connection()
    try:
        conn.executescript(SCHEMA_SQL)
        conn.commit()
    finally:
        conn.close()


@contextmanager
def transaction():
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def insert_entry(title, content_encrypted, iv, mood="neutral", category="默认", word_count=0):
    with transaction() as conn:
        cursor = conn.execute(
            """INSERT INTO entries (title, content_encrypted, iv, mood, category, word_count)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (title, content_encrypted, iv, mood, category, word_count))
        return cursor.lastrowid


def update_entry(entry_id, title, content_encrypted, iv, mood="neutral", category="默认", word_count=0):
    with transaction() as conn:
        conn.execute(
            """UPDATE entries SET title=?, content_encrypted=?, iv=?, mood=?,
               category=?, word_count=?, updated_at=datetime('now','localtime')
               WHERE id=?""",
            (title, content_encrypted, iv, mood, category, word_count, entry_id))


def delete_entry(entry_id):
    with transaction() as conn:
        conn.execute("DELETE FROM entries WHERE id=?", (entry_id,))


def get_entry(entry_id):
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM entries WHERE id=?", (entry_id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_all_entries(order="DESC"):
    conn = get_connection()
    try:
        rows = conn.execute(
            f"SELECT id, title, mood, category, created_at, updated_at, word_count "
            f"FROM entries ORDER BY created_at {order}").fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def search_entries(keyword="", mood="", category="", date_from="", date_to=""):
    query = ("SELECT id, title, mood, category, created_at, updated_at, word_count "
             "FROM entries WHERE 1=1")
    params = []
    if keyword:
        query += " AND title LIKE ?"
        params.append(f"%{keyword}%")
    if mood:
        query += " AND mood = ?"
        params.append(mood)
    if category:
        query += " AND category = ?"
        params.append(category)
    if date_from:
        query += " AND date(created_at) >= ?"
        params.append(date_from)
    if date_to:
        query += " AND date(created_at) <= ?"
        params.append(date_to)
    query += " ORDER BY created_at DESC"
    conn = get_connection()
    try:
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_entries_by_date(target_date):
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT id, title, mood, category, created_at, word_count "
            "FROM entries WHERE date(created_at) = ? ORDER BY created_at DESC",
            (target_date,)).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_entry_count():
    conn = get_connection()
    try:
        row = conn.execute("SELECT COUNT(*) as cnt FROM entries").fetchone()
        return row["cnt"]
    finally:
        conn.close()


def get_total_word_count():
    conn = get_connection()
    try:
        row = conn.execute("SELECT COALESCE(SUM(word_count),0) as total FROM entries").fetchone()
        return row["total"]
    finally:
        conn.close()


def upsert_habit(today, entry_count=1, write_time="", total_words=0, duration_sec=0, mood=""):
    with transaction() as conn:
        existing = conn.execute("SELECT * FROM habits WHERE date=?", (today,)).fetchone()
        if existing:
            old = dict(existing)
            old_moods = json.loads(old.get("moods", "{}"))
            if mood:
                old_moods[mood] = old_moods.get(mood, 0) + 1
            conn.execute(
                """UPDATE habits SET entry_count=?, last_write_time=?, total_words=?,
                   session_duration_sec=?, moods=? WHERE date=?""",
                (old["entry_count"] + entry_count, write_time or old["last_write_time"],
                 old["total_words"] + total_words, old["session_duration_sec"] + duration_sec,
                 json.dumps(old_moods, ensure_ascii=False), today))
        else:
            moods_dict = {mood: 1} if mood else {}
            conn.execute(
                """INSERT INTO habits (date, entry_count, first_write_time, last_write_time,
                   total_words, session_duration_sec, moods)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (today, entry_count, write_time, write_time, total_words, duration_sec,
                 json.dumps(moods_dict, ensure_ascii=False)))


def get_habits(days=30):
    conn = get_connection()
    try:
        rows = conn.execute("SELECT * FROM habits ORDER BY date DESC LIMIT ?", (days,)).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_consecutive_days():
    conn = get_connection()
    try:
        rows = conn.execute("SELECT date FROM habits ORDER BY date DESC").fetchall()
        if not rows:
            return 0
        today = date.today()
        dates = sorted([date.fromisoformat(r["date"]) for r in rows], reverse=True)
        consecutive = 0
        expected = today
        for d in dates:
            if d == expected:
                consecutive += 1
                expected = d - date.resolution
            elif d < expected:
                break
        return consecutive
    finally:
        conn.close()


def start_session(entry_id=None):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with transaction() as conn:
        cursor = conn.execute(
            """INSERT INTO writing_sessions (started_at, entry_id, day_of_week, hour_of_day)
               VALUES (?, ?, ?, ?)""",
            (now, entry_id, datetime.now().weekday(), datetime.now().hour))
        return cursor.lastrowid


def end_session(session_id, word_count_delta=0):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with transaction() as conn:
        session = conn.execute("SELECT started_at FROM writing_sessions WHERE id=?", (session_id,)).fetchone()
        if session:
            started = datetime.strptime(session["started_at"], "%Y-%m-%d %H:%M:%S")
            duration = int((datetime.now() - started).total_seconds())
            conn.execute(
                """UPDATE writing_sessions SET ended_at=?, duration_sec=?, word_count_delta=?
                   WHERE id=?""", (now, duration, word_count_delta, session_id))


def get_writing_sessions(days=30):
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM writing_sessions WHERE started_at >= date('now', ?) ORDER BY started_at DESC",
            (f"-{days} days",)).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def save_keywords(keywords, entry_id, category=""):
    today = date.today().isoformat()
    with transaction() as conn:
        for kw in keywords:
            conn.execute(
                "INSERT INTO keyword_tracking (keyword, category, entry_id, tracked_date) VALUES (?, ?, ?, ?)",
                (kw, category, entry_id, today))


def get_top_keywords(days=90, limit=50):
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT keyword, COUNT(*) as freq FROM keyword_tracking "
            "WHERE tracked_date >= date('now', ?) GROUP BY keyword ORDER BY freq DESC LIMIT ?",
            (f"-{days} days", limit)).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_keywords_by_entry(entry_id):
    conn = get_connection()
    try:
        rows = conn.execute("SELECT keyword FROM keyword_tracking WHERE entry_id=?", (entry_id,)).fetchall()
        return [r["keyword"] for r in rows]
    finally:
        conn.close()


def log_recommendation(rec_type, rec_content):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with transaction() as conn:
        cursor = conn.execute(
            "INSERT INTO recommendation_log (rec_type, rec_content, generated_at) VALUES (?, ?, ?)",
            (rec_type, rec_content, now))
        return cursor.lastrowid


def feedback_recommendation(rec_id, followed, dismissed=False):
    with transaction() as conn:
        conn.execute(
            "UPDATE recommendation_log SET was_followed=?, was_dismissed=? WHERE id=?",
            (1 if followed else 0, 1 if dismissed else 0, rec_id))


def get_recommendation_stats():
    conn = get_connection()
    try:
        total = conn.execute("SELECT COUNT(*) as cnt FROM recommendation_log").fetchone()["cnt"]
        followed = conn.execute("SELECT COUNT(*) as cnt FROM recommendation_log WHERE was_followed=1").fetchone()["cnt"]
        dismissed = conn.execute("SELECT COUNT(*) as cnt FROM recommendation_log WHERE was_dismissed=1").fetchone()["cnt"]
        by_type = conn.execute(
            "SELECT rec_type, COUNT(*) as cnt, SUM(was_followed) as followed, SUM(was_dismissed) as dismissed "
            "FROM recommendation_log GROUP BY rec_type").fetchall()
        return {"total": total, "followed": followed, "dismissed": dismissed, "by_type": [dict(r) for r in by_type]}
    finally:
        conn.close()


def get_setting(key):
    conn = get_connection()
    try:
        row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return row["value"] if row else None
    finally:
        conn.close()


def set_setting(key, value):
    with transaction() as conn:
        conn.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, value))


def delete_setting(key):
    with transaction() as conn:
        conn.execute("DELETE FROM settings WHERE key=?", (key,))


def get_stats():
    conn = get_connection()
    try:
        total_entries = get_entry_count()
        total_words = get_total_word_count()
        consecutive = get_consecutive_days()
        mood_stats = conn.execute("SELECT mood, COUNT(*) as cnt FROM entries GROUP BY mood").fetchall()
        category_stats = conn.execute("SELECT category, COUNT(*) as cnt FROM entries GROUP BY category").fetchall()
        return {
            "total_entries": total_entries, "total_words": total_words,
            "consecutive_days": consecutive,
            "moods": {r["mood"]: r["cnt"] for r in mood_stats},
            "categories": {r["category"]: r["cnt"] for r in category_stats},
        }
    finally:
        conn.close()
