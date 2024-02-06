from aiogram.fsm.state import StatesGroup, State


class Register(StatesGroup):
    entering_email = State()
    entering_username = State
    entering_password = State()


class Login(StatesGroup):
    entering_email = State()
    entering_password = State()
