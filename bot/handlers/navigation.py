from config import HOME_TEXT
from bot.instance import bot
from bot.handlers.commands import help_command
from bot.keyboards import build_login_keyboard, build_main_menu_keyboard
from bot.messaging import edit_message
from bot.state import user_history


def show_about(call, parts):
    about_text = (
        "للتسجيل في البوت والحصول على صلاحية الوصول للمحتوى، "
        "يلزم إدخال بريدك الجامعي فقط (لا يُقبل البريد الشخصي). "
        "سيتم إرسال رمز التحقق إلى بريدك الإلكتروني.\n\n"
        "⚠️ ملاحظة: في بعض الأحيان قد يصل رمز التحقق إلى البريد غير الهام (Spam).\n\n"
        "في حال واجهتك أي مشكلة، يرجى التواصل مع الدعم الفني عبر:\n"
        "@Course_path_support"
    )
    bot.send_message(call.message.chat.id, about_text, reply_markup=build_login_keyboard())


def show_back(call, parts):
    from bot.routes import route  # lazy import لتفادي دورة استيراد مع routes.py

    user_id = call.from_user.id
    stack = user_history.get(user_id, [])

    if not stack:
        edit_message(call, HOME_TEXT, build_main_menu_keyboard())
        return

    current = stack.pop() if stack else None

    while stack and stack[-1] == current:
        stack.pop()

    if not stack:
        edit_message(call, HOME_TEXT, build_main_menu_keyboard())
        return

    prev_data = stack[-1]
    route(call, prev_data)


def show_home(call, parts):
    user_history.pop(call.from_user.id, None)
    user_id = call.from_user.id
    stack = user_history.get(user_id, [])
    stack.clear()
    edit_message(call, HOME_TEXT, build_main_menu_keyboard())


def show_help(call, parts):
    help_command(call.message)
