from untils.Imports import *
import json
from datetime import datetime, timedelta
import asyncio

from .locks import *

async def update_tasks_periodically_link():
    """Обновление ссылочных заданий"""
    while True:
        try:
            all_tasks = await DB.select_link_tasks()
            random.shuffle(all_tasks)
            
            with link_cache_lock:
                global available_tasks
                # Сохраняем старые задания, если новые не загрузились
                available_tasks = all_tasks if all_tasks else available_tasks
                print(f"Ссылочные задания обновлены. Доступно: {len(available_tasks)}")
                
        except Exception as e:
            print(f"Ошибка в update_tasks_periodically_link: {e}")

        await asyncio.sleep(600)