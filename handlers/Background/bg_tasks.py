from untils.Imports import *
import json
from datetime import datetime, timedelta
import asyncio

from .boost import *
from .link import *
from .reaction import *
from .chat import *
from .post import *
from .channel import *
from .mining import *
from .db import *
from .locks import *
from handlers.Tasks.tasks import all_price

task_processing_lock = asyncio.Lock()
semaphore = asyncio.Semaphore(2)



# Глобальная блокировка для доступа к кэшу


async def check_all_active_boosts(bot: Bot):
    """Проверяет все активные бусты и обрабатывает ежедневные платежи"""
    print("[BG TASK] Фоновая задача проверки бустов запущена")
    
    while True:
        try:
            print("\n[BG TASK] Начало новой итерации проверки")
            pending_tasks = await DB.get_pending_bg_tasks()
            print(f"[BG TASK] Получено задач: {len(pending_tasks)}")
            
            if not pending_tasks:
                print("[BG TASK] Нет задач для обработки")
                await asyncio.sleep(30)
                continue
            
            for task in pending_tasks:
                task_id, task_type, task_data_json, status, created_at, next_run_at, attempts = task
                print(f"\n[BG TASK] Обрабатываем задачу ID: {task_id}, тип: {task_type}")
                
                try:
                    # Удаляем текущую задачу перед обработкой
                    await DB.mark_bg_task_completed(task_id)
                    
                    task_data = json.loads(task_data_json)
                    
                    if task_type == 'boost_check':
                        boost_task = await Boost.get_task_by_id(task_data['task_id'])
                        
                        if not boost_task:
                            print(f"[BG TASK] Задание {task_data['task_id']} не найдено")
                            continue
                            
                        is_active = await Boost.has_user_boosted(
                            task_data['user_id'], 
                            task_data['chat_id']
                        )
                        
                        if not is_active:
                            print(f"[BG TASK] Буст неактивен")
                            await bot.send_message(
                                task_data['user_id'],
                                f"❌ Ваш буст для задания {task_data['task_id']} был удален. Начисления прекращены."
                            )
                            continue
                        
                        daily_cost = all_price['boost']
                        await DB.add_balance(amount=daily_cost, user_id=task_data['user_id'])
                        await DB.add_transaction(
                            user_id=task_data['user_id'],
                            amount=daily_cost,
                            description=f"Доход за день {task_data['days_checked'] + 1} буста",
                        )

                        days_left = task_data['total_days'] - (task_data['days_checked'] + 1)
                        
                        # Уведомляем пользователей
                        await bot.send_message(
                            task_data['user_id'],
                            f"🎉 Вы получили {daily_cost} MITcoin за {task_data['days_checked'] + 1}-й день буста!\n"
                            f"Осталось дней: {days_left}"
                        )
                            
                        if days_left > 0:
                            # Создаем новую задачу только если есть оставшиеся дни
                            await DB.add_bg_task(
                                task_type='boost_check',
                                task_data={
                                    'task_id': task_data['task_id'],
                                    'user_id': task_data['user_id'],
                                    'chat_id': task_data['chat_id'],
                                    'days_checked': task_data['days_checked'] + 1,
                                    'total_days': task_data['total_days']
                                },
                                delay_seconds=86400  # 24 часа (1 день)
                            )
                        else:
                            await bot.send_message(
                                task_data['user_id'],
                                f"✅ Буст для задания {task_data['task_id']} завершен!"
                            )
                            await bot.send_message(
                                boost_task[1],  # creator_id
                                f"✅ Один из пользователей закончил {task_data['total_days']}-дневный буст вашего канала"
                            )

                except Exception as e:
                    print(f"[BG TASK ERROR] Ошибка при выполнении задачи {task_id}: {str(e)}")
                    continue
            
            print("[BG TASK] Итерация завершена, ожидаем 30 секунд")
            await asyncio.sleep(30)
            
        except Exception as e:
            print(f"[BG TASK CRITICAL] Критическая ошибка в основном цикле: {str(e)}")
            await asyncio.sleep(60)

