from utils.Imports import *
import asyncio
from typing import Optional, List, Dict, Any

from utils.Imports import *
import asyncio
from typing import Optional, List, Dict, Any

# Глобальные переменные
task_cache = {
    'tasks': {},
    'common_tasks_count': None,
    'cache_expiry': {}
}

all_price = {
    "channel": 1500,
    "chat": 1500,
    "post": 250,
    "comment": 750,
    "reaction": 500,
    "link": 1500,
    "boost": 5000
}

class RedisTasksManager:
    @staticmethod
    async def start_periodic_check(bot: Bot):
        """Запуск периодической проверки заданий"""
        while True:
            try:
                await RedisTasksManager.check_all_tasks(bot)
            except Exception as e:
                print(f"Ошибка в периодической проверке заданий: {e}")
            await asyncio.sleep(1800)  # 30 минут

    @staticmethod
    async def check_all_tasks(bot: Bot):
        """Проверка всех типов заданий"""
        task_types = ['channel', 'chat', 'post', 'comment', 'link', 'reaction', 'boost']
        
        for task_type in task_types:
            await RedisTasksManager.check_tasks_of_type(bot, task_type)
        
        await RedisTasksManager.update_common_tasks_count(bot)

    @staticmethod
    async def check_tasks_of_type(bot: Bot, task_type: str):
        """Проверка заданий конкретного типа с подробным логированием"""
        try:
            print(f"\nНачинаем проверку заданий типа: {task_type}")
            
            # Получаем текущий кэш (если есть)
            old_cache = await RedisTasksManager.get_cached_tasks(task_type) or []
            print(f"Текущий кэш ({task_type}): {len(old_cache)} заданий")
            
            # Получаем задания из БД
            task_mapping = {
                'channel': DB.select_chanel_tasks,
                'chat': DB.select_chat_tasks,
                'post': DB.select_post_tasks,
                'comment': DB.select_like_comment,
                'link': DB.select_link_tasks,
                'reaction': DB.select_reaction_tasks,
                'boost': DB.select_boost_tasks
            }
            
            db_tasks = await task_mapping[task_type]()
            print(f"Заданий в БД ({task_type}): {len(db_tasks)}")
            
            if not db_tasks:
                print(f"Нет заданий в БД для типа {task_type}, очищаем кэш")
                await RedisTasksManager.invalidate_cache(task_type)
                return

            valid_tasks = []
            invalid_tasks = []

            for task in db_tasks:
                try:
                    is_valid = await RedisTasksManager.is_task_valid(bot, task_type, task)
                    print(f"Задание {task[0]} - {'валидно' if is_valid else 'невалидно'}")
                    
                    if is_valid:
                        task_data = await RedisTasksManager.prepare_task_data(bot, task_type, task)
                        if task_data:
                            valid_tasks.append(task_data)
                    else:
                        invalid_tasks.append(task)
                except Exception as e:
                    print(f"Ошибка проверки задания {task[0]}: {e}")
                    invalid_tasks.append(task)

            print(f"Найдено валидных заданий: {len(valid_tasks)}, невалидных: {len(invalid_tasks)}")

            # Обрабатываем невалидные задания
            for task in invalid_tasks:
                await RedisTasksManager.handle_invalid_task(task_type, task, bot)

            if valid_tasks:
                print(f"Обновляем кэш для {task_type} с {len(valid_tasks)} заданиями")
                await RedisTasksManager.cache_tasks(task_type, valid_tasks)
            elif not old_cache:
                print(f"Нет валидных заданий и нет старого кэша, очищаем кэш для {task_type}")
                await RedisTasksManager.invalidate_cache(task_type)
            else:
                print(f"Оставляем старый кэш для {task_type} ({len(old_cache)} заданий)")

        except Exception as e:
            print(f"Критическая ошибка при проверке заданий типа {task_type}: {e}")

    @staticmethod
    async def is_task_valid(bot: Bot, task_type: str, task: tuple) -> bool:
        """Проверка валидности задания с улучшенной логикой и логами"""
        try:
            print(f"\n🔍 Начало проверки задания (тип: {task_type})")

            if task_type == 'boost':
                task_id, user_id, target_id, amount, task_type_db, status, days = task[:7]
            else:
                task_id, user_id, target_id, amount, task_type_db, status = task[:6]

            print(f"📌 Задание ID: {task_id}, User: {user_id}, Target: {target_id}, Amount: {amount}")

            # Общая валидация
            if not all([task_id, user_id, target_id, amount]):
                print("❌ Не хватает обязательных данных для задания.")
                return False

            # Проверки по типу
            if task_type == 'channel':
                print("➡ Проверка задания на канал...")
                return await RedisTasksManager._check_channel_task(bot, target_id)
            elif task_type == 'chat':
                print("➡ Проверка задания на чат...")
                return await RedisTasksManager._check_chat_task(bot, target_id)
            elif task_type == 'boost':
                print("➡ Проверка задания на буст...")
                return await RedisTasksManager._check_boost_task(bot, target_id)
            elif task_type in ['post', 'reaction']:
                print("➡ Проверка задания на пост/реакцию...")
                return await RedisTasksManager._check_post_reaction_task(bot, target_id)
            elif task_type in ['comment', 'link']:
                print("✅ Минимальная проверка: задание считается валидным.")
                return True

            print("✅ Тип задания не требует дополнительной проверки.")
            return True

        except Exception as e:
            print(f"❌ Ошибка при проверке задания: {e}")
            return False


    @staticmethod
    async def _check_channel_task(bot: Bot, target_id: int) -> bool:
        try:
            chat = await bot.get_chat(target_id)
            print(f"✅ Канал найден: {chat.title} ({chat.id})")

            bot_member = await bot.get_chat_member(chat.id, (await bot.get_me()).id)
            print(f"ℹ️ Статус бота в канале: {bot_member.status}")

            if bot_member.status == "administrator" and bot_member.can_invite_users:
                print("✅ Бот админ и может приглашать.")
                return True
            else:
                print("❌ Бот не админ или не может приглашать.")
                return False
        except Exception as e:
            print(f"❌ Ошибка при проверке канала: {e}")
            return False


    @staticmethod
    async def _check_chat_task(bot: Bot, target_id: int) -> bool:
        return True
        # try:
        #     chat = await bot.get_chat(target_id)
        #     print(f"✅ Чат найден: {chat.title} ({chat.id})")

        #     try:
        #         member = await bot.get_chat_member(target_id, (await bot.get_me()).id)
        #         print(f"✅ Бот является участником чата (статус: {member.status})")
        #         return True
        #     except Exception:
        #         print("❌ Бот не является участником чата.")
        #         return False

        # except Exception as e:
        #     print(f"❌ Ошибка при проверке чата: {e}")
        #     return False


    @staticmethod
    async def _check_boost_task(bot: Bot, target_id: int) -> bool:
        return True
        # try:
        #     chat = await bot.get_chat(target_id)
        #     print(f"✅ Чат/канал для буста найден: {chat.title} ({chat.id})")

        #     bot_member = await bot.get_chat_member(chat.id, (await bot.get_me()).id)
        #     print(f"ℹ️ Статус бота: {bot_member.status}, может постить: {bot_member.can_post_messages}")

        #     if bot_member.status == "administrator" and bot_member.can_post_messages:
        #         print("✅ Бот админ и может публиковать сообщения.")
        #         return True
        #     else:
        #         print("❌ Бот не админ или не может публиковать сообщения.")
        #         return False
        # except Exception as e:
        #     print(f"❌ Ошибка при проверке чата для буста: {e}")
        #     return False

    @staticmethod
    async def _check_post_reaction_task(bot: Bot, target_id: str) -> bool:
        try:
            if ':' not in target_id:
                print("❌ Некорректный формат target_id, ожидалось 'username:message_id'")
                return False

            chat_part, message_id_str = target_id.split(':')
            message_id = int(message_id_str)

            # Приводим chat_part к правильному виду
            try:
                # Если это число — это ID
                chat_id = int(chat_part)
            except ValueError:
                # Иначе это username, добавим @ если нужно
                chat_id = f"@{chat_part}" if not chat_part.startswith("@") else chat_part

            print(f"📨 Пробуем переслать сообщение из {chat_id}, ID: {message_id}")

            try:
                await bot.forward_message(INFO_ID, chat_id, message_id)
                print("✅ Сообщение успешно переслано, доступно.")
                return True
            except Exception as e:
                print(f"❌ Не удалось переслать сообщение: {e}")
                return False

        except Exception as e:
            print(f"❌ Ошибка при проверке поста/реакции: {e}")
            return False


    @staticmethod
    async def print_cache_status():
        """Вывод подробного статуса кэша"""
        print("\nТекущий статус кэша:")
        for task_type in ['channel', 'chat', 'post', 'comment', 'link', 'reaction', 'boost']:
            cached_tasks = await RedisTasksManager.get_cached_tasks(task_type) or []
            print(f"{task_type.upper()}: {len(cached_tasks)} заданий")
            
            # Выводим примеры заданий для диагностики
            for i, task in enumerate(cached_tasks[:3]):
                print(f"  Задание {i+1}: ID={task.get('id')}, target={task.get('target_id')}, amount={task.get('amount')}")
        
        common_counts = task_cache.get('common_tasks_count', {}).get('data', {})
        print("\nОбщее количество заданий по типам:")
        for task_type, count in common_counts.items():
            print(f"{task_type}: {count}")

    @staticmethod
    async def check_all_tasks(bot: Bot):
        """Проверка всех типов заданий с выводом статуса"""
        task_types = ['channel', 'chat', 'post', 'comment', 'link', 'reaction', 'boost']
        
        for task_type in task_types:
            await RedisTasksManager.check_tasks_of_type(bot, task_type)
        
        await RedisTasksManager.update_common_tasks_count(bot)
        await RedisTasksManager.print_cache_status()  # Добавьте эту строку
            
    @staticmethod
    async def prepare_task_data(bot: Bot, task_type: str, task: tuple) -> Optional[Dict[str, Any]]:
        """Подготовка данных задания для кэша"""
        try:
            if task_type == 'boost':
                task_id, user_id, target_id, amount, task_type_db, status, days = task[:7]
            else:
                task_id, user_id, target_id, amount, task_type_db, status = task[:6]

            task_data = {
                'id': task_id,
                'user_id': user_id,
                'target_id': target_id,
                'amount': amount,
                'type': task_type_db,
                'status': status,
                'is_active': True
            }

            if task_type in ['channel', 'chat', 'boost']:
                try:
                    # Преобразуем target_id, если это username без @
                    if isinstance(target_id, str) and not target_id.startswith("@"):
                        target_id = f"@{target_id}"

                    print(f"➡ Получаем чат target_id={target_id}")
                    chat = await bot.get_chat(target_id)

                    task_data.update({
                        'title': chat.title,
                        'username': getattr(chat, 'username', None),
                        'invite_link': getattr(chat, 'invite_link', None)
                    })

                    if task_type == 'boost':
                        task_data['days'] = days

                except Exception as e:
                    print(f"❌ Ошибка получения чата target_id={target_id}: {e}")
                    return None

            elif task_type == 'reaction':
                reaction_type = task[6] if len(task) > 6 else None
                task_data['reaction_type'] = reaction_type

            return task_data

        except Exception as e:
            print(f"❌ Ошибка подготовки данных задания: {e}")
            return None


    @staticmethod
    async def handle_invalid_task(task_type: str, task: tuple, bot: Bot):
        """Обработка невалидного задания: удаление, возврат средств, уведомление"""
        try:
            task_id = task[0]
            user_id = task[1]
            amount = task[3]

            print(f"⚠️ Удаление невалидного задания #{task_id} (тип: {task_type})")

            # Удаляем задание из БД
            await DB.delete_task(task_id)
            print(f"🗑 Задание #{task_id} удалено из базы")

            # Возврат средств
            refund_amount = amount * all_price.get(task_type, 0)
            if refund_amount > 0:
                await DB.add_balance(user_id, refund_amount)
                await DB.add_transaction(
                    user_id=user_id,
                    amount=refund_amount,
                    description=f"Возврат за невалидное задание #{task_id}",
                    additional_info=None
                )
                print(f"💰 Возвращено {refund_amount} MITcoin пользователю {user_id}")

                # Уведомление пользователя
                try:
                    await bot.send_message(
                        user_id,
                        f"⚠️ Ваше задание #{task_id} (тип: {task_type}) было удалено из-за несоответствия требованиям.\n"
                        f"💸 Средства в размере {refund_amount} MITcoin возвращены на ваш баланс."
                    )
                    print(f"📩 Пользователь {user_id} уведомлён")
                except Exception as e:
                    print(f"❌ Не удалось отправить уведомление пользователю {user_id}: {e}")

        except Exception as e:
            print(f"❌ Ошибка обработки невалидного задания {task_id}: {e}")


    @staticmethod
    async def get_cached_tasks(task_type: str) -> Optional[List[Dict[str, Any]]]:
        """Получить задания из кэша по типу"""
        try:
            # Проверяем наличие данных в кэше и их актуальность
            if task_type in task_cache['tasks']:
                cached_data = task_cache['tasks'][task_type]
                if 'expiry' in cached_data and cached_data['expiry'] < asyncio.get_event_loop().time():
                    del task_cache['tasks'][task_type]  # Удаляем просроченные данные
                    return None
                return cached_data.get('data', None)
            return None
        except Exception as e:
            print(f"Get cached tasks error: {e}")
            return None

    @staticmethod
    async def cache_tasks(task_type: str, tasks: List[Dict[str, Any]], ttl: int = 1800) -> bool:
        """Сохранить задания в кэш"""
        try:
            expiry_time = asyncio.get_event_loop().time() + ttl if ttl > 0 else None
            task_cache['tasks'][task_type] = {
                'data': tasks,
                'expiry': expiry_time
            }
            return True
        except Exception as e:
            print(f"Cache tasks error: {e}")
            return False

    @staticmethod
    async def invalidate_cache(task_type: str) -> None:
        """Удалить задания из кэша"""
        try:
            if task_type in task_cache['tasks']:
                del task_cache['tasks'][task_type]
        except Exception as e:
            print(f"Invalidate cache error: {e}")

    @staticmethod
    async def add_new_task_to_cache(task_type: str, task_data: Dict[str, Any]) -> bool:
        """Добавить новое задание в кэш"""
        try:
            current_tasks = await RedisTasksManager.get_cached_tasks(task_type) or []
            current_tasks.append(task_data)
            return await RedisTasksManager.cache_tasks(task_type, current_tasks)
        except Exception as e:
            print(f"Error adding new task to cache: {e}")
            return False

    async def refresh_task_cache(bot: Bot, task_type: str) -> bool:
        """Обновить кэш заданий с проверкой доступности (без очистки старого кэша)"""
        try:
            task_mapping = {
                'channel': DB.select_chanel_tasks,
                'chat': DB.select_chat_tasks,
                'post': DB.select_post_tasks,
                'comment': DB.select_like_comment,
                'link': DB.select_link_tasks,
                'reaction': DB.select_reaction_tasks,
                'boost': DB.select_boost_tasks
            }

            if task_type not in task_mapping:
                print(f"Unknown task type: {task_type}")
                return False

            # Получаем текущий кэш (если есть)
            old_cache = await RedisTasksManager.get_cached_tasks(task_type) or []
            
            # Получаем новые задания из БД
            db_tasks = await task_mapping[task_type]()
            if not db_tasks:
                # Если нет заданий в БД, только тогда очищаем кэш
                await RedisTasksManager.invalidate_cache(task_type)
                return True

            valid_tasks = []
            for task in db_tasks:
                try:
                    if await RedisTasksManager.is_task_valid(bot, task_type, task):
                        task_data = await RedisTasksManager.prepare_task_data(bot, task_type, task)
                        if task_data:
                            valid_tasks.append(task_data)
                except Exception as e:
                    print(f"Error processing task {task[0]}: {e}")
                    continue

            if valid_tasks:
                # Создаем временный кэш с новыми данными
                temp_cache = {
                    'data': valid_tasks,
                    'expiry': asyncio.get_event_loop().time() + 1800
                }
                
                # Атомарно обновляем кэш
                task_cache['tasks'][task_type] = temp_cache
                return True
            
            # Если не найдено валидных заданий, но есть старый кэш - оставляем старый
            if old_cache:
                return True
                
            # Если нет ни новых, ни старых заданий - очищаем кэш
            await RedisTasksManager.invalidate_cache(task_type)
            return False

        except Exception as e:
            print(f"Critical error in refresh_task_cache: {e}")
            return False

    @staticmethod
    async def check_tasks_of_type(bot: Bot, task_type: str):
        """Проверка заданий конкретного типа с сохранением старого кэша"""
        try:
            # Получаем текущий кэш (если есть)
            old_cache = await RedisTasksManager.get_cached_tasks(task_type) or []
            
            # Получаем задания из БД
            task_mapping = {
                'channel': DB.select_chanel_tasks,
                'chat': DB.select_chat_tasks,
                'post': DB.select_post_tasks,
                'comment': DB.select_like_comment,
                'link': DB.select_link_tasks,
                'reaction': DB.select_reaction_tasks,
                'boost': DB.select_boost_tasks
            }
            
            db_tasks = await task_mapping[task_type]()
            if not db_tasks:
                # Если нет заданий в БД, только тогда очищаем кэш
                await RedisTasksManager.invalidate_cache(task_type)
                return

            valid_tasks = []
            invalid_tasks = []

            for task in db_tasks:
                try:
                    if await RedisTasksManager.is_task_valid(bot, task_type, task):
                        task_data = await RedisTasksManager.prepare_task_data(bot, task_type, task)
                        if task_data:
                            valid_tasks.append(task_data)
                    else:
                        invalid_tasks.append(task)
                except Exception as e:
                    print(f"Ошибка проверки задания {task[0]}: {e}")
                    invalid_tasks.append(task)

            # Обрабатываем невалидные задания
            for task in invalid_tasks:
                await RedisTasksManager.handle_invalid_task(task_type, task, bot)

            if valid_tasks:
                # Создаем временный кэш с новыми данными
                temp_cache = {
                    'data': valid_tasks,
                    'expiry': asyncio.get_event_loop().time() + 1800
                }
                
                # Атомарно обновляем кэш
                task_cache['tasks'][task_type] = temp_cache
            elif not old_cache:
                # Если нет ни новых, ни старых заданий - очищаем кэш
                await RedisTasksManager.invalidate_cache(task_type)

        except Exception as e:
            print(f"Ошибка проверки заданий типа {task_type}: {e}")

    @staticmethod
    async def update_common_tasks_count(bot: Bot) -> bool:
        """Обновить общий счетчик заданий"""
        try:
            task_types = ['channel', 'chat', 'post', 'comment', 'link', 'reaction', 'boost']
            counts = {}
            
            for task_type in task_types:
                cached_tasks = await RedisTasksManager.get_cached_tasks(task_type)
                if cached_tasks is None:
                    await RedisTasksManager.refresh_task_cache(bot, task_type)
                    cached_tasks = await RedisTasksManager.get_cached_tasks(task_type) or []
                
                counts[task_type] = len(cached_tasks)
            
            total = sum(counts.values())
            counts['total'] = total
            
            # Сохраняем в кэш
            task_cache['common_tasks_count'] = {
                'data': counts,
                'expiry': asyncio.get_event_loop().time() + 1800  # TTL 5 минут
            }
            return True
        except Exception as e:
            print(f"Error updating common tasks count: {e}")
            return False

async def set_cached_data(key: str, value: Any, ttl: int = 1800) -> bool:
    """Сохранить данные в кэш"""
    try:
        expiry_time = asyncio.get_event_loop().time() + ttl if ttl > 0 else None
        if key not in task_cache:
            task_cache[key] = {}
        task_cache[key] = {
            'data': value,
            'expiry': expiry_time
        }
        return True
    except Exception as e:
        print(f"Set cached data error: {e}")
        return False