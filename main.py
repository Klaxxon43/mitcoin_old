import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.enums.parse_mode import ParseMode
from aiogram.client.default import DefaultBotProperties
from datetime import datetime, timedelta

from utils.Imports import *
from handlers.client.client import router
from handlers.Admin.admin import admin
from handlers.client.promo import pr
from datebase.db import DB 
from datebase.db_create import DB as DB_CREATE
# from other.casino import casino
from handlers.inline_query import iq
from handlers.buyStars import BuyStars
from handlers.client.mining import mining
from handlers.bots import bots, pytz
from handlers.Tasks.tasks import tasks
from handlers.Tasks.redis_task_manager import RedisTasksManager
from handlers.Admin.contest import on_startup as on_startup_contest
from handlers.Background.bg_tasks import restore_background_tasks, check_all_active_boosts, start_background_tasks
from zoneinfo import ZoneInfo

logging.basicConfig(level=logging.INFO)

# Фоновые задачи
scheduler_task = None
boost_task = None

async def on_startup(bot: Bot) -> None:
    global scheduler_task, boost_task
    os.makedirs("./data", exist_ok=True)
    await DB.create()
    await DB_CREATE.create()
    await start_background_tasks(bot, DB)
    await on_startup_contest(bot)
    scheduler_task = asyncio.create_task(run_scheduler(bot))
    await restore_background_tasks(bot)
    boost_task = asyncio.create_task(check_all_active_boosts(bot))
    # asyncio.create_task(check_recurring_contests(bot))  # Добавлено
    asyncio.create_task(RedisTasksManager.start_periodic_check(bot))

async def daily_task(bot: Bot):
    # ⁡⁣⁣⁢Ежедневные задания⁡
    try:
        logger.info('[daily] Выполняю reset_daily_statistics')
        await DB.reset_daily_statistics()
        logger.info('[daily] reset_daily_statistics выполнена')

        now_moscow = datetime.now(ZoneInfo("Europe/Moscow"))
        if now_moscow.weekday() == 0:  # Понедельник по МСК
            await DB.reset_weekly_statistics()
        
        await reset_daily_and_weekly_tasks(bot)
        logger.info("✅ Выполнена задача 00:00 по МСК")
    except Exception as e:
        logger.error(f'Ошибка при выполнении задачи 00:00 по МСК\n\nОшибка:{e}')
        for id in ADMINS_ID:
            await bot.send_message(id, f'Ошибка при выполнении задачи 00:00 по МСК\n\nОшибка:{e} \n😭Исправь меня')

async def run_scheduler(bot: Bot):
    logger.info("[Scheduler] Запущен run_scheduler") 
    msk_timezone = pytz.timezone('Europe/Moscow')
    while True:
            now = datetime.now(msk_timezone)
            next_midnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            seconds = (next_midnight - now).total_seconds()
            logger.info(f"[Scheduler] Следующее срабатывание через {seconds} секунд")
            await asyncio.sleep(seconds)
            logger.info('[Scheduler] выполняю')
            await daily_task(bot)


async def reset_daily_and_weekly_tasks(bot: Bot):
    async with DB.con.cursor() as cur:
        await cur.execute('''
            UPDATE users 
            SET 
                dayly_completed_task = 0,
                last_daily_reset = datetime('now')
            WHERE 
                datetime(last_daily_reset) < datetime('now', '-1 day')
                OR last_daily_reset IS NULL
        ''')

        await cur.execute('''
            UPDATE users 
            SET 
                weekly_completed_task = 0,
                last_weekly_reset = datetime('now')
            WHERE 
                datetime(last_weekly_reset) < datetime('now', '-7 days')
                OR last_weekly_reset IS NULL
        ''')

        await DB.con.commit()

    logger.debug("[Reset] Сброс ежедневных/еженедельных задач выполнен")


async def main():
    bot = Bot(API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    dp.include_routers(pr, router, admin, iq, BuyStars, mining, bots, tasks)

    dp.startup.register(on_startup)
    # dp.shutdown.register(on_shutdown)

    logger.info("[Bot] Запуск polling...")
    await dp.start_polling(bot, skip_updates=False)



if __name__ == "__main__":
    asyncio.run(main())
