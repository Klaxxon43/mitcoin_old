import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.enums.parse_mode import ParseMode
from config import *
from client import client, start_background_tasks
from admin import admin
from db import DB
from aiogram.client.default import DefaultBotProperties
from db import db_main

logging.basicConfig(level=logging.INFO)


# Функция, которая будет вызвана при запуске бота
async def on_startup(bot: Bot) -> None:
    # Создаем директорию, если она не существует
    os.makedirs("./data", exist_ok=True)
    await DB.create()
    await start_background_tasks(bot, DB)
    asyncio.create_task(run_scheduler(bot))  # Запускаем планировщик


# Функция, которая будет вызвана при остановке бота
async def on_shutdown(bot: Bot) -> None:
    await bot.session.close()


async def daily_task(bot: Bot):
    await DB.reset_daily_statistics()
    print("Выполняю задачу в 00:00!")
    # Пример отправки сообщения через бота
    # await bot.send_message(chat_id=ADMIN_CHAT_ID, text="Ежедневная задача выполнена!")


async def run_scheduler(bot: Bot):
    while True:
        # Получаем текущее время
        now = asyncio.get_event_loop().time()
        target_time = (24 * 3600) - (now % (24 * 3600))  # Время до следующей 00:00

        # Ждем до 00:00
        await asyncio.sleep(target_time)

        # Выполняем задачу
        await daily_task(bot)


async def main():
    bot = Bot(API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    dp.include_routers(client, admin)
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    # Запуск бота в режиме polling
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())