"""نقل البيانات من SQLite (DataBase/FCIT_bot.db) إلى PostgreSQL.
تشغيل من جذر المشروع: py -3 -m scripts.migrate_to_postgres
"""
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db.connection import get_db_connection

SQLITE_PATH = "DataBase/FCIT_bot.db"

SCHEMA_STATEMENTS = [
    """CREATE TABLE IF NOT EXISTS major_terms(
        major_code TEXT,
        term INTEGER,
        course_id TEXT,
        UNIQUE(major_code, term, course_id)
        )""",
    """CREATE TABLE IF NOT EXISTS courses(
        course_name TEXT NOT NULL,
        course_code INTEGER NOT NULL,
        course_title TEXT,
        section TEXT NOT NULL,
        title TEXT,
        ord INTEGER NOT NULL,
        UNIQUE(course_name, course_code, course_title, section, title, ord)
        )""",
    """CREATE TABLE IF NOT EXISTS slides(
        course_id TEXT NOT NULL,
        slide_type TEXT NOT NULL,
        button_title TEXT NOT NULL,
        title TEXT,
        ord INTEGER NOT NULL,
        UNIQUE(course_id, slide_type, button_title, title, ord)
        )""",
    """CREATE TABLE IF NOT EXISTS exams(
        course_id TEXT NOT NULL,
        exam_type TEXT NOT NULL,
        button_title TEXT NOT NULL,
        title TEXT,
        ord INTEGER NOT NULL,
        UNIQUE(course_id, exam_type, button_title, title, ord)
        )""",
    """CREATE TABLE IF NOT EXISTS info_sources(
        course_id TEXT NOT NULL PRIMARY KEY,
        info TEXT,
        sources TEXT
        )""",
    """CREATE TABLE IF NOT EXISTS users(
        user_id BIGINT PRIMARY KEY,
        username TEXT,
        email TEXT NOT NULL UNIQUE,
        verified INTEGER DEFAULT 0
        )""",
    """CREATE TABLE IF NOT EXISTS correct_users(
        id SERIAL PRIMARY KEY,
        chat_id BIGINT UNIQUE NOT NULL,
        username TEXT,
        created_at TEXT NOT NULL
        )""",
]

# (اسم الجدول, أعمدة الإدراج)
TABLES = [
    ("major_terms", ["major_code", "term", "course_id"]),
    ("courses", ["course_name", "course_code", "course_title", "section", "title", "ord"]),
    ("slides", ["course_id", "slide_type", "button_title", "title", "ord"]),
    ("exams", ["course_id", "exam_type", "button_title", "title", "ord"]),
    ("info_sources", ["course_id", "info", "sources"]),
    ("users", ["user_id", "username", "email", "verified"]),
]


def migrate():
    sqlite_conn = sqlite3.connect(SQLITE_PATH)
    pg_conn = get_db_connection()

    try:
        pg_cur = pg_conn.cursor()
        for statement in SCHEMA_STATEMENTS:
            pg_cur.execute(statement)
        pg_conn.commit()
        print("تم إنشاء الجداول في PostgreSQL ✅\n")

        sqlite_cur = sqlite_conn.cursor()
        for table_name, columns in TABLES:
            sqlite_cur.execute(f"SELECT {', '.join(columns)} FROM {table_name}")
            rows = sqlite_cur.fetchall()

            placeholders = ", ".join(["%s"] * len(columns))
            pg_cur.executemany(
                f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders}) ON CONFLICT DO NOTHING",
                rows
            )
            pg_conn.commit()

            pg_cur.execute(f"SELECT COUNT(*) FROM {table_name}")
            pg_count = pg_cur.fetchone()[0]

            status = "✅" if pg_count == len(rows) else "⚠️"
            print(f"{table_name}: sqlite={len(rows)} | postgres={pg_count} {status}")

    finally:
        sqlite_conn.close()
        pg_conn.close()


if __name__ == "__main__":
    migrate()
