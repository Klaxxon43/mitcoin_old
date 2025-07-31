from .tasks import *

@tasks.callback_query(F.data == 'reaction_pr_button')
async def reaction_post_handler(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    user_id = callback.from_user.id
    user = await DB.select_user(user_id)
    balance = user['balance'] if user['balance'] is not None else 0
    
    if balance >= all_price['reaction']:
        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(text="Любая реакция", callback_data="reaction_any"))
        builder.add(InlineKeyboardButton(text="Конкретная реакция", callback_data="reaction_specific"))
        builder.add(InlineKeyboardButton(text="🔙 Назад", callback_data="pr_menu_cancel"))
        builder.adjust(2, 1)
        await callback.message.edit_text(
            f'🎭 Задание на реакции\n\n💵 {all_price["reaction"]} MITcoin\n\nВыберите тип реакции:',
            reply_markup=builder.as_markup()
        )
    else:
        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(text="Пополнить баланс", callback_data="cancel_all"))
        builder.add(InlineKeyboardButton(text="🔙 Назад", callback_data="pr_menu_cancel"))
        await callback.message.edit_text(
            f'😢 <b>Недостаточно средств на балансе</b> Ваш баланс: {balance} MITcoin\n<em>Пополните баланс...</em>',
            reply_markup=builder.as_markup()
        )

@tasks.callback_query(F.data.startswith('reaction_'))
async def reaction_post2(callback: types.CallbackQuery, state: FSMContext):
    reaction_type = callback.data.split('_')[1]
    await state.update_data(reaction_type=reaction_type)
    
    if reaction_type == 'specific':
        await callback.message.edit_text(
            '🎭 Введите конкретную реакцию (эмодзи), которую нужно оставить:',
            reply_markup=pr_menu_canc()
        )
        await state.set_state(ReactionPromotionStates.reaction_task_create2)
    else:
        await callback.message.edit_text(
            '🎭 Введите количество выполнений задания (от 1 до 1000):',
            reply_markup=pr_menu_canc()
        )
        await state.set_state(ReactionPromotionStates.reaction_task_create3)

@tasks.message(ReactionPromotionStates.reaction_task_create2)
async def reaction_post3(message: types.Message, state: FSMContext):
    if len(message.text.strip()) > 2 or message.text.strip() not in emoji.EMOJI_DATA:
        await message.answer('❌ Пожалуйста, введите один корректный эмодзи')
        return
    
    await state.update_data(specific_reaction=message.text.strip())
    await message.answer(
        '🎭 Введите количество выполнений задания (от 1 до 1000):',
        reply_markup=pr_menu_canc()
    )
    await state.set_state(ReactionPromotionStates.reaction_task_create3)

@tasks.message(ReactionPromotionStates.reaction_task_create3)
async def reaction_post4(message: types.Message, state: FSMContext, bot: Bot):
    try:
        executions = int(message.text.strip())
        if not 1 <= executions <= 1000:
            await message.answer('❌ Количество выполнений должно быть от 1 до 1000')
            return
        
        user_id = message.from_user.id
        user = await DB.select_user(user_id)
        balance = user['balance'] if user['balance'] is not None else 0
        
        total_cost = executions * all_price['reaction']
        if balance < total_cost:
            builder = InlineKeyboardBuilder()
            builder.add(InlineKeyboardButton(text="🔙 Назад", callback_data="pr_menu_cancel"))
            await message.answer(
                f'❌ Недостаточно средств. Требуется: {total_cost} MITcoin\nВаш баланс: {balance} MITcoin',
                reply_markup=builder.as_markup()
            )
            await state.clear()
            return
        
        await state.update_data(executions=executions, balance=balance)
        await message.answer(
            '🎭 Теперь перешлите пост с канала, где нужно оставить реакцию:',
            reply_markup=pr_menu_canc()
        )
        await state.set_state(ReactionPromotionStates.reaction_task_create4)
    except ValueError:
        await message.answer('❌ Некорректный ввод. Введите целое число от 1 до 1000')

