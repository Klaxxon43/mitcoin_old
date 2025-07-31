from utils.Imports import *
from .client import *
from .states import *

async def parse_entity_reference(bot: Bot, reference: str, task_type: str):
    """
    Парсит ссылку/идентификатор для разных типов заданий
    Возвращает информацию о сущности в унифицированном формате
    """
    try:
        if task_type in ["comment", "reaction"] and ":" in reference:
            channel_ref, post_id = reference.split(":", 1)
            
            # Пробуем разные варианты парсинга channel_ref
            try:
                # Вариант 1: это числовой ID канала
                if channel_ref.lstrip('-').isdigit():
                    chat = await bot.get_chat(int(channel_ref))
                # Вариант 2: это @username
                elif channel_ref.startswith('@'):
                    chat = await bot.get_chat(channel_ref)
                # Вариант 3: это t.me/username или https://t.me/username
                elif 't.me/' in channel_ref:
                    username = channel_ref.split('t.me/')[-1].split('/')[0]
                    chat = await bot.get_chat(f"@{username}")
                # Вариант 4: это просто имя канала без @
                else:
                    # Сначала пробуем как username без @
                    try:
                        chat = await bot.get_chat(f"@{channel_ref}")
                    except:
                        # Если не получилось, пробуем как числовой ID
                        if channel_ref.lstrip('-').isdigit():
                            chat = await bot.get_chat(int(channel_ref))
                        else:
                            raise ValueError("Не удалось определить формат ссылки на канал")
                
                return {
                    "id": chat.id,
                    "post_id": post_id,
                    "title": chat.title,
                    "username": f"@{chat.username}" if chat.username else None,
                    "invite_link": chat.invite_link,
                    "type": chat.type,
                    "raw_reference": reference
                }
            except Exception as e:
                return {
                    "error": f"Не удалось получить информацию о канале: {e}",
                    "raw_reference": reference,
                    "channel_part": channel_ref,
                    "post_id": post_id
                }
        
        # Для обычных каналов/чатов
        elif task_type in ["channel", "chat", "boost"]:
            try:
                chat = await bot.get_chat(reference)
                return {
                    "id": chat.id,
                    "title": chat.title,
                    "username": f"@{chat.username}" if chat.username else None,
                    "invite_link": chat.invite_link,
                    "type": chat.type
                }
            except Exception as e:
                return {
                    "error": f"Не удалось получить информацию: {e}",
                    "raw_reference": reference
                }
        
        # Для ссылок на ботов
        elif task_type == "link":
            try:
                user = await bot.get_chat(reference)
                if user.type != "private":
                    return {
                        "error": "Указанная сущность не является ботом",
                        "raw_reference": reference
                    }
                return {
                    "id": user.id,
                    "username": f"@{user.username}" if user.username else None,
                    "first_name": user.first_name,
                    "is_bot": True
                }
            except Exception as e:
                return {
                    "error": f"Не удалось получить информацию о боте: {e}",
                    "raw_reference": reference
                }
        
        # Для всех остальных случаев
        else:
            return {
                "raw_reference": reference,
                "error": "Неизвестный тип задания для парсинга"
            }
    
    except Exception as e:
        return {
            "error": f"Ошибка при обработке ссылки: {e}",
            "raw_reference": reference
        }

async def format_entity_info(entity_info: dict, task_type: str) -> str:
    """Форматирует информацию о сущности для сообщения"""
    lines = []
    
    if "error" in entity_info:
        lines.append(f"⚠️ Ошибка: {entity_info['error']}")
        if "channel_part" in entity_info:
            lines.append(f"Часть канала: {entity_info['channel_part']}")
        if "post_id" in entity_info:
            lines.append(f"ID поста: {entity_info['post_id']}")
        lines.append(f"Исходная ссылка: {entity_info.get('raw_reference', '—')}")
        return "\n".join(lines)
    
    if task_type in ["channel", "chat", "boost"]:
        lines.append(f"📌 Название: {entity_info.get('title', '—')}")
        lines.append(f"🆔 ID: {entity_info.get('id', '—')}")
        lines.append(f"👤 Username: {entity_info.get('username', '—')}")
        lines.append(f"🔗 Ссылка: {entity_info.get('invite_link', '—')}")
        lines.append(f"📝 Тип: {entity_info.get('type', '—')}")
    
    elif task_type in ["comment", "reaction"]:
        lines.append(f"📌 Канал: {entity_info.get('title', '—')}")
        lines.append(f"🆔 ID канала: {entity_info.get('id', '—')}")
        lines.append(f"📝 ID поста: {entity_info.get('post_id', '—')}")
        lines.append(f"👤 Username: {entity_info.get('username', '—')}")
        
        # Добавляем полную ссылку на пост, если есть username
        if entity_info.get('username'):
            username = entity_info['username'].lstrip('@')
            post_id = entity_info.get('post_id', '')
            lines.append(f"🔗 Ссылка на пост: https://t.me/{username}/{post_id}")
        elif entity_info.get('id') and entity_info.get('post_id'):
            # Для каналов без username используем ID (работает в некоторых клиентах)
            lines.append(f"🔗 Ссылка (по ID): https://t.me/c/{str(abs(entity_info['id']))}/{entity_info['post_id']}")
    
    elif task_type == "link":
        lines.append(f"🤖 Бот: {entity_info.get('first_name', '—')}")
        lines.append(f"🆔 ID: {entity_info.get('id', '—')}")
        lines.append(f"👤 Username: {entity_info.get('username', '—')}")
        if entity_info.get('username'):
            lines.append(f"🔗 Ссылка: https://t.me/{entity_info['username'].lstrip('@')}")
    
    return "\n".join(lines)

