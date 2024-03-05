import datetime
import json

import secrets
import string
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.utils.formatting import Text

from src.services.config import cookie_key
from src.services.categories.banks import BanksService
from src.services.auth import AuthService
from src.services.categories.ei_categories import EiCategoriesService
from src.services.transactions import TransactionsService
from src.utils import kb, utils
from src.routers.ei_categories import router as ei_categories_router
from src.routers.banks import router as banks_router
from src.routers.auth import router as auth_router
from src.routers.add_transaction import router as transactions_router
from src.routers.transactions_history import (
    router as transactions_history_router)
from src.users import users

router = Router()
router.include_router(ei_categories_router)
router.include_router(banks_router)
router.include_router(auth_router)
router.include_router(transactions_router)
router.include_router(transactions_history_router)

users_file = 'users_db.json'

with open(users_file, encoding='utf-8') as file:
    for user, data in json.load(file).items():
        users[int(user)] = data

with open('src/utils/summary_template.txt', encoding='utf-8') as file:
    summary_template = file.read()


def generate_password() -> str:
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for i in range(12))


async def auth(
        user_id: int | None = None, email: str | None = None,
        password: str | None = None
) -> str:
    if not email or not password:
        email = users[user_id]['email']
        password = users[user_id]['password']

    response = await AuthService.login(email, password)
    if response.status_code == 204:
        return response.cookies[cookie_key]


@router.message(Command('start'))
async def start_handler(msg: Message):
    user_id = msg.from_user.id
    username = msg.chat.username
    first_name = msg.from_user.first_name

    if user_id not in users:
        email = username + '@gmail.com'
        password = generate_password()

        response = await AuthService.register(email, password, username)
        if response.status_code != 201:
            raise RuntimeError(f'Пользователь не зарегистрирован. '
                               f'{username=}, {email=}, {password=}, '
                               f'{response.status_code=}')

        token = await auth(user_id, email, password)

        users[user_id] = {
            'email': email,
            'password': password,
            'username': username,
            'token': token
        }

        with open(users_file, 'w', encoding='utf-8') as file:
            json.dump(users, file, ensure_ascii=False, indent=4)
    else:
        email = users[int(user_id)]['email']
        password = users[int(user_id)]['password']
        token = await auth(user_id, email, password)
        print(token)

    content = Text(f'Привет, {first_name}!')
    await msg.answer(**content.as_kwargs(), reply_markup=kb.main_menu())


@router.callback_query(F.data == 'exit')
@router.message(F.text.lower() == kb.BT_MAIN_MENU.lower())
async def go_to_main_menu(msg: Message | CallbackQuery, state: FSMContext):
    if isinstance(msg, CallbackQuery):
        await msg.message.edit_text('Вы в главном меню.')
    else:
        await msg.answer('Вы в главном меню.', reply_markup=kb.main_menu())
    await state.clear()


@router.message(F.text.lower() == kb.BT_SUMMARY.lower())
async def get_summary(msg: Message, state: FSMContext):
    user_id = msg.from_user.id
    token = users[user_id]['token']

    response = await BanksService.read(token)
    balance = sum(x['amount'] for x in response.json())

    start_month_date = utils.get_start_month_date()

    incomes_fact = (await TransactionsService.get_sum(
        token,
        group='income',
        date_from=start_month_date,
        date_to=datetime.date.today()
    )).json()

    expenses_fact = (await TransactionsService.get_sum(
        token,
        group='expense',
        date_from=start_month_date,
        date_to=datetime.date.today()
    )).json()

    categories = (await EiCategoriesService.read(
            token,
            date_from=utils.get_start_month_date(),
            date_to=datetime.date.today()
    )).json()

    incomes_general = 0
    expenses_general = 0
    for category in categories:
        if category['group'] == 'income':
            if category['monthly_limit'] is None:
                incomes_general += category['amount']
            else:
                incomes_general += (
                    category['amount']
                    if category['amount'] > category['monthly_limit']
                    else category['monthly_limit'])
        else:
            if category['monthly_limit'] is None:
                expenses_general += category['amount']
            else:
                expenses_general += (
                    category['amount']
                    if category['amount'] > category['monthly_limit']
                    else category['monthly_limit'])

    incomes_predict = incomes_general - incomes_fact
    expenses_predict = expenses_general - expenses_fact

    answer_text = summary_template.format(
        balance=balance,
        incomes_fact=incomes_fact,
        incomes_predict=incomes_predict,
        incomes_general=incomes_general,
        expenses_fact=expenses_fact,
        expenses_predict=expenses_predict,
        expenses_general=expenses_general,
        delta_fact=incomes_fact - expenses_fact,
        delta_predict=incomes_predict - expenses_predict,
        delta_general=incomes_general - expenses_general
    )

    await msg.answer(answer_text, reply_markup=kb.main_menu())
    await state.clear()
