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
    choosing_group = State()
    choosing_action_1 = State()
    choosing_action_2 = State()
    choosing_bank = State()
    entering_name = State()
    entering_amount = State()
    entering_credit_card_balance = State()
    entering_credit_card_limit = State()
