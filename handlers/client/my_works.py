from untils.Imports import *
from .client import *
from .states import *

@router.callback_query(F.data == 'my_works')
async def taskss_handler(callback: types.CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    tasks = await DB.get_tasks_by_user(user_id)  # Получаем задачи пользователя
    print(tasks)  # Проверяем данные

    # Начинаем с первой страницы
    page = 1
    tasks_on_page, total_pages = paginate_tasks(tasks, page)

    # Генерируем инлайн кнопки
    keyboard = await generate_tasks_keyboard2(tasks_on_page, page, total_pages, bot)

    await callback.message.edit_text("💼 <b>Ваши задания:</b>", reply_markup=keyboard)


@router.callback_query(lambda c: c.data.startswith("page_"))
async def change_page_handler(callback: types.CallbackQuery, bot: Bot):
    # Получаем номер страницы из callback_data
    page = int(callback.data.split('_')[1])
    
    # Получаем ID пользователя
    user_id = callback.from_user.id
    
    # Получаем задачи пользователя
    tasks = await DB.get_tasks_by_user(user_id)
    
    # Получаем задания на нужной странице
    tasks_on_page, total_pages = paginate_tasks(tasks, page)

    # Генерируем инлайн кнопки
    keyboard = await generate_tasks_keyboard2(tasks_on_page, page, total_pages, bot)

    # Обновляем сообщение с новыми кнопками
    await callback.message.edit_text("💼 <b>Ваши задания:</b>", reply_markup=keyboard)


async def check_admin_and_get_invite_link(bot, target_id):
    try:
        # Проверяем, является ли target_id числом (ID чата) или строкой (юзернейм)
        try:
            chat_id = int(target_id)
            is_id = True
        except ValueError:
            chat_id = target_id
            is_id = False

        chat_administrators = await bot.get_chat_administrators(chat_id)
        # Проверяем, является ли бот администратором
        for admin in chat_administrators:
            if admin.user.id == bot.id:
                # Если бот админ, генерируем ссылку-приглашение
                try:
                    chat = await bot.get_chat(chat_id)
                    invite_link = chat.invite_link
                    return invite_link
                except Exception as e:
                    print(f'Ошибка получения инвайта для {chat_id}, ошибка - {e}')
                    return "😑 Предоставьте боту права администратора, иначе задание выполняться не будет"
        return "😑 Предоставьте боту права администратора, иначе задание выполняться не будет"
    except Exception as e:
        print(f'Ошибка при проверке прав администратора: {e}')
        return "😑 Предоставьте боту права администратора, иначе задание выполняться не будет"


@router.callback_query(lambda c: c.data.startswith("task_"))
async def task_detail_handler(callback: types.CallbackQuery, bot: Bot):
    await callback.answer()
    task_id = int(callback.data.split('_')[1])
    task = await DB.get_task_by_id(task_id)

    # Определяем тип задачи 
    task_type = TASK_TYPES.get(task[4], 'Неизвестно')
    amount = task[3]  # Количество оставшихся выполнений
    max_amount = task[5]  # Количество при создании задания
    time = task[7]  # Дата создания задания

    # Для буста (тип 6) показываем специальную информацию
    if task[4] == 6:  # Буст
        days = task[6] or 1  # Количество дней буста
        daily_price = all_price['boost']
        total_days_paid = await Boost.get_paid_days_for_boost(task_id)
        
        task_info = f"""
<b>{task_type}</b>

👥 <b>Количество:</b> <em>{max_amount} шт.</em>
☑️ Выполнено: <em>{max_amount-amount} шт.</em>
🔋 Осталось: <em>{amount} шт.</em>

📅 <b>Срок буста:</b> <em>{days} дней</em>
💰 <b>Стоимость за день:</b> <em>{daily_price} MITcoin за буст</em>
📅 <b>Дата создания:</b> <em>{time if time else "Не указана"}</em>
"""
        try:
            chat = await bot.get_chat(task[2])
            chat_title = chat.title
            task_info += f"""
📢 <b>Канал:</b> <em>{chat_title}</em>
"""
        except:
            task_info += f"""
📢 <b>Канал:</b> <em>{task[2]}</em>
"""
    else:
        price_per_unit = {1: 1500, 2: 1500, 3: 300, 4: 750, 5: 1000, 6: 5000, 7: 250}
        cost = amount * price_per_unit.get(task[4], 0)
        
        task_info = f"""
<b>{task_type}</b>

🧮 <b>Количество при создании:</b> <em>{max_amount}</em>
🧮 <b>Оставшихся выполнений:</b> <em>{amount}</em>
💰 <b>Стоимость:</b> <em>{cost} MITcoin </em>
📅 <b>Дата создания:</b>  <em>{time if time else "Не указана"}</em>
"""

        # Дополнительная информация в зависимости от типа задания
        if task[4] in [1, 2]:  # Канал или чат
            target_id = task[2]
            invite_link = await check_admin_and_get_invite_link(bot, target_id)
            try:
                chat = await bot.get_chat(target_id)
                chat_title = chat.title
            except Exception as e:
                chat_title = "⚠️ Бот был удален с канала или не является администратором ⚠️"
            task_info += f"""
📢 <b>Канал/чат:</b> <em>{chat_title}</em>
🔗 <b>Ссылка:</b> {invite_link}
"""
        elif task[4] == 3:  # Пост
            target_id = task[2]
            if ":" in target_id:
                chat_id, message_id = map(int, target_id.split(":"))
                try:
                    chat = await bot.get_chat(chat_id)
                    chat_title = chat.title
                except Exception as e:
                    chat_title = "Неизвестный канал"
                task_info += f"""
📢 <b>Канал:</b> <em>{chat_title}</em>
🔗 <b>Ссылка на пост:</b> https://t.me/{chat_id}/{message_id}
"""
        elif task[4] == 4:  # Комментарии
            target_id = task[2]
            if ":" in target_id:
                chat_id, message_id = map(int, target_id.split(":"))
                try:
                    chat = await bot.get_chat(chat_id)
                    chat_title = chat.title
                except Exception as e:
                    chat_title = "Неизвестный канал"
                task_info += f"""
📢 <b>Канал:</b> <em>{chat_title}</em>
🔗 <b>Ссылка на пост:</b> https://t.me/{chat_id}/{message_id}
"""
        elif task[4] == 5:  # Бот
            target_id = task[2]
            if target_id.startswith("https://t.me/"):
                username = target_id.split("/")[-1].split("?")[0]
            elif target_id.startswith("@"):
                username = target_id[1:]
            else:
                username = target_id
            task_info += f"""
🤖 <b>Бот:</b> <code>@{username}</code>
🔗 <b>Ссылка:</b> {target_id}
"""
        elif task[4] == 7:  # Реакция
            target_id = task[2]
            if ":" in target_id:
                channel_part, post_id = target_id.split(":")

                # Пытаемся определить, числовой ли это id, или username
                try:
                    channel_id = int(channel_part)
                except ValueError:
                    channel_id = None

                # Асинхронно получить chat и username
                channel_username = None
                if channel_id is not None:
                    try:
                        chat = await bot.get_chat(channel_id)
                        if chat.username:
                            channel_username = chat.username
                        else:
                            # Если username нет, показываем id
                            channel_username = str(channel_id)
                    except Exception:
                        # Если не удалось получить чат — показываем просто id
                        channel_username = str(channel_id)
                else:
                    # channel_part — это username, уберём @ если есть
                    username_candidate = channel_part.lstrip("@")
                    try:
                        chat = await bot.get_chat(f"@{username_candidate}")
                        if chat.username:
                            channel_username = chat.username
                        else:
                            # Нет username — выведем как есть
                            channel_username = username_candidate
                    except Exception:
                        channel_username = username_candidate

                specific_reaction = task[6] if task[6] else "Любая положительная"
                task_info += f"""
📢 <b>Канал:</b> <code>@{channel_username}</code>
🔗 <b>Ссылка на пост:</b> https://t.me/{channel_username}/{post_id}
🎯 <b>Реакция:</b> <em>{specific_reaction}</em>
        """

    # Кнопки управления заданием
    builder = InlineKeyboardBuilder()

    builder.row(
            InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"delete_{task_id}"),
            InlineKeyboardButton(text="✏️Изменить количество", callback_data=f"edit_{task_id}"),
        )
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="my_works"))
    
    await callback.message.edit_text(task_info, reply_markup=builder.as_markup())


