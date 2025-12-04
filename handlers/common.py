# handlers/common.py
from aiogram import Dispatcher
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext

from strings import strings
from keyboards import main_keyboard
from db import get_recent_history


async def back_to_main_handler(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        strings.texts["start"],
        reply_markup=main_keyboard(),
    )


async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(strings.texts["start"], reply_markup=main_keyboard())


async def cmd_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        strings.texts["cancelled"],
        reply_markup=main_keyboard(),
    )


async def history_handler(message: Message):
    rows = get_recent_history(message.from_user.id)
    if not rows:
        await message.answer(strings.texts["history_empty"])
        return

    lines = []
    for r in rows:
        lines.append(f"{r['sent_at']} — {r['pill_name']} ({r['action']})")
    await message.answer("📜 *Last reminders:*\n\n" + "\n".join(lines), parse_mode="Markdown")


def register_common_handlers(dp: Dispatcher):
    dp.message.register(cmd_start, Command("start"))
    dp.message.register(cmd_cancel, Command("cancel"))

    dp.message.register(history_handler, Command("history"))
    dp.message.register(history_handler, lambda m: m.text ==
                        strings.buttons["history"])

    # 👇 новий хендлер на кнопку "Назад у головне меню"
    dp.message.register(
        back_to_main_handler,
        lambda m: m.text == strings.buttons["back_to_main"],
    )
