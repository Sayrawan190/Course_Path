from pathlib import Path
import re

asem = Path(r"DataBase/Courses/STAT-352/Exams/Quizzes")
for f in asem.rglob("*Quiz_ch8&9&10*"):
    print(f)
    # print(f.name, " --> ", f.name.split("_", 1)[1].split(".", -1)[0])
    



print(asem.rglob("*Quiz_ch8&9&10*"))