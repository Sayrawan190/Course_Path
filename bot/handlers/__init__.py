# استيراد كل موديولات الـ handlers هنا يسجل كل الـ decorators
# (bot.message_handler / bot.callback_query_handler) بنفس الترتيب المطلوب.
# الترتيب مهم: لازم أوامر السلاش والفلاتر النصية المحددة تُسجَّل قبل
# handle_text (اللي يلتقط أي رسالة نصية) حتى ما تسرقه.
from bot.handlers import commands       # noqa: F401  /start /help
from bot.handlers import admin          # noqa: F401  /SQL /Sync /Output /SendFixError /Commands
from bot.handlers import content_admin  # noqa: F401  !Add !DeleteFile
from bot.handlers import catalog_admin  # noqa: F401  !AddCourse !SetInfo !SetSources !DeleteCourse !Reorder
from bot.handlers import search         # noqa: F401  handle_text (بحث تلقائي عن رمز المادة)
from bot.handlers import callback       # noqa: F401  callback_query_handler
