from aiogram.fsm.state import StatesGroup, State


class ManageCategory(StatesGroup):
    choosing_action = State()
    choosing_category_group = State()
    choosing_category_name = State()


class ChangeBalance(StatesGroup):
    entering_new_balance = State()


class AddExpense(StatesGroup):
    choosing_category = State()
    entering_amount = State()


class AddIncome(StatesGroup):
    entering_amount = State()


