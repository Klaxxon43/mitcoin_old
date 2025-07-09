from .tasks import *

@tasks.callback_query(F.data == 'boost_pr_button')
async def boost_post_handler(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    user_id = callback.from_user.id
    user = await DB.select_user(user_id)
    balance = user['balance']
    if balance is None:
        balance = 0
    if balance >= all_price['boost']:
        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(text="1 день", callback_data="boost_1_day"))
        builder.add(InlineKeyboardButton(text="1 неделя", callback_data="boost_7_days"))
        builder.add(InlineKeyboardButton(text="1 месяц", callback_data="boost_30_days"))
        builder.add(InlineKeyboardButton(text="🔙 Назад", callback_data="pr_menu_cancel"))
        builder.adjust(3, 1)
        await callback.message.edit_text(f'''
📢 Буст канала

💵 {all_price['boost']} MITcoin

Выберите срок буста:
        ''', reply_markup=builder.as_markup())
    else:
        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(text="Пополнить баланс", callback_data="cancel_all"))
        builder.add(InlineKeyboardButton(text="🔙 Назад", callback_data="pr_menu_cancel"))
        await callback.message.edit_text(
            f'😢 <b>Недостаточно средств на балансе</b> Ваш баланс: {balance} MITcoin\n<em>Пополните баланс...</em>',
            reply_markup=builder.as_markup())

@tasks.callback_query(F.data.startswith('boost_'))
async def boost_post2(callback: types.CallbackQuery, state: FSMContext):
    days = int(callback.data.split('_')[1])
    await state.update_data(days=days)
    await callback.message.edit_text('''
📢 Введите количество выполнений задания (сколько раз нужно выполнить буст):
    ''', reply_markup=pr_menu_canc())
    await state.set_state(BoostPromotionStates.boost_task_create2)

@tasks.message(BoostPromotionStates.boost_task_create2)
async def boost_post3(message: types.Message, state: FSMContext, bot: Bot):
    try:
        executions = int(message.text.strip())
        if executions < 1:
            await message.answer('❌ Количество выполнений должно быть не менее 1. Попробуйте ещё раз.')
            return
        
        user_id = message.from_user.id
        user = await DB.select_user(user_id)
        balance = user.get('balance', 0)
        
        total_cost = executions * all_price['boost']
        
        if balance < total_cost:
            builder = InlineKeyboardBuilder()
            builder.row(
                InlineKeyboardButton(text="💰 Пополнить баланс", callback_data="top_up_balance"),
                InlineKeyboardButton(text="❌ Отмена", callback_data="back_menu")
            )
            await message.answer(
                f'❌ Недостаточно средств на балансе\n\n'
                f'Требуется: {total_cost} MITcoin\n'
                f'Ваш баланс: {balance} MITcoin',
                reply_markup=builder.as_markup()
            )
            return
        
        await state.update_data(
            executions=executions,
            total_cost=total_cost,
            current_balance=balance
        )
        
        kb = types.ReplyKeyboardMarkup(
            keyboard=[[
                types.KeyboardButton(
                    text="📢 Выбрать канал",
                    request_chat=types.KeyboardButtonRequestChat(
                        request_id=1,
                        chat_is_channel=True,
                        user_administrator_rights=types.ChatAdministratorRights(
                                                            is_anonymous=False,
                                                            can_manage_chat=False,
                                                            can_delete_messages=False,
                                                            can_manage_video_chats=False,
                                                            can_restrict_members=False,
                                                            can_promote_members=False,
                                                            can_change_info=False,
                                                            can_invite_users=True,
                                                            can_post_stories=False,
                                                            can_edit_stories=False,
                                                            can_delete_stories=False,
                                                            can_post_messages=True,
                                                            can_edit_messages=False,
                                                            can_pin_messages=False
                                                        ),
                        bot_administrator_rights=types.ChatAdministratorRights(
                                                        is_anonymous=False,
                                                        can_manage_chat=False,
                                                        can_delete_messages=False,
                                                        can_manage_video_chats=False,
                                                        can_restrict_members=False,
                                                        can_promote_members=False,
                                                        can_change_info=False,
                                                        can_invite_users=True,
                                                        can_post_stories=False,
                                                        can_edit_stories=False,
                                                        can_delete_stories=False,
                                                        can_post_messages=True,
                                                        can_edit_messages=False,
                                                        can_pin_messages=False
                                                    )
                    )
                )
            ]],
            resize_keyboard=True,
            one_time_keyboard=True
        )
        
        await message.answer(
            '📢 Теперь выберите канал, в котором нужно бустить посты.\n\n'
            'Бот должен быть администратором этого канала.',
            reply_markup=kb
        )
        await state.set_state(BoostPromotionStates.boost_task_create3)
        
    except ValueError:
        await message.answer('❌ Некорректный ввод. Введите целое число.')

