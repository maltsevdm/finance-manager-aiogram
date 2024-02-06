from aiogram import types
from aiogram.utils.keyboard import ReplyKeyboardBuilder

BT_SUMMARY = 'Сводка'
BT_CHANGE_BALANCE = 'Изменить баланс'
BT_REGISTER = 'Зарегистрироваться'
BT_LOGIN = 'Войти'
BT_MAIN_MENU = 'Главное меню'
BT_MANAGE_CATEGORIES = 'Управление категориями'
BT_ADD_TRANSACTION = 'Добавить транзакцию'
BT_ADD_INCOME = 'Добавить поступление'
BT_MY_CATEGORIES = 'Мои категории'
BT_ADD_CATEGORY = 'Добавить категорию'
BT_CHANGE_CATEGORY = 'Изменить'
BT_REMOVE_CATEGORY = 'Удалить'
BT_CATEGORIES_INCOME = 'Категории поступлений'
BT_CATEGORIES_EXPENSE = 'Категории расходов'
BT_CATEGORIES_BANK = 'Счета'
BT_CATEGORIES_ALL = 'Все'


def auth():
    buttons = [
        [types.KeyboardButton(text=BT_REGISTER),
         types.KeyboardButton(text=BT_LOGIN)]
    ]
    keyboard = types.ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
    return keyboard


def main_menu():
    buttons = [
        [
            types.KeyboardButton(text=BT_SUMMARY),
            types.KeyboardButton(text='Аккаунт')
        ],
        [types.KeyboardButton(text=BT_ADD_TRANSACTION)],
        [types.KeyboardButton(text=BT_MANAGE_CATEGORIES)]
    ]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True
    )
    return keyboard


def category_manager():
    buttons = [
        [types.KeyboardButton(text=BT_MY_CATEGORIES)],
        [types.KeyboardButton(text=BT_ADD_CATEGORY)],
        [types.KeyboardButton(text=BT_MAIN_MENU)]
    ]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True
    )
    return keyboard


def change_category():
    buttons = [
        [types.KeyboardButton(text='Изменить имя')],
        [types.KeyboardButton(text='Удалить')],
        [types.KeyboardButton(text=BT_MAIN_MENU)]
    ]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True
    )
    return keyboard


def category_group():
    buttons = [
        [
            types.KeyboardButton(text=BT_CATEGORIES_INCOME),
            types.KeyboardButton(text=BT_CATEGORIES_EXPENSE),
            types.KeyboardButton(text=BT_CATEGORIES_BANK),
            types.KeyboardButton(text=BT_MAIN_MENU),
        ]
    ]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True
    )
    return keyboard


def main_menu_button():
    buttons = [
        [types.KeyboardButton(text=BT_MAIN_MENU)]
    ]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True
    )
    return keyboard


def from_categories(categories: list) -> ReplyKeyboardBuilder:
    builder = ReplyKeyboardBuilder()
    for category in categories:
        builder.add(types.KeyboardButton(text=category))
    return builder
