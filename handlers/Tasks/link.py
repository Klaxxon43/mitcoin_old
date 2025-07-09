from .tasks import *

@tasks.callback_query(F.data == 'link_task_button')
async def link_task_handler(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    user_id = callback.from_user.id
    user = await DB.select_user(user_id)
    balance = user['balance']
    if balance is None:
        balance = 0
    maxcount = balance // all_price['link']
    await callback.message.edit_text(f'''
🔗 Переход по ссылке

💵 {all_price['link']} MITcoin = 1 задание

баланс: <b>{balance}</b>; Всего вы можете купить <b>{maxcount}</b> заданий

<b>Сколько нужно заданий</b>❓

<em>Что бы создать задание на вашем балансе должно быть не менее {all_price['link']} MITcoin</em>
    ''', reply_markup=pr_menu_canc())
    await state.set_state(LinkPromotionStates.link_task_create)

@tasks.message(LinkPromotionStates.link_task_create)
async def link_task2(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    user = await DB.select_user(user_id) 
    balance = user['balance']
    if balance is None:
        balance = 0
    try:
        uscount = int(message.text.strip())
        if uscount >= 1:
            price = all_price['link'] * uscount
            await state.update_data(uscount=uscount, price=price, balance=balance)
            if balance >= price:
                builder = InlineKeyboardBuilder()
                builder.add(InlineKeyboardButton(text="✅ Продолжить", callback_data="link_task_confirm"))
                builder.add(InlineKeyboardButton(text="🔙 Назад", callback_data="pr_menu_cancel"))
                await message.answer(
                    f'👍 <b>Количество: {uscount}</b>\n💰<b> Стоимость - {price} MITcoin</b>\n\n<em>Нажмите кнопку <b>Продолжить</b> или введите другое число...</em>',
                    reply_markup=builder.as_markup())
            else:
                builder = InlineKeyboardBuilder()
                builder.add(InlineKeyboardButton(text="Пополнить баланс", callback_data="cancel_all"))
                builder.add(InlineKeyboardButton(text="🔙 Назад", callback_data="pr_menu_cancel"))
                await message.answer(
                    f'😢 <b>Недостаточно средств на балансе</b> \nВаш баланс: {balance} MITcoin\n<em>Пополните баланс или измените желаемое количество заданий...</em>',
                    reply_markup=builder.as_markup())
        else:
            await message.answer('<b>❗Минимальная покупка от 1 задания!</b>\nВведи корректное число...',
                                 reply_markup=pr_menu_canc())
    except ValueError:
        await message.answer('<b>Ошибка ввода</b>\nПопробуй ввести целое число...', reply_markup=pr_menu_canc())

@tasks.callback_query(F.data == 'link_task_confirm')
async def link_task3(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    uscount = data.get('uscount')
    price = data.get('price')
    balance = data.get('balance')
    await state.clear()
    await callback.message.edit_text(f'''
🔗 Теперь введите ссылку на бота, по которой нужно перейти. Я жду...
    ''', reply_markup=pr_menu_canc())
    await state.set_state(LinkPromotionStates.link_task_create2)
    await state.update_data(uscount=uscount, price=price, balance=balance)

@tasks.message(LinkPromotionStates.link_task_create2)
async def link_task4(message: types.Message, state: FSMContext, bot: Bot):
    async with task_creation_lock:
        user_id = message.from_user.id
        data = await state.get_data()
        amount = data.get('uscount')
        price = data.get('price')
        balance = data.get('balance')

        link = message.text.strip()
        if not link.startswith("https://t.me/"):
            await message.answer("❌ Некорректная ссылка. Убедитесь, что ссылка начинается с https://t.me/.")
            return

        try:
            builder = InlineKeyboardBuilder()
            builder.add(InlineKeyboardButton(text="Автоматическая проверка 🤖", callback_data="auto_check"))
            builder.add(InlineKeyboardButton(text="Ручная проверка 👨‍💻", callback_data="manual_check"))
            await message.answer(
                "🔍 <b>Выберите тип проверки задания:</b>\n\n"
                "🤖 <b>Автоматическая проверка:</b> Пользователь пересылает сообщение от бота.\n"
                "👨‍💻 <b>Ручная проверка:</b> Пользователь отправляет скриншот, который проверяется администратором.",
                reply_markup=builder.as_markup())
            await state.update_data(link=link, amount=amount, price=price, balance=balance)
            await state.set_state(LinkPromotionStates.link_task_create3)
        except Exception as e:
            print(f"Ошибка при создании задания: {e}")
            await message.answer("❌ Произошла ошибка при создании задания. Попробуйте позже.")

@tasks.callback_query(F.data == 'auto_check')
async def auto_check_handler(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    user_id = callback.from_user.id
    link = data.get('link')
    amount = data.get('amount')
    price = data.get('price')
    balance = data.get('balance')

    try:
        task_type = 5
        other = 0  # 0 - автоматическая проверка
        new_balance = balance - price
        await DB.update_balance(user_id, balance=new_balance)
        await DB.add_task(user_id=user_id, target_id=link, amount=amount, task_type=task_type, other=other)

        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(text="🔙 Вернуться в меню", callback_data="back_menu"))
        await callback.message.answer(
            "🥳 Задание на переход по ссылке создано! Оно будет размещено в разделе <b>Заработать</b>\n\nКогда задание будет выполнено - Вы получите уведомление 😉",
            reply_markup=builder.as_markup())
        await DB.add_transaction(
            user_id=callback.from_user.id,
            amount=price, 
            description="создание задания на переход по ссылке",
            additional_info=None
        )

        await bot.send_message(TASKS_CHAT_ID, f'''
🔔 СОЗДАНО НОВОЕ ЗАДАНИЕ 🔔
⭕️ Тип задания: 🔗 Переход по ссылке, автоматическая проверка
💸 Цена: {all_price['link']} 
👥 Количество выполнений: {amount}
💰 Стоимость: {amount * all_price['link']} 
''')
        await state.clear()
    except Exception as e:
        print(f"Ошибка при создании задания: {e}")
        await callback.message.answer("❌ Произошла ошибка при создании задания. Попробуйте позже.")

@tasks.callback_query(F.data == 'manual_check')
async def manual_check_handler(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user_id = callback.from_user.id
    link = data.get('link')
    amount = data.get('amount')
    price = data.get('price')
    balance = data.get('balance')

    try:
        await callback.message.answer(
            "📝 <b>Опишите, что должен сделать пользователь, перейдя по ссылке:</b>\n\n"
            "<em>Например: 'Напишите боту команду /start и отправьте скриншот ответа.'</em>",
            reply_markup=pr_menu_canc())
        await state.set_state(LinkPromotionStates.link_task_create4)
    except Exception as e:
        print(f"Ошибка при создании задания: {e}")
        await callback.message.answer("❌ Произошла ошибка при создании задания. Попробуйте позже.")

@tasks.message(LinkPromotionStates.link_task_create4)
async def link_task5(message: types.Message, state: FSMContext, bot: Bot):
    user_id = message.from_user.id
    data = await state.get_data()
    link = data.get('link')
    amount = data.get('amount')
    price = data.get('price')
    balance = data.get('balance')
    description = message.text.strip()

    try:
        task_type = 5
        other = f"1|{description}"  # 1 - ручная проверка, | - разделитель
        new_balance = balance - price
        await DB.update_balance(user_id, balance=new_balance)
        await DB.add_task(user_id=user_id, target_id=link, amount=amount, task_type=task_type, other=other)

        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(text="🔙 Вернуться в меню", callback_data="back_menu"))
        await message.answer(
            "🥳 Задание на переход по ссылке создано! Оно будет размещено в разделе <b>Заработать</b>\n\nКогда задание будет выполнено - Вы получите уведомление 😉",
            reply_markup=builder.as_markup())
        await DB.add_transaction(
            user_id=message.from_user.id,
            amount=price, 
            description="создание задания на переход по ссылке",
            additional_info=None
        )

        await bot.send_message(TASKS_CHAT_ID, f'''
🔔 СОЗДАНО НОВОЕ ЗАДАНИЕ 🔔
⭕️ Тип задания: 🔗 Переход по ссылке, ручная проверка
❗️ Условие выполнения: {description}
💸 Цена: {all_price['link']} 
👥 Количество выполнений: {price / all_price['link']}
💰 Стоимость: {price} 
''')
        await state.clear()
    except Exception as e:
        print(f"Ошибка при создании задания: {e}")
        await message.answer("❌ Произошла ошибка при создании задания. Попробуйте позже.")




















@tasks.callback_query(F.data == 'work_link')
async def works_link_handler(callback: types.CallbackQuery, bot: Bot, state: FSMContext):
    user_id = callback.from_user.id
    
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Автоматическая проверка 🤖", callback_data="work_link_auto"))
    builder.add(InlineKeyboardButton(text="Ручная проверка 👨‍💻", callback_data="work_link_manual"))
    builder.add(InlineKeyboardButton(text="🔙 Назад", callback_data="work_menu"))
    builder.adjust(1)
    
    await callback.message.edit_text(
        "🔍 <b>Выберите тип задания для выполнения:</b>",
        reply_markup=builder.as_markup()
    )

@tasks.callback_query(F.data == 'work_link_auto')
async def work_link_auto_handler(callback: types.CallbackQuery, bot: Bot, state: FSMContext):
    user_id = callback.from_user.id
    
    try:
        # Получаем задания из Redis или БД
        all_tasks = await RedisTasksManager.get_cached_tasks('link')
        if not all_tasks:
            all_tasks = await DB.select_link_tasks()
            if all_tasks:
                await RedisTasksManager.cache_tasks('link', all_tasks)

        if all_tasks:
            available_tasks = [
                task for task in all_tasks
                if not await DB.is_task_completed(user_id, task[0])
                and not await DB.is_task_failed(user_id, task[0])
                and not await DB.is_task_pending(user_id, task[0])
                and task[6] == 0  # Автоматическая проверка
            ]
            
            if not available_tasks:
                await callback.message.edit_text(
                    "Нет доступных заданий с автоматической проверкой",
                    reply_markup=back_work_menu_kb(user_id)
                )
                return 
            
            random_task = random.choice(available_tasks)
            task_id, target_link, amount = random_task[0], random_task[2], random_task[3]

            await state.set_state(LinkPromotionStates.performing_task)
            await state.update_data(task_id=task_id, target_link=target_link, task_type=0)

            await callback.message.answer(
                f"🔗 <b>Задание:</b> Перейдите по ссылке: {target_link}",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 Назад", callback_data="work_link")],
                    [InlineKeyboardButton(text="⏭ Пропустить", callback_data=f"skip_task_{task_id}")],
                    [InlineKeyboardButton(text="Репорт ⚠️", callback_data=f"report_link_{task_id}")]
                ]))
        else:
            await callback.message.edit_text(
                "Нет доступных заданий",
                reply_markup=back_work_menu_kb(user_id)
            )
    except Exception as e:
        print(f"Ошибка в work_link_auto_handler: {e}")
        await callback.message.edit_text(
            "Произошла ошибка. Попробуйте позже.",
            reply_markup=back_work_menu_kb(user_id)
        )

@tasks.callback_query(F.data == 'work_link_manual')
async def work_link_manual_handler(callback: types.CallbackQuery, bot: Bot, state: FSMContext):
    user_id = callback.from_user.id
    
    try:
        # Получаем задания из Redis или БД
        all_tasks = await RedisTasksManager.get_cached_tasks('link')
        if not all_tasks:
            all_tasks = await DB.select_link_tasks()
            if all_tasks:
                await RedisTasksManager.cache_tasks('link', all_tasks)

        if all_tasks:
            available_tasks = [
                task for task in all_tasks
                if not await DB.is_task_completed(user_id, task[0])
                and not await DB.is_task_failed(user_id, task[0])
                and not await DB.is_task_pending(user_id, task[0])
                and task[6] != 0  # Только ручная проверка
            ]
            
            if not available_tasks:
                await callback.message.edit_text(
                    "Нет доступных заданий с ручной проверкой",
                    reply_markup=back_work_menu_kb(user_id)
                )
                return
            
            random_task = random.choice(available_tasks)
            task_id, target_link, amount, other = random_task[0], random_task[2], random_task[3], random_task[6]
            
            try:
                description = str(other).split("|")[1] if "|" in str(other) else "Выполните условия задания"
            except:
                description = "Выполните условия задания"

            await state.set_state(LinkPromotionStates.performing_task)
            await state.update_data(
                task_id=task_id,
                target_link=target_link,
                task_type=1,
                description=description
            )

            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data="work_link")],
                [InlineKeyboardButton(text="Отправить скриншот 📷", callback_data=f"link_{task_id}")],
                [InlineKeyboardButton(text="⏭ Пропустить", callback_data=f"skip_task_{task_id}")],
                [InlineKeyboardButton(text="Репорт ⚠️", callback_data=f"report_link_{task_id}")]
            ])

            await callback.message.answer(
                f"🔗 <b>Задание:</b> {target_link}\n\n"
                f"📝 <b>Условие:</b> {description}\n\n"
                f"💸 <b>Награда:</b> {all_price['link']} MITcoin\n\n"
                f"Отправьте скриншот выполнения:",
                reply_markup=keyboard
            )
        else:
            await callback.message.edit_text(
                "Нет доступных заданий",
                reply_markup=back_work_menu_kb(user_id)
            )
    except Exception as e:
        print(f"Ошибка в work_link_manual_handler: {e}")
        await callback.message.edit_text(
            "Произошла ошибка. Попробуйте позже.",
            reply_markup=back_work_menu_kb(user_id)
        )