@router.callback_query(lambda c: c.data.startswith("delete_"))
async def delete_task_handler(callback: types.CallbackQuery):
    task_id = int(callback.data.split('_')[1])
    task = await DB.get_task_by_id(task_id)
    amount = task[3] 
    if amount is None:
        amount = 1
    price_per_unit = {1: 1500, 2: 1500, 3: 300}
    cost = amount * price_per_unit.get(task[4], 0)
    user_id = callback.from_user.id
    user = await DB.select_user(user_id)
    balance = user['balance']
    new_balance = balance + cost

    # Удаляем задачу из базы данных
    await DB.delete_task(task_id)
    await DB.update_balance(user_id, balance=new_balance)
    await callback.message.edit_text("Задание удалено!")

    # После удаления возвращаем пользователя к его заданиям
    user_id = callback.from_user.id
    tasks = await DB.get_tasks_by_user(user_id)
    page = 1
    tasks_on_page, total_pages = paginate_tasks(tasks, page)
    keyboard = await generate_tasks_keyboard(tasks_on_page, page, total_pages)

    await callback.message.edit_text("💼 <b>Ваши задания:</b>", reply_markup=keyboard)



@router.callback_query(lambda c: c.data.startswith("edit_"))
async def edit_task_handler(callback: types.CallbackQuery, state: FSMContext):
    # Получаем ID задания из callback-запроса
    task_id = int(callback.data.split('_')[1])
    
    # Получаем задачу из базы данных
    task = await DB.get_task_by_id(task_id)
    if not task:
        await callback.message.edit_text("Задание не найдено!")
        return

    # Сохраняем ID задания в состоянии FSM
    await state.update_data(task_id=task_id)

    # Запрашиваем у пользователя новое количество выполнений
    await callback.message.edit_text("✏️ Введите новое количество выполнений для задания:")
    
    # Переводим бота в состояние ожидания ввода нового количества
    await state.set_state(EditTaskState.waiting_for_amount)

