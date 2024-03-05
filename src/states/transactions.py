from aiogram.fsm.state import StatesGroup, State


class AddTransaction(StatesGroup):
    choosing_group = State()
    choosing_category_from = State()
    choosing_category_to = State()
    entering_amount = State()
    choosing_date = State()
    entering_date = State()
    entering_note = State()


class AddExpense(StatesGroup):
    choosing_category = State()
    entering_amount = State()


class AddIncome(StatesGroup):
    entering_amount = State()


class EditTransaction(StatesGroup):
    choosing_action = State()
    entering_new_value = State()