@tasks.callback_query(F.data.startswith('link_'))
async def link_task_screenshot_handler(callback: types.CallbackQuery, state: FSMContext):
    task_id = int(callback.data.split('_')[1])
    await state.update_data(task_id=task_id)
    
    data = await state.get_data()
    task_type = data.get("task_type")
    
    if task_type == 0:
        await callback.message.answer("Пожалуйста, перешлите сообщение от бота для проверки.")
    else:
        await callback.message.answer("📷 Пожалуйста, отправьте скриншот для проверки.")
    
    await state.set_state(LinkPromotionStates.performing_task)


@tasks.message(F.forward_from, LinkPromotionStates.performing_task)
async def check_forwarded_message(message: types.Message, bot: Bot, state: FSMContext):
    user_id = message.from_user.id
    forwarded_from = message.forward_from

    if not forwarded_from:
        await message.answer("❌ Это сообщение не является пересланным от бота.")
        return

    data = await state.get_data()
    task_id = data.get("task_id")
    target_link = data.get("target_link")
    task_type = data.get("task_type")

    if not task_id or not target_link or task_type != 0:
        await message.answer("❌ Данные задания не найдены или тип задания не соответствует. Попробуйте начать заново.")
        await state.clear()
        return

    task = await DB.get_task_by_id(task_id)
    if not task:
        await message.answer("❌ Задание не найдено в базе данных.")
        await state.clear()
        return

    try:
        bot_username = target_link.split("/")[-1].split("?")[0]
    except Exception as e:
        await message.answer("❌ Некорректная ссылка на бота.")
        return

    await DB.increment_statistics(1, 'links')
    await DB.increment_statistics(2, 'links')
    await DB.increment_statistics(1, 'all_taasks')
    await DB.increment_statistics(2, 'all_taasks')

    if forwarded_from.username == bot_username:
        try:
            await DB.add_completed_task(user_id, task_id, task[2], all_price['link'], task[1], status=0)
            await DB.add_balance(user_id, int(all_price['link']))
            await update_dayly_and_weekly_tasks_statics(user_id)
            await message.answer(
                f"✅ Задание выполнено! Ваш баланс пополнен на {all_price['link']} MITcoin.\n\n"
                f"🔗 Ссылка: {target_link}\n"
                f"📝 Описание: Переход по ссылке",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="Дальше ⏭️", callback_data="work_link_auto")]]
                ))
            await state.clear()
        except Exception as e:
            print(f"Ошибка при добавлении выполненного задания: {e}")
            await message.answer("❌ Произошла ошибка при обработке задания. Попробуйте позже.")
    else:
        await message.answer("❌ Пересланное сообщение не соответствует заданию.")

