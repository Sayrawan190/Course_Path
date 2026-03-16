import sqlite3

conn = sqlite3.connect(r"DataBase/FCIT_bot.db", check_same_thread=False)
cur = conn.cursor()

# cur.execute("DROP TABLE IF EXISTS slides")
# cur.execute("DROP TABLE IF EXISTS exams")

# 1042067067 خياط

# 5016425883 مشاري

# 7911073309 عبدالمجيد

# 840957323  ثامر 

cur.execute("DELETE FROM users WHERE email = 'xxxxxxx'")

cur.execute("""CREATE TABLE IF NOT EXISTS major_Terms(
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
            user_id integer PRIMARY KEY,
            username TEXT,
            email TEXT NOT NULL UNIQUE,
            verified INTEGER DEFAULT 0
            )""")




conn.commit()
conn.close()