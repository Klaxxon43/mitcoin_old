import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.enums.parse_mode import ParseMode
from config import *
from client import client, start_background_tasks
from admin import admin
from db import DB
from aiogram.client.default import DefaultBotProperties
from aiogram.types import BotCommand, BotCommandScopeDefault
from aiohttp import web
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

logging.basicConfig(level=logging.INFO)


# Функция, которая будет вызвана при запуске бота
async def on_startup(bot: Bot) -> None:
    await bot.set_webhook(f"{BASE_URL}{WEBHOOK_PATH}")
    await DB.create()
    await start_background_tasks(bot, DB)

# Функция, которая будет вызвана при остановке бота
async def on_shutdown(bot: Bot) -> None:
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.session.close()


def main():
    bot = Bot(API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    dp.include_routers(client, admin)
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    app = web.Application()
    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,  
        bot=bot  
    )
    webhook_requests_handler.register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)
    web.run_app(app, host=HOST, port=PORT)


main()

