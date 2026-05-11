import sys
from pathlib import Path

import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from config.conf import BOT_TOKEN, REDIS_URL
from handlers.user import router as user_router
from handlers.admin import router as admin_router
from database.utils import init_db
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery,InlineKeyboardMarkup,InlineKeyboardButton


async def main():
    bot = Bot(token=BOT_TOKEN)
    storage = RedisStorage.from_url(REDIS_URL)
    dp = Dispatcher(storage=storage)

    await init_db()

    dp.include_router(user_router)
    dp.include_router(admin_router)

    # @dp.message(F.photo)
    # async def catch_photo_id(message: Message):
    #     file_id = message.photo[-1].file_id
    #     await message.answer(f"✅ file_id: <code>{file_id}</code>", parse_mode="HTML")
    #     await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())