import json

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from src.users import users
from src.utils import kb
from config import cookie_key
from src.services.auth import AuthService
from src.states.auth import Login

router = Router()


@router.message(Login.entering_email, F.text)
async def entry_email(msg: Message, state: FSMContext):
    await state.update_data(email=msg.text.lower())
    await msg.answer('Введите пароль:', reply_markup=kb.main_menu_button())
    await state.set_state(Login.entering_password)


@router.message(StateFilter(None), F.text.lower() == kb.BT_LOGIN.lower())
async def login_handler(msg: Message, state: FSMContext):
    user_id = msg.from_user.id
    user = user_id in users
    if user:
        await msg.answer('Вы уже авторизованы.',
                         reply_markup=kb.main_menu())
    else:
        await msg.answer('Введите e-mail:.',
                         reply_markup=kb.main_menu_button())
        await state.set_state(Login.entering_email)


@router.message(F.text.lower() == kb.BT_REGISTER.lower())
async def register_handler(msg: Message):
    user_id = msg.from_user.id
    # user = crud.get_user(user_id)
    user = user_id in users
    if user:
        await msg.answer('Вы уже зарегистрированы.',
                         reply_markup=kb.main_menu())
    else:
        # crud.add_user(user_id, msg.chat.username)
        await msg.answer('Ты зарегистрирован.', reply_markup=kb.main_menu())


@router.message(Login.entering_password, F.text)
async def entry_password(msg: Message, state: FSMContext):
    user_data = await state.get_data()
    email = user_data['email']
    password = msg.text

    response = await AuthService.login(email, password)

    if response.status_code == 204:
        token = response.cookies[cookie_key]
        response = await AuthService.get_profile(token)
        username = response.json()['username']

        await msg.answer(f'Привет, {username}!',
                         reply_markup=kb.main_menu())
        await state.clear()

        users[msg.from_user.id] = {
            'email': email,
            'password': password,
            'username': username,
            'token': token
        }
        with open('users_db.json', 'w', encoding='utf-8') as file:
            json.dump(users, file)

    else:
        await msg.answer(f'Неверный e-mail или пароль.')
