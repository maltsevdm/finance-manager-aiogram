from aiogram.fsm.state import StatesGroup, State


class ManageEiCategory(StatesGroup):
    choosing_group = State()
    choosing_action = State()


class AddCategory(StatesGroup):
    entering_name = State()
    entering_monthly_limit = State()


class ChangeCategory(StatesGroup):
    choosing_action = State()
    entering_new_value = State()

