import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.enums.parse_mode import ParseMode
from config import *
from handlers.client.client import router
from handlers.Admin.admin import admin
from handlers.promo import pr
from datebase.db import DB
from datebase.db_create import DB as DB_CREATE
from aiogram.client.default import DefaultBotProperties
from other.casino import casino
from handlers.inline_query import iq
from handlers.buyStars import BuyStars
from handlers.mining import mining
from handlers.bots import bots, pytz
from datetime import datetime, timedelta
from aiocryptopay import AioCryptoPay, Networks
from handlers.Tasks.tasks import tasks
from handlers.Admin.contest import on_startup as on_startup_contest
from handlers.Background.bg_tasks import restore_background_tasks, check_all_active_boosts, start_background_tasks
from handlers.Checks.menu import check_router

logging.basicConfig(level=logging.INFO)

async def on_startup(bot: Bot) -> None:
    os.makedirs("./data", exist_ok=True)
    await DB.create()
    await DB_CREATE.create()
    await start_background_tasks(bot, DB)
    await on_startup_contest(bot)
    asyncio.create_task(run_scheduler(bot))
    await restore_background_tasks(bot)
    asyncio.create_task(check_all_active_boosts(bot))

async def on_shutdown(bot: Bot) -> None:
    await bot.session.close()

async def daily_task(bot: Bot):
    await DB.reset_daily_statistics()
    await reset_daily_and_weekly_tasks(bot)
    print("Выполняю задачу в 00:00!")

async def run_scheduler(bot: Bot):
    msk_timezone = pytz.timezone('Europe/Moscow')
    while True:
        try:
            now = datetime.now(msk_timezone)
            next_midnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            target_time = (next_midnight - now).total_seconds()
            print(f"Время до следующей 00:00 по МСК: {target_time} секунд")
            await asyncio.sleep(target_time)
            await daily_task(bot)
        except Exception as e:
            logging.error(f"Ошибка в run_scheduler: {e}")
            await asyncio.sleep(60)

async def reset_daily_and_weekly_tasks(bot: Bot):
    """Сбрасывает ежедневные и еженедельные задачи при необходимости"""
    async with DB.con.cursor() as cur:
        # Сбрасываем дневные задачи, если прошло больше 24 часов
        await cur.execute('''
            UPDATE users 
            SET 
                daily_completed_task = 0,
                last_daily_reset = datetime('now')
            WHERE 
                datetime(last_daily_reset) < datetime('now', '-1 day')
                OR last_daily_reset IS NULL
        ''')
        
        # Сбрасываем недельные задачи, если прошло больше 7 дней
        await cur.execute('''
            UPDATE users 
            SET 
                weekly_completed_task = 0,
                last_weekly_reset = datetime('now')
            WHERE 
                datetime(last_weekly_reset) < datetime('now', '-7 days')
                OR last_weekly_reset IS NULL
        ''')
        
        affected_rows = cur.rowcount
        await DB.con.commit()
    
    # Логируем действие
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{now}] Выполнен сброс ежедневных/еженедельных задач. Затронуто строк: {affected_rows}")
    

async def main():
    # Создаем event loop явно
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    bot = Bot(API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    dp.include_routers(pr, router, admin, casino, iq, BuyStars, mining, bots, tasks, check_router)
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())