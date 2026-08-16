from logging_config import logger
from db.connection import get_db_connection, db_lock


# ==========================================================
# Users
# ==========================================================
def get_user_verified(user_id):
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT verified FROM users WHERE user_id = %s", (user_id,))
        row = cursor.fetchone()
        conn.close()
    return row


def create_user(user_id, username):
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (user_id, username, email, verified) VALUES (%s, %s, %s, %s)",
            (user_id, username, None, 0)
        )
        conn.commit()
        conn.close()


def add_or_verify_user(user_id, username, email, verified=False):
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO users (user_id, username, email, verified)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT(user_id) DO UPDATE SET verified=excluded.verified
        """, (user_id, username, email, int(verified)))
        conn.commit()
        conn.close()


# ==========================================================
# Majors / Terms / Courses
# ==========================================================
def get_terms_for_major(major_code):
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT term FROM major_Terms WHERE major_code = %s ORDER BY term", (major_code,))
        rows = cursor.fetchall()
        conn.close()
    return [row[0] for row in rows]


def get_courses_for_major_term(major_code, term):
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT DISTINCT course_id FROM major_Terms WHERE major_code = %s AND term = %s",
            (major_code, term)
        )
        rows = cursor.fetchall()
        conn.close()
    return [row[0] for row in rows]


def course_exists(course_code):
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT 1 FROM major_Terms WHERE course_id = %s LIMIT 1",
            (course_code,)
        )
        row = cursor.fetchone()
        conn.close()
    return row is not None


def get_course_title(*args):
    try:
        if len(args) == 1:
            course_id = args[0]
            course_name, course_code = course_id.split("-", 1)
        elif len(args) == 2:
            course_name, course_code = args
        else:
            return "غير معروف"

        with db_lock:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT DISTINCT course_title FROM courses WHERE course_name = %s AND course_code = %s",
                (course_name, course_code)
            )
            row = cursor.fetchone()
            conn.close()
        return row[0] if row else "غير معروف"

    except Exception as e:
        logger.error("get_course_title error: %s", e)
        return "غير معروف"


def get_sections_for_course(course_name, course_code):
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT section, title FROM courses WHERE course_name = %s and course_code = %s GROUP BY section, title ORDER BY MIN(ord)",
            (course_name, course_code)
        )
        rows = cursor.fetchall()
        conn.close()
    return [(row[0], row[1]) for row in rows]


# ==========================================================
# Slides / Exams metadata
# ==========================================================
def get_slide_types(course_id):
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT slide_type, button_title FROM slides WHERE course_id = %s", (course_id,))
        rows = cursor.fetchall()
        conn.close()
    return [(row[0], row[1]) for row in rows]


def get_exam_types(course_id):
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT exam_type, button_title FROM exams WHERE course_id = %s", (course_id,))
        rows = cursor.fetchall()
        conn.close()
    return [(row[0], row[1]) for row in rows]


def get_chapters_for_slide(course_id, slide_type):
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT title FROM slides WHERE course_id = %s AND slide_type = %s GROUP BY title ORDER BY MIN(ord)",
            (course_id, slide_type)
        )
        rows = cursor.fetchall()
        conn.close()
    return [row[0] for row in rows]


def get_exams_titles(course_id, exam_type):
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT title FROM exams WHERE course_id = %s AND exam_type = %s GROUP BY title ORDER BY MIN(ord)",
            (course_id, exam_type)
        )
        rows = cursor.fetchall()
        conn.close()
    return [row[0] for row in rows]


def get_next_ord(table_name, course_id, type_column, file_type):
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            f"SELECT COALESCE(MAX(ord), 0) + 1 FROM {table_name} WHERE course_id = %s AND {type_column} = %s",
            (course_id, file_type)
        )
        next_ord = cursor.fetchone()[0]
        conn.close()
    return next_ord


# ==========================================================
# Info / Sources
# ==========================================================
def get_info_text(course_id):
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT info FROM info_sources WHERE course_id = %s", (course_id,))
        row = cursor.fetchone()
        conn.close()

    # التحقق من أن القيمة مو None أو فاضية
    if not row or not row[0] or not row[0].strip():
        return "لا توجد معلومات متاحة حاليًا"

    return row[0].replace("||", "\n")


def get_sources_text(course_id):
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT sources FROM info_sources WHERE course_id = %s", (course_id,))
        row = cursor.fetchone()
        conn.close()

    # التحقق من أن القيمة مو None أو فاضية
    if not row or not row[0] or not row[0].strip():
        return "لا توجد مصادر متاحة حاليًا"

    return row[0].replace("||", "\n")