@tasks.message(BoostPromotionStates.boost_task_create3)
async def boost_post4(message: types.Message, state: FSMContext, bot: Bot):
    if not message.chat_shared:
        await message.answer("❗ Пожалуйста, выберите канал с помощью кнопки ниже.")
        return

    chat_id = message.chat_shared.chat_id
    user_id = message.from_user.id
    data = await state.get_data()
    executions = data.get('executions')
    total_cost = data.get('total_cost')

    try:
        chat = await bot.get_chat(chat_id)
        bot_info = await bot.get_me()
        member = await bot.get_chat_member(chat_id, bot_info.id)

        if member.status != "administrator" or not member.can_post_messages:
            await state.update_data(pending_channel_id=chat_id)
            invite_link = f"https://t.me/{bot_info.username}?startchannel&admin=post_messages+invite_users"
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="➕ Добавить в админы", url=invite_link)],
                [InlineKeyboardButton(text="🔄 Проверить", callback_data="check_boost_admin_rights")],
                [InlineKeyboardButton(text="❌ Отмена", callback_data="back_menu")]
            ])
            await message.answer(
                f"😕 Бот найден в канале <b>{chat.title}</b>, но ему не выданы админ-права.",
                reply_markup=keyboard
            )
            return

    except Exception as e:
        print("Ошибка при проверке канала:", e)
        await message.answer("❌ Ошибка при проверке канала.")
        return

    # Создаем задание
    await DB.add_balance(user_id, -total_cost)
    await DB.add_transaction(
        user_id=user_id,
        amount=total_cost,
        description="создание задания на буст",
        additional_info=None
    )
    
    task_id = await DB.add_task(
        user_id=user_id,
        target_id=chat_id,
        amount=executions,
        task_type=6,  # Тип задания "буст"
        other=data['days']
    )

    # Формируем данные для кэша
    task_data = {
        'id': task_id,
        'user_id': user_id,
        'target_id': chat_id,
        'amount': executions,
        'type': 6,
        'status': 1,
        'days': data['days'],
        'title': chat.title,
        'username': getattr(chat, 'username', None),
        'is_active': True
    }

    # Добавляем в кэш и обновляем счетчики
    await RedisTasksManager.add_new_task_to_cache('boost', task_data)
    await RedisTasksManager.update_common_tasks_count(bot)

    await message.answer(
        f"✅ Задание на буст постов в канале <b>{chat.title}</b> создано успешно!",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Вернуться в меню", callback_data="back_menu")]]
        )
    )

    await bot.send_message(
        TASKS_CHAT_ID,
        f"🔔 СОЗДАНО НОВОЕ ЗАДАНИЕ\nТип: ⭐️ Буст постов\nКанал: {chat.title}\nЦена: {all_price['boost']}\nВыполнений: {executions}"
    )

    await state.clear()

@tasks.callback_query(F.data == "check_boost_admin_rights")
async def check_boost_admin_rights(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    await callback.answer()
    data = await state.get_data()
    user_id = callback.from_user.id
    chat_id = data.get("pending_channel_id")
    executions = data.get('executions')
    total_cost = data.get('total_cost')

    try:
        chat = await bot.get_chat(chat_id)
        bot_info = await bot.get_me()
        member = await bot.get_chat_member(chat_id, bot_info.id)

        if member.status != "administrator" or not member.can_post_messages:
            await callback.message.edit_text(
                f"⛔ Боту по-прежнему не выданы нужные права в канале <b>{chat.title}</b>.\n\n"
                f"🔧 Убедитесь, что он <b>админ</b> и может <b>публиковать сообщения</b>.",
                reply_markup=callback.message.reply_markup
            )
            return

        # Создание задания
        await DB.add_balance(user_id, -total_cost)
        await DB.add_transaction(
            user_id=user_id,
            amount=total_cost,
            description="создание задания на буст постов",
            additional_info=None
        )
        await DB.add_task(
            user_id=user_id,
            target_id=chat_id,
            amount=executions,
            task_type=6,
            other=data['days']
        )

        await callback.message.edit_text(
            f"✅ Задание на буст постов в канале <b>{chat.title}</b> создано успешно!\n\n"
            f"Количество выполнений: {executions}",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Вернуться в меню", callback_data="back_menu")]
            ])
        )

        await bot.send_message(TASKS_CHAT_ID, f'''
🔔 СОЗДАНО НОВОЕ ЗАДАНИЕ 🔔
⭕️ Тип задания: ⭐️ Буст постов
📢 Канал: {chat.title}
💸 Цена: {all_price['boost']}
👥 Кол-во выполнений: {executions}
💰 Стоимость: {total_cost}
''')

        await state.clear()

    except Exception as e:
        print("Ошибка в check_boost_admin_rights:", e)
        await callback.message.edit_text("⚠ Произошла ошибка при проверке прав. Попробуйте позже.")


