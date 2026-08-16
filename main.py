import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

from logging_config import logger
from bot.instance import bot

# استيراد الحزمة يسجّل كل الـ handlers (أوامر السلاش، الرسائل، الأزرار)
from bot import handlers  # noqa: F401


def main():
    print("Bot is running... ✅")
    bot.infinity_polling()


if __name__ == "__main__":
    main()
