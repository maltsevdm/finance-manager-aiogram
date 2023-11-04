from aiogram import Router, types, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.utils.formatting import as_list, as_marked_section
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from states import ChangeBalance, AddExpense, AddIncome, ManageCategory
from database import crud
import kb


router = Router()
users = {}


@router.message(Command('start'))
async def start_handler(msg: Message):
    user_id = msg.from_user.id
    user = crud.get_user(user_id)
    if user:
        await msg.answer('Привет! Вы уже зарегистрированы.', reply_markup=kb.main_menu())
    else:
        await msg.answer('Привет! Вы не зарегистрированы.', reply_markup=kb.register())


@router.message(F.text.lower() == kb.BT_REGISTER.lower())
async def register_handler(msg: Message):
    user_id = msg.from_user.id
    user = crud.get_user(user_id)
    if user:
        await msg.answer('Вы уже зарегистрированы.', reply_markup=kb.main_menu())
    else:
        crud.add_user(user_id, msg.chat.username)
        await msg.answer('Ты зарегистрирован.', reply_markup=kb.main_menu())


@router.message(F.text.lower() == kb.BT_MAIN_MENU.lower())
async def go_to_main_menu(msg: Message, state: FSMContext):
    await msg.answer('Вы в главном меню.', reply_markup=kb.main_menu())
    await state.clear()


@router.message(StateFilter(None), F.text.lower() == kb.BT_GET_BALANCE.lower())
async def get_balance(msg: Message):
    user_id = msg.from_user.id
    balance = crud.get_balance(user_id)
    await msg.answer(f'Баланс: {balance} рублей.',
                     reply_markup=kb.main_menu())


@router.message(StateFilter(None), F.text.lower() == kb.BT_CHANGE_BALANCE.lower())
async def balance_entry(msg: Message, state: FSMContext):
    await msg.answer('Введите новый баланс:',
                     reply_markup=kb.main_menu_button())
    await state.set_state(ChangeBalance.entering_new_balance)


@router.message(ChangeBalance.entering_new_balance, F.text)
async def change_balance(msg: Message, state: FSMContext):
    new_balance = int(msg.text)
    user_id = msg.from_user.id
    crud.update_balance(user_id, new_balance)
    await msg.answer('Баланс изменён.', reply_markup=kb.main_menu())
    await state.clear()


@router.message(StateFilter(None), F.text.lower() == kb.BT_MANAGE_CATEGORIES.lower())
async def manage_categories(msg: Message, state: FSMContext):
    await msg.answer('Выберите действие:', reply_markup=kb.category_manager())
    await state.set_state(ManageCategory.choosing_action)


@router.message(ManageCategory.choosing_action, F.text.lower() == kb.BT_ADD_CATEGORY.lower())
async def add_category(msg: Message, state: FSMContext):
    await state.update_data(action=msg.text.lower())
    answer_text = 'Выберите какого типа категорию добавить:'
    await msg.answer(answer_text, reply_markup=kb.type_category())
    await state.set_state(ManageCategory.choosing_category_group)


@router.message(ManageCategory.choosing_action, F.text.lower() == kb.BT_REMOVE_CATEGORY.lower())
async def add_category(msg: Message, state: FSMContext):
    await state.update_data(action=msg.text.lower())
    answer_text = 'Выберите из какого типа удалить категорию:'
    await msg.answer(answer_text, reply_markup=kb.type_category())
    await state.set_state(ManageCategory.choosing_category_group)


@router.message(ManageCategory.choosing_category_group, F.text.lower())
async def choice_category_type(msg: Message, state: FSMContext):
    msg_text = msg.text.lower()
    user_data = await state.get_data()
    action = user_data['action']
    if msg_text in [kb.BT_CATEGORIES_INCOME.lower(), kb.BT_CATEGORIES_EXPENSE.lower()]:
        oper_type = 'income' if msg_text == kb.BT_CATEGORIES_INCOME.lower() else 'expense'
        await state.update_data(category_group=oper_type)
        if action == kb.BT_ADD_CATEGORY.lower():
            await msg.answer('Введите имя категории:', reply_markup=kb.main_menu_button())
        else:
            categories = crud.get_categories(msg.from_user.id, oper_type)
            builder = kb.from_categories(categories)
            await msg.answer('Выберите категорию:', reply_markup=builder.as_markup(resize_keyboard=True))
        await state.set_state(ManageCategory.choosing_category_name)
    else:
        await msg.answer('Неверный выбор!', reply_markup=kb.main_menu_button())