@tasks.message(ReactionPromotionStates.reaction_task_create4)
async def reaction_post5(message: types.Message, state: FSMContext, bot: Bot):
    user_id = message.from_user.id
    data = await state.get_data()
    reaction_type = data.get('reaction_type')
    specific_reaction = data.get('specific_reaction')
    executions = data.get('executions')
    balance = data.get('balance')
    
    if not message.forward_from_chat or message.forward_from_chat.type != 'channel':
        await message.answer('❌ Некорректный формат. Перешлите пост именно с канала.')
        return
    
    try:
        # Получаем информацию о канале
        chat = await bot.get_chat(message.forward_from_chat.id)
        channel_id = chat.id
        channel_username = chat.username
        
        # Проверяем права бота
        chat_member = await bot.get_chat_member(chat_id=channel_id, user_id=bot.id)
        if chat_member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR]:
            raise Exception("Бот не является администратором канала.")
            
        # Проверяем доступ к посту
        try:
            await bot.forward_message(
                chat_id=user_id,
                from_chat_id=channel_id,
                message_id=message.forward_from_message_id
            )
        except Exception as e:
            await message.answer('❌ Не удалось получить доступ к посту. Проверьте, что пост существует.')
            return
            
    except Exception as e:
        bot_username = (await bot.get_me()).username
        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(
            text="➕ Добавить бота в канал", 
            url=f"http://t.me/{bot_username}?startchannel&admin=invite_users+manage_chat"
        ))
        builder.add(InlineKeyboardButton(text='🔁 Повторить', callback_data="retryreaction_task"))
        builder.adjust(1)
        await message.answer(
            f"❌ Бот не является администратором этого канала. Добавьте бота в канал и назначьте администратором.",
            reply_markup=builder.as_markup()
        )
        return
    
    # Сохраняем ID канала и сообщения
    target_id = f"{channel_id}:{message.forward_from_message_id}"
    task_type = 7
    total_cost = executions * all_price['reaction']
    
    try:
        await DB.update_balance(user_id, balance - total_cost)
        
        await DB.add_task(
            user_id=user_id,
            target_id=target_id,
            amount=executions,
            task_type=task_type,
            other=specific_reaction if reaction_type == 'specific' else None,
        )
        
        await DB.add_transaction(
            user_id=user_id,
            amount=total_cost, 
            description="Создание задания на реакции",
            additional_info=None
        )
        
        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(text="🔙 Вернуться в меню", callback_data="back_menu"))
        
        # Получаем username для отображения, если он есть
        channel_link = f"https://t.me/{channel_username}/{message.forward_from_message_id}" if channel_username else f"ID канала: {channel_id}"
        
        await message.answer(
            f"✅ Задание на реакции создано!\n\n"
            f"📌 Пост: {channel_link}\n"
            f"🎯 Реакция: {specific_reaction if specific_reaction else 'Любая положительная'}\n"
            f"🔄 Количество: {executions}\n"
            f"💸 Списано: {total_cost} MITcoin",
            reply_markup=builder.as_markup()
        )
        
        await bot.send_message(
            TASKS_CHAT_ID,
            f"🔔 Новое задание на реакции\n"
            f"👤 Пользователь: @{message.from_user.username}\n"
            f"📌 Пост: {channel_link}\n"
            f"🎯 Реакция: {specific_reaction if specific_reaction else 'Любая'}\n"
            f"🔄 Количество: {executions}\n"
            f"💰 Стоимость: {total_cost} MITcoin"
        )
        # После создания задания
        await RedisTasksManager.refresh_task_cache(bot, "reaction")
        await RedisTasksManager.update_common_tasks_count(bot)

    except Exception as e:
        logger.info(f"Ошибка при создании задания: {e}")
        await message.answer('❌ Произошла ошибка при создании задания. Попробуйте позже.')
    
    await state.clear()












