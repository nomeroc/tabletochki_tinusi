# bot.py
import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from config import settings
from db import init_db
from handlers.common import register_common_handlers
from handlers.pills import register_pill_handlers
from handlers.reminders import register_reminder_handlers, setup_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

async def main():
    init_db()

    bot = Bot(
        settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN),
    )
    dp = Dispatcher()

    # register all handlers
    register_common_handlers(dp)
    register_pill_handlers(dp)
    register_reminder_handlers(dp)

    # scheduler for reminders
    await setup_scheduler(bot)

    print("Bot is running...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
