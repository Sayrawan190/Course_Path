import sqlite3
import csv

DB_PATH = r"DataBase/FCIT_bot.db"
MAJOR_CSV_PATH = r"DataBase/major_terms.csv"  
COURSES_CSV_PATH = r"DataBase/courses.csv"  
EXAMS_CSV_PATH = r"DataBase/Exams.csv"  
INFOSOURCES_CSV_PATH = r"DataBase/info_sources.csv"  
SLIDES_CSV_PATH = r"DataBase/slides.csv"  

def start_sync():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()


    # ====================== Major Sync ======================
    # 2) امسح القديم عشان ما يصير تكرار
    cur.execute("DELETE FROM major_terms")

    # 3) اقرأ CSV وادخل البيانات
    with open(MAJOR_CSV_PATH, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)

        rows_to_insert = []
        for row in reader:
            major_code = row["major_code"].strip()
            term = int(row["term"])
            course_id = row["course_id"].strip()

            rows_to_insert.append((major_code, term, course_id))

    cur.executemany(
        "INSERT OR IGNORE INTO major_terms (major_code, term, course_id) VALUES (?, ?, ?)",
        rows_to_insert
    )

    print(f"Inserted {len(rows_to_insert)} rows into major_terms ✅")
    # ========================================================


    # ===================== Courses Sync =====================
    cur.execute("DELETE FROM courses")

    with open(COURSES_CSV_PATH, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)

        rows_to_insert = []
        for row in reader:
            course_name = row["course_name"].strip()
            course_code = int(row["course_code"])
            course_title = row["course_title"].strip()
            section = row["section"].strip()
            title = row["title"].strip()
            ord = int(row["ord"])

            rows_to_insert.append((course_name, course_code, course_title, section, title, ord))

    cur.executemany(
        "INSERT OR IGNORE INTO courses (course_name, course_code, course_title, section, title, ord) VALUES (?, ?, ?, ?, ?, ?)",
        rows_to_insert
    )

    print(f"Inserted {len(rows_to_insert)} rows into courses ✅")
    # ========================================================

    # =================== Slides Sync =====================
    cur.execute("DELETE FROM slides")
    with open(SLIDES_CSV_PATH, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
        
            rows_to_insert = []
            for row in reader:
                course_id = row["course_id"].strip()
                slide_type = row["slide_type"].strip()
                button_title = row["button_title"].strip()
                title = row["title"].strip()
                file_path = row["file_path"].strip()
                ord = int(row["ord"])
        
                rows_to_insert.append((course_id, slide_type, button_title, title, file_path, ord))

    cur.executemany(
        "INSERT OR IGNORE INTO slides (course_id, slide_type, button_title, title, file_path, ord) VALUES (?, ?, ?, ?, ?, ?)",
        rows_to_insert)

    print(f"Inserted {len(rows_to_insert)} rows into slides ✅")
    # ========================================================

    # ==================== Exams Sync =====================
    cur.execute("DELETE FROM exams")

    with open(EXAMS_CSV_PATH, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)

        rows_to_insert = []
        for row in reader:
            course_id = row["course_id"].strip()
            exam_type = row["exam_type"].strip()
            button_title = row["button_title"].strip()
            title = row["title"].strip()
            file_path = row["file_path"].strip()
            ord = int(row["ord"])

            rows_to_insert.append((course_id, exam_type, button_title, title, file_path, ord))

    cur.executemany(
        "INSERT OR IGNORE INTO exams (course_id, exam_type, button_title, title, file_path, ord) VALUES (?, ?, ?, ?, ?, ?)",
        rows_to_insert
    )

    print(f"Inserted {len(rows_to_insert)} rows into exams ✅")
    # ========================================================

    # =================== Info Sources Sync =====================
    cur.execute("DELETE FROM info_sources")
    with open(INFOSOURCES_CSV_PATH, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)

        rows_to_insert = []
        for row in reader:
            course_id = row["course_id"].strip()
            info = row["info"].strip()
            sources = row["sources"].strip()

            rows_to_insert.append((course_id, info, sources))

    cur.executemany(
        "INSERT OR IGNORE INTO info_sources (course_id, info, sources) VALUES (?, ?, ?)",
        rows_to_insert)

    print(f"Inserted {len(rows_to_insert)} rows into info_sources ✅")
    # ========================================================



    conn.commit()
    conn.close()


