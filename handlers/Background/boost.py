from untils.Imports import *
import json
from datetime import datetime, timedelta
import asyncio
from .locks import *

task_processing_lock = asyncio.Lock()

async def update_boost_tasks_periodically(bot: Bot):
    """
    Фоновая задача, которая каждые 10 минут обновляет список заданий на буст.
    """
    while True:
        global available_boost_tasks
        async with task_processing_lock:
            # Получаем все задания из базы данных
            all_tasks = await DB.select_boost_tasks()
            
            # Фильтруем задания, проверяя доступ бота к каналам
            filtered_tasks = []
            errors = []
            for task in all_tasks:
                try:
                    # Извлекаем chat_id или username
                    target = await extract_chat_id_or_username(task[2])
                    print(target)
                    
                    # Пытаемся получить информацию о канале
                    
                    # chat: Chat = await bot.get_chat(target)
                    # Если ошибки нет, значит бот имеет доступ к каналу
                    filtered_tasks.append(task)
                except Exception as e:
                    errors.append(f"Ошибка при проверке доступа к каналу {task[2]}: {str(e)}")
                    continue
            
            # Перемешиваем список заданий для случайного порядка
            random.shuffle(filtered_tasks)
            
            # Обновляем глобальный список доступных заданий
            available_boost_tasks = filtered_tasks
            
            # Отправляем отчёт в чат INFO_ID
            report_message = (
                f"✅ Задания на буст обновлены.\n"
                f"📊 Всего заданий: {len(all_tasks)}\n"
                f"🟢 Доступных заданий: {len(filtered_tasks)}\n"
                f"🔴 Ошибок: {len(errors)}\n"
            )
            if errors:
                report_message += "\nОшибки:\n" + "\n".join(errors)
            
            try:
                await bot.send_message(chat_id=INFO_ID, text=report_message)
            except Exception as e:
                print(f"Ошибка при отправке отчёта: {e}")
        
        # Ждем 10 минут перед следующим обновлением
        await asyncio.sleep(600)  # 600 секунд = 10 минут



async def extract_chat_id_or_username(target: str) -> str:
    """
    Извлекает chat_id или username из строки.
    Поддерживает форматы:
    - ID канала (например, -1001234567890)
    - @username (например, @channel)
    - https://t.me/username (например, https://t.me/channel)
    - username (например, klaxxon_off)
    """
    # Если это ссылка, извлекаем username
    if target.startswith("https://t.me/"):
        return target.split("/")[-1]  # Извлекаем часть после последнего /
    # Если это @username, убираем @
    elif target.startswith("@"):
        return target[1:]
    # Если это числовой ID (начинается с "-100"), возвращаем как есть
    elif re.match(r"^-?\d+$", target):
        return target
    # В остальных случаях считаем, что это username (например, klaxxon_off)
    else:
        return target
    


async def check_subscriptions_periodically_boost(bot: Bot):
    while True:
        await asyncio.sleep(7200)  # Каждые 2 часа
        print('Провожу проверку')
        try:
            # Получаем активные задания (status = 1) и задания на буст (status = 6)
            active_tasks = await DB.get_active_completed_tasks()
            boost_tasks = await DB.get_boost_tasks()  # Нужно добавить метод get_boost_tasks в DB

            # Обработка заданий на буст (status = 0)
            for task in boost_tasks:
                user_id, task_id, target_id, task_sum, owner_id, status, rem_days, *_ = task
                
                # Проверка буста
                try:
                    channel_username = target_id  # Предполагаем, что target_id содержит username канала
                    is_boost_active = None #await boost(channel_username, user_id)
                    print(f'Проверка буста для {user_id} в {channel_username}: {is_boost_active}')
                    
                    if not is_boost_active:
                        # Отправка предупреждения
                        try:
                            await bot.send_message(
                                user_id,
                                f"⚠️ Буст для канала {channel_username} неактивен!\n"
                                "Пожалуйста, возобновите буст в течение 2 часов, "
                                f"иначе будет списано {task_sum} $MICO!"
                            )
                            
                            # Ждем 2 часа и проверяем снова
                            await asyncio.sleep(7200)
                            is_boost_active = None #await boost(channel_username, user_id)
                            
                            if not is_boost_active:
                                # Списание средств
                                await DB.add_balance(user_id, -task_sum)
                                await DB.add_balance(owner_id, task_sum)
                                await DB.update_completed_task(task_id, status=0) 
                                
                                await bot.send_message(
                                    user_id,
                                    f"❌ Вам списан штраф {task_sum} $MICO "
                                    f"за неактивный буст канала {channel_username}!"
                                )
                                await bot.send_message(
                                    owner_id,
                                    f"💸 Вам возвращено {task_sum} $MICO "
                                    f"от пользователя {user_id} за неактивный буст"
                                )
                                
                                await DB.con.execute(''' DELETE FROM completed_tasks 
                                                     WHERE user_id = ? AND target_id =?''',
                                                       (user_id, channel_username)) 
                                await DB.con.commit() 
                        except Exception as e:
                            print(f"Ошибка обработки штрафа за буст: {e}") 
                            
                except Exception as e:
                    print(f"Ошибка проверки буста: {e}")

            # Ежедневное уменьшение rem_days
            if datetime.now().hour == 0 or datetime.now().hour == 1:  # В полночь
                # if is_boost_active:
                await DB.con.execute('''
                    UPDATE completed_tasks 
                    SET rem_days = rem_days - 1 
                    WHERE user_id = ? AND target_id = ? AND rem_days > 0
                ''', (user_id, channel_username))
                await DB.con.commit() 
                
        except Exception as e:
            print(f"Ошибка в фоновой задаче: {e}")
