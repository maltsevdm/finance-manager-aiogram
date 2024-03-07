from aiogram import Router, F

from aiogram.fsm.context import FSMContext

from aiogram.types import (Message, InlineKeyboardButton, InlineKeyboardMarkup,
                           CallbackQuery)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.services.categories.banks import BanksService
from src.services.categories.ei_categories import EiCategoriesService
from src.services.transactions import TransactionsService
from src.states.transactions import EditTransaction
from src.users import users
from src.utils import kb
from src.utils.utils import validate_date

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


def kb_action(group: str):
    if group == 'transfer':
        change_dest_test = 'Изменить счёт назначения'
    elif group == 'income':
        change_dest_test = 'Изменить категорию доходов'
    else:
        change_dest_test = 'Изменить категорию расходов'

    buttons = [
        [InlineKeyboardButton(
            text=f'Изменить {"счёт назначения" if group == "income" else "счёт списания"}',
            callback_data='change_bank')],
        [InlineKeyboardButton(text=change_dest_test,
                              callback_data='change_dest')],
        [InlineKeyboardButton(text='Изменить дату',
                              callback_data='change_date')],
        [InlineKeyboardButton(text='Изменить сумму',
                              callback_data='change_amount')],
        [InlineKeyboardButton(text='Изменить комментарий',
                              callback_data='change_note')],
        [InlineKeyboardButton(text='Удалить',
                              callback_data='transaction_remove')],
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


def from_list(data: dict, cols: int = 1) -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    for id, el in data.items():
        builder.add(
            InlineKeyboardButton(text=el,
                                 callback_data=f'change_category_{id}'))
    builder.adjust(cols)
    return builder


@router.callback_query(F.data == 'back_to_transactions')
@router.message(F.text.lower() == kb.BT_TRANSACTIONS_HISTORY.lower())
async def get_history(msg: Message | CallbackQuery, state: FSMContext):
    answer_text = 'История транзакций:'
    user_id = msg.from_user.id
    token = users[user_id]['token']

    response = await TransactionsService.get(token, limit=10)
    assert response.status_code == 200
    transactions_src = response.json()

    transactions_dict = {}
    transactions_data = {}
    for transaction in transactions_src:
        date = transaction['date']
        if date not in transactions_data:
            transactions_data[date] = {
                'items': [],
                'sum_incomes': 0,
                'sum_expenses': 0
            }

        transactions_data[date]['items'].append(transaction)
        if transaction['group'] == 'income':
            transactions_data[date]['sum_incomes'] += transaction['amount']
        if transaction['group'] == 'expense':
            transactions_data[date]['sum_expenses'] += transaction['amount']

        transactions_dict[transaction['id']] = transaction

    await state.update_data(transactions=transactions_dict)

    i = 1
    for date, date_data in transactions_data.items():
        date_incomes = date_data['sum_incomes']
        date_expenses = date_data['sum_expenses']
        answer_text += (f'\n\n<b>{date}</b> (<i><b>Д</b>: {date_incomes} | '
                        f'<b>Р</b>: {date_expenses}</i>)')
        for transaction in date_data['items']:
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


@router.callback_query(EditTransaction.choosing_action,
                       F.data == 'change_amount')
@router.callback_query(EditTransaction.choosing_action, F.data == 'change_date')
@router.callback_query(EditTransaction.choosing_action, F.data == 'change_note')
async def entry_transaction_date(callback: CallbackQuery, state: FSMContext):
    _, *attr_list = callback.data.split('_')
    attr = '_'.join(attr_list)

    attrs_text = {
        'amount': 'новую сумму',
        'date': 'новую дату (гггг-мм-дд)',
        'note': 'новый комментарий'
    }

    await callback.message.edit_text(f'Введите {attrs_text[attr]}:')
    await state.update_data(attr=attr)
    await state.set_state(EditTransaction.entering_new_value)
    await callback.answer()


@router.callback_query(EditTransaction.choosing_action, F.data == 'change_bank')
@router.callback_query(EditTransaction.choosing_action, F.data == 'change_dest')
async def choice_new_bank_or_dest(callback: CallbackQuery, state: FSMContext):
    state_date = await state.get_data()
    transaction = state_date['transaction']
    group = transaction['group']
    user_id = callback.from_user.id
    token = users[user_id]['token']

    _, attr = callback.data.split('_')

    if attr == 'bank' or group == 'transfer':
        response = await BanksService.read(token)
    else:
        response = await EiCategoriesService.read(token, group)

    assert response.status_code == 200

    items_data = response.json()
    items_for_kb = {item['id']: item['name'] for item in items_data}
    builder = from_list(items_for_kb)
    builder.add(
        InlineKeyboardButton(text=kb.BT_GO_BACK,
                             callback_data='back_to_choice_action'),
        InlineKeyboardButton(text=kb.BT_EXIT, callback_data='exit')
    )
    builder.adjust(2)

    if attr == 'bank':
        a = 'Выберите новый счёт списания:'
    else:
        if group == 'income':
            a = 'Выберите новую категорию поступления:'
        elif group == 'expense':
            a = 'Выберите новую категория расходов:'
        else:
            a = 'Выберите новый счёт назначения:'

    await state.update_data(change=attr)
    await callback.message.edit_text(a, reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data == 'back_to_choice_action')
@router.callback_query(EditTransaction.choosing_action,
                       F.data.startswith('edit_'))
async def edit_transaction(callback: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()

    if callback.data == 'back_to_choice_action':
        transaction = state_data['transaction']
    else:
        id_transaction = int(callback.data.split('_')[1])
        transactions = state_data['transactions']
        transaction = transactions[id_transaction]

    description = get_full_description(transaction)
    text = description + '\n\nЧто хотите сделать с транзакцией?'

    await state.update_data(transaction=transaction)
    await callback.message.edit_text(text,
                                     reply_markup=kb_action(
                                         transaction['group']))
    await callback.answer()


@router.callback_query(F.data == 'transaction_remove')
async def remove_transaction(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    state_data = await state.get_data()
    transaction = state_data['transaction']

    response = await TransactionsService.delete(
        users[user_id]['token'], transaction['id'])

    answer_text = f'Транзакция{"" if response.status_code == 200 else " не"} удалена.'
    await callback.message.edit_text(answer_text)
    await state.clear()
    await callback.answer()


@router.message(EditTransaction.entering_new_value)
async def edit_transaction_attr(msg: Message, state: FSMContext):
    user_id = msg.from_user.id
    token = users[user_id]['token']
    state_data = await state.get_data()
    attr = state_data['attr']
    new_value = msg.text

    type_conversion_funcs = {
        'amount': float,
        'note': str,
        'date': validate_date
    }

    try:
        new_value = type_conversion_funcs[attr](new_value)
    except ValueError:
        await msg.answer('Некорректный ввод. Повторите попытку.',
                         reply_markup=kb.main_menu())
        return

    await update_transaction(
        token=token,
        data={attr: new_value},
        callback=msg,
        state=state
    )


@router.callback_query(F.data.startswith('change_category_'))
async def choice_new_category(callback: CallbackQuery, state: FSMContext):
    *_, id_new_category = callback.data.split('_')
    state_data = await state.get_data()
    attr = state_data['change']
    user_id = callback.from_user.id
    token = users[user_id]['token']
    attr = 'bank_id' if attr == 'bank' else 'destination_id'

    await update_transaction(
        token=token,
        data={attr: id_new_category},
        callback=callback,
        state=state
    )


async def update_transaction(
        token: str,
        data: dict,
        callback: CallbackQuery | Message,
        state: FSMContext
):
    state_data = await state.get_data()
    transaction = state_data['transaction']

    response = await TransactionsService.update(
        token=token, id=transaction['id'], data=data)

    is_ok = response.status_code == 200
    answer_text = f'Транзакция{"" if is_ok else " не"} обновлена.'

    if isinstance(callback, CallbackQuery):
        # await callback.message.edit_text(answer_text)
        await callback.answer('Транзакция обновлена', show_alert=not is_ok)
    else:
        await callback.answer(answer_text, reply_markup=kb.main_menu())
    await state.clear()
    await get_history(callback, state)
