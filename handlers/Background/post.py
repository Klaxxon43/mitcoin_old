from untils.Imports import *
from datetime import datetime, timedelta
import asyncio

from .locks import *

async def process_tasks_periodically(bot: Bot):
    """Обновление постовых заданий с сохранением доступности"""
    while True:
        try:
            all_tasks = await DB.select_post_tasks()
            random.shuffle(all_tasks)
            
            new_processed_tasks = []
            for task in all_tasks:
                try:
                    channel_id, post_id = map(int, task[2].split(':'))
                    await bot.forward_message(chat_id=INFO_ID, from_chat_id=channel_id, message_id=post_id)
                    new_processed_tasks.append(task)
                except Exception as e:
                    print(f"Ошибка при проверке поста {task[2]}: {e}")
                    continue

            with post_cache_lock:
                global processed_tasks
                # Сохраняем старые задания, если новые не прошли проверку
                processed_tasks = new_processed_tasks if new_processed_tasks else processed_tasks
                print(f"Постовые задания обновлены. Доступно: {len(processed_tasks)}")

        except Exception as e:
            print(f"Критическая ошибка в process_tasks_periodically: {e}")

        await asyncio.sleep(600)