@tasks.callback_query(F.data == 'work_reaction')
async def works_reaction_handler(callback: types.CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    
    try:
        # 1. Получаем задания из кэша
        cached_tasks = await RedisTasksManager.get_cached_tasks('reaction') or []
        
        # 2. Фильтруем доступные задания
        available_tasks = []
        for task in cached_tasks:
            try:
                task_id = task.get('id') or task.get('task_id')
                if not task_id:
                    continue

                if await DB.is_task_available_for_user(user_id, task['id']):
                    if task.get('is_active', True):
                        available_tasks.append(task)
            except Exception:
                continue

        if not available_tasks:
            await callback.message.edit_text(
                "🎉 Вы выполнили все доступные задания на реакции!",
                reply_markup=back_work_menu_kb(user_id))
            return

        # 3. Выбираем случайное задание
        task = random.choice(available_tasks)
        task_id = task.get('id') or task.get('task_id')
        target_id = str(task.get('target_id', ''))
        reaction_type = task.get('other', 'Любая положительная')
        amount = abs(task.get('amount', 0))

        # 4. Обрабатываем target_id (канал:пост)
        if ':' in target_id:
            channel_part, post_id = target_id.split(':')
        else:
            channel_part = target_id
            post_id = None

        # 5. Получаем информацию о канале
        try:
            # Пытаемся получить чат по ID (если channel_part число)
            try:
                chat_id = int(channel_part)
                chat = await bot.get_chat(chat_id)
            except ValueError:
                # Если не число - пробуем как username
                username = channel_part.lstrip('@')
                chat = await bot.get_chat(f"@{username}")
            
            channel_name = chat.title
            channel_username = chat.username
            chat_id = chat.id
        except Exception as e:
            logger.info(f"Ошибка получения канала {channel_part}: {e}")
            await callback.answer("⚠ Канал недоступен", show_alert=True)
            return

        # 6. Формируем ссылку на пост
        if channel_username:
            if post_id:
                post_link = f"https://t.me/{channel_username}/{post_id}"
            else:
                post_link = f"https://t.me/{channel_username}"
        else:
            if post_id:
                post_link = f"tg://openmessage?chat_id={chat_id}&message_id={post_id}"
            else:
                post_link = f"tg://resolve?domain={chat_id}"

        # 7. Создаем интерфейс задания
        builder = InlineKeyboardBuilder()
        
        if post_link:
            builder.row(InlineKeyboardButton(
                text="🚀 Перейти к заданию", 
                url=post_link
            ))
        
        builder.row(
            InlineKeyboardButton(
                text="✅ Проверить выполнение", 
                callback_data=f"checkreaction_{task_id}"
            ),
            InlineKeyboardButton(
                text="⚠ Проблема с заданием", 
                callback_data=f"report_reaction_{task_id}"
            )
        )
        builder.row(InlineKeyboardButton(
            text="🔙 Назад", 
            callback_data="work_menu"
        ))

        # 8. Отправляем сообщение с заданием
        await callback.message.answer_sticker(
            'CAACAgIAAxkBAAENFeZnLS0EwvRiToR0f5njwCdjbSmWWwACTgEAAhZCawpt1RThO2pwgjYE'
        )
        
        message_text = [
            "🎭 <b>Задание на реакцию</b>\n\n",
            f"📢 <b>Канал:</b> <a href='{post_link}'>{channel_name}</a>",
            f"💸 <b>Награда:</b> <code>{all_price['reaction']}</code> $MICO",
            f"👍 <b>Реакция:</b> {reaction_type if reaction_type else 'Любая положительная'}\n\n",
            "<em>Перейдите по ссылке выше, оставьте указанную реакцию и нажмите «Проверить выполнение»\n"
            "Если возникнут проблемы, вы можете подать репорт, нажав на кнопку '⚠ Проблема с заданием'</em>"
        ]
        
        await callback.message.answer(
            "\n".join(message_text),
            reply_markup=builder.as_markup(),
            disable_web_page_preview=True
        )

    except Exception as e:
        logger.info(f"Ошибка в обработчике реакций: {e}")
        await callback.answer("⚠ Произошла ошибка", show_alert=True)
        await callback.message.answer(
            "⚠ Произошла ошибка при обработке запроса",
            reply_markup=back_work_menu_kb(user_id))
        

@tasks.callback_query(F.data.startswith('checkreaction_'))
async def check_reaction_handler(callback: types.CallbackQuery, bot: Bot, state: FSMContext):
    user_id = callback.from_user.id
    
    try:
        task_id = int(callback.data.split('_')[-1])
        task = await DB.get_task_by_id(task_id)
        
        if not task or len(task) < 7:
            raise ValueError("Неполные данные задания")
            
        target_id = task[2]
        specific_reaction = task[6]
        
        # Обрабатываем target_id
        if ':' in target_id:
            channel_part, post_id = target_id.split(':')
            post_id = int(post_id)
        else:
            channel_part = target_id
            post_id = None
        
        # Получаем информацию о канале
        try:
            # Пробуем получить чат как ID (если channel_part число)
            try:
                chat_id = int(channel_part)
                chat = await bot.get_chat(chat_id)
            except ValueError:
                # Если не число - пробуем как username
                username = channel_part.lstrip('@')
                chat = await bot.get_chat(f"@{username}")
            
            channel_id = chat.id
            channel_username = chat.username
            channel_title = chat.title
        except Exception as e:
            logger.info(f"Ошибка получения канала {channel_part}: {e}")
            await callback.answer("⚠ Канал недоступен", show_alert=True)
            return

        # Формируем ссылку
        if channel_username:
            if post_id:
                post_link = f"https://t.me/{channel_username}/{post_id}"
            else:
                post_link = f"https://t.me/{channel_username}"
        else:
            if post_id:
                post_link = f"tg://openmessage?chat_id={channel_id}&message_id={post_id}"
            else:
                post_link = f"tg://resolve?domain={channel_id}"

        # Формируем сообщение
        builder = InlineKeyboardBuilder()
        
        if post_link:
            builder.row(InlineKeyboardButton(
                text="🚀 Перейти к заданию", 
                url=post_link
            ))
        
        builder.row(
            InlineKeyboardButton(
                text="✅ Проверить выполнение", 
                callback_data=f"checkreaction_{task_id}"
            ),
            InlineKeyboardButton(
                text="⚠ Проблема с заданием", 
                callback_data=f"report_reaction_{task_id}"
            )
        )
        builder.row(InlineKeyboardButton(
            text="🔙 Назад", 
            callback_data="work_reaction"  # Возврат к выбору задания
        ))

        message_text = (
            f"📸 <b>Отправьте скриншот</b> с выполненным заданием (реакция на пост).\n\n"
            f"<i>Скриншот должен четко показывать поставленную реакцию на нужный пост</i>"
        )

        await callback.message.answer(message_text, reply_markup=builder.as_markup())
        await state.set_state(ReactionProof.waiting_for_screenshot)
        await state.update_data(
            task_id=task_id,
            channel_id=channel_id,
            post_id=post_id,
            specific_reaction=specific_reaction,
            channel_username=channel_username,
            channel_title=channel_title,
            post_link=post_link
        )
        await callback.answer()
        
    except Exception as e:
        logger.info(f"Ошибка в check_reaction_handler: {e}")
        await callback.answer("Произошла ошибка, попробуйте позже.", show_alert=True)

@tasks.message(ReactionProof.waiting_for_screenshot)
async def handle_screenshot(message: types.Message, state: FSMContext, bot: Bot):
    user_id = message.from_user.id
    data = await state.get_data()
    task_id = data.get('task_id')
    channel_id = data.get('channel_id')  # Используем channel_id вместо target_id
    post_id = data.get('post_id')
    specific_reaction = data.get('specific_reaction')
    channel_username = data.get('channel_username')
    
    if not message.photo:
        await message.answer("❌ Пожалуйста, отправьте скриншот.")
        return
    
    screenshot_id = message.photo[-1].file_id
    
    # Формируем target_id в правильном формате
    target_id = f"{channel_id}:{post_id}" if post_id else str(channel_id)
    
    try:
        # Добавляем задание в таблицу ожидания подтверждения
        await DB.add_pending_reaction_task(
            user_id=user_id,
            task_id=task_id,
            target_id=target_id,  # Теперь target_id всегда будет заполнен
            post_id=post_id,
            reaction=specific_reaction,
            screenshot=screenshot_id
        ) 
        
        # Уведомляем пользователя
        kb = InlineKeyboardBuilder()
        kb.button(text='⏭ Далее', callback_data='work_reaction')
        kb.button(text='🔙 Назад', callback_data='work_menu')
        await message.answer("✅ Скриншот отправлен на проверку. Ожидайте подтверждения.", reply_markup=kb.as_markup())
        
        # Отправляем админу задание на проверку (только если есть post_id)
        if post_id:
            builder = InlineKeyboardBuilder()
            builder.add(InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"confirm_reaction_{task_id}_{user_id}"))
            builder.add(InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_reaction_{task_id}_{user_id}"))
            builder.add(InlineKeyboardButton(text="🔗 Перейти к посту", url=f"https://t.me/{channel_username}/{post_id}"))
            builder.adjust(1)
            
            sent_message = await bot.send_photo(
                CHECK_CHAT_ID,
                photo=screenshot_id,
                caption=f"#реакция\n" 
                        f"📝 <b>Задание на реакцию</b>\n\n"
                        f"👤 Пользователь: @{message.from_user.username} (ID: {user_id})\n"
                        f"📌 Пост: https://t.me/{channel_username}/{post_id}\n"
                        f"🎯 Реакция: {specific_reaction if specific_reaction else 'Любая'}\n"
                        f"🆔 ID задания: {task_id}\n\n"
                        f"Проверьте выполнение задания:",
                reply_markup=builder.as_markup()
            )
            
            # Сохраняем ID сообщения в state
            await state.update_data(admin_message_id=sent_message.message_id)
        
        await state.clear()
        
    except Exception as e:
        logger.info(f"Ошибка при обработке скриншота: {e}")
        await message.answer("❌ Произошла ошибка при обработке вашего скриншота. Пожалуйста, попробуйте позже.")


@tasks.callback_query(F.data.startswith('confirm_reaction_'))
async def confirm_reaction_handler(callback: types.CallbackQuery, bot: Bot, state: FSMContext):
    parts = callback.data.split('_')
    if len(parts) < 3:
        await callback.answer("Некорректный формат callback данных.")
        return
    
    task_id = int(parts[-2])  # Предпоследний элемент — task_id
    user_id = int(parts[-1])  # Последний элемент — user_id
    
    # Получаем задание из таблицы ожидания
    pending_task = await DB.get_pending_reaction_task(task_id, user_id)
    if not pending_task:
        await callback.answer("Задание не найдено.")
        return
    
    # Извлекаем данные из кортежа по индексам
    pending_id, user_id, task_id, target_id, post_id, reaction, screenshot, status = pending_task
    
    try:
        # Разбираем target_id на ID канала и ID сообщения
        channel_id, post_id = target_id.split(':')
        channel_id = int(channel_id)
        post_id = int(post_id)
        
        # Получаем информацию о канале
        chat = await bot.get_chat(channel_id)
        channel_username = chat.username if chat.username else f"c/{chat.id}"
    except Exception as e:
        channel_username = "неизвестный канал"
    
    # Добавляем задание в таблицу completed_tasks
    await DB.add_completed_task(
        user_id=user_id,
        task_id=task_id,
        target_id=target_id,
        task_sum=all_price['reaction'],
        owner_id=user_id,
        status=0,
        other=0
    )

    await update_dayly_and_weekly_tasks_statics(user_id)
    await DB.increment_statistics(1, 'likes')
    await DB.increment_statistics(2, 'likes')
    await DB.increment_statistics(1, 'all_taasks')
    await DB.increment_statistics(2, 'all_taasks')
    
    # Удаляем задание из таблицы ожидания
    await DB.delete_pending_reaction_task(task_id, user_id)
    
    # Начисляем баланс пользователю
    await DB.add_balance(amount=all_price['reaction'], user_id=user_id)

    task = await DB.get_task_by_id(task_id)
    if task:
        new_amount = task[3] - 1  # task[3] — это текущее количество выполнений
        await DB.update_task_amount2(task_id, new_amount)
    
    # Уведомляем пользователя
    await bot.send_message(
        user_id,
        f"🎉 <b>Ваше задание на реакцию подтверждено!</b>\n\n"
        f"💸 Вам начислено: {all_price['reaction']} MITcoin\n"
        f"📌 Пост: https://t.me/{channel_username}/{post_id}\n"
        f"🎯 Реакция: {reaction if reaction else 'Любая'}\n"
        f"🆔 ID задания: {task_id}"
    )
    
    # # Уведомляем создателя задания
    # creator_id = user_id
    # await bot.send_message(
    #     creator_id,
    #     f"🎉 <b>Задание на реакцию выполнено!</b>\n\n"
    #     f"👤 Пользователь: @{callback.from_user.username} (ID: {user_id})\n"
    #     f"📌 Пост: https://t.me/{channel_username}/{post_id}\n"
    #     f"🎯 Реакция: {reaction if reaction else 'Любая'}\n"
    #     f"🆔 ID задания: {task_id}"
    # )
    
    # Удаляем сообщение с заданием
    data = await state.get_data()
    admin_message_id = data.get('admin_message_id')
    if admin_message_id:
        await bot.delete_message(CHECK_CHAT_ID, admin_message_id)
    
    await callback.answer("✅ Задание подтверждено.")
    # После создания задания
    await RedisTasksManager.refresh_task_cache(bot, "reaction")


@tasks.callback_query(F.data.startswith('reject_reaction_'))
async def reject_reaction_handler(callback: types.CallbackQuery, bot: Bot, state: FSMContext):
    parts = callback.data.split('_')
    if len(parts) < 3:
        await callback.answer("Некорректный формат callback данных.")
        return
    
    task_id = int(parts[-2])  # Предпоследний элемент — task_id
    user_id = int(parts[-1])  # Последний элемент — user_id
    
    # Получаем задание из таблицы ожидания
    pending_task = await DB.get_pending_reaction_task(task_id, user_id)
    if not pending_task:
        await callback.answer("Задание не найдено.")
        return
    
    # Извлекаем данные из кортежа по индексам
    pending_id, user_id, task_id, target_id, post_id, reaction, screenshot, status = pending_task
    
    try:
        # Разбираем target_id на ID канала и ID сообщения
        channel_id, post_id = target_id.split(':')
        channel_id = int(channel_id)
        post_id = int(post_id)
        
        # Получаем информацию о канале
        chat = await bot.get_chat(channel_id)
        channel_username = chat.username if chat.username else f"c/{chat.id}"
    except Exception as e:
        channel_username = "неизвестный канал"
    
    # Добавляем задание в список проваленных для пользователя
    await DB.add_failed_task(user_id, task_id)
    
    # Удаляем задание из таблицы ожидания
    await DB.delete_pending_reaction_task(task_id, user_id)
    
    # Уведомляем пользователя
    await bot.send_message(
        user_id,
        f"❌ <b>Ваше задание на реакцию отклонено.</b>\n\n"
        f"📌 Пост: https://t.me/{channel_username}/{post_id}\n"
        f"🎯 Реакция: {reaction if reaction else 'Любая'}\n"
        f"🆔 ID задания: {task_id}\n\n"
        f"Пожалуйста, убедитесь, что вы выполнили задание правильно."
    )
    
    # Удаляем сообщение с заданием
    data = await state.get_data()
    admin_message_id = data.get('admin_message_id')
    if admin_message_id:
        await bot.delete_message(CHECK_CHAT_ID, admin_message_id)
    
    await callback.answer("❌ Задание отклонено.")


