@tasks.message(F.photo, LinkPromotionStates.performing_task)
async def handle_screenshot(message: types.Message, state: FSMContext, bot: Bot):
    user_id = message.from_user.id
    data = await state.get_data()
    task_id = data.get('task_id')
    target_link = data.get('target_link')
    task_type = data.get('task_type')

    if task_type != 1:
        await message.answer("❌ Это задание требует автоматической проверки.")
        return

    if not message.photo:
        await message.answer("❌ Пожалуйста, отправьте скриншот.")
        return

    screenshot_id = message.photo[-1].file_id

    task = await DB.get_task_by_id(task_id)
    if not task:
        await message.answer("❌ Задание не найдено в базе данных.")
        return

    description = str(task[6]).split("|")[1] if task[6] else "Описание отсутствует"

    await DB.add_pending_reaction_task(
        user_id=user_id,
        task_id=task_id,
        target_id=target_link,
        post_id = 0,
        reaction = 0,
        screenshot=screenshot_id
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='⏭ Далее', callback_data='work_link_manual')],
        [InlineKeyboardButton(text='🔙 Назад', callback_data='work_menu')]
    ])
    await message.answer("✅ Скриншот отправлен на проверку. Ожидайте подтверждения.", reply_markup=kb)

    builder = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"confirm_link_{task_id}_{user_id}")],
        [InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_link_{task_id}_{user_id}")]
    ])

    await bot.send_photo(
        CHECK_CHAT_ID,
        photo=screenshot_id,
        caption=(
            f"#ссылка\n"
            f"📝 <b>Задание на переход по ссылке</b>\n\n"
            f"👤 Пользователь: @{message.from_user.username} (ID: {user_id})\n"
            f"🔗 Ссылка: {target_link}\n"
            f"📝 Условие: {description}\n"
            f"💸 Награда: {all_price['link']} MITcoin\n"
            f"🆔 ID задания: {task_id}\n\n"
            f"Проверьте выполнение задания:"
        ),
        reply_markup=builder
    )

    await state.clear()

