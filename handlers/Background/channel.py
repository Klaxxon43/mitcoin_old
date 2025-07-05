from untils.Imports import *
import json
from datetime import datetime, timedelta
import asyncio

from .locks import *


async def scheduled_cache_update(bot, DB):
    """Функция для запуска обновления кэша задач раз в 5 минут."""
    while True:
        await update_task_cache_for_all_users(bot, DB)
        await asyncio.sleep(300)  # Changed from 600 to 300 seconds (5 minutes)

async def update_task_cache_for_all_users(bot, DB):
    tasks = [cache_all_tasks(bot, DB)]
    await asyncio.gather(*tasks)
    print("Кэш (каналы) обновлен")



async def cache_all_tasks(bot, DB):
    """Кэшируем задания на каналы с сохранением старых данных во время обновления"""
    try:
        all_tasks = await DB.select_chanel_tasks()
        new_tasks_with_links = []
        print(f'Все задания в БД: {len(all_tasks)}')
        
        from handlers.Tasks.channel import semaphore
        async with semaphore:
            for task in all_tasks:
                try:
                    chat = await bot.get_chat(task[2])
                    if not chat.invite_link:
                        print(f"Канал {task[2]} не имеет invite_link, пропускаем")
                        continue
                        
                    if task[3] <= 0:
                        print(f"Задание {task[0]} имеет amount={task[3]}, пропускаем")
                        continue
                        
                    new_tasks_with_links.append((*task, chat.title))
                    
                except Exception as e:
                    print(f'Ошибка при обработке задания {task[0]}: {str(e)}')
                    continue

        # Обновляем кэш
        from .bg_tasks import cache_lock, task_cache
        with cache_lock:
            task_cache['all_tasks'] = new_tasks_with_links
            print(f"Кэш обновлен. Заданий: {len(new_tasks_with_links)}")
            
    except Exception as e:
        print(f'Критическая ошибка в cache_all_tasks: {str(e)}')



async def check_subscriptions_periodically(bot: Bot):
    while True:
        await asyncio.sleep(7200)  # Каждые 2 часа
        print('провожу проверку')
        try:
            active_tasks = await DB.get_active_completed_tasks()
            print(active_tasks)
            for task in active_tasks:
                user_id, task_id, target_id, task_sum, owner_id, status, rem_days, *_ = task
                
                # Проверка подписки
                try:
                    member = await bot.get_chat_member(target_id, user_id)
                    print('member: '+ str(member))
                    is_subscribed = member.status in ['member', 'administrator', 'creator']
                except Exception:
                    is_subscribed = False

                if not is_subscribed:
                    # Отправка предупреждения
                    try:
                        chat = await bot.get_chat(target_id)
                        invite_link = chat.invite_link
                        keyboard = InlineKeyboardMarkup(inline_keyboard=[
                            [InlineKeyboardButton(text="Подписаться", url=invite_link)] 
                        ])
                        
                        await bot.send_message(
                            user_id,
                            f"⚠️ Вы отписались от {chat.title}!\n"
                            "Пожалуйста, подпишитесь снова в течение 2 часов, "
                            f"иначе будет списано {task_sum} MITcoin!",
                            reply_markup=keyboard
                        )
                        
                        # Ждем 2 часа и проверяем снова
                        await asyncio.sleep(7200) 
                        member = await bot.get_chat_member(target_id, user_id)
                        is_subscribed = member.status in ['member', 'administrator', 'creator']
                        
                        if not is_subscribed:
                            # Списание средств
                            await DB.add_balance(user_id, -task_sum)
                            await DB.add_balance(owner_id, task_sum)
                            await DB.update_completed_task(user_id, status=0) 
                            
                            await bot.send_message(
                                user_id,
                                f"❌ Вам списан штраф {task_sum} MITcoin "
                                f"за отписку от {chat.title}!"
                            )
                            await bot.send_message(
                                owner_id,
                                f"💸 Вам возвращено {task_sum} MITcoin "
                                f"от пользователя {user_id} за отписку"
                            )
                            
                    except Exception as e:
                        print(f"Ошибка обработки штрафа: {e}")

            # Ежедневное уменьшение rem_days
            if datetime.now().hour == 0 or datetime.now().hour == 1:  # В полночь
                await DB.con.execute('''
                    UPDATE completed_tasks 
                    SET rem_days = rem_days - 1 
                    WHERE status = 1 AND rem_days > 0
                ''')
                await DB.con.commit()
                
        except Exception as e:
            print(f"Ошибка в фоновой задаче: {e}")
