# utils/redis_task_manager.py
import redis
import json
from datetime import timedelta
from typing import Optional, List, Dict, Any
import asyncio
import random

from utils.redis_utils import *
from utils.Imports import *

class RedisTasksManager:
    @staticmethod
    async def get_cached_tasks(task_type: str) -> Optional[List[Dict[str, Any]]]:
        """Получить задания из кэша Redis по типу"""
        try:
            cached_data = redis_client.get(f"tasks:{task_type}")
            if cached_data:
                return json.loads(cached_data)
            return None
        except Exception as e:
            print(f"Redis get_cached_tasks error: {e}")
            return None

    @staticmethod
    async def cache_tasks(task_type: str, tasks: List[Dict[str, Any]], ttl: int = 300) -> bool:
        """Сохранить задания в кэш Redis"""
        try:
            redis_client.setex(
                f"tasks:{task_type}",
                timedelta(seconds=ttl),
                json.dumps(tasks)
            )
            return True
        except Exception as e:
            print(f"Redis cache_tasks error: {e}")
            return False

    @staticmethod
    async def invalidate_cache(task_type: str) -> None:
        """Удалить задания из кэша Redis"""
        try:
            redis_client.delete(f"tasks:{task_type}")
        except Exception as e:
            print(f"Redis invalidate_cache error: {e}")

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


    @staticmethod
    async def refresh_task_cache(bot: Bot, task_type: str) -> bool:
        """Обновить кэш заданий с проверкой доступности"""
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

            db_tasks = await task_mapping[task_type]()
            if not db_tasks:
                await RedisTasksManager.invalidate_cache(task_type)
                return True

            valid_tasks = []
            for task in db_tasks:
                try:
                    if task_type == 'boost':
                        task_id, user_id, target_id, amount, task_type_db, status, days = task[:7]
                    else:
                        task_id, user_id, target_id, amount, task_type_db, status = task[:6]

                    # Проверка для channel, chat, boost
                    if task_type in ['channel', 'chat', 'boost']:
                        try:
                            chat = await bot.get_chat(target_id)
                            bot_member = await bot.get_chat_member(chat.id, (await bot.get_me()).id)
                            
                            if task_type == 'boost':
                                if not (bot_member.status == "administrator" and bot_member.can_post_messages):
                                    continue
                            elif not (bot_member.status == "administrator" and bot_member.can_invite_users):
                                continue
                                
                            task_data = {
                                'id': task_id,
                                'user_id': user_id,
                                'target_id': target_id,
                                'amount': amount,
                                'type': task_type_db,
                                'status': status,
                                'title': chat.title,
                                'username': getattr(chat, 'username', None),
                                'invite_link': getattr(chat, 'invite_link', None),
                                'is_active': True
                            }
                            
                            if task_type == 'boost':
                                task_data['days'] = days
                                
                            valid_tasks.append(task_data)
                        except Exception as e:
                            print(f"Task {task_id} channel unavailable: {e}")
                            continue

                    # Проверка поста — пересылка в INFO_ID
                    elif task_type == 'post':
                        try:
                            chat_part, message_id_str = target_id.split(':')
                            message_id = int(message_id_str)
                            # Пробуем переслать сообщение в INFO_ID
                            await bot.forward_message(INFO_ID, chat_part, message_id)
                        except Exception as e:
                            print(f"Task {task_id} post forwarding failed: {e}")
                            continue  # Пропускаем если пересылка неудачна

                        task_data = {
                            'id': task_id,
                            'user_id': user_id,
                            'target_id': target_id,
                            'amount': amount,
                            'type': task_type_db,
                            'status': status,
                            'is_active': True
                        }
                        valid_tasks.append(task_data)

                    # Проверка реакции — тоже пересылка поста в INFO_ID + добавляем reaction_type
                    elif task_type == 'reaction':
                        reaction_type = task[6] if len(task) > 6 else None

                        try:
                            chat_part, message_id_str = target_id.split(':')
                            message_id = int(message_id_str)
                            await bot.forward_message(INFO_ID, chat_part, message_id)
                        except Exception as e:
                            print(f"Task {task_id} reaction post forwarding failed: {e}")
                            continue  # Пропускаем если пересылка неудачна

                        task_data = {
                            'id': task_id,
                            'user_id': user_id,
                            'target_id': target_id,
                            'amount': amount,
                            'type': task_type_db,
                            'status': status,
                            'reaction_type': reaction_type,
                            'is_active': True
                        }
                        valid_tasks.append(task_data)

                    else:
                        # Остальные типы без проверки поста
                        task_data = {
                            'id': task_id,
                            'user_id': user_id,
                            'target_id': target_id,
                            'amount': amount,
                            'type': task_type_db,
                            'status': status,
                            'is_active': True
                        }
                        valid_tasks.append(task_data)

                except Exception as e:
                    print(f"Error processing task {task[0]}: {e}")
                    continue

            if valid_tasks:
                return await RedisTasksManager.cache_tasks(task_type, valid_tasks)
            
            await RedisTasksManager.invalidate_cache(task_type)
            return False

        except Exception as e:
            print(f"Critical error in refresh_task_cache: {e}")
            return False



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
            
            await set_cached_data("common_tasks_count", counts, ttl=300)
            return True
        except Exception as e:
            print(f"Error updating common tasks count: {e}")
            return False 