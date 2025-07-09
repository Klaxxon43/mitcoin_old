from utils.Imports import *
from utils.redis_utils import *
from datetime import datetime, timedelta
import asyncio
from .locks import *

async def update_tasks_periodically():
    """Обновление заданий"""
    cache_key = "post"  # Заменить на соответствующий ключ для каждого типа
    
    try:
        cached_tasks = await get_cached_data(cache_key)
        if cached_tasks:
            with cache_lock:  # Использовать соответствующий lock
                global available_tasks  # Или processed_tasks, available_reaction_tasks и т.д.
                available_tasks = cached_tasks
            return
            
        all_tasks = await DB.select_tasks()  # Соответствующий метод для каждого типа
        random.shuffle(all_tasks)
        
        # Сохраняем в Redis и обновляем глобальную переменную
        await set_cached_data(cache_key, all_tasks, ttl=600)
        with cache_lock:
            available_tasks = all_tasks
            print(f"Задания обновлены. Доступно: {len(available_tasks)}")
            
    except Exception as e:
        print(f"Ошибка в update_tasks_periodically: {e}")

    await asyncio.sleep(600)