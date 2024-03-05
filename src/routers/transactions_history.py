import datetime

from aiogram import Router, F

from aiogram.fsm.context import FSMContext

from aiogram.types import (Message, InlineKeyboardButton, InlineKeyboardMarkup,
                           CallbackQuery)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.services.transactions import TransactionsService
from src.states.transactions import EditTransaction
from src.users import users
from src.utils import kb

router = Router()


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
        InlineKeyboardButton(text=kb.BT_EXIT, callback_data='exit')
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
        [InlineKeyboardButton(text=kb.BT_GO_BACK,
                              callback_data='back_to_transactions'),
         InlineKeyboardButton(text=kb.BT_EXIT, callback_data='exit')]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


def get_short_description(item: dict):
    direction = '⬅' if item['group'] == 'income' else '➡'
    return (f'{item["bank_name"]} {direction} '
            f'{item["destination_name"]} | {item["amount"]} ₽')


def get_full_description(item: dict):
    groups = {
        'income': 'Поступление',
        'expense': 'Трата',
        'transfer': 'Перевод'
    }

    return f'''
<b>Тип</b>: <i>{groups[item['group']]}</i>
<b>Дата</b>: <i>{item['date']}</i>
<b>Счёт списания</b>: <i>{item['bank_name']}</i>
<b>Категория назначения</b>: <i>{item['destination_name']}</i>
<b>Дата</b>: <i>{item['date']}</i>
<b>Сумма</b>: <i>{item['amount']}</i>
<b>Комментарий</b>: <i>{"" if not item['note'] else item['note']}</i>'''


@router.callback_query(F.data == 'back_to_transactions')
@router.message(F.text.lower() == kb.BT_TRANSACTIONS_HISTORY.lower())
async def get_history(msg: Message | CallbackQuery, state: FSMContext):
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

    i = 1
    for date, transactions in transactions_data.items():
        answer_text += f'\n\n<b>{date}</b>'
        for transaction in transactions:
            answer_text += f'\n<b>{i}.</b> {get_short_description(transaction)}'
            i += 1

    answer_text += '\n\nВыберите номер транзакции для редактирования:'

    builder = kb_navigation(transactions_src)

    if isinstance(msg, CallbackQuery):
        await msg.message.edit_text(answer_text,
                                    reply_markup=builder.as_markup())
    else:
        await msg.answer(answer_text, reply_markup=builder.as_markup())
    await state.set_state(EditTransaction.choosing_action)


@router.callback_query(EditTransaction.choosing_action, F.data == 'change_date')
async def entry_transaction_date(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text('Введите новую дату (гггг-мм-дд):')
    await state.update_data(attr='date')
    await state.set_state(EditTransaction.entering_new_value)
    await callback.answer()


@router.callback_query(EditTransaction.choosing_action,
                       F.data.startswith('edit_'))
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

    description = get_full_description(transaction)
    text = description + '\n\nЧто хотите сделать с транзакцией?'

    await state.update_data(id=id_transaction)
    await callback.message.edit_text(text, reply_markup=kb_action())


@router.message(EditTransaction.entering_new_value)
async def edit_transaction_date(msg: Message, state: FSMContext):
    date = msg.text
    user_id = msg.from_user.id
    token = users[user_id]['token']
    # TODO: Обработка неправильно ввода даты
    datetime.datetime.strptime(date, '%Y-%m-%d')
    state_data = await state.get_data()
    id_tr = state_data['id']

    response = await TransactionsService.update(
        token=token, id=id_tr, **{'date': date})

    if response.status_code == 200:
        await msg.answer(f'Транзакция обновлена.', reply_markup=kb.main_menu())
    else:
        await msg.answer('Транзакция не обновлена.', reply_markup=kb.main_menu())
    await state.clear()
