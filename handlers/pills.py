# handlers/pills.py
from datetime import datetime
from typing import Set, List

from aiogram import Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardRemove, CallbackQuery
from aiogram.fsm.context import FSMContext

from strings import strings
from keyboards import (
    main_keyboard,
    schedule_type_keyboard,
    days_select_keyboard,
    DAY_FULL_UA,
    back_keyboard,
)
from states import AddPillStates, EditPillStates, DeletePillStates
from db import (
    create_reminder,
    get_user_reminders,
    delete_reminder,
    get_reminder,
    update_reminder,
)


# ---------- Helpers ----------

def valid_time_str(t: str) -> bool:
    try:
        datetime.strptime(t, "%H:%M")
        return True
    except ValueError:
        return False


def parse_days(text: str):
    """
    Still used for /edit where you type days manually (англійською).
    """
    text = text.strip().lower()
    if text == "daily":
        return "daily"

    mapping = {
        "mon": 0, "monday": 0,
        "tue": 1, "tuesday": 1,
        "wed": 2, "wednesday": 2,
        "thu": 3, "thursday": 3,
        "fri": 4, "friday": 4,
        "sat": 5, "saturday": 5,
        "sun": 6, "sunday": 6,
    }
    parts = [p.strip() for p in text.replace(";", ",").split(",") if p.strip()]
    numbers = []
    for p in parts:
        if p in mapping:
            numbers.append(mapping[p])
        else:
            return None
    if not numbers:
        return None
    return ",".join(sorted(set(str(n) for n in numbers), key=int))


# ---------- ADD PILL FLOW ----------

async def add_pill_entry(message: Message, state: FSMContext):
    await state.set_state(AddPillStates.name)
    await message.answer(
        strings.texts["add_name"],
        parse_mode="Markdown",
        reply_markup=back_keyboard(),
    )


async def add_pill_name(message: Message, state: FSMContext):
    await state.update_data(pill_name=message.text.strip())
    await state.set_state(AddPillStates.time)
    await message.answer(
        strings.texts["add_time"],
        parse_mode="Markdown",
        reply_markup=back_keyboard(),
    )


async def add_pill_time(message: Message, state: FSMContext):
    t = message.text.strip()
    if not valid_time_str(t):
        await message.answer(strings.texts["invalid_time"])
        return

    await state.update_data(time_str=t)
    await state.set_state(AddPillStates.schedule_type)
    await message.answer(
        strings.texts["add_schedule_type"],
        reply_markup=schedule_type_keyboard(),
    )


async def add_schedule_type_callback(callback: CallbackQuery, state: FSMContext):
    # schedule:daily or schedule:custom
    _, mode = callback.data.split(":", 1)
    data = await state.get_data()
    pill_name = data["pill_name"]
    time_str = data["time_str"]

    if mode == "daily":
        create_reminder(
            user_id=callback.from_user.id,
            pill_name=pill_name,
            time_str=time_str,
            days="daily",
        )
        await state.clear()
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.answer()
        await callback.message.answer(
            f"Збережено! ✨\n\n"
            f"Пігулка: *{pill_name}*\n"
            f"Час: *{time_str}*\n"
            f"Дні: *щодня*",
            parse_mode="Markdown",
            reply_markup=main_keyboard(),
        )
    else:
        # custom days – show UA weekday picker
        await state.set_state(AddPillStates.days_custom)
        await state.update_data(selected_days=[])
        await callback.answer()
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.message.answer(
            strings.texts["add_days_custom"],
            reply_markup=days_select_keyboard(set()),
        )


async def days_toggle_callback(callback: CallbackQuery, state: FSMContext):
    """
    Toggle day (✖️ / ✔️) in the inline weekday menu.
    """
    _, idx_str = callback.data.split(":", 1)
    idx = int(idx_str)

    data = await state.get_data()
    selected: Set[int] = set(data.get("selected_days", []))

    if idx in selected:
        selected.remove(idx)
    else:
        selected.add(idx)

    await state.update_data(selected_days=list(selected))

    kb = days_select_keyboard(selected)
    await callback.message.edit_reply_markup(reply_markup=kb)
    await callback.answer()


async def days_confirm_callback(callback: CallbackQuery, state: FSMContext):
    """
    Confirm selected days → save reminder.
    """
    data = await state.get_data()
    selected: List[int] = sorted(set(data.get("selected_days", [])))

    if not selected:
        await callback.answer(
            strings.texts["choose_days_warn_empty"],
            show_alert=True,
        )
        return

    pill_name = data["pill_name"]
    time_str = data["time_str"]

    # DB format: "0,2,4"
    days_str = ",".join(str(i) for i in selected)
    # Human-readable UA list
    human_days = ", ".join(DAY_FULL_UA[i] for i in selected)

    create_reminder(
        user_id=callback.from_user.id,
        pill_name=pill_name,
        time_str=time_str,
        days=days_str,
    )

    await state.clear()
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.answer()
    await callback.message.answer(
        f"Збережено! ✨\n\n"
        f"Пігулка: *{pill_name}*\n"
        f"Час: *{time_str}*\n"
        f"Дні: *{human_days}*",
        parse_mode="Markdown",
        reply_markup=main_keyboard(),
    )