async def get_work_function_by_type(task_type: str):
    """Возвращает функцию для работы с заданиями по типу"""
    return {
        "channel": 'work_channels',
        "chat": 'work_chats',
        "reaction": 'work_reactions',
        "link": 'work_links',
        "boost": 'work_boosts',
        "comment": 'work_comments'

    }.get(task_type, None)
# ============ Репорты ============

@router.callback_query(F.data.startswith("report_"))
async def handle_report(callback: types.CallbackQuery, bot: Bot, state: FSMContext):
    parts = callback.data.split("_")

    if len(parts) == 3:
        # Первичная обработка — отображение причин
        task_type, task_id = parts[1], int(parts[2])

        buttons_by_type = {
            "channel": [
                ("Такого канала не существует", "channel|not|exist"),
                ("Канал приватный", "channel|private")
            ],
            "chat": [
                ("Такого чата не существует", "chat|not|exist"),
                ("Чат приватный", "chat|private")
            ],
            "reaction": [
                ("Такого канала не существует", "channel|not|exist"),
                ("Такого поста не существует", "post|not|exist"),
                ("Реакция недоступна", "reaction|unavailable"),
                ("Канал приватный", "channel|private")
            ],
            "link": [
                ("Бот не найден", "bot|not|found"),
                ("Бот не работает", "bot|not|working")
            ],
            "boost": [
                ("Канал не найден", "channel|not|found"),
                ("Канал приватный", "channel|private")
            ],
            "comment": [
                ("Такого канала не существует", "channel|not|exist"),
                ("Такого поста не существует", "post|not|exist"),
                ("Канал приватный", "channel|private")
            ]
        }

        builder = InlineKeyboardBuilder()
        for text, code in buttons_by_type.get(task_type, []):
            builder.add(InlineKeyboardButton(
                text=text,
                callback_data=f"report_{task_type}_{task_id}_reason_{code}"
            ))

        builder.add(InlineKeyboardButton(
            text="Другая причина",
            callback_data=f"report_{task_type}_{task_id}_other"
        ))
        builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data=f"chaneltask_{task_id}"))
        builder.adjust(1)

        await callback.message.edit_text("⚠️ Выберите причину репорта:", reply_markup=builder.as_markup())

    elif len(parts) == 5 and parts[3] == "reason":
        try:
            # Обработка выбранной причины
            task_type, task_id, reason_code = parts[1], int(parts[2]), parts[4]
            user_id = callback.from_user.id
            task = await DB.get_task_by_id(task_id)
            if not task:
                await callback.answer("Задание не найдено", show_alert=True)
                return

            # Получаем информацию о сущности
            entity_info = await parse_entity_reference(bot, task[2], task_type)
            entity_text = await format_entity_info(entity_info, task_type)

            reasons = {
                'channel|not|exist': "Такого канала не существует",
                'chat|not|exist': "Такого чата не существует",
                'post|not|exist': "Такого поста не существует",
                'reaction|unavailable': "Реакция недоступна",
                'bot|not|found': "Бот не найден",
                'channel|not|found': "Канал не найден",
                'channel|private': "Канал приватный",
                'chat|private': "Чат приватный",
                'bot|not|working': "Бот не работает"
            }
            reason_text = reasons.get(reason_code, "Неизвестная причина")

            bonus = 1
            builder = InlineKeyboardBuilder()
            builder.add(
                InlineKeyboardButton(
                    text="✅ Принять и удалить",
                    callback_data=f"accept_report_{task_id}_{user_id}_{reason_code}_{bonus}"
                ))
            builder.add(
                InlineKeyboardButton(
                    text="❌ Отклонить",
                    callback_data=f"reject_report_{user_id}"
                )
            )
            builder.adjust(1)

            msg = (
                f"⚠️ <b>Новый репорт на задание</b>\n\n"
                f"<b>Тип задания:</b> {task_type}\n"
                f"<b>Причина:</b> {reason_text}\n"
                f"<b>ID задания:</b> {task_id}\n\n"
                f"<b>Информация о сущности:</b>\n{entity_text}\n\n"
                f"<b>От пользователя:</b> @{callback.from_user.username or '—'} (ID: {user_id})"
            )
            
            for admin in ADMINS_ID:
                try:
                    await bot.send_message(admin, msg, reply_markup=builder.as_markup())
                except Exception as e:
                    logger.info(f"❌ Не удалось отправить сообщение админу {admin}: {e}")

            await callback.message.delete()

            await DB.skip_task(user_id, task_id)
            all_tasks = task_cache.get('all_tasks', [])
            tasks = await get_available_tasks(user_id, all_tasks)

            # Создаем клавиатуру для перенаправления
            builder = InlineKeyboardBuilder()
            
            # Кнопка на задания того же типа
            work_func = await get_work_function_by_type(task_type)
            if work_func:
                builder.add(InlineKeyboardButton(
                    text=f"➡️ Продолжить",
                    callback_data=f"work_{task_type}"
                ))
            
            # Кнопка на общее меню заданий
            builder.add(InlineKeyboardButton(
                text="📋 Все типы заданий",
                callback_data="work_menu"
            ))
            
            builder.adjust(1)
            
            await callback.message.answer(
                "✅ Репорт успешно отправлен на проверку!\n"
                "Вы можете продолжить выполнение других заданий:",
                reply_markup=builder.as_markup()
            )
            
        except Exception as e:
            logger.info(f"Ошибка при обработке репорта: {e}")
            await callback.answer("Произошла ошибка при обработке репорта", show_alert=True)
            
    elif len(parts) == 4 and parts[3] == "other":
        await state.set_state(ReportStates.waiting_description)
        await state.update_data(task_id=int(parts[2]), task_type=parts[1])
        await callback.message.edit_text("Пожалуйста, опишите проблему:")


