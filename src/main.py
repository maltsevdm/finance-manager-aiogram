import asyncio
import logging

from aiogram import Bot, Dispatcher

from src import config
from src.handlers import router


async def main():
    bot = Bot(token=config.TOKEN, parse_mode='HTML')
    dp = Dispatcher()
    dp.include_routers(router)
    logging.basicConfig(level=logging.INFO)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
