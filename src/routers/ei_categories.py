from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import (Message, InlineKeyboardButton, InlineKeyboardMarkup,
                           CallbackQuery)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.services.categories.ei_categories import EiCategoriesService
from src.utils import kb
from src.states.ei_categories import ManageEiCategory, AddCategory, \
    ChangeCategory
from src.users import users
from src.utils.kb import BT_ADD, BT_GO_BACK

router = Router()


def get_kb_group():
    buttons = [
        [InlineKeyboardButton(text='Категории доходов',
                              callback_data='income')],
        [InlineKeyboardButton(text='Категории расходов',
                              callback_data='expense')]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


def get_kb_action_change_category():
    buttons = [
        [InlineKeyboardButton(text='Изменить имя',
                              callback_data='category_changename')],
        [InlineKeyboardButton(text='Изменить месячный лимит',
                              callback_data='category_changemonthlylimit')],
        [InlineKeyboardButton(text='Удалить',
                              callback_data='category_remove')],
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


def from_list(data: dict, cols: int = 1) -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    for item in data:
        text = f'{item["name"]}'

        builder.add(
            InlineKeyboardButton(text=text,
                                 callback_data='edit_' + str(item['id'])))
    builder.adjust(cols)
    return builder


def get_description(item: dict) -> str:
    description = f'''<b>{item['name']}</b> 
    Сумма: <i>{item['amount']}</i>'''
    if item['monthly_limit'] is not None:
        remainder = item['monthly_limit'] - item['amount']
        remainder = 0 if remainder < 0 else remainder

        description += f'''\n    Месячный лимит: <i>{item['monthly_limit']}</i>
    Остаток: <i>{remainder}</i>'''

    return description


def get_kb_action_change_category():
    buttons = [
        [InlineKeyboardButton(text='Изменить имя',
                              callback_data='change_name')],
        [InlineKeyboardButton(text='Изменить месячный лимит',
                              callback_data='change_monthly_limit')],
        [InlineKeyboardButton(text='Удалить', callback_data='remove')],
    ]
    buttons.append([InlineKeyboardButton(text=BT_GO_BACK,
                                         callback_data='back_to_categories')])
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


@router.callback_query(F.data == 'back_to_group_selection')
@router.message(F.text.lower() == kb.BT_CATEGORIES.lower())
async def manage_categories(msg: Message | CallbackQuery, state: FSMContext):
    answer_text = 'Выберите группу:'
    await state.update_data(group=None)
    if isinstance(msg, CallbackQuery):
        await msg.message.edit_text(answer_text, reply_markup=get_kb_group())
        await msg.answer()
    else:
        await msg.answer(answer_text, reply_markup=get_kb_group())
    await state.set_state(ManageEiCategory.choosing_group)


@router.callback_query(F.data == 'back_to_categories')
@router.callback_query(ManageEiCategory.choosing_group)
async def choice_category(callback: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    group = state_data.get('group')
    if group is None:
        group = callback.data
        await state.update_data(group=group)
    user_id = callback.from_user.id
    token = users[user_id]['token']

    response = await EiCategoriesService.read(token, group=group)
    assert response.status_code == 200

    categories_data = response.json()
    categories_dict = {}
    for item in categories_data:
        categories_dict[int(item['id'])] = item

    if categories_data:
        await state.update_data(items=categories_dict)
        answer_text = (f'<b>Ваши категории '
                       f'{"расходов" if group == "expense" else "доходов"}</b>')
        for item in categories_data:
            answer_text += '\n\n' + get_description(item)

        answer_text += '\n\nВыберите категорию для редактирования.'

        builder = from_list(categories_data)
        builder.add(
            InlineKeyboardButton(text=BT_ADD, callback_data='add'),
            InlineKeyboardButton(text=BT_GO_BACK,
                                 callback_data='back_to_group_selection')
        )
        builder.adjust(2)

        await callback.message.edit_text(
            answer_text, reply_markup=builder.as_markup())

        await state.set_state(ManageEiCategory.choosing_action)
    else:
        builder = InlineKeyboardBuilder()
        builder.add(
            InlineKeyboardButton(text=BT_ADD, callback_data='add'),
            InlineKeyboardButton(text=BT_GO_BACK,
                                 callback_data='back_to_group_selection')
        )

        await callback.message.edit_text(
            'Вы ещё не добавили ни одной категории.',
            reply_markup=builder.as_markup())
        await state.clear()
    await callback.answer()


@router.callback_query(ManageEiCategory.choosing_action, F.data == 'add')
async def add_category(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text('Введите имя категории:')
    await state.set_state(AddCategory.entering_name)
    await callback.answer()


@router.message(AddCategory.entering_name, F.text)
async def add_category_enter_name(msg: Message, state: FSMContext):
    await state.update_data(name=msg.text)
    await msg.answer('Введите месячный лимит (0 - месячного лимит нет):',
                     reply_markup=kb.main_menu_button())
    await state.set_state(AddCategory.entering_monthly_limit)


@router.message(AddCategory.entering_monthly_limit, F.text)
async def add_category_enter_monthly_limit(msg: Message, state: FSMContext):
    state_data = await state.get_data()
    user_id = msg.from_user.id
    token = users[user_id]['token']

    monthly_limit = msg.text
    name = state_data['name']

    response = await EiCategoriesService.create(
        token=token,
        name=name,
        group=state_data['group'],
        monthly_limit=None if int(monthly_limit) == 0 else float(monthly_limit)
    )

    if response.status_code == 200:
        await msg.answer(f'Категория {name} успешно добавлена.',
                         reply_markup=kb.main_menu())
    else:
        await msg.answer(f'Ошибка! Категория не добавлена. '
                         f'Детали: {response.json()["detail"]}',
                         reply_markup=kb.main_menu())
    await state.clear()


@router.callback_query(ManageEiCategory.choosing_action,
                       F.data.startswith('edit_'))
async def update_category(callback: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    items = state_data['items']
    id_item = callback.data.split('_')[1]
    item = items[int(id_item)]
    answer_text = get_description(item) + '\n\nЧто хотите сделать с категорией?'

    await state.update_data(id_selected_category=id_item)
    await callback.message.edit_text(
        answer_text, reply_markup=get_kb_action_change_category())
    await state.set_state(ChangeCategory.choosing_action)
    await callback.answer()


@router.callback_query(ChangeCategory.choosing_action,
                       F.data.startswith('change_'))
async def enter_new_value(callback: CallbackQuery, state: FSMContext):
    attrs = {
        'name': 'новое имя',
        'monthly_limit': 'новый месячный лимит'
    }

    _, *attr = callback.data.split('_')
    attr = '_'.join(attr)
    await state.update_data(attr=attr)
    await callback.message.edit_text(f'Введите {attrs[attr]}:')
    await state.set_state(ChangeCategory.entering_new_value)
    await callback.answer()


@router.message(ChangeCategory.entering_new_value, F.text)
async def change_bank_name(msg: Message, state: FSMContext):
    type_conversion_funcs = {
        'name': str,
        'amount': float,
        'credit_card_balance': float,
        'credit_card_limit': float
    }

    user_id = msg.from_user.id
    state_data = await state.get_data()
    id_category = state_data['id_selected_category']
    attr = state_data['attr']
    token = users[user_id]['token']

    type_conversion_func = type_conversion_funcs[attr]
    response = await EiCategoriesService.update(
        token=token, id=id_category, **{attr: type_conversion_func(msg.text)})

    if response.status_code == 200:
        await msg.answer(f'Категория обновлена.', reply_markup=kb.main_menu())
    else:
        await msg.answer('Категория не обновлена.', reply_markup=kb.main_menu())
    await state.clear()


@router.callback_query(ChangeCategory.choosing_action, F.data == 'remove')
async def remove_category(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    state_data = await state.get_data()
    id_category = state_data['id_selected_category']

    response = await EiCategoriesService.delete(
        users[user_id]['token'], id_category)

    if response.status_code == 200:
        await callback.message.edit_text(f'Категория удалена.')
    else:
        await callback.message.edit_text('Категория не удалена.')
    await state.clear()
    await callback.answer()
