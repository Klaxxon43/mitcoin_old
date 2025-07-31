from utils.Imports import *
from utils.redis_utils import *
import json
from datetime import datetime, timedelta
import asyncio

from .locks import *

semaphore = asyncio.Semaphore(2)

async def scheduled_cache_update_chat(bot, DB):
    """Функция для запуска обновления кэша задач раз в 5 минут."""
    while True:
        await update_task_cache_for_all_users_chat(bot, DB)
        await asyncio.sleep(500)  # Задержка в 300 секунд (7 минут)

async def update_task_cache_for_all_users_chat(bot, DB):
    tasks = [get_cached_tasks_chat(bot, DB)]
    await asyncio.gather(*tasks)
    logger.info("Кэш (чаты) обновлен")


async def get_cached_tasks_chat(bot, DB):
    """Кэшируем задания на чаты с сохранением старых данных"""
    cache_key = "chat_tasks"
    cached_tasks = await get_cached_data(cache_key)
    
    if cached_tasks:
        with chat_cache_lock:
            task_cache_chat['all_tasks'] = cached_tasks
        return
    
    all_tasks = await DB.select_chat_tasks()
    new_tasks = []
    
    async with semaphore:
        for task in all_tasks:
            try:
                invite_link = await check_admin_and_get_invite_link_chat(bot, task[2])
                if invite_link and task[3] > 0:
                    try:
                        chat = await bot.get_chat(task[2])
                        chat_title = chat.title
                    except:
                        chat_title = "Неизвестный чат"
                    new_tasks.append((*task, chat_title))
            except Exception as e:
                continue

    with chat_cache_lock:
        if new_tasks:
            await set_cached_data(cache_key, new_tasks, ttl=300)
            task_cache_chat['all_tasks'] = new_tasks
            logger.info(f"Кэш чатов обновлен. Заданий: {len(new_tasks)}")


async def check_admin_and_get_invite_link_chat(bot, target_id):
    try:
        ChatFullInfo = await bot.get_chat(target_id)
        invite_link = ChatFullInfo.invite_link
        return invite_link
    except Exception as e:
        logger.info(e)
        return False
    