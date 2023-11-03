import asyncio
import logging

from aiogram import Bot, Dispatcher, F, types
from aiogram.enums.parse_mode import ParseMode
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message

import config
from handlers import router


# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO)
# Объект бота
bot = Bot(token=config.TOKEN)
# Диспетчер
dp = Dispatcher()
users = {}


@dp.message(Command("start"))
async def start_handler(msg: Message):
    user_id = msg.from_user.id
    if user_id in users:
        kb = [
            [types.KeyboardButton(text='Баланс')]
        ]
        keyboard = types.ReplyKeyboardMarkup(
            keyboard=kb,
            resize_keyboard=True)
        await msg.answer('Привет! Ты зарегистрирован.', reply_markup=keyboard)
    else:
        kb = [
            [types.KeyboardButton(text='Зарегистрироваться')]
        ]
        keyboard = types.ReplyKeyboardMarkup(
            keyboard=kb,
            resize_keyboard=True)
        await msg.answer('Привет! Ты не зарегистрирован.', reply_markup=keyboard)


@dp.message(F.text.lower() == 'зарегистрироваться')
async def register_handler(msg: Message):
    user_id = msg.from_user.id
    users[user_id] = {'balance': 0, 'categories': []}
    kb = [
        [types.KeyboardButton(text='Баланс')]
    ]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True)
    await msg.answer('Ты зарегистрирован.', reply_markup=keyboard)


@dp.message(F.text.lower() == 'баланс')
async def register_handler(msg: Message):
    user_id = msg.from_user.id
    balance = users[user_id]['balance']
    await msg.answer(f'Баланс: {balance} рублей.')


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
