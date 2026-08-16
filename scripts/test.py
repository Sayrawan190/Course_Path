from pathlib import Path
import re

asem = Path(r"DataBase/Courses/STAT-352/Exams/Quizzes")

f = "CPCS-214_Mew_w"
name = f.split("_",1)[-1]
print(name)
