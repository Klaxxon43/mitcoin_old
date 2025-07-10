import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.enums.parse_mode import ParseMode
from aiogram.client.default import DefaultBotProperties
from datetime import datetime, timedelta

from config import *
from handlers.client.client import router
from handlers.Admin.admin import admin
from handlers.client.promo import pr
from datebase.db import DB
from datebase.db_create import DB as DB_CREATE
from other.casino import casino
from handlers.inline_query import iq
from handlers.buyStars import BuyStars
from handlers.client.mining import mining
from handlers.bots import bots, pytz
from handlers.Tasks.tasks import tasks
from handlers.Admin.contest import on_startup as on_startup_contest, check_recurring_contests
from handlers.Background.bg_tasks import restore_background_tasks, check_all_active_boosts, start_background_tasks
from handlers.Checks.menu import check_router

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
    asyncio.create_task(check_recurring_contests(bot))  # Добавлено


async def on_shutdown(bot: Bot) -> None:
    global scheduler_task, boost_task
    if scheduler_task:
        scheduler_task.cancel()
        try:
            await scheduler_task
        except asyncio.CancelledError:
            pass

    if boost_task:
        boost_task.cancel()
        try:
            await boost_task
        except asyncio.CancelledError:
            pass

    await bot.session.close()
    print("[Shutdown] Завершено корректно.")


async def daily_task(bot: Bot):
    await DB.reset_daily_statistics()
    await reset_daily_and_weekly_tasks(bot)
    print("✅ Выполнена задача 00:00 по МСК")


async def run_scheduler(bot: Bot):
    msk_timezone = pytz.timezone('Europe/Moscow')
    while True:
        try:
            now = datetime.now(msk_timezone)
            next_midnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            seconds = (next_midnight - now).total_seconds()
            print(f"[Scheduler] Следующее срабатывание через {seconds} секунд")
            await asyncio.sleep(seconds)
            await daily_task(bot)
        except asyncio.CancelledError:
            print("[Scheduler] Остановлен")
            break
        except Exception as e:
            logging.exception(f"[Scheduler] Ошибка: {e}")
            await asyncio.sleep(60)


async def reset_daily_and_weekly_tasks(bot: Bot):
    async with DB.con.cursor() as cur:
        await cur.execute('''
            UPDATE users 
            SET 
                daily_completed_task = 0,
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

    print("[Reset] Сброс ежедневных/еженедельных задач выполнен")


async def main():
    bot = Bot(API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    dp.include_routers(pr, router, admin, casino, iq, BuyStars, mining, bots, tasks, check_router)

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    try:
        print("[Bot] Запуск polling...")
        await dp.start_polling(bot, skip_updates=False)
    except (KeyboardInterrupt, SystemExit):
        print("[Bot] Остановка по запросу")
    finally:
        await on_shutdown(bot)


if __name__ == "__main__":
    asyncio.run(main())
