from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import (Message, InlineKeyboardButton, InlineKeyboardMarkup,
                           CallbackQuery)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.services.categories.banks import BanksService
from src.utils import kb
from src.states.banks import AddBank, ChangeBank, ManageBank
from src.users import users
from src.utils.kb import BT_ADD, BT_GO_BACK

router = Router()

bank_types = {
    'cash': 'Наличка',
    'credit_card': 'Кредитная карта',
    'debit_card': 'Дебетовая карта'
}


def get_kb_group():
    buttons = [
        [InlineKeyboardButton(text='Наличка',
                              callback_data='cash')],
        [InlineKeyboardButton(text='Дебетовая карта',
                              callback_data='debit_card')],
        [InlineKeyboardButton(text='Кредитная карта',
                              callback_data='credit_card')]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


def get_kb_action_change_bank(group: str):
    buttons = [
        [InlineKeyboardButton(text='Изменить имя',
                              callback_data='change_name')],
        [InlineKeyboardButton(text='Изменить сумму',
                              callback_data='change_amount')],
        [InlineKeyboardButton(text='Удалить',
                              callback_data='remove')],
    ]
    if group == 'credit_card':
        buttons.insert(2, [InlineKeyboardButton(text='Изменить баланс карты',
                                                callback_data='change_credit_card_balance')])
        buttons.insert(2, [InlineKeyboardButton(text='Изменить кредитный лимит',
                                                callback_data='change_credit_card_limit')])
    buttons.append([InlineKeyboardButton(text=BT_GO_BACK,
                                         callback_data='back_to_banks')])
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


def from_list(data: dict, cols: int = 1) -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    for bank in data:
        text = f'{bank["name"]}'

        builder.add(
            InlineKeyboardButton(text=text,
                                 callback_data='edit_' + str(bank['id'])))
    builder.adjust(cols)
    return builder


def get_description(item: dict) -> str:
    description = f'''<b>{item['name']}</b> 
    Тип: <i>{bank_types[item['group']]}</i>
    Ваши деньги: <i>{item['amount']}</i>'''
    if item['group'] == 'credit_card':
        description += f'''\n    Баланс карты: <i>{item['credit_card_balance']}</i>
    Кредитный лимит: <i>{item['credit_card_limit']}</i>'''
    return description


@router.message(F.text.lower() == kb.BT_BANKS.lower())
@router.callback_query(F.data == 'back_to_banks')
async def manage_banks(msg: Message | CallbackQuery, state: FSMContext):
    user_id = msg.from_user.id
    token = users[user_id]['token']

    response = await BanksService.read(token)
    assert response.status_code == 200

    banks_data = response.json()
    banks_dict = {}
    for bank in banks_data:
        banks_dict[int(bank['id'])] = bank

    if banks_data:
        await state.update_data(banks=banks_dict)
        answer_text = '<b>Ваши счета</b>'

        for bank in banks_data:
            answer_text += '\n\n' + get_description(bank)

        answer_text += '\n\nВыберите счёт для редактирования.'

        builder = from_list(banks_data)

        builder.add(
            InlineKeyboardButton(text=BT_ADD, callback_data='add')
        )
        builder.adjust(2)

        if isinstance(msg, CallbackQuery):
            await msg.message.edit_text(
                answer_text, reply_markup=builder.as_markup())
        else:
            await msg.answer(
                answer_text, reply_markup=builder.as_markup())
        await state.set_state(ManageBank.choosing_action)
    else:
        await msg.answer('Вы ещё не добавили ни одного счёта.')
        await state.clear()


@router.callback_query(ManageBank.choosing_action, F.data == 'add')
async def choice_action(callback: CallbackQuery, state: FSMContext):
    answer_text = 'В какую группу добавить счёт?'
    await state.set_state(AddBank.choosing_group)
    await callback.message.edit_text(answer_text, reply_markup=get_kb_group())
    await callback.answer()


@router.callback_query(ManageBank.choosing_action, F.data.startswith('edit_'))
async def update_category(callback: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    banks = state_data['banks']
    id_bank = callback.data.split('_')[1]
    bank = banks[int(id_bank)]
    group = bank['group']
    answer_text = get_description(bank) + '\n\nЧто хотите сделать со счётом?'
    await state.update_data(id_selected_category=id_bank)
    await callback.message.edit_text(
        answer_text, reply_markup=get_kb_action_change_bank(group))
    await state.set_state(ChangeBank.choosing_action)
    await callback.answer()


@router.callback_query(ChangeBank.choosing_action, F.data.startswith('change_'))
async def enter_new_value(callback: CallbackQuery, state: FSMContext):
    attrs = {
        'name': 'новое имя',
        'amount': 'новую сумму',
        'credit_card_balance': 'новый баланс карты',
        'credit_card_limit': 'новый кредитный лимит',
    }

    _, *attr = callback.data.split('_')
    attr = '_'.join(attr)
    await state.update_data(attr=attr)
    await callback.message.edit_text(f'Введите {attrs[attr]}:')
    await state.set_state(ChangeBank.entering_new_value)
    await callback.answer()


@router.callback_query(ChangeBank.choosing_action, F.data == 'remove')
async def remove_category(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    state_data = await state.get_data()
    id_category = state_data['id_selected_category']

    response = await BanksService.delete(
        users[user_id]['token'], id_category)

    if response.status_code == 200:
        await callback.message.edit_text(f'Счёт удален.')
    else:
        await callback.message.edit_text('Счёт не удален.')
    await state.clear()
    await callback.answer()


@router.callback_query(AddBank.choosing_group)
async def add_bank_choice_group(callback: CallbackQuery, state: FSMContext):
    group = callback.data

    await state.update_data(group=group)
    await callback.message.edit_text('Введите имя счёта:')
    await state.set_state(AddBank.entering_name)
    await callback.answer()


@router.message(AddBank.entering_name, F.text)
async def add_bank_enter_name(msg: Message, state: FSMContext):
    name = msg.text
    await state.update_data(name=name)
    await msg.answer('Введите баланс счёта:',
                     reply_markup=kb.main_menu_button())
    await state.set_state(AddBank.entering_amount)


@router.message(AddBank.entering_amount, F.text)
async def add_bank_enter_amount(msg: Message, state: FSMContext):
    amount = float(msg.text)
    state_data = await state.get_data()
    group = state_data['group']
    await state.update_data(amount=amount)

    if group == 'credit_card':
        await msg.answer('Введите баланс кредитной карты:',
                         reply_markup=kb.main_menu_button())
        await state.set_state(AddBank.entering_credit_card_balance)
    else:
        user_id = msg.from_user.id
        token = users[user_id]['token']
        name = state_data['name']

        response = await BanksService.create(
            token=token, name=name, group=group, amount=amount)

        if response.status_code == 200:
            await msg.answer(f'Счёт {name} успешно добавлен.',
                             reply_markup=kb.main_menu())
        else:
            await msg.answer(f'Ошибка! Счёт не добавлен. '
                             f'Детали: {response.json()["detail"]}',
                             reply_markup=kb.main_menu())
        await state.clear()


@router.message(AddBank.entering_credit_card_balance, F.text)
async def add_category_enter_credit_card_balance(msg: Message,
                                                 state: FSMContext):
    credit_card_balance = float(msg.text)
    await state.update_data(credit_card_balance=credit_card_balance)
    await msg.answer('Введите кредитный лимит:',
                     reply_markup=kb.main_menu_button())
    await state.set_state(AddBank.entering_credit_card_limit)


@router.message(AddBank.entering_credit_card_limit, F.text)
async def add_category_enter_credit_card_limit(msg: Message, state: FSMContext):
    credit_card_limit = float(msg.text)
    state_data = await state.get_data()
    user_id = msg.from_user.id
    token = users[user_id]['token']
    name = state_data['name']

    response = await BanksService.create(
        token=token,
        name=name,
        group=state_data['group'],
        amount=state_data['amount'],
        credit_card_balance=state_data['credit_card_balance'],
        credit_card_limit=credit_card_limit
    )

    if response.status_code == 200:
        await msg.answer(f'Счёт {name} успешно добавлен.',
                         reply_markup=kb.main_menu())
    else:
        await msg.answer(f'Ошибка! Счёт не добавлен. '
                         f'Детали: {response.json()["detail"]}',
                         reply_markup=kb.main_menu())
    await state.clear()


@router.message(ChangeBank.entering_new_value, F.text)
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
    response = await BanksService.update(
        token=token, id=id_category, **{attr: type_conversion_func(msg.text)})

    if response.status_code == 200:
        await msg.answer(f'Счёт обновлен.', reply_markup=kb.main_menu())
    else:
        await msg.answer('Счёт не обновлен.', reply_markup=kb.main_menu())
    await state.clear()
