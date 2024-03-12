import asyncio
import datetime
import time

import aioschedule
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.utils.formatting import Text

from src.database.pymongoAPI import users_db
from config import cookie_key
from src.services.categories.banks import BanksService
from src.services.auth import AuthService
from src.services.categories.ei_categories import EiCategoriesService
from src.services.transactions import TransactionsService
from src.utils import kb, utils
from src.routers.ei_categories import router as ei_categories_router
from src.routers.banks import router as banks_router
from src.routers.add_transaction import router as transactions_router
from src.routers.account import router as account_router
from src.routers.transactions_history import (
    router as transactions_history_router)
from src.utils.utils import generate_password

router = Router()
router.include_router(ei_categories_router)
router.include_router(banks_router)
router.include_router(transactions_router)
router.include_router(transactions_history_router)
router.include_router(account_router)

with open('src/utils/summary_template.txt', encoding='utf-8') as file:
    summary_template = file.read()


async def auth(
        user_id: int | None = None, email: str | None = None,
        password: str | None = None
) -> str:
    if not email or not password:
        user = users_db.find_by_user_id(user_id)
        email = user['email']
        password = user['password']

    response = await AuthService.login(email, password)
    if response.status_code == 204:
        return response.cookies[cookie_key]


async def check_predict_transactions(msg: Message):
    user_id = msg.from_user.id
    token = users_db.get_field_by_user_id(user_id, 'token')

    response = await TransactionsService.get(token)
    assert response.status_code == 200
    transactions = response.json()
    count = len(transactions)
    if count:
        await msg.bot.send_message(
            user_id,
            f'У вас сегодня запланировано {len(transactions)} транзакций.')


async def observe_transactions(msg: Message):
    aioschedule.every().day.at('06:00').do(check_predict_transactions, msg=msg)

    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(0)


@router.message(Command('start'))
async def start_handler(msg: Message):
    user_id = msg.from_user.id
    username = msg.chat.username
    first_name = msg.from_user.first_name
    user = users_db.find_by_user_id(user_id)

    if user is None:
        email = username + '@gmail.com'
        password = generate_password()

        response = await AuthService.register(email, password, username)
        if response.status_code != 201:
            raise RuntimeError(f'Пользователь не зарегистрирован. '
                               f'{username=}, {email=}, {password=}, '
                               f'{response.status_code=}')

        token = await auth(user_id, email, password)

        user = {
            'user_id': user_id,
            'username': username,
            'email': email,
            'password': password,
            'token': token,
            'check_predict_transactions_started': False
        }

        users_db.create_user(user)
    else:
        token = await auth(user_id, user['email'], user['password'])
        users_db.change_user(user_id, 'token', token)

    content = Text(f'Привет, {first_name}!')
    asyncio.create_task(observe_transactions(msg))
    await msg.answer(**content.as_kwargs(), reply_markup=kb.main_menu())


async def print_hello_world(name, msg):
    await msg.answer(f'hello {name}')
    print(time.time(), f'hello {name}')
    return


async def print_hello(msg: Message):
    # aioschedule.every().day.at('11:49').do(print_hello_world, name='world', msg=msg)
    aioschedule.every(5).seconds.do(print_hello_world, name='world', msg=msg)

    while True:
        # await aioschedule.run_pending()
        await msg.answer('hello')
        await asyncio.sleep(1)


@router.message(Command('test'))
async def test(msg: Message):
    asyncio.create_task(print_hello(msg))


@router.message(Command('test2'))
async def test(msg: Message):
    await msg.answer('working')


@router.callback_query(F.data == 'exit')
@router.message(F.text.lower() == kb.BT_MAIN_MENU.lower())
async def go_to_main_menu(msg: Message | CallbackQuery, state: FSMContext):
    if isinstance(msg, CallbackQuery):
        await msg.message.delete()
        await msg.answer('Вы в главном меню.', show_alert=False)
    else:
        await msg.answer('Вы в главном меню.', reply_markup=kb.main_menu())
    await state.clear()


@router.message(F.text.lower() == kb.BT_SUMMARY.lower())
async def get_summary(msg: Message, state: FSMContext):
    user_id = msg.from_user.id
    token = users_db.get_field_by_user_id(user_id, 'token')

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
        date_to=utils.get_end_month_date()
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
