import datetime

from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext

from aiogram.types import (Message, InlineKeyboardButton, InlineKeyboardMarkup,
                           CallbackQuery)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.services.categories.banks import BanksService
from src.services.categories.ei_categories import EiCategoriesService
from src.services.transactions import TransactionsService
from src.states.transactions import AddTransaction, EditTransaction
from src.users import users
from src.utils import kb

router = Router()


def from_list(data: list, cols: int = 1) -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    for el in data:
        id = el['id']
        date = el['date']
        amount = el['amount']
        bank_name = el['bank_name']
        dest_name = el['destination_name']
        group = el['group']
        direction = '<-' if group == 'income' else '->'
        text = f'{date} | {bank_name} {direction} {dest_name} | {amount} руб.'

        builder.add(
            InlineKeyboardButton(text=text, callback_data=f'transaction_{id}'))
    builder.adjust(cols)
    return builder


def kb_navigation(li: list):
    cols = len(li) // 2
    builder = InlineKeyboardBuilder()
    for i, tr in enumerate(li):
        builder.add(
            InlineKeyboardButton(text=str(i + 1),
                                 callback_data=f'edit_{tr["id"]}'))
    builder.add(
        InlineKeyboardButton(text='Ранее', callback_data='earlier'),
        InlineKeyboardButton(text='Позднее', callback_data='later'),
        InlineKeyboardButton(text='Выход', callback_data='exit')
    )
    builder.adjust(cols)
    return builder


def kb_action():
    buttons = [
        [InlineKeyboardButton(text='Изменить счёт списания',
                              callback_data='change_bank')],
        [InlineKeyboardButton(text='Изменить категорию назначения',
                              callback_data='change_dest')],
        [InlineKeyboardButton(text='Изменить дату',
                              callback_data='change_date')],
        [InlineKeyboardButton(text='Изменить сумму',
                              callback_data='change_amount')],
        [InlineKeyboardButton(text='Изменить комментарий',
                              callback_data='change_note')],
        [InlineKeyboardButton(text='Удалить', callback_data='remove')],
        [InlineKeyboardButton(text='🔙 Назад', callback_data='back'),
         InlineKeyboardButton(text='❌ Выход', callback_data='exit')]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


@router.message(StateFilter(None),
                F.text.lower() == kb.BT_TRANSACTIONS_HISTORY.lower())
async def get_history(msg: Message, state: FSMContext):
    answer_text = 'История транзакций:'
    user_id = msg.from_user.id
    token = users[user_id]['token']

    response = await TransactionsService.get(token, limit=10)
    assert response.status_code == 200
    transactions_src = response.json()

    await state.update_data(transactions=transactions_src)

    transactions_data = {}
    for transaction in transactions_src:
        date = transaction['date']
        transactions_data.setdefault(date, []).append(transaction)

    for date, transactions in transactions_data.items():
        answer_text += f'\n\n<b>{date}</b>'
        for i, transaction in enumerate(transactions):
            direction = '⬅' if transaction['group'] == 'income' else '➡'
            answer_text += (
                f'\n{i + 1}. {transaction["bank_name"]} {direction} '
                f'{transaction["destination_name"]} | {transaction["amount"]} ₽')

    answer_text += '\n\nВыберите номер транзакции для редактирования:'

    builder = kb_navigation(transactions_src)

    await msg.answer(answer_text, reply_markup=builder.as_markup())
    await state.set_state(EditTransaction.changing)


@router.callback_query(EditTransaction.changing, F.data.startswith('edit_'))
async def edit_transaction(callback: CallbackQuery, state: FSMContext):
    id_transaction = int(callback.data.split('_')[1])
    state_data = await state.get_data()
    transactions = state_data['transactions']
    for tr in transactions:
        if tr['id'] == id_transaction:
            transaction = tr
            break
    else:
        print('Транзакция почему-то не найдена :(')
        return

    text = f'''<b>Дата</b>: {transaction['date']}
<b>Счёт списания</b>: {transaction['bank_name']}     
<b>Категория назначения</b>: {transaction['destination_name']}
<b>Дата</b>: {transaction['date']}
<b>Сумма</b>: {transaction['amount']}
<b>Комментарий</b>: {"" if not transaction['note'] else transaction['note']}
     
Что хотите сделать с транзакцией?'''

    await state.update_data(id=id_transaction)
    await callback.message.edit_text(text, reply_markup=kb_action())


@router.callback_query(EditTransaction.changing, F.data.startswith('edit_'))
async def edit_transaction(callback: CallbackQuery, state: FSMContext):
    ...