@router.message(EditTaskState.waiting_for_amount)
async def process_amount_input(message: types.Message, state: FSMContext, bot: Bot):
    try:
        new_amount = int(message.text)
        if new_amount <= 0:
            await message.answer("❌ Количество выполнений должно быть больше 0.")
            return

        # Получаем данные из состояния
        data = await state.get_data()
        task_id = data.get("task_id")
        
        # Получаем текущее задание
        task = await DB.get_task_by_id(task_id)
        if not task:
            await message.answer("❌ Задание не найдено!")
            await state.clear()
            return
            
        # Распаковываем данные задания
        user_id = message.from_user.id
        target_id = task[2]      # ID цели
        old_amount = task[3]     # Текущее количество оставшихся выполнений
        task_type = task[4]      # Тип задания
        max_amount = task[5]     # Изначальное количество
        days = task[6] if len(task) > 6 else 1  # Дни для буста
        
        # Проверяем, чтобы новое количество было не меньше уже выполненных
        completed = max_amount - old_amount
        if new_amount < completed:
            await message.answer(
                f"❌ Нельзя установить количество {new_amount}, так как уже выполнено {completed}!"
            )
            return

        # Рассчитываем разницу
        difference = new_amount - max_amount
        
        # Для бустов (тип 6) особый расчет
        if task_type == 6:
            daily_price = all_price['boost']
            cost_difference = difference * daily_price * days
        else:
            # Для обычных заданий
            price_per_unit = {
                1: 1500,  # Подписка на канал
                2: 1500,  # Подписка на чат
                3: 300,   # Реакция
                4: 750,   # Комментарий
                5: 1000,  # Бот
                7: 250    # Реакция
            }.get(task_type, 0)
            cost_difference = difference * price_per_unit

        # Получаем баланс пользователя
        user_data = await DB.select_user(user_id)
        balance = user_data['balance']
        
        # Проверяем достаточно ли средств при увеличении
        if difference > 0 and cost_difference > balance:
            await message.answer(
                f"❌ Недостаточно средств. Требуется: {cost_difference} MITcoin\n"
                f"Ваш баланс: {balance} MITcoin"
            )
            return

        # Обновляем баланс
        new_balance = balance - cost_difference
        await DB.update_balance(user_id, new_balance)

        # Обновляем задание в базе данных
        new_remaining = new_amount - completed
        await DB.update_task_amount(task_id, new_remaining)
        await DB.update_task_max_amount(task_id, new_amount)

        # Логируем транзакцию
        transaction_type = "Увеличение" if difference > 0 else "Уменьшение"
        description = {
            1: "подписок на канал",
            2: "подписок на чат", 
            3: "реакций",
            4: "комментариев",
            5: "ботов",
            6: "бустов",
            7: "реакций"
        }.get(task_type, "заданий")
        
        await DB.add_transaction(
            user_id=user_id,
            amount=abs(cost_difference),
            description=f"{transaction_type} {description}",
            additional_info=f"Задание ID: {task_id}. Было: {max_amount}, Стало: {new_amount}"
        )

        # Обновляем список заданий пользователя
        tasks = await DB.get_tasks_by_user(user_id)
        page = 1
        tasks_on_page, total_pages = paginate_tasks(tasks, page)
        keyboard = await generate_tasks_keyboard(tasks_on_page, page, total_pages)

        # Формируем сообщение о результате
        if task_type == 6:
            result_message = (
                f"✅ Количество бустов обновлено!\n"
                f"📅 Дней буста: {days}\n"
                f"🧮 Было: {max_amount} → Стало: {new_amount}\n"
                f"💰 Изменение баланса: {'-' if difference > 0 else '+'}{abs(cost_difference)} MITcoin\n"
                f"💵 Новый баланс: {new_balance} MITcoin"
            )
        else:
            result_message = (
                f"✅ Количество выполнений обновлено!\n"
                f"🧮 Было: {max_amount} → Стало: {new_amount}\n"
                f"💰 Изменение баланса: {'-' if difference > 0 else '+'}{abs(cost_difference)} MITcoin\n"
                f"💵 Новый баланс: {new_balance} MITcoin"
            )

        await message.answer(f"{result_message}\n\n💼 <b>Ваши задания:</b>", reply_markup=keyboard)
        
    except ValueError:
        await message.answer("❌ Пожалуйста, введите корректное число.")
    except Exception as e:
        print(f"Ошибка в process_amount_input: {e}")
        await message.answer("❌ Произошла ошибка при обновлении задания.")
    finally:
        await state.clear()





