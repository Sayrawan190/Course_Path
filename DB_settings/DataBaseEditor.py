import sqlite3

conn = sqlite3.connect(r"DataBase/FCIT_bot.db", check_same_thread=False)
cur = conn.cursor()

# cur.execute("DROP TABLE IF EXISTS slides")
# cur.execute("DROP TABLE IF EXISTS exams")

# 810634477|x5awc|sbahakim0006@stu.kau.edu.sa|1  xxxxx
# 840957323|hodorth|talshehri0155@stu.kau.edu.sa|1
# 978939794|smmb12|sbabgi0008@stu.kau.edu.sa|1
# 1042067067|KHiA6|malkhayyt@stu.kau.edu.sa|1
# 1401478668|Sayrawan_190|aalserawan@stu.kau.edu.sa|1  xxxxx
# 1824597807|onlym_h|malhusaini0003@stu.kau.edu.sa|1  xxxxx
# 5016425883|Emporer0|malraegi0001@stu.kau.edu.sa|1
# 7911073309|r2plx|Abazi0007@stu.kau.edu.sa|1

# cur.execute("INSERT INTO users VALUES (840957323,'hodorth','talshehri0155@stu.kau.edu.sa',1)")
# cur.execute("INSERT INTO users VALUES (978939794,'smmb12','sbabgi0008@stu.kau.edu.sa',1)")
# cur.execute("INSERT INTO users VALUES (1042067067,'KHiA6','malkhayyt@stu.kau.edu.sa',1)")
# cur.execute("INSERT INTO users VALUES (5016425883,'Emporer0','malraegi0001@stu.kau.edu.sa',1)")
# cur.execute("INSERT INTO users VALUES (7911073309,'r2plx','Abazi0007@stu.kau.edu.sa',1)")


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

def delete_user(user_id):
    conn = sqlite3.connect(r"DataBase/FCIT_bot.db", check_same_thread=False)
    cur = conn.cursor()

    cur.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
    conn.commit()

    deleted = cur.rowcount
    conn.close()

    return deleted > 0

ADMIN_IDS = {1401478668, 810634477}

def execute_sql_query(sql_text):
    conn = sqlite3.connect(r"DataBase/FCIT_bot.db", check_same_thread=False)
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