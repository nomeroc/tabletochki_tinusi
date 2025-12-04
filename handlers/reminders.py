# handlers/reminders.py
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo
import logging

from aiogram import Dispatcher, F, Bot
from aiogram.types import CallbackQuery
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import settings
from strings import strings
from keyboards import reminder_inline
from db import (
    get_reminders_for_time,
    set_last_sent_today,
    insert_history,
    get_reminder_by_id,
)


logger = logging.getLogger(__name__)
tz = ZoneInfo(settings.timezone)
scheduler = AsyncIOScheduler(timezone=settings.timezone)

# one global scheduler for whole app
scheduler = AsyncIOScheduler(timezone=settings.timezone)


async def check_reminders_job(bot: Bot):
    # час у таймзоні, де живеш ти і scheduler (Europe/Kyiv)
    now = datetime.now(tz)
    today_str = now.date().isoformat()
    time_str = now.strftime("%H:%M")
    weekday = now.weekday()

    logger.info(
        f"[check_reminders_job] now={now}, time_str={time_str}, weekday={weekday}")

    rows = get_reminders_for_time(time_str)
    logger.info(
        f"[check_reminders_job] found {len(rows)} reminders with time {time_str}")

    if not rows:
        return

    for r in rows:
        logger.info(
            f"[check_reminders_job] candidate id={r['id']} days={r['days']} last_sent_date={r['last_sent_date']}"
        )

        if r["days"] != "daily":
            day_list = [int(x) for x in r["days"].split(",") if x]
            if weekday not in day_list:
                logger.info(
                    f"[check_reminders_job] skip id={r['id']} (weekday not in {day_list})")
                continue

        if r["last_sent_date"] == today_str:
            logger.info(
                f"[check_reminders_job] skip id={r['id']} (already sent today)")
            continue

        from random import choice
        phrase_template = strings.reminder_phrases or ["Time to take {pill} 💊"]
        text = choice(phrase_template).replace("{pill}", r["pill_name"])

        logger.info(
            f"[check_reminders_job] sending to user={r['user_id']} pill={r['pill_name']}")

        await bot.send_message(
            chat_id=r["user_id"],
            text=text,
            reply_markup=reminder_inline(r["id"]),
        )

        set_last_sent_today(r["id"])
        insert_history(r["id"], now.isoformat(timespec="seconds"), "sent")


async def send_snoozed_reminder(bot: Bot, reminder_id: int):
    row = get_reminder_by_id(reminder_id)
    if not row:
        return
    from random import choice
    phrase_template = strings.reminder_phrases or ["Time to take {pill} 💊"]
    text = choice(phrase_template).replace("{pill}", row["pill_name"])

    await bot.send_message(
        chat_id=row["user_id"],
        text=text + " (повторне нагадування) ⏰",
        reply_markup=reminder_inline(reminder_id),
    )
    insert_history(reminder_id, datetime.now(
        tz).isoformat(timespec="seconds"), "snoozed_15")


async def reminder_taken(callback: CallbackQuery):
    _, id_str = callback.data.split(":", 1)
    reminder_id = int(id_str)

    insert_history(reminder_id, datetime.now(
        tz).isoformat(timespec="seconds"), "taken")
    await callback.answer(strings.texts["taken_ok"])
    # прибираємо кнопки
    await callback.message.edit_reply_markup(reply_markup=None)


async def reminder_snooze(callback: CallbackQuery, bot: Bot):
    _, id_str, minutes_str = callback.data.split(":")
    reminder_id = int(id_str)
    minutes = int(minutes_str)

    now_local = datetime.now(tz)

    insert_history(
        reminder_id,
        now_local.isoformat(timespec="seconds"),
        f"snooze_{minutes}",
    )

    run_date = now_local + timedelta(minutes=minutes)
    scheduler.add_job(
        send_snoozed_reminder,
        "date",
        run_date=run_date,
        args=(bot, reminder_id),
    )

    # прибираємо кнопки з поточного повідомлення
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.answer(strings.texts["snooze_ok"].format(minutes=minutes))



async def reminder_snooze_handler(callback: CallbackQuery, bot: Bot):
    await reminder_snooze(callback, bot)


def register_reminder_handlers(dp: Dispatcher):
    dp.callback_query.register(
        reminder_taken,
        F.data.startswith("taken:"),
    )

    dp.callback_query.register(
        reminder_snooze_handler,
        F.data.startswith("snooze:"),
    )


async def setup_scheduler(bot: Bot):
    scheduler.add_job(
        check_reminders_job,
        "interval",
        minutes=1,
        args=(bot,),
        id="check_reminders",
        replace_existing=True,
    )
    scheduler.start()
