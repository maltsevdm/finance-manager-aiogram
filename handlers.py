import json

from aiogram import Router, types, F
from aiogram.enums import ParseMode
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message
from aiogram.utils.formatting import as_list, as_marked_section
from aiogram.utils.keyboard import ReplyKeyboardBuilder

router = Router()
users = {}


class OrderCategory(StatesGroup):
    choosing_category_name = State()


class ChangeBalance(StatesGroup):
    entering_new_balance = State()


class AddExpense(StatesGroup):
    choosing_category = State()
    entering_amount = State()


class AddIncome(StatesGroup):
    entering_amount = State()


def get_main_keyboard():
    buttons = [
        [
            types.KeyboardButton(text='Баланс'),
            types.KeyboardButton(text='Изменить баланс')
        ],
        [
            types.KeyboardButton(text='Добавить расход'),
            types.KeyboardButton(text='Добавить поступление'),
        ],
        [
            types.KeyboardButton(text='Мои категории'),
            types.KeyboardButton(text='Добавить категорию'),
        ]
    ]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True
    )
    return keyboard


def get_keyboard_mainmenu():
    buttons = [
        [types.KeyboardButton(text='Главное меню')]
    ]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True
    )
    return keyboard


@router.message(Command("start"))
async def start_handler(msg: Message):
    user_id = msg.from_user.id
    if user_id in users:
        await msg.answer('Привет! Ты зарегистрирован.',
                         reply_markup=get_main_keyboard())
    else:
        kb = [
            [types.KeyboardButton(text='Зарегистрироваться')]
        ]
        keyboard = types.ReplyKeyboardMarkup(
            keyboard=kb,
            resize_keyboard=True)
        await msg.answer('Привет! Ты не зарегистрирован.',
                         reply_markup=keyboard)


@router.message(F.text.lower() == 'зарегистрироваться')
async def register_handler(msg: Message):
    user_id = msg.from_user.id
    users[user_id] = {'balance': 0, 'categories': {}}
    await msg.answer('Ты зарегистрирован.',
                     reply_markup=get_main_keyboard())


@router.message(F.text.lower() == 'главное меню')
async def go_to_main_menu(msg: Message, state: FSMContext):
    await msg.answer('Вы в главном меню.', reply_markup=get_main_keyboard())
    await state.clear()


@router.message(StateFilter(None), F.text.lower() == 'баланс')
async def get_balance(msg: Message):
    user_id = msg.from_user.id
    balance = users[user_id]['balance']
    await msg.answer(f'Баланс: {balance} рублей.',
                     reply_markup=get_main_keyboard())


@router.message(StateFilter(None), F.text.lower() == 'изменить баланс')
async def balance_entry(msg: Message, state: FSMContext):
    await msg.answer('Введите новый баланс:',
                     reply_markup=get_keyboard_mainmenu())
    await state.set_state(ChangeBalance.entering_new_balance)


@router.message(ChangeBalance.entering_new_balance, F.text)
async def change_balance(msg: Message, state: FSMContext):
    new_balance = msg.text
    user_id = msg.from_user.id
    users[user_id]['balance'] = int(new_balance)
    await msg.answer('Баланс изменён.', reply_markup=get_main_keyboard())
    await state.clear()


@router.message(F.text.lower() == 'мои категории')
async def get_categories(msg: Message):
    categories = users[msg.from_user.id]['categories'].keys()
    if categories:
        content = as_list(
            as_marked_section(
                'Ваши категории:',
                *categories,
                marker='- '
            )
        )
        # msg_text = **content.as_kwargs()
        await msg.answer(**content.as_kwargs(),
                         reply_markup=get_main_keyboard())
    else:
        await msg.answer('Вы ещё не добавили ни одной категории.',
                         reply_markup=get_main_keyboard())


@router.message(StateFilter(None), F.text.lower() == 'добавить категорию')
async def add_category(msg: Message, state: FSMContext):
    await msg.answer('Напишите имя категории:',
                     reply_markup=get_keyboard_mainmenu())
    await state.set_state(OrderCategory.choosing_category_name)


@router.message(OrderCategory.choosing_category_name, F.text)
async def category_entry(msg: Message, state: FSMContext):
    user_id = msg.from_user.id
    await state.update_data(chosen_food=msg.text.lower())
    category = msg.text
    if category in users[user_id]['categories']:
        await msg.answer(
            f'Такая категория уже существует.\nВведите новое имя категории:',
            reply_markup=get_main_keyboard())
    else:
        users[user_id]['categories'][category] = []
        await msg.answer(f'Категория {category} добавлена.',
                         reply_markup=get_main_keyboard())
        await state.clear()


@router.message(StateFilter(None), F.text.lower() == 'добавить расход')
async def choose_category(msg: Message, state: FSMContext):
    user_id = msg.from_user.id
    categories = users[user_id]['categories'].keys()
    if categories:
        builder = ReplyKeyboardBuilder()
        for category in categories:
            builder.add(types.KeyboardButton(text=category))
        await msg.answer('Выберите категорию',
                         reply_markup=builder.as_markup(resize_keyboard=True))
        await state.set_state(AddExpense.choosing_category)
    else:
        await msg.answer('Вы ещё не добавили ни одной категории.',
                         reply_markup=get_main_keyboard())


@router.message(AddExpense.choosing_category, F.text)
async def entry_expense_amount(msg: Message, state: FSMContext):
    await state.update_data(chosen_category=msg.text)
    await msg.answer('Введите значение:', reply_markup=get_keyboard_mainmenu())
    await state.set_state(AddExpense.entering_amount)


@router.message(AddExpense.entering_amount, F.text)
async def add_expense(msg: Message, state: FSMContext):
    user_id = msg.from_user.id
    amount = int(msg.text)
    user_data = await state.get_data()
    category = user_data['chosen_category']
    users[user_id]['categories'][category].append(amount)
    users[user_id]['balance'] -= amount
    balance = users[user_id]['balance']
    await msg.answer(
        f'Добавлен расход в категорию {category} - {amount} руб. \nВаш баланс: {balance} руб.',
        reply_markup=get_main_keyboard())
    await state.clear()


@router.message(StateFilter(None), F.text.lower() == 'добавить поступление')
async def choose_category(msg: Message, state: FSMContext):
    await msg.answer('Введите значение:', reply_markup=get_keyboard_mainmenu())
    await state.set_state(AddIncome.entering_amount)


@router.message(AddIncome.entering_amount, F.text)
async def add_expense(msg: Message, state: FSMContext):
    user_id = msg.from_user.id
    amount = int(msg.text)
    users[user_id]['balance'] += amount
    balance = users[user_id]['balance']
    await msg.answer(
        f'Добавлено поступление {amount} руб. \nВаш баланс: {balance} руб.',
        reply_markup=get_main_keyboard())
    await state.clear()
