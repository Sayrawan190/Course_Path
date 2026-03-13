import random
import yagmail
from datetime import datetime, timedelta
import sqlite3

yagBot = yagmail.SMTP("teamcreators15@gmail.com","uomw ldlhkiqv iovg")
otp_storage = {}

#موقت فقط
conn = sqlite3.connect(r"DataBase/FCIT_bot.db")
cursor = conn.cursor()


    #name@stu.kau.edu.sa
    #must be stu first then kau 
def check_Email(email):
    try:
        Fparts = email.split("@")
        #['name','stu.kau.edu.sa']
        LastParts = Fparts[1].split(".")
        stu = LastParts[0]
        kau = LastParts[1]

        if stu == "stu" and kau == "kau":
            return True
        else:
            return False
    except Exception:
        print("Error not valid email")
        return False


def is_email_used(email):
    conn = sqlite3.connect(r"DataBase/FCIT_bot.db")
    cursor = conn.cursor()
    #الايميل مره بس لكل مستخدم مهم جدن
    cursor.execute("SELECT 1 FROM users WHERE email = ?", (email,))
    result = cursor.fetchone()

    return result is not None



def generate_otp():
    return random.randint(100000, 999999)

def create_otp(user_id , email):
    otp = generate_otp()
    expiry_time = datetime.now() + timedelta(minutes=3)

    otp_storage[user_id] = {
        "otp": otp,
        "expires_at": expiry_time,
        "email": email

    }
    print(otp_storage[user_id])
    return otp



def TOTP_Send(ValidEmail , otp):
    yagBot.send(
        to= ValidEmail,
        subject="KAU Verification Code",
        contents=f"رمز التحقق الخاص بك هو: {otp}"
    )


def verify_otp(user_id, user_input):
    if user_id not in otp_storage:
        return False, "ما فيه كود تحقق الرجاء تسجيل دخولك من جديد"

    data = otp_storage[user_id]

    if datetime.now() > data["expires_at"]:
        del otp_storage[user_id]
        return False, "انتهت صلاحية الكود"

    if data["otp"] == user_input:
        return True, "تم التحقق بنجاح"

    return False, "كود خطأ"