async def restore_background_tasks(bot: Bot):
    """Восстанавливает все активные фоновые задачи при запуске бота"""
    print("[BG TASK] Восстановление фоновых задач...")
    try:
        async with DB.con.cursor() as cur:
            await cur.execute('''
                SELECT * FROM background_tasks 
                WHERE status IN ('pending', 'failed', 'running')
            ''')
            tasks = await cur.fetchall()
            print(f"[BG TASK] Найдено задач для восстановления: {len(tasks)}")
            
            for task in tasks:
                task_id, task_type, task_data_json, status, created_at, next_run_at, attempts = task
                print(f"[BG TASK] Обработка задачи ID: {task_id}, тип: {task_type}")
                
                try:
                    task_data = json.loads(task_data_json)
                    
                    if task_type == 'boost_check':
                        # Для задач буста проверяем, что задание еще существует
                        boost_task = await Boost.get_task_by_id(task_data['task_id'])
                        if not boost_task:
                            print(f"[BG TASK] Задание {task_data['task_id']} не найдено, удаляем задачу")
                            await cur.execute('DELETE FROM background_tasks WHERE task_id = ?', (task_id,))
                            continue
                            
                        try:
                            # Обрабатываем дату с миллисекундами или без
                            if isinstance(next_run_at, str):
                                if '.' in next_run_at:
                                    next_run = datetime.strptime(next_run_at, '%Y-%m-%d %H:%M:%S.%f')
                                else:
                                    next_run = datetime.strptime(next_run_at, '%Y-%m-%d %H:%M:%S')
                            else:
                                next_run = next_run_at
                            
                            delay = (next_run - datetime.now()).total_seconds()
                            delay = max(60, delay)  # Минимум 1 минута
                            
                            print(f"[BG TASK] Восстанавливаем задачу, delay: {delay} сек.")
                            
                            # Создаем новую задачу
                            await DB.add_bg_task(
                                task_type='boost_check',
                                task_data=task_data,
                                delay_seconds=delay
                            )
                        except ValueError as e:
                            print(f"[BG TASK ERROR] Ошибка парсинга даты {next_run_at}: {e}")
                            # Если не удалось распарсить дату, ставим задержку 1 час
                            await DB.add_bg_task(
                                task_type='boost_check',
                                task_data=task_data,
                                delay_seconds=3600
                            )
                    
                    # Удаляем старую задачу
                    await cur.execute('DELETE FROM background_tasks WHERE task_id = ?', (task_id,))
                    print(f"[BG TASK] Задача {task_id} восстановлена и удалена из старых")
                    
                except Exception as e:
                    print(f"[BG TASK ERROR] Ошибка при восстановлении задачи {task_id}: {e}")
            
            await DB.con.commit()
    except Exception as e:
        print(f"[BG TASK ERROR] Критическая ошибка при восстановлении задач: {e}")
    finally:
        print("[BG TASK] Восстановление задач завершено")


async def start_background_tasks(bot: Bot, DB):
    asyncio.create_task(check_all_active_boosts(bot)) #boost
    asyncio.create_task(update_boost_tasks_periodically(bot)) #boost
    asyncio.create_task(scheduled_cache_update_chat(bot, DB)) #chat
    asyncio.create_task(update_tasks_periodically_link())
    asyncio.create_task(restore_background_tasks(bot))
    asyncio.create_task(update_reaction_tasks_periodically()) #reactions
    asyncio.create_task(process_tasks_periodically(bot)) #post
    asyncio.create_task(scheduled_cache_update(bot, DB)) #channel
    asyncio.create_task(remind_mining_collection(bot))
    asyncio.create_task(scheduled_db_backup(bot)) #отправка бд в чат
    asyncio.create_task(check_subscriptions_periodically(bot))
    asyncio.create_task(check_subscriptions_periodically_boost(bot))