@tasks.callback_query(F.data == "retry_boost_task")
async def retry_boost_task(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer("<b>Пожалуйста, повторно отправьте ссылку на канал </b>")
    await state.set_state(BoostPromotionStates.boost_task_create3)
    await callback.answer()









@tasks.callback_query(F.data == 'work_boost')
async def works_boost_handler(callback: types.CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    user = await DB.select_user(user_id)
    
    if not callback.from_user.is_premium and user_id not in ADMINS_ID:
        kb = InlineKeyboardBuilder()
        kb.button(text='🔙 Назад', callback_data='work_menu')
        await callback.message.edit_text('Чтобы выполнять задания этого типа, требуется <b>TG Premium</b>', reply_markup=kb.as_markup())
        return 

    # Пытаемся получить задания из кэша
    cached_tasks = await RedisTasksManager.get_cached_tasks('boost')
    
    if not cached_tasks:
        # Если в кэше нет, загружаем из БД и кэшируем
        if await RedisTasksManager.refresh_task_cache(bot):
            cached_tasks = await RedisTasksManager.get_cached_tasks('boost')
        else:
            cached_tasks = []

    if not cached_tasks:
        await callback.message.edit_text(
            "На данный момент доступных заданий на буст нет, возвращайся позже 😉",
            reply_markup=back_work_menu_kb(user_id)
        )
        return
    
    # Фильтруем задания, исключая те, которые пользователь уже выполнял
    available_tasks = [
        task for task in cached_tasks
        if not await DB.is_task_completed(user_id, task['id'])
        and not await DB.is_task_failed(user_id, task['id'])
        and not await DB.is_task_pending(user_id, task['id'])
    ]
    
    if not available_tasks:
        await callback.message.edit_text(
            "На данный момент доступных заданий на буст нет, возвращайся позже 😉",
            reply_markup=back_work_menu_kb(user_id)
        )
        return
    
    random_task = random.choice(available_tasks)
    task_id, target_id, days = random_task['id'], random_task['target_id'], random_task['days']
    
    try:
        await callback.message.answer_sticker(
            'CAACAgIAAxkBAAENFeZnLS0EwvRiToR0f5njwCdjbSmWWwACTgEAAhZCawpt1RThO2pwgjYE'
        )
        
        # Получаем информацию о канале из кэша
        channel_name = random_task.get('title', target_id)
        channel_username = random_task.get('username', None)
        
        builder = InlineKeyboardBuilder()
        if channel_username:
            builder.add(InlineKeyboardButton(text="🚀 Забустить", url=f'https://t.me/boost/{channel_username}'))
        else:
            builder.add(InlineKeyboardButton(text="🚀 Забустить", callback_data="no_username"))
            
        builder.add(InlineKeyboardButton(text="Проверить ✅", callback_data=f"checkboost_{task_id}"))
        builder.add(InlineKeyboardButton(text="✋Ручная проверка", callback_data=f"2checkboost_{task_id}"))
        builder.add(InlineKeyboardButton(text="⏭ Пропустить", callback_data=f"skip_task_{task_id}"))
        builder.add(InlineKeyboardButton(text="Репорт ⚠️", callback_data=f"report_boost_{task_id}"))
        builder.add(InlineKeyboardButton(text="🔙 Назад", callback_data="work_menu"))
        builder.adjust(1, 2, 2, 1)
        
        await callback.message.answer(
            f"📢 Буст канала: {channel_name}\n💸 Цена: {all_price['boost']} $MICO\nСрок: {days} день\n\n"
            "Нажмите кнопку <b>Проверить</b>, чтобы подтвердить выполнение задания.",
            reply_markup=builder.as_markup()
        )
    except Exception as e:
        print(f"Ошибка: {e}")
        await callback.message.edit_text(
            "Произошла ошибка при обработке задания. Попробуйте позже.",
            reply_markup=back_work_menu_kb(user_id))

@tasks.callback_query(F.data.startswith('checkboost_'))
async def check_boost_handler(callback: types.CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    task_id = int(callback.data.split('_')[-1])
    task = await DB.get_task_by_id(task_id)
    if not task:
        await callback.answer("Задание не найдено.")
        return

    target_id = task[2]
    chat = await get_chat_info(bot, target_id)
    if not chat:
        await callback.answer("❌ Не удалось получить информацию о канале")
        return
    
    target_chat_id = chat.id
    boost_detected = await Boost.has_user_boosted_without_reward(user_id, target_chat_id)

    if boost_detected:
        await Boost.mark_boost_reward_given(user_id, target_chat_id)
        
        # Первое начисление (сразу)
        first_payment = all_price['boost']
        await DB.add_balance(amount=first_payment, user_id=user_id)
        
        # Создаем запись о выполненном задании
        await DB.add_completed_task(
            user_id=user_id,
            task_id=task_id,
            target_id=target_id,
            task_sum=first_payment,
            owner_id=task[1],
            status=1,
            other=task[6]
        )
        
        # Уменьшаем количество выполнений
        new_amount = task[3] - 1
        await DB.update_task_amount(task_id, new_amount)
        
        # Если остались дни для ежедневных начислений
        if task[6] > 1:
            await DB.add_bg_task(
                task_type='boost_check',
                task_data={
                    'task_id': task_id,
                    'user_id': user_id,
                    'chat_id': target_chat_id,
                    'days_checked': 1,  # Уже сделали первое начисление
                    'total_days': task[6]
                },
                delay_seconds=86400*2  # Ровно 24 часа до следующего начисления
            )
        
        await callback.message.answer(
            f"👍 <b>Буст засчитан! +{first_payment} MITcoin</b>\n\n"
            f"Следующее начисление за второй день буста будет через 48 часов, после завершения второго дня буста, далее спустя каждые 24 часа" + 
            (f"\nВсего дней буста: {task[6]}" if task[6] > 1 else ""),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Дальше ⏭️", callback_data="work_boost")]
            ])
        )
        RedisTasksManager.refresh_task_cache(bot)
        if new_amount <= 0:
            creator_id = task[1]
            await DB.delete_task(task_id)
            await bot.send_message(
                creator_id,
                f"🎉 Ваше задание на буст было успешно выполнено!",
                reply_markup=back_menu_kb(user_id)
            )
    else:
        await callback.answer(
            "❌ Буст не был выполнен или уже был засчитан. Попробуйте ещё раз.", 
            show_alert=True
        )

@tasks.callback_query(F.data.startswith('2checkboost_'))
async def _(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    task_id = int(callback.data.split('_')[-1])  # Извлекаем ID задания из callback_data

    # Получаем данные задания
    task = await DB.get_task_by_id(task_id)
    if not task:
        await callback.answer("Задание не найдено.")
        return

    target_id = task[2]
    await callback.message.answer(
        '😞 Не получилось проверить буст автоматически?\n'
        '✌️ Нам жаль, что вы столкнулись с этой проблемой, а пока мы решаем её, вы можете попробовать ручную проверку.\n\n'
        '❗️ Чтобы сделать это, отправьте сюда скриншот того, как вы выполнили задание. Мы заметим это и в скором времени начислим вам награду!'
    )
    await state.set_state(BoostProof.waiting_for_screenshot)
    await state.update_data(task_id=task_id, target_id=target_id)


@tasks.message(BoostProof.waiting_for_screenshot)
async def handle_boost_screenshot(message: types.Message, state: FSMContext, bot: Bot):
    user_id = message.from_user.id
    data = await state.get_data()
    task_id = data.get('task_id')
    target_id = data.get('target_id')

    if not message.photo:
        await message.answer("❌ Пожалуйста, отправьте скриншот.")
        return

    screenshot_id = message.photo[-1].file_id  # Берём самое большое изображение

    # Добавляем задание в таблицу ожидания подтверждения
    await DB.add_pending_reaction_task( 
        user_id=user_id,
        task_id=task_id,
        target_id=target_id,
        post_id =0,
        reaction= 0,
        screenshot=screenshot_id
    )

    # Уведомляем пользователя
    kb = InlineKeyboardBuilder()
    kb.button(text='⏭ Далее', callback_data='work_boost')
    kb.button(text='🔙 Назад', callback_data='work_menu')
    await message.answer("✅ Скриншот отправлен на проверку. Ожидайте подтверждения.", reply_markup=kb.as_markup())

    # Отправляем админу задание на проверку
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"confirm_boost_{task_id}_{user_id}"))
    builder.add(InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_boost_{task_id}_{user_id}"))
    builder.add(InlineKeyboardButton(text="🔗 Перейти к каналу", url=f"https://t.me/{str(target_id).replace('@', '')}"))
    builder.adjust(1)

    sent_message = await bot.send_photo(
        CHECK_CHAT_ID,
        photo=screenshot_id,
        caption=(
            f"#буст\n"
            f"📢 <b>Задание на буст канала</b>\n\n"
            f"👤 Пользователь: @{message.from_user.username} (ID: {user_id})\n"
            f"📌 Канал: {target_id}\n"
            f"🆔 ID задания: {task_id}\n\n"
            f"Проверьте выполнение задания:"
        ),
        reply_markup=builder.as_markup()
    )

    # Сохраняем ID сообщения в state
    await state.update_data(admin_message_id=sent_message.message_id)

    # Запускаем фоновую задачу для автоматического подтверждения через 24 часа
    asyncio.create_task(auto_confirm_boost_task(task_id, user_id, bot, message.from_user.username, state))

    await state.clear()

async def auto_confirm_boost_task(task_id, user_id, bot, username, state):
    await asyncio.sleep(24 * 3600)  # Ждем 24 часа
    pending_task = await DB.get_pending_reaction_task(task_id, user_id)
    if pending_task:
        await confirm_boost_handler(task_id, user_id, bot, username, state)

@tasks.callback_query(F.data.startswith('confirm_boost_'))
async def confirm_boost_handler(callback: types.CallbackQuery, bot: Bot, state: FSMContext):
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
    pending_id, user_id, task_id, target_id, _, _, screenshot, status = pending_task

    try:
        target_chat = await bot.get_chat(f"@{target_id}")
    except:
        target_chat = await bot.get_chat(target_id)
    target_chat_id = target_chat.id

    # Помечаем награду как выданную
    await Boost.mark_boost_reward_given(user_id, target_chat_id)

    # Добавляем задание в таблицу completed_tasks
    await DB.add_completed_task(
        user_id=user_id,
        task_id=task_id,
        target_id=target_id,
        task_sum=all_price['boost'],
        owner_id=user_id,
        status=1,
        other=0
    )

    # Удаляем задание из таблицы ожидания
    await DB.delete_pending_reaction_task(task_id, user_id)

    # Начисляем баланс пользователю
    await DB.add_balance(amount=all_price['boost'], user_id=user_id)

    task = await DB.get_task_by_id(task_id)
    if task:
        new_amount = task[3] - 1  # task[3] — это текущее количество выполнений
        await DB.update_task_amount2(task_id, new_amount)

    # Уведомляем пользователя
    await bot.send_message(
        user_id,
        f"🎉 <b>Ваше задание на буст подтверждено!</b>\n\n"
        f"💸 Вам начислено: {all_price['boost']} MITcoin\n"
        f"📌 Канал: {target_id}\n"
        f"🆔 ID задания: {task_id}"
    )

    await update_dayly_and_weekly_tasks_statics(user_id)

    # Уведомляем создателя задания
    creator_id = user_id
    await bot.send_message(
        creator_id,
        f"🎉 <b>Ваше задание на буст выполнено!</b>\n\n"
        f"👤 Пользователь: @{callback.from_user.username} (ID: {user_id})\n" 
        f"📌 Канал: {target_id}\n"
        f"🆔 ID задания: {task_id}"
    )

    # Удаляем сообщение с заданием
    data = await state.get_data()
    admin_message_id = data.get('admin_message_id')
    if admin_message_id:
        await bot.delete_message(CHECK_CHAT_ID, admin_message_id)

    await DB.increment_statistics(1, 'boosts')
    await DB.increment_statistics(2, 'boosts')
    await DB.increment_statistics(1, 'all_taasks')
    await DB.increment_statistics(2, 'all_taasks')

    await callback.answer("✅ Задание подтверждено.")
    RedisTasksManager.refresh_task_cache(bot)

@tasks.callback_query(F.data.startswith('reject_boost_'))
async def reject_boost_handler(callback: types.CallbackQuery, bot: Bot, state: FSMContext):
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
    pending_id, user_id, task_id, target_id, _, _, screenshot, status = pending_task

    # Добавляем задание в список проваленных для пользователя
    await DB.add_failed_task(user_id, task_id)

    # Удаляем задание из таблицы ожидания
    await DB.delete_pending_reaction_task(task_id, user_id)

    # Уведомляем пользователя
    await bot.send_message(
        user_id,
        f"❌ <b>Ваше задание на буст отклонено.</b>\n\n"
        f"📌 Канал: @{target_id}\n"
        f"🆔 ID задания: {task_id}\n\n"
        f"Пожалуйста, убедитесь, что вы выполнили задание правильно."
    )

    # Уведомляем админа
    await bot.send_message(
        CHECK_CHAT_ID,
        f"❌ <b>Задание на буст отклонено.</b>\n\n"
        f"👤 Пользователь: @{callback.from_user.username} (ID: {user_id})\n"
        f"📌 Канал: @{target_id}\n"
        f"🆔 ID задания: {task_id}"
    )

    # Удаляем сообщение с заданием
    data = await state.get_data()
    admin_message_id = data.get('admin_message_id')
    if admin_message_id:
        await bot.delete_message(CHECK_CHAT_ID, admin_message_id)

    await callback.answer("❌ Задание отклонено.")



def is_user_boosting(chat_boost: ChatBoostUpdated, user_id: int, chat_id: int) -> bool:
    source = chat_boost.boost.source
    
    # Проверяем, что источник буста - премиум пользователь
    if isinstance(source, ChatBoostSourcePremium):
        return (
            source.user is not None
            and source.user.id == user_id
            and chat_boost.chat.id == chat_id
        )
    return False

@tasks.chat_boost()
async def on_chat_boost(chat_boost: ChatBoostUpdated, bot: Bot):
    source = chat_boost.boost.source
    
    # Обрабатываем только бусты от премиум пользователей
    if isinstance(source, ChatBoostSourcePremium):
        if source.user is None:
            return
            
        user_id = source.user.id
        chat_id = chat_boost.chat.id

        # Сохраняем факт буста в БД
        await Boost.add_user_boost(user_id=user_id, chat_id=chat_id)

@tasks.removed_chat_boost()
async def on_chat_boost_removed(removed_chat_boost: ChatBoostRemoved, bot: Bot):
    source = removed_chat_boost.source

    # Обрабатываем только снятие буста от премиум пользователей
    if isinstance(source, ChatBoostSourcePremium):
        if source.user is None:
            return

        user_id = source.user.id
        chat_id = removed_chat_boost.chat.id

        # Удаляем запись о бусте в БД
        await Boost.remove_user_boost(user_id=user_id, chat_id=chat_id)



async def get_chat_info(bot: Bot, target_id):
    """Получает информацию о канале по ID или username"""
    try:
        # Если target_id - число (ID канала в формате -100...)
        if isinstance(target_id, int) or (isinstance(target_id, str) and target_id.lstrip('-').isdigit()):
            chat_id = int(target_id)
            chat = await bot.get_chat(chat_id)
            return chat
            
        # Если target_id - строка и начинается с @ (username)
        elif isinstance(target_id, str) and target_id.startswith('@'):
            chat = await bot.get_chat(target_id)
            return chat
            
        # Если формат неясен (например, просто строка без @)
        else:
            try:
                # Пробуем как числовой ID
                chat_id = int(target_id)
                chat = await bot.get_chat(chat_id)
                return chat
            except ValueError:
                # Пробуем как username (добавляем @ если его нет)
                username = target_id if target_id.startswith('@') else f'@{target_id}'
                chat = await bot.get_chat(username)
                return chat
                
    except Exception as e:
        print(f"Error getting chat info for {target_id}: {e}")
        return None

