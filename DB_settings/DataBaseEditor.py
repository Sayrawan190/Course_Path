from db.connection import get_db_connection, db_lock

with db_lock:
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""CREATE TABLE IF NOT EXISTS major_terms(
                major_code TEXT,
                term INTEGER,
                course_id TEXT,
                UNIQUE(major_code, term, course_id)
                )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS courses(
                course_name TEXT NOT NULL,
                course_code INTEGER NOT NULL,
                course_title TEXT,
                section TEXT NOT NULL,
                title TEXT,
                ord INTEGER  NOT NULL,
                UNIQUE(course_name, course_code, course_title, section, title, ord)
                )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS slides(
                course_id TEXT NOT NULL,
                slide_type TEXT NOT NULL,
                button_title TEXT NOT NULL,
                title TEXT,
                ord INTEGER  NOT NULL,
                UNIQUE(course_id, slide_type, button_title, title, ord)
                )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS exams(
                course_id TEXT NOT NULL,
                exam_type TEXT NOT NULL,
                button_title TEXT NOT NULL,
                title TEXT,
                ord INTEGER  NOT NULL,
                UNIQUE(course_id, exam_type, button_title, title, ord)
                )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS info_sources(
                course_id TEXT NOT NULL PRIMARY KEY,
                info TEXT,
                sources TEXT
                )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS users(
                user_id BIGINT PRIMARY KEY,
                username TEXT,
                email TEXT NOT NULL UNIQUE,
                verified INTEGER DEFAULT 0
                )""")

    conn.commit()
    conn.close()


def delete_user(user_id):
    with db_lock:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("DELETE FROM users WHERE user_id = %s", (user_id,))
        conn.commit()

        deleted = cur.rowcount
        conn.close()

    return deleted > 0


ADMIN_IDS = {1401478668, 810634477}


def execute_sql_query(sql_text):
    with db_lock:
        conn = get_db_connection()
        cur = conn.cursor()

        try:
            cur.execute(sql_text)

            if sql_text.strip().lower().startswith("select"):
                rows = cur.fetchall()
                conn.close()
                return True, rows
            else:
                conn.commit()
                affected_rows = cur.rowcount
                conn.close()
                return True, affected_rows

        except Exception as error:
            conn.close()
            return False, str(error)
