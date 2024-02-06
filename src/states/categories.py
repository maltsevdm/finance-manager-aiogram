from aiogram.fsm.state import StatesGroup, State


class ManageCategory(StatesGroup):
    choosing_action = State()


class AddCategory(StatesGroup):
    choosing_group = State()
    entering_name = State()


class ChangeCategory(StatesGroup):
    choosing_group = State()
    choosing_action_1 = State()
    choosing_action_2 = State()
    choosing_category = State()
    entering_name = State()
    entering_amount = State()
