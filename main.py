import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.enums.parse_mode import ParseMode
from config import API_TOKEN
from client import client, start_background_tasks
from admin import admin
from db import DB
from aiogram.client.default import DefaultBotProperties

logging.basicConfig(level=logging.INFO)

async def main():
    bot = Bot(API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    dp.include_routers(client, admin)
    await bot.delete_webhook(drop_pending_updates=True)
    await DB.create()
    await start_background_tasks(bot, DB)
    await dp.start_polling(bot)


asyncio.run(main())