@tasks.callback_query(F.data.startswith('confirm_link_'))
async def confirm_comment_handler(callback: types.CallbackQuery, bot: Bot, state: FSMContext):
    parts = callback.data.split('_')
    if len(parts) < 3:
        await callback.answer("Некорректный формат callback данных.")
        return

    task_id = int(parts[-2])
    user_id = int(parts[-1])

    pending_task = await DB.get_pending_reaction_task(task_id, user_id)
    if not pending_task:
        await callback.answer("Задание не найдено.")
        return

    pending_id, user_id, task_id, target_id, _, _, screenshot, status = pending_task

    await DB.add_completed_task(
        user_id=user_id,
        task_id=task_id,
        target_id=target_id,
        task_sum=all_price['link'],
        owner_id=user_id,
        status=0,
        other=0
    )

    await DB.delete_pending_reaction_task(task_id, user_id)
    await DB.add_balance(amount=1000, user_id=user_id)

    task = await DB.get_task_by_id(task_id)
    if task:
        new_amount = task[3] - 1
        await DB.update_task_amount2(task_id, new_amount)

    await bot.send_message(
        user_id,
        f"🎉 <b>Ваше задание на переход по ссылке подтверждено!</b>\n\n"
        f"💸 Вам начислено: {all_price['link']} MITcoin\n"
        f"🔗 Ссылка: {target_id}\n"
        f"🆔 ID задания: {task_id}"
    )
    
    creator_id = user_id
    # await bot.send_message(
    #     creator_id,
    #     f"🎉 <b>Ваше задание на переход по ссылке выполнено!</b>\n\n"
    #     f"👤 Пользователь: @{callback.from_user.username} (ID: {user_id})\n" 
    #     f"🔗 Ссылка: {target_id}\n"
    #     f"🆔 ID задания: {task_id}"
    # )
    
    await update_dayly_and_weekly_tasks_statics(user_id)
    await DB.increment_statistics(1, 'links')
    await DB.increment_statistics(2, 'links')
    await DB.increment_statistics(1, 'all_taasks')
    await DB.increment_statistics(2, 'all_taasks')

    await callback.answer("✅ Задание подтверждено.")

