# keyboards.py
from typing import Set

from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from strings import strings

# Ukrainian short and full day names
DAY_SHORT_UA = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Нд"]
DAY_FULL_UA = [
    "Понеділок",
    "Вівторок",
    "Середа",
    "Четвер",
    "П'ятниця",
    "Субота",
    "Неділя",
]


def main_keyboard() -> ReplyKeyboardMarkup:
    b = strings.buttons
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=b["add_pill"]),
                KeyboardButton(text=b["my_pills"]),
            ],
            [
                KeyboardButton(text=b["edit_pill"]),
                KeyboardButton(text=b["delete_pill"]),
            ],
            [
                KeyboardButton(text=b["history"]),
            ],
        ],
        resize_keyboard=True,
    )


def schedule_type_keyboard() -> InlineKeyboardMarkup:
    b = strings.buttons
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=b["schedule_daily"],
                    callback_data="schedule:daily",
                ),
                InlineKeyboardButton(
                    text=b["schedule_custom"],
                    callback_data="schedule:custom",
                ),
            ]
        ]
    )


def days_select_keyboard(selected: Set[int]) -> InlineKeyboardMarkup:
    """
    selected: set of weekday indices (0=Mon ... 6=Sun)
    Button text: 'Пн ✖️' / 'Пн ✔️'
    """
    rows = []
    for i in range(0, 7, 2):
        row = []
        for idx in (i, i + 1):
            if idx > 6:
                continue
            checked = "✔️" if idx in selected else "✖️"
            text = f"{DAY_SHORT_UA[idx]} {checked}"
            row.append(
                InlineKeyboardButton(
                    text=text,
                    callback_data=f"daytoggle:{idx}",
                )
            )
        rows.append(row)

    # confirm row
    b = strings.buttons
    rows.append(
        [
            InlineKeyboardButton(
                text=b["days_confirm"],
                callback_data="days_confirm",
            )
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=rows)


def reminder_inline(reminder_id: int) -> InlineKeyboardMarkup:
    b = strings.buttons
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=b["pill_taken"],
                    callback_data=f"taken:{reminder_id}",
                ),
                InlineKeyboardButton(
                    text=b["remind_later_15"],
                    callback_data=f"snooze:{reminder_id}:15",
                ),
            ]
        ]
    )

def back_keyboard() -> ReplyKeyboardMarkup:
    b = strings.buttons
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=b["back_to_main"])]],
        resize_keyboard=True,
    )