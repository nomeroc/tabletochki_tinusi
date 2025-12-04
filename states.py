# states.py
from aiogram.fsm.state import StatesGroup, State


class AddPillStates(StatesGroup):
    name = State()
    time = State()
    schedule_type = State()
    days_custom = State()


class EditPillStates(StatesGroup):
    choose_id = State()
    time = State()
    days = State()


class DeletePillStates(StatesGroup):
    choose_id = State()
