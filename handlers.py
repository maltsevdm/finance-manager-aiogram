import json

from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import Message

router = Router()






# @router.message()
# async def message_handler(msg: Message):
#     user_id = msg.from_user.id
#     if msg.text == 'Зарегистрироваться':
#         users[user_id] = {'balance': 0, 'catigories': []}
#         kb = [
#             [types.KeyboardButton(text='Баланс')]
#         ]
#         keyboard = types.ReplyKeyboardMarkup(
#             keyboard=kb,
#             resize_keyboard=True)
#         await msg.answer('Ты зарегистрирован.', reply_markup=keyboard)
#     elif msg.text == 'Баланс':
#         balance = users[user_id]['balance']
#         await msg.answer(f'Баланс: {balance} рублей.')