@tasks.callback_query(F.data.startswith('reject_link_'))
async def reject_comment_handler(callback: types.CallbackQuery, bot: Bot, state: FSMContext):
    parts = callback.data.split('_')
    if len(parts) < 3:
        await callback.answer("Некорректный формат callback данных.")
        return

    task_id = int(parts[-2])
    user_id = int(parts[-1])

    pending_task = await DB.get_pending_reaction_task(task_id, user_id)
    if not pending_task:
        await callback.answer("Задание не найдено.")
        return

    pending_id, user_id, task_id, target_id, _, _, screenshot, status = pending_task

    await DB.add_failed_task(user_id, task_id)
    await DB.delete_pending_reaction_task(task_id, user_id)

    await bot.send_message(
        user_id,
        f"❌ <b>Ваше задание на переход по ссылке отклонено.</b>\n\n"
        f"🔗 Ссылка: {target_id}\n"
        f"🆔 ID задания: {task_id}\n\n"
        f"Пожалуйста, убедитесь, что вы выполнили задание правильно."
    )

    await bot.send_message(
        CHECK_CHAT_ID,
        f"❌ <b>Задание на переход по ссылке отклонено.</b>\n\n"
        f"👤 Пользователь: @{callback.from_user.username} (ID: {user_id})\n"
        f"🔗 Ссылка: {target_id}\n"
        f"🆔 ID задания: {task_id}"
    )

    await callback.answer("❌ Задание отклонено.")

