async def generate_tasks_keyboard(tasks, page, total_pages):
    builder = InlineKeyboardBuilder()

    # Выводим задания на текущей странице (по 5 на страницу)
    for task in tasks:
        task_type = TASK_TYPES.get(task[4], 'Неизвестно')
        amount = task[3]  
        button_text = f"{task_type} | {amount}"
        # Каждая кнопка в новой строке
        builder.row(InlineKeyboardButton(text=button_text, callback_data=f"task_{task[0]}"))

    # Кнопка "Назад"
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="profile"))

    # Кнопки пагинации
    pagination = []
    if page > 1:
        pagination.append(InlineKeyboardButton(text="⬅️", callback_data=f"page_{page - 1}"))
    pagination.append(InlineKeyboardButton(text=str(page), callback_data="current_page"))
    if page < total_pages:
        pagination.append(InlineKeyboardButton(text="➡️", callback_data=f"page_{page + 1}"))

    builder.row(*pagination)  # Кнопки пагинации в одну строку

    return builder.as_markup()




async def generate_tasks_keyboard2(tasks, page, total_pages, bot):
    builder = InlineKeyboardBuilder()  # Создаем builder один раз

    # Выводим задания на текущей странице (по 5 на страницу)
    for task in tasks:
        # Распаковываем данные задачи
        task_id, user_id, target_id, amount, task_type_id, max_amount, _, time = task  # Добавлено time

        # Получаем тип задачи
        task_type = TASK_TYPES.get(task_type_id, 'Неизвестно')

        # Обрабатываем target_id в зависимости от типа задачи
        if task_type_id == 5:  # Тип 5 - Бот
            if target_id.startswith("https://t.me/"):
                username = target_id.split("/")[-1].split("?")[0]
            elif target_id.startswith("@"):
                username = target_id[1:]
            else:
                username = target_id
            chat_name = f"@{username}"  # Указываем username бота
        else:
            try:
                # Если target_id содержит ":" (например, "klaxxon_off:2748" или "-1001952919981:2757")
                if ":" in str(target_id):
                    target_id = str(target_id).split(":")[0]  # Берем только часть до ":"

                # Если target_id начинается с "https://t.me/" или "@"
                if str(target_id).startswith("https://t.me/"):
                    target_id = str(target_id).replace("https://t.me/", "")
                elif str(target_id).startswith("@"):
                    target_id = str(target_id).replace("@", "")

                # Если target_id содержит нечисловые символы (например, "klaxxon_off")
                if not str(target_id).lstrip('-').isdigit():
                    target_id = "@" + str(target_id)  # Добавляем "@" для username

                # Получаем информацию о канале/чате
                chat = await bot.get_chat(target_id)
                chat_name = chat.title
            except Exception as e:
                print(f"Ошибка при получении информации о канале: {e}")
                chat_name = "Неизвестный"

        # Формируем текст кнопки
        button_text = f"{task_type} | {chat_name} | {amount}/{max_amount}"
        
        # Добавляем кнопку в builder
        builder.row(InlineKeyboardButton(text=button_text, callback_data=f"task_{task_id}"))

    # Кнопка "Назад"
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="profile"))

    # Кнопки пагинации
    pagination = []
    if page > 1:
        pagination.append(InlineKeyboardButton(text="⬅️", callback_data=f"page_{page - 1}"))
    pagination.append(InlineKeyboardButton(text=str(page), callback_data="current_page"))
    if page < total_pages:
        pagination.append(InlineKeyboardButton(text="➡️", callback_data=f"page_{page + 1}"))

    builder.row(*pagination)  # Кнопки пагинации в одну строку

    return builder.as_markup()