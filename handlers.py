import json

from aiogram import Router, F
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.utils.formatting import Text

from config import cookie_key
from src.services.categories import CategoriesService
from src.services.auth import AuthService
from src.services.transactions import TransactionsService
from src.utils import kb
from src.routers.categories import router as categories_router
from src.routers.auth import router as auth_router
from src.routers.transactions import router as transactions_router
from src.users import users

router = Router()
router.include_router(categories_router)
router.include_router(auth_router)
router.include_router(transactions_router)

with open('users_db.json', encoding='utf-8') as file:
    for user, data in json.load(file).items():
        users[int(user)] = data


@router.message(Command('start'))
async def start_handler(msg: Message):
    user_id = msg.from_user.id
    if user_id in users:
        content = Text(f'Привет, {users[user_id]["username"]}!.')
        await msg.answer(**content.as_kwargs(), reply_markup=kb.main_menu())
    else:
        await msg.answer('Привет! Вы не авторизованы.', reply_markup=kb.auth())


async def auth(
        user_id: int | None = None, email: str | None = None,
        password: str | None = None
):
    if not email or not password:
        email = users[user_id]['email']
        password = users[user_id]['password']

    response = await AuthService.login(email, password)
    if response.status_code == 204:
        return response.cookies[cookie_key]


@router.message(F.text.lower() == kb.BT_MAIN_MENU.lower())
async def go_to_main_menu(msg: Message, state: FSMContext):
    await msg.answer('Вы в главном меню.', reply_markup=kb.main_menu())
    await state.clear()


@router.message(F.text.lower() == kb.BT_SUMMARY.lower())
async def get_summary(msg: Message, state: FSMContext):
    user_id = msg.from_user.id
    token = users[user_id]['token']

    response = await CategoriesService.get(token, 'bank')
    balance = sum(x['amount'] for x in response.json())

    response = await TransactionsService.get(token)
    transactions = response.json()
    expenses = 0
    incomes = 0
    if transactions:
        for transaction in response.json():
            if transaction['group'] == 'expense':
                expenses += transaction['amount']
            elif transaction['group'] == 'income':
                incomes += transaction['amount']

    delta = incomes - expenses
    if delta > 0:
        delta_emoji = '🟢'
    elif delta == 0:
        delta_emoji = '🟡'
    else:
        delta_emoji = '🔴'

    answer_text = f'''▫ <b>Баланс</b>: {balance} рублей
💰 <b>Доходы</b>: {incomes} рублей
💸 <b>Расходы</b>: {expenses} рублей
{delta_emoji} <b>Разница</b>: {delta} рублей
'''

    await msg.answer(answer_text, reply_markup=kb.main_menu())
    await state.clear()
