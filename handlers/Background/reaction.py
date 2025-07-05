from untils.Imports import *
import json
from datetime import datetime, timedelta
import asyncio

from .locks import *

async def update_reaction_tasks_periodically():
    """Обновление заданий на реакции"""
    while True:
        try:
            all_tasks = await DB.select_reaction_tasks()
            
            with reaction_cache_lock:
                global available_reaction_tasks
                # Сохраняем старые задания при ошибке
                available_reaction_tasks = all_tasks if all_tasks else available_reaction_tasks
                print(f"Задания на реакции обновлены. Доступно: {len(available_reaction_tasks)}")

        except Exception as e:
            print(f"Ошибка в update_reaction_tasks_periodically: {e}")

        await asyncio.sleep(600)