from aiogram.fsm.state import StatesGroup, State


class ManageBank(StatesGroup):
    choosing_action = State()


class AddBank(StatesGroup):
    choosing_group = State()
    entering_name = State()
    entering_amount = State()
    entering_credit_card_balance = State()
    entering_credit_card_limit = State()


class ChangeBank(StatesGroup):
    choosing_action = State()
    entering_new_value = State()