@router.message(ManageCategory.choosing_category_name, F.text)
async def choice_category_name(msg: Message, state: FSMContext):
    user_id = msg.from_user.id
    user_data = await state.get_data()
    category_group = user_data['category_group']
    action = user_data['action']
    category = msg.text
    categories = crud.get_categories(user_id, category_group)
    if category in categories:
        if action == kb.BT_REMOVE_CATEGORY.lower():
            crud.remove_category(user_id, category_group, category)
            await msg.answer(f'Категория {category} удалена.', reply_markup=kb.main_menu())
            await state.clear()
        else:
            await msg.answer(
                f'Такая категория уже существует.\nВведите новое имя категории:',
                reply_markup=kb.main_menu_button()
            )
    else:
        if action == kb.BT_ADD_CATEGORY.lower():
            crud.add_category(user_id, category_group, category)
            await msg.answer(f'Категория {category} добавлена.', reply_markup=kb.main_menu())
            await state.clear()
        else:
            await msg.answer(
                'Такая категория не существует.\nВведите новое имя категории:',
                reply_markup=kb.main_menu_button()
            )


@router.message(ManageCategory.choosing_action, F.text.lower() == kb.BT_MY_CATEGORIES.lower())
async def get_categories(msg: Message, state: FSMContext):
    categories = crud.get_categories(msg.from_user.id)
    if categories:
        content = as_list(
            as_marked_section(
                'Ваши категории:',
                *categories,
                marker='- '
            )
        )
        await msg.answer(**content.as_kwargs(), reply_markup=kb.category_manager())
    else:
        await msg.answer('Вы ещё не добавили ни одной категории.', reply_markup=kb.category_manager())


@router.message(StateFilter(None), F.text.lower() == kb.BT_ADD_EXPENSE.lower())
async def choose_category(msg: Message, state: FSMContext):
    user_id = msg.from_user.id
    categories = crud.get_categories(user_id)
    if categories:
        builder = kb.from_categories(categories)
        await msg.answer('Выберите категорию', reply_markup=builder.as_markup(resize_keyboard=True))
        await state.set_state(AddExpense.choosing_category)
    else:
        await msg.answer('Вы ещё не добавили ни одной категории.',
                         reply_markup=kb.main_menu())


@router.message(AddExpense.choosing_category, F.text)
async def entry_expense_amount(msg: Message, state: FSMContext):
    await state.update_data(chosen_category=msg.text)
    await msg.answer('Введите значение:', reply_markup=kb.main_menu_button())
    await state.set_state(AddExpense.entering_amount)


@router.message(AddExpense.entering_amount, F.text)
async def add_expense(msg: Message, state: FSMContext):
    user_id = msg.from_user.id
    amount = int(msg.text)
    user_data = await state.get_data()
    category = user_data['chosen_category']
    balance = crud.add_expense(user_id, amount)
    await msg.answer(
        f'Добавлен расход в категорию {category} - {amount} руб. \nВаш баланс: {balance} руб.',
        reply_markup=kb.main_menu())
    await state.clear()


@router.message(StateFilter(None), F.text.lower() == kb.BT_ADD_INCOME.lower())
async def choose_category(msg: Message, state: FSMContext):
    await msg.answer('Введите значение:', reply_markup=kb.main_menu_button())
    await state.set_state(AddIncome.entering_amount)


@router.message(AddIncome.entering_amount, F.text)
async def add_expense(msg: Message, state: FSMContext):
    user_id = msg.from_user.id
    amount = int(msg.text)
    users[user_id]['balance'] += amount
    balance = users[user_id]['balance']
    await msg.answer(
        f'Добавлено поступление {amount} руб. \nВаш баланс: {balance} руб.',
        reply_markup=kb.main_menu())
    await state.clear()
