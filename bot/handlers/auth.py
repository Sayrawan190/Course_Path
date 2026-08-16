from config import HOME_TEXT
from logging_config import logger
from services import totp
from bot.instance import bot
from bot.keyboards import build_main_menu_keyboard
from db.queries import add_or_verify_user, get_user_verified


def _redispatch_if_command(message):
    """
    next_step_handler يبلع أي رسالة جاية من نفس المحادثة (حتى لو كانت أمر
    زي /SQL) قبل ما توصل لمعالجات الأوامر العادية. هذي الدالة تكتشف إذا
    كانت الرسالة أمر بوت (يبدأ بـ / أو !) وتعيد توجيهها للمسار الطبيعي
    بدل ما تتفسر كإيميل أو كود تحقق.
    """
    text = message.text or ""
    if text.startswith("/") or text.startswith("!"):
        bot.process_new_messages([message])
        return True
    return False


def start_verify_button(call, parts):
    user_id = call.from_user.id

    row = get_user_verified(user_id)

    if row and row[0] > 0:
        bot.send_message(call.message.chat.id, HOME_TEXT, reply_markup=build_main_menu_keyboard())
        return

    msg = bot.send_message(call.message.chat.id, "أرسل ايميلك الجامعي للتحقق:")
    bot.register_next_step_handler(msg, ask_email)


def ask_email(message):
    if _redispatch_if_command(message):
        return

    user_id = message.from_user.id
    email = message.text

    if not totp.check_Email(email):
        msg = bot.send_message(message.chat.id, "الرجاء ارسال ايميلك الجامعي بشكل صحيح (مثال: xxxxx@stu.kau.edu.sa")
        bot.register_next_step_handler(msg, ask_email)
        return

    if totp.is_email_used(email):
        msg = bot.send_message(message.chat.id, "هذا الإيميل مستخدم مسبقاً ادخل ايميل غير مستخدم")
        bot.register_next_step_handler(msg, ask_email)
        return

    otp = totp.create_otp(user_id, email)
    totp.TOTP_Send(email, otp)
    msg = bot.send_message(message.chat.id, "تم إرسال كود التحقق الرجاء ادخاله خلال 3 دقايق")
    bot.register_next_step_handler(msg, verify)


def verify(message):
    if _redispatch_if_command(message):
        return

    user_id = message.from_user.id
    username = message.from_user.username
    if not username:
        username = "None"
    try:
        user_input = int(message.text)
    except ValueError:
        msg = bot.send_message(message.chat.id, "الرجاء ادخال كود التحقق من ارقام فقط")
        bot.register_next_step_handler(msg, verify)
        return

    ok, msg_text = totp.verify_otp(user_id, user_input)

    if ok:
        email = totp.otp_storage.get(user_id, {}).get("email", None)
        logger.info("Verify -> userID= %s || Username= %s || email= %s", message.from_user.id, message.from_user.username, email)
        if email:
            add_or_verify_user(user_id, username, email, verified=True)
            del totp.otp_storage[user_id]
            bot.send_message(
                message.chat.id,
                "تم تسجيل دخولك بنجاح",
                reply_markup=build_main_menu_keyboard()
            )
    else:
        msg = bot.send_message(message.chat.id, "أدخل الكود الصحيح:")
        bot.register_next_step_handler(msg, verify)