@router.message(ReportStates.waiting_description)
async def report_other_description(message: types.Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    task_id = data.get("task_id")
    task_type = data.get("task_type")
    user_id = message.from_user.id
    description = message.text

    task = await DB.get_task_by_id(task_id)
    if not task:
        await message.answer("Задание не найдено")
        await state.clear()
        return

    # Получаем информацию о сущности
    entity_info = await parse_entity_reference(bot, task[2], task_type)
    entity_text = await format_entity_info(entity_info, task_type)

    bonus = 0
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="✅ Принять и удалить",
            callback_data=f"accept_report_{task_id}_{user_id}_custom_{bonus}"
        ),
        InlineKeyboardButton(
            text="❌ Отклонить",
            callback_data=f"reject_report_{user_id}"
        )
    )

    msg = (
        f"⚠️ <b>Новый репорт на задание</b>\n\n"
        f"<b>Тип задания:</b> {task_type}\n"
        f"<b>Причина:</b> {description}\n"
        f"<b>ID задания:</b> {task_id}\n\n"
        f"<b>Информация о сущности:</b>\n{entity_text}\n\n"
        f"<b>От пользователя:</b> @{message.from_user.username or '—'} (ID: {user_id})"
    )

    for admin in ADMINS_ID:
        try:
            await bot.send_message(admin, msg, reply_markup=builder.as_markup())
        except Exception as e:
            logger.info(f"❌ Не удалось отправить сообщение админу {admin}: {e}")    
    await message.answer("Репорт успешно отправлен. Спасибо!")
    await DB.skip_task(user_id, task_id)
    await state.clear()


@router.callback_query(F.data.startswith("accept_report_"))
async def accept_report_handler(callback: types.CallbackQuery, bot: Bot):
    parts = callback.data.split("_")
    task_id = int(parts[2])
    user_id = int(parts[3])
    reason_code = parts[4]
    bonus = int(parts[5])

    task = await DB.get_task_by_id(task_id)
    if not task:
        await callback.answer("Задание не найдено")
        return

    creator_id = task[1]
    await DB.delete_task(task_id)

    reason_text = {
        'channel|not|exist': "Такого канала не существует",
        'chat|not|exist': "Такого чата не существует",
        'post|not|exist': "Такого поста не существует",
        'reaction|unavailable': "Реакция недоступна",
        'bot|not|found': "Бот не найден",
        'channel|not|found': "Канал не найден",
        'channel|private': "Канал приватный",
        'chat|private': "Чат приватный",
        'bot|not|working': "Бот не работает",
        'custom': "Указанная пользователем причина"
    }.get(reason_code, "Неизвестная причина")

    try:
        if bonus == 1:
            await DB.add_balance(user_id, 1000)
            await bot.send_message(user_id, f"✅ Ваш репорт принят\nЗадание удалено\nНачислено +1000 на баланс.")
        else:
            await bot.send_message(user_id, "✅ Ваш репорт принят\nЗадание удалено.")

        await bot.send_message(creator_id, f"❌ Ваше задание (ID {task_id}) было удалено\nПричина: {reason_text}")
    except Exception as e:
        logger.info(f"Ошибка при отправке уведомлений: {e}")

    await callback.message.delete()
    await callback.answer("Репорт обработан")


@router.callback_query(F.data.startswith("reject_report_"))
async def reject_report_handler(callback: types.CallbackQuery, bot: Bot):
    user_id = int(callback.data.split("_")[2])
    try:
        await bot.send_message(user_id, "❌ Ваш репорт был отклонён\nСпасибо за участие.")
    except:
        pass
    await callback.message.delete()
    await callback.answer("Репорт отклонён")