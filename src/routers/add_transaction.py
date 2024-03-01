import datetime

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import (Message, InlineKeyboardButton, InlineKeyboardMarkup,
                           CallbackQuery)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.services.categories.banks import BanksService
from src.services.categories.ei_categories import EiCategoriesService
from src.services.transactions import TransactionsService
from src.states.transactions import AddTransaction
from src.users import users
from src.utils import kb

router = Router()


def get_kb_group():
    buttons = [
        [InlineKeyboardButton(text='Поступление',
                              callback_data='transaction_income')],
        [InlineKeyboardButton(text='Расход',
                              callback_data='transaction_expense')],
        [InlineKeyboardButton(text='Перевод',
                              callback_data='transaction_transfer')]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


def get_kb_dates():
    buttons = [
        [InlineKeyboardButton(text='Сегодня',
                              callback_data='transaction_today')],
        [InlineKeyboardButton(text='Вчера',
                              callback_data='transaction_yesterday')],
        [InlineKeyboardButton(text='Другая дата',
                              callback_data='transaction_other')]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


def from_list(data: dict, cols: int = 1) -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    for id, el in data.items():
        builder.add(
            InlineKeyboardButton(text=el,
                                 callback_data=f'transaction_{id}_{el}'))
    builder.adjust(cols)
    return builder


@router.message(F.text.lower() == kb.BT_ADD_TRANSACTION.lower())
async def add_transaction(msg: Message, state: FSMContext):
    answer_text = '➕ Добавление транзакции\n'
    await state.update_data(answer_text=answer_text)
    answer_text += '\n🔄 Выберите тип:'
    await msg.answer(answer_text, reply_markup=get_kb_group())
    await state.set_state(AddTransaction.choosing_group)


@router.callback_query(AddTransaction.choosing_group,
                       F.data.startswith('transaction_'))
async def choice_bank(callback: CallbackQuery, state: FSMContext):
    group = callback.data.split('_')[1]
    user_id = callback.from_user.id
    token = users[user_id]['token']
    answer_text = (await state.get_data())['answer_text']
    await state.update_data(group=group)

    response = await BanksService.read(token)

    assert response.status_code == 200

    banks_data = response.json()
    banks_for_kb = {bank['id']: bank['name'] for bank in banks_data}

    builder = from_list(banks_for_kb)
    answer_text += f"\n🔄 Тип: {'расход' if group == 'expense' else 'поступление' if group == 'income' else 'перевод'}"

    await callback.message.edit_text(
        answer_text + f'\n\n⬆ Выберите счёт {"поступления" if group == "income" else "списания"}:',
        reply_markup=builder.as_markup()
    )
    await state.update_data(answer_text=answer_text)
    await state.set_state(AddTransaction.choosing_category_from)
    await callback.answer()


@router.callback_query(AddTransaction.choosing_category_from,
                       F.data.startswith('transaction_'))
async def choice_destination(callback: CallbackQuery, state: FSMContext):
    state_date = await state.get_data()
    group = state_date['group']
    answer_text = state_date['answer_text']
    user_id = callback.from_user.id
    token = users[user_id]['token']
    id_bank, bank = callback.data.split('_')[1:]
    await state.update_data(id_bank=int(id_bank))

    if group == 'transfer':
        response = await BanksService.read(token)
    else:
        response = await EiCategoriesService.read(token, group)

    assert response.status_code == 200

    categories_data = response.json()
    categories_for_kb = {category['id']: category['name']
                         for category in categories_data}

    builder = from_list(categories_for_kb)

    if group == 'income':
        a = 'Выберите категорию поступления'
    elif group == 'expense':
        a = 'Выберите категория расходов'
    else:
        a = 'Выберите счёт назначения'

    answer_text += f'\n⬆ Счёт {"списания" if group != "income" else "поступления"}: {bank}'
    await callback.message.edit_text(
        answer_text + f'\n\n⬇ {a}:',
        reply_markup=builder.as_markup()
    )
    await state.update_data(answer_text=answer_text)
    await state.set_state(AddTransaction.choosing_category_to)
    await callback.answer()


@router.callback_query(AddTransaction.choosing_category_to,
                       F.data.startswith('transaction_'))
async def choosing_date(callback: CallbackQuery, state: FSMContext):
    id_dest, dest = callback.data.split('_')[1:]
    state_date = await state.get_data()
    answer_text = state_date['answer_text']
    await state.update_data(id_destination=int(id_dest))
    answer_text += f'\n⬇ Категория назначения: {dest}'
    await callback.message.edit_text(
        answer_text + '\n\n📅 Выберите дату:',
        reply_markup=get_kb_dates())
    await state.update_data(answer_text=answer_text)
    await state.set_state(AddTransaction.choosing_date)
    await callback.answer()


@router.callback_query(AddTransaction.choosing_date,
                       F.data.startswith('transaction_'))
async def pre_entering_amount(callback: CallbackQuery, state: FSMContext):
    date_str = callback.data.split('_')[1]

    if date_str in ['today', 'yesterday']:
        if date_str == 'today':
            date_dt_str = datetime.date.today().strftime('%Y-%m-%d')
        else:
            date_dt_str = ((datetime.date.today() - datetime.timedelta(days=1))
                           .strftime('%Y-%m-%d'))
        await entering_amount(callback, state, date_dt_str)

    else:
        await callback.message.edit_text('Введите дату (гггг-мм-дд):')
        await state.update_data(callback=callback)
        await state.set_state(AddTransaction.entering_date)


@router.message(AddTransaction.entering_date, F.text)
async def entering_date(msg: Message, state: FSMContext):
    state_date = await state.get_data()
    date_str = msg.text
    datetime.datetime.strptime(date_str, '%Y-%m-%d')
    await entering_amount(state_date['callback'], state, date_str)


async def entering_amount(
        callback: CallbackQuery, state: FSMContext, date_dt_str: str
):
    state_date = await state.get_data()
    answer_text = state_date['answer_text']
    await state.update_data(date=date_dt_str)
    await state.set_state(AddTransaction.entering_amount)
    await callback.message.delete()
    answer_text += f'\n📅 Дата: {date_dt_str}'

    old_message = await callback.message.answer(
        text=answer_text + '\n\n💰 Введите сумму:',
        reply_markup=kb.main_menu_button())
    await state.update_data(answer_text=answer_text,
                            delete_message=old_message.message_id)
    await callback.answer()


@router.message(AddTransaction.entering_amount, F.text)
async def send_transaction(msg: Message, state: FSMContext):
    state_data = await state.get_data()
    answer_text = state_data['answer_text']
    delete_message = state_data['delete_message']
    amount = float(msg.text)
    user_id = msg.from_user.id
    token = users[user_id]['token']
    response = await TransactionsService.add(
        token,
        group=state_data['group'],
        amount=amount,
        id_bank=state_data['id_bank'],
        id_destination=state_data['id_destination'],
        date=state_data['date']
    )

    answer_text += f'\n💰 Сумма: {amount}'

    if response.status_code == 200:
        await msg.delete()
        await msg.bot.delete_message(msg.chat.id, delete_message)
        await msg.answer(answer_text + '\n\n✅ Транзакция добавлена!',
                         reply_markup=kb.main_menu())
    elif response.status_code in range(400, 500):
        await msg.answer('Ошибка при добавлении транзакции!',
                         reply_markup=kb.main_menu())
    else:
        await msg.answer(
            'Транзакции не добавлена. Какие-то проблемы со стороны сервера. '
            'Попробуйте позже.',
            reply_markup=kb.main_menu())
    await state.clear()
