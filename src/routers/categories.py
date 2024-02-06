from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, \
    CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.utils import kb
from src.services.categories import CategoriesService
from src.states.categories import ManageCategory, AddCategory, ChangeCategory
from src.users import users

router = Router()


def get_kb_action():
    buttons = [
        [InlineKeyboardButton(text='Мои категории',
                              callback_data='category_my')],
        [InlineKeyboardButton(text='Добавить категорию',
                              callback_data='category_add')]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


def get_kb_group():
    buttons = [
        [InlineKeyboardButton(text='Категории поступлений',
                              callback_data='category_income')],
        [InlineKeyboardButton(text='Категории расходов',
                              callback_data='category_expense')],
        [InlineKeyboardButton(text='Счета',
                              callback_data='category_bank')]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


def get_kb_action_change_category(group: str):
    buttons = [
        [InlineKeyboardButton(text='Изменить имя',
                              callback_data='category_changename')],
        [InlineKeyboardButton(text='Удалить',
                              callback_data='category_remove')],
    ]
    if group == 'bank':
        buttons.insert(1,
                       [InlineKeyboardButton(text='Изменить сумму',
                                             callback_data='category_changeamount')]
                       )
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


def from_list(data: dict, cols: int = 1) -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    for category in data:
        if category['group'] == 'bank':
            text = f'{category["name"]} ({int(category["amount"])} ₽)'
        else:
            text = f'{category["name"]}'
        builder.add(
            InlineKeyboardButton(
                text=text,
                callback_data=f'category_{category["id"]}_{category["name"]}')
        )
    builder.adjust(cols)
    return builder


@router.message(StateFilter(None),
                F.text.lower() == kb.BT_MANAGE_CATEGORIES.lower())
async def manage_categories(msg: Message, state: FSMContext):
    answer_text = 'Выберите действие:'
    await msg.answer(answer_text, reply_markup=get_kb_action())
    await state.set_state(ManageCategory.choosing_action)


@router.callback_query(ManageCategory.choosing_action,
                       F.data.startswith('category_'))
async def choice_action(callback: CallbackQuery, state: FSMContext):
    action = callback.data.split('_')[1]
    if action == 'my':
        answer_text = 'Из какой группы получить категории?'
        await state.set_state(ChangeCategory.choosing_action_1)
    else:
        answer_text = 'В какую группу добавить категорию?'
        await state.set_state(AddCategory.choosing_group)
    await callback.message.edit_text(answer_text, reply_markup=get_kb_group())


@router.callback_query(ChangeCategory.choosing_action_1)
async def get_categories(callback: CallbackQuery, state: FSMContext):
    group = callback.data.split('_')[1]

    user_id = callback.from_user.id
    token = users[user_id]['token']
    await state.update_data(group=group)

    response = await CategoriesService.get(token, group)
    assert response.status_code == 200

    categories_data = response.json()

    if categories_data:
        builder = from_list(categories_data)
        await callback.message.edit_text(
            f'Ваши {group}:', reply_markup=builder.as_markup())
        await state.set_state(ChangeCategory.choosing_category)
    else:
        await callback.message.edit_text(
            'Вы ещё не добавили ни одной категории в эту группу.')


@router.callback_query(ChangeCategory.choosing_category)
async def update_category(callback: CallbackQuery, state: FSMContext):
    id_category, category = callback.data.split('_')[1:]
    group = (await state.get_data())['group']
    await state.update_data(id_selected_category=id_category,
                            selected_category=category)
    await callback.message.edit_text(
        f'Что хотите сделать с категорией {category}?',
        reply_markup=get_kb_action_change_category(group))
    await state.set_state(ChangeCategory.choosing_action_2)


@router.callback_query(
    ChangeCategory.choosing_action_2, F.data == 'category_changename')
async def enter_category_name(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text('Введите новое имя:')
    await state.set_state(ChangeCategory.entering_name)


@router.callback_query(
    ChangeCategory.choosing_action_2, F.data == 'category_changeamount')
async def enter_category_amount(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text('Введите новую сумму:')
    await state.set_state(ChangeCategory.entering_amount)


@router.callback_query(ChangeCategory.choosing_action_2,
                       F.data == 'category_remove')
async def remove_category(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    state_data = await state.get_data()
    id_category = state_data['id_selected_category']
    category = state_data['selected_category']

    response = await CategoriesService.remove(
        users[user_id]['token'], id_category)

    if response.status_code == 200:
        await callback.message.edit_text(f'Категория {category} удалена.')
    else:
        await callback.message.edit_text('Категория не удалена.')
    await state.clear()


@router.callback_query(AddCategory.choosing_group)
async def add_category_choice_group(callback: CallbackQuery, state: FSMContext):
    group = callback.data.split('_')[1]

    await state.update_data(group=group)
    await callback.message.edit_text('Введите имя категории:')
    await state.set_state(AddCategory.entering_name)


@router.message(AddCategory.entering_name, F.text)
async def add_category_enter_name(msg: Message, state: FSMContext):
    state_data = await state.get_data()
    user_id = msg.from_user.id
    token = users[user_id]['token']
    category = msg.text

    response = await CategoriesService.add(
        token, name=category, group=state_data['group'])

    if response.status_code == 200:
        await msg.answer(f'Категория {category} успешно добавлена.',
                         reply_markup=kb.main_menu())
    else:
        await msg.answer(f'Ошибка! Категория не добавлена. '
                         f'Детали: {response.json()["detail"]}',
                         reply_markup=kb.main_menu())
    await state.clear()


@router.message(ChangeCategory.entering_name, F.text)
async def change_category_name(msg: Message, state: FSMContext):
    user_id = msg.from_user.id
    state_data = await state.get_data()
    id_category = state_data['id_selected_category']
    token = users[user_id]['token']

    response = await CategoriesService.update(token, id_category, name=msg.text)

    if response.status_code == 200:
        await msg.answer(f'Категория {msg.text} обновлена.',
                         reply_markup=kb.main_menu())
    else:
        await msg.answer('Категория не обновлена.',
                         reply_markup=kb.main_menu())
    await state.clear()


@router.message(ChangeCategory.entering_amount, F.text)
async def change_category_amount(msg: Message, state: FSMContext):
    state_data = await state.get_data()
    id_category = state_data['id_selected_category']
    category = state_data['selected_category']
    token = users[msg.from_user.id]['token']

    response = await CategoriesService.update(token, id_category,
                                              amount=float(msg.text))

    if response.status_code == 200:
        await msg.answer(f'Категория {category} обновлена.',
                         reply_markup=kb.main_menu())
    else:
        await msg.answer('Категория не обновлена.',
                         reply_markup=kb.main_menu())
    await state.clear()
