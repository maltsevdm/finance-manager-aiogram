import datetime

from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, \
    CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.services.categories import CategoriesService
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


def get_kb_categories_from():
    buttons = [
        [InlineKeyboardButton(text='Tinkoff S7',
                              callback_data='transaction_tinkoff s7')],
        [InlineKeyboardButton(text='Tinkoff Black',
                              callback_data='transaction_tinkoff black')],
        [InlineKeyboardButton(text='Alpha',
                              callback_data='transaction_alpha')]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


def get_kb_categories_to():
    buttons = [
        [InlineKeyboardButton(text='Продукты',
                              callback_data='transaction_products')],
        [InlineKeyboardButton(text='Транспорт',
                              callback_data='transaction_transport')],
        [InlineKeyboardButton(text='Прочее',
                              callback_data='transaction_other')]
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


@router.message(StateFilter(None),
                F.text.lower() == kb.BT_ADD_TRANSACTION.lower())
async def add_transaction(msg: Message, state: FSMContext):
    answer_text = '➕ Добавление транзакции\n'
    await state.update_data(answer_text=answer_text)
    answer_text += '\n🔄 Выберите тип:'
    await msg.answer(answer_text, reply_markup=get_kb_group())
    await state.set_state(AddTransaction.choosing_group)


@router.callback_query(AddTransaction.choosing_group,
                       F.data.startswith('transaction_'))
async def choice_category_from(callback: CallbackQuery, state: FSMContext):
    group = callback.data.split('_')[1]
    user_id = callback.from_user.id
    token = users[user_id]['token']
    answer_text = (await state.get_data())['answer_text']
    await state.update_data(group=group)

    if group == 'income':
        response = await CategoriesService.get(token, 'income')
    else:
        response = await CategoriesService.get(token, 'bank')

    assert response.status_code == 200

    categories_data = response.json()
    categories_for_kb = {category['id']: category['name']
                         for category in categories_data}

    builder = from_list(categories_for_kb)
    answer_text += f"\n🔄 Тип: {'расход' if group == 'expense' else 'поступление' if group == 'income' else 'перевод'}"
    await callback.message.edit_text(
        answer_text + '\n\n⬆ Выберите категорию списания:',
        reply_markup=builder.as_markup()
    )
    await state.update_data(answer_text=answer_text)
    await state.set_state(AddTransaction.choosing_category_from)
    await callback.answer()


@router.callback_query(AddTransaction.choosing_category_from,
                       F.data.startswith('transaction_'))
async def choice_category_to(callback: CallbackQuery, state: FSMContext):
    state_date = await state.get_data()
    group = state_date['group']
    answer_text = state_date['answer_text']
    user_id = callback.from_user.id
    token = users[user_id]['token']
    id_category_from, category_from = callback.data.split('_')[1:]
    await state.update_data(id_category_from=int(id_category_from))

    if group == 'expense':
        response = await CategoriesService.get(token, 'expense')
    else:
        response = await CategoriesService.get(token, 'bank')

    assert response.status_code == 200

    categories_data = response.json()
    categories_for_kb = {category['id']: category['name']
                         for category in categories_data}

    builder = from_list(categories_for_kb)

    answer_text += f'\n⬆ Категория списания: {category_from}'
    await callback.message.edit_text(
        answer_text + '\n\n⬇ Выберите категорию назначения:',
        reply_markup=builder.as_markup()
    )
    await state.update_data(answer_text=answer_text)
    await state.set_state(AddTransaction.choosing_category_to)
    await callback.answer()


@router.callback_query(AddTransaction.choosing_category_to,
                       F.data.startswith('transaction_'))
async def choosing_date(callback: CallbackQuery, state: FSMContext):
    id_category_to, category_to = callback.data.split('_')[1:]
    state_date = await state.get_data()
    answer_text = state_date['answer_text']
    await state.update_data(id_category_to=int(id_category_to))
    answer_text += f'\n⬇ Категория назначения: {category_to}'
    await callback.message.edit_text(
        answer_text + '\n\n📅 Выберите дату:',
        reply_markup=get_kb_dates())
    await state.update_data(answer_text=answer_text)
    await state.set_state(AddTransaction.choosing_date)
    await callback.answer()


@router.callback_query(AddTransaction.choosing_date,
                       F.data.startswith('transaction_'))
async def entering_amount(callback: CallbackQuery, state: FSMContext):
    state_date = await state.get_data()
    answer_text = state_date['answer_text']
    date_str = callback.data.split('_')[1]
    if date_str == 'today':
        date_dt_str = datetime.date.today().strftime('%Y-%m-%d')
    elif date_str == 'yesterday':
        date_dt_str = ((datetime.date.today() - datetime.timedelta(days=1))
                       .strftime('%Y-%m-%d'))
    else:
        date_dt_str = '2024-01-01'

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
    response = await TransactionsService.add(token, amount=amount, **state_data)

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

# await callback.msg.answer('Выберите из какой категории:',
#                  reply_markup=get_kb_categories())

# async def add_expense_choose_category(msg: Message, state: FSMContext):
#     user_id = msg.from_user.id
#     token = users[user_id]['token']
#     if msg.text.lower() == kb.BT_ADD_INCOME.lower():
#         response = await CategoriesService.get(token, 'income')
#     else:
#         response = await CategoriesService.get(token, 'bank')
#
#     assert response.status_code == 200
#
#     categories = [x['name'] for x in response.json()]
#
#     if categories:
#         builder = kb.from_categories(categories)
#         await msg.answer('Выберите категорию',
#                          reply_markup=builder.as_markup(resize_keyboard=True))
#         await state.set_state(AddExpense.choosing_category)
#     else:
#         await msg.answer('Вы ещё не добавили ни одной категории.',
#                          reply_markup=kb.main_menu())
#
#
# @router.message(AddExpense.choosing_category, F.text)
# async def entry_expense_amount(msg: Message, state: FSMContext):
#     await state.update_data(chosen_category=msg.text)
#     await msg.answer('Введите значение:', reply_markup=kb.main_menu_button())
#     await state.set_state(AddExpense.entering_amount)
#
#
# @router.message(AddExpense.entering_amount, F.text)
# async def add_expense(msg: Message, state: FSMContext):
#     user_id = msg.from_user.id
#     amount = int(msg.text)
#     user_data = await state.get_data()
#     category = user_data['chosen_category']
#     balance = crud.add_expense(user_id, amount)
#     await msg.answer(
#         f'Добавлен расход в категорию {category} - {amount} руб. \nВаш баланс: {balance} руб.',
#         reply_markup=kb.main_menu())
#     await state.clear()
#
#
# @router.message(StateFilter(None), F.text.lower() == kb.BT_ADD_INCOME.lower())
# async def add_income_choose_category(msg: Message, state: FSMContext):
#     await msg.answer('Введите значение:', reply_markup=kb.main_menu_button())
#     await state.set_state(AddIncome.entering_amount)
#
#
# @router.message(AddIncome.entering_amount, F.text)
# async def add_income_enter_amount(msg: Message, state: FSMContext):
#     user_id = msg.from_user.id
#     amount = int(msg.text)
#     users[user_id]['balance'] += amount
#     balance = users[user_id]['balance']
#     await msg.answer(
#         f'Добавлено поступление {amount} руб. \nВаш баланс: {balance} руб.',
#         reply_markup=kb.main_menu())
#     await state.clear()