from aiogram.fsm.state import StatesGroup, State


class ChangeBalance(StatesGroup):
    entering_new_balance = State()


