import asyncio
import logging

from aiogram import Bot, Dispatcher

from config import settings
from routers import router as main_router

bot = Bot(token=settings.BOT_TOKEN)
dp = Dispatcher()
dp.include_router(main_router)


async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