# ---------- LIST PILLS ----------

async def list_pills(message: Message):
    rows = get_user_reminders(message.from_user.id)
    if not rows:
        await message.answer(strings.texts["list_empty"])
        return

    lines = []
    for r in rows:
        if r["days"] == "daily":
            readable = "щодня"
        else:
            readable = r["days"]  # raw 0,2,4 – можна потім гарно показати
        lines.append(
            f"ID: *{r['id']}* — {r['pill_name']} о {r['time_str']} ({readable})"
        )

    await message.answer(
        "📋 *Ваші пігулки:*\n\n" + "\n".join(lines),
        parse_mode="Markdown",
    )


# ---------- DELETE PILL ----------

async def delete_pill_start(message: Message, state: FSMContext):
    await state.set_state(DeletePillStates.choose_id)
    await message.answer(
        strings.texts["delete_ask_id"],
        parse_mode="Markdown",
        reply_markup=back_keyboard(),
    )


async def delete_pill_choose(message: Message, state: FSMContext):
    try:
        pill_id = int(message.text.strip())
    except ValueError:
        await message.answer(strings.texts["need_numeric_id"])
        return

    name = delete_reminder(message.from_user.id, pill_id)
    if not name:
        await message.answer(strings.texts["pill_not_found"])
        return

    await state.clear()
    await message.answer(
        f"Видалено пігулку *{name}* ✅",
        parse_mode="Markdown",
        reply_markup=main_keyboard(),
    )


# ---------- EDIT PILL ----------

async def edit_pill_start(message: Message, state: FSMContext):
    await state.set_state(EditPillStates.choose_id)
    await message.answer(
        strings.texts["edit_ask_id"],
        parse_mode="Markdown",
        reply_markup=back_keyboard(),
    )


async def edit_choose_id(message: Message, state: FSMContext):
    try:
        pill_id = int(message.text.strip())
    except ValueError:
        await message.answer(strings.texts["need_numeric_id"])
        return

    row = get_reminder(message.from_user.id, pill_id)
    if not row:
        await message.answer(strings.texts["pill_not_found"])
        return

    await state.update_data(edit_pill_id=pill_id)
    await state.set_state(EditPillStates.time)

    await message.answer(
        f"Редагуємо *{row['pill_name']}*.\n\n"
        f"Поточний час: {row['time_str']}\n\n"
        + strings.texts["edit_ask_time"],
        parse_mode="Markdown",
    )


async def edit_time(message: Message, state: FSMContext):
    t = message.text.strip()
    if not valid_time_str(t):
        await message.answer(strings.texts["invalid_time"])
        return

    await state.update_data(new_time=t)
    await state.set_state(EditPillStates.days)
    await message.answer(
        strings.texts["edit_ask_days"],
        parse_mode="Markdown",
    )


async def edit_days(message: Message, state: FSMContext):
    days_raw = message.text.strip()
    days = parse_days(days_raw)
    if days is None:
        await message.answer(strings.texts["invalid_days"], parse_mode="Markdown")
        return

    data = await state.get_data()
    pill_id = data["edit_pill_id"]
    new_time = data["new_time"]

    update_reminder(pill_id, new_time, days)
    await state.clear()
    await message.answer(
        f"Оновлено ✅\n\nНовий час: *{new_time}*\nНові дні: *{days_raw}*",
        parse_mode="Markdown",
        reply_markup=main_keyboard(),
    )


# ---------- REGISTER ----------

def register_pill_handlers(dp: Dispatcher):
    b = strings.buttons

    # Add
    dp.message.register(add_pill_entry, Command("add"))
    dp.message.register(add_pill_entry, F.text == b["add_pill"])
    dp.message.register(add_pill_name, AddPillStates.name)
    dp.message.register(add_pill_time, AddPillStates.time)

    # schedule-type callbacks
    dp.callback_query.register(
        add_schedule_type_callback,
        AddPillStates.schedule_type,
        F.data.startswith("schedule:"),
    )

    # day toggle & confirm callbacks
    dp.callback_query.register(
        days_toggle_callback,
        AddPillStates.days_custom,
        F.data.startswith("daytoggle:"),
    )
    dp.callback_query.register(
        days_confirm_callback,
        AddPillStates.days_custom,
        F.data == "days_confirm",
    )

    # List
    dp.message.register(list_pills, Command("list"))
    dp.message.register(list_pills, F.text == b["my_pills"])

    # Delete
    dp.message.register(delete_pill_start, Command("delete"))
    dp.message.register(delete_pill_start, F.text == b["delete_pill"])
    dp.message.register(delete_pill_choose, DeletePillStates.choose_id)

    # Edit
    dp.message.register(edit_pill_start, Command("edit"))
    dp.message.register(edit_pill_start, F.text == b["edit_pill"])
    dp.message.register(edit_choose_id, EditPillStates.choose_id)
    dp.message.register(edit_time, EditPillStates.time)
    dp.message.register(edit_days, EditPillStates.days)
