from .tasks import *

@tasks.callback_query(F.data == 'comment_pr_button')
async def like_post_handler(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    user_id = callback.from_user.id
    user = await DB.select_user(user_id)
    balance = user['balance']
    if balance is None:
        balance = 0
    maxcount = balance // all_price["comment"]
    await callback.message.edit_text(f'''
💬 Комментарий под постом

💵 {all_price["comment"]} MITcoin = 1 комментарий

баланс: <b>{balance}</b>; Всего вы можете купить <b>{maxcount}</b> комментариев

<b>Сколько нужно комментариев</b>❓

<em>Что бы создать задание на вашем балансе должно быть не менее {all_price["comment"]} MITcoin</em>
    ''', reply_markup=pr_menu_canc())
    await state.set_state(CommentPromotionStates.awaiting_comments_count)

@tasks.message(CommentPromotionStates.awaiting_comments_count)
async def like_post2(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    user = await DB.select_user(user_id)
    balance = user['balance']
    if balance is None:
        balance = 0
    try:
        uscount = int(message.text.strip())
        if uscount >= 1:
            price = all_price["comment"] * uscount
            await state.update_data(uscount=uscount, price=price, balance=balance)
            if balance >= price:
                builder = InlineKeyboardBuilder()
                builder.add(InlineKeyboardButton(text="✅ Продолжить", callback_data="comment_post_confirm"))
                builder.add(InlineKeyboardButton(text="🔙 Назад", callback_data="pr_menu_cancel"))
                await message.answer(
                    f'👍 <b>Количество: {uscount}</b>\n💰<b> Стоимость - {price} MITcoin</b>\n\n<em>Нажмите кнопку <b>Продолжить</b> или введите другое число...</em>',
                    reply_markup=builder.as_markup())
            else:
                builder = InlineKeyboardBuilder()
                builder.add(InlineKeyboardButton(text="Пополнить баланс", callback_data="cancel_all"))
                builder.add(InlineKeyboardButton(text="🔙 Назад", callback_data="pr_menu_cancel"))
                await message.answer(
                    f'😢 <b>Недостаточно средств на балансе</b> \nВаш баланс: {balance} MITcoin\n<em>Пополните баланс или измените желаемое количество комментариев...</em>',
                    reply_markup=builder.as_markup())
        else:
            await message.answer('<b>❗Минимальная покупка от 1 комментария!</b>\nВведи корректное число...',
                                 reply_markup=pr_menu_canc())
    except ValueError:
        await message.answer('<b>Ошибка ввода</b>\nПопробуй ввести целое число...', reply_markup=pr_menu_canc())

@tasks.callback_query(F.data == 'comment_post_confirm')
async def like_post3(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    uscount = data.get('uscount')
    price = data.get('price')
    balance = data.get('balance')
    await state.clear()
    await callback.message.edit_text(f'''
👍 Теперь перешлите пост, под которым нужно набрать комментарии. Я жду...
    ''', reply_markup=pr_menu_canc())
    await state.set_state(CommentPromotionStates.awaiting_post_for_comments)
    await state.update_data(uscount=uscount, price=price, balance=balance)

@tasks.message(CommentPromotionStates.awaiting_post_for_comments)
async def like_post4(message: types.Message, state: FSMContext, bot: Bot):
    async with task_creation_lock:
        user_id = message.from_user.id
        data = await state.get_data()
        amount = data.get('uscount')
        price = data.get('price')
        balance = data.get('balance')

        if message.forward_from_chat:
            message_id = message.forward_from_message_id
            chat_id = message.forward_from_chat.id
            target_id_code = f'{chat_id}:{message_id}'

            try:
                await bot.forward_message(chat_id=user_id, from_chat_id=chat_id, message_id=message_id)
                task_type = 4  # Тип задания на комменты
                new_balance = balance - price
                await DB.update_balance(user_id, balance=new_balance)
                await DB.add_task(user_id=user_id, target_id=target_id_code, amount=amount, task_type=task_type)

                builder = InlineKeyboardBuilder()
                builder.add(InlineKeyboardButton(text="🔙 Вернуться в меню", callback_data="back_menu"))
                await message.answer(
                    "🥳 Задание на комментарии создано! Оно будет размещено в разделе <b>Заработать</b>\n\nКогда задание будет выполнено - Вы получите уведомление 😉",
                    reply_markup=builder.as_markup())
                
                await DB.add_transaction(
                    user_id=message.from_user.id,
                    amount=price, 
                    description="создание задания на комментарий",
                    additional_info=None
                )

                await bot.send_message(TASKS_CHAT_ID, f'''
🔔 СОЗДАНО НОВОЕ ЗАДАНИЕ 🔔
⭕️ Тип задания: 💬 Комментарий
💸 Цена: {all_price["comment"]}
👥 Количество выполнений: {amount}
💰 Стоимость: {amount * all_price["comment"]} 
''')
                await state.clear()
            except:
                bot_username = (await bot.get_me()).username
                invite_link = f"http://t.me/{bot_username}?startchannel&admin=invite_users+manage_chat"
                add_button = InlineKeyboardButton(text="➕ Добавить бота в канал", url=invite_link)
                add_button1 = InlineKeyboardButton(text="❌ Отмена", callback_data='pr_menu_cancel')
                keyboard = InlineKeyboardMarkup(inline_keyboard=[[add_button], [add_button1]])
                await message.answer(
                    '😶 Добавьте бота в канал с правами админа при помощи кнопки снизу и перешлите пост заново...',
                    reply_markup=keyboard)


















@tasks.callback_query(F.data == 'work_comment')
async def works_like_handler(callback: types.CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    all_tasks = await DB.select_like_comment()  # Получаем список всех заданий на комментарии

    if all_tasks:
        # Фильтруем задания, исключая выполненные, проваленные и находящиеся на проверке
        available_tasks = [
            task for task in all_tasks
            if not await DB.is_task_completed(user_id, task[0])  # Исключаем выполненные
            and not await DB.is_task_failed(user_id, task[0])  # Исключаем проваленные
            and not await DB.is_task_pending(user_id, task[0])  # Исключаем задания на проверке
        ]
        
        if not available_tasks:
            await callback.message.edit_text(
                "На данный момент доступных заданий на комментарии нет, возвращайся позже 😉",
                reply_markup=back_work_menu_kb(user_id)
            )
            return 
        
        # Выбираем случайное задание из списка доступных
        random_task = random.choice(available_tasks)
        task_id, target_id, amount = random_task[0], random_task[2], random_task[3]
        chat_id, message_id = map(int, target_id.split(":"))
        
        try:
            # Пересылаем пост пользователю
            await bot.forward_message(chat_id=user_id, from_chat_id=chat_id, message_id=message_id)
            await callback.message.answer_sticker(
                'CAACAgIAAxkBAAENFeZnLS0EwvRiToR0f5njwCdjbSmWWwACTgEAAhZCawpt1RThO2pwgjYE')
            await asyncio.sleep(3)

            # Создаем клавиатуру с кнопкой "Проверить"
            builder = InlineKeyboardBuilder()
            builder.add(InlineKeyboardButton(text="Проверить ✅", callback_data=f"comment_{task_id}"))
            builder.add(InlineKeyboardButton(text="✋Ручная проверка", callback_data=f"2comment_{task_id}"))
            builder.add(InlineKeyboardButton(text="⏭ Пропустить", callback_data=f"skip_task_{task_id}"))
            builder.add(InlineKeyboardButton(text="Репорт ⚠️", callback_data=f"report_comment_{task_id}"))
            builder.add(InlineKeyboardButton(text="🔙 Назад", callback_data="work_menu"))

            builder.adjust(2, 2, 1)

            await callback.message.answer(
                "💬 Напишите комментарий под постом и нажмите кнопку <b>Проверить</b>, чтобы подтвердить выполнение задания.\n\n"
                "<em>Комментарий не должен быть эмодзи, стикером, GIF или другим не текстовым содержимым.</em>\n"
                "<em>Комментарий должен содержать осмысленный текст, соответствующий теме поста.</em>\n"
                "<em>Комментарии, не соответствующие этим критериям, могут быть отклонены при проверке.</em>\n\n",
                reply_markup=builder.as_markup()
            )
        except Exception as e:
            print(f"Ошибка: {e}")
            await callback.message.edit_text(
                "Произошла ошибка при обработке задания. Попробуйте позже.",
                reply_markup=back_work_menu_kb(user_id)
            )
    else:
        await callback.message.edit_text(
            "На данный момент заданий на комментарии нет, возвращайся позже 😉",
            reply_markup=back_work_menu_kb(user_id)
        )

@tasks.callback_query(F.data.startswith('comment_'))
async def check_like_handler(callback: types.CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    task_id = int(callback.data.split('_')[-1])  # Извлекаем ID задания из callback_data

    # Получаем данные задания
    task = await DB.get_task_by_id(task_id)
    if not task:
        await callback.answer("Задание не найдено.")
        return

    target_id = task[2]
    chat_id, message_id = map(int, target_id.split(":"))

    # Проверяем, поставил ли пользователь лайк
    like_detected = None #await comment(user_id, chat_id, message_id)

    if like_detected:
        # # Лайк обнаружен
        await DB.increment_statistics(1, 'comments')
        await DB.increment_statistics(2, 'comments')
        await DB.increment_statistics(1, 'all_taasks')
        await DB.increment_statistics(2, 'all_taasks')

        await callback.message.answer(
            f"👍 <b>Комментарий засчитан! +{all_price["comment"]} MITcoin</b>\n\nНажмите кнопку для перехода к следующему заданию.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Дальше ⏭️", callback_data="work_comment")]]
            )
        ) 

        await update_dayly_and_weekly_tasks_statics(user_id)
        await DB.update_task_amount(task_id)
        updated_task = await DB.get_task_by_id(task_id)
        await DB.add_completed_task(user_id, task_id, target_id, all_price["comment"], task[1], status=0)
        await DB.add_balance(amount=all_price["comment"], user_id=user_id)

        if updated_task[3] == 0:
            delete_task = await DB.get_task_by_id(task_id)
            creator_id = delete_task[1]
            await DB.delete_task(task_id)
            await bot.send_message(creator_id, f"🎉 Одно из ваших заданий на комментарий было успешно выполнено!",
                                   reply_markup=back_menu_kb(user_id))
    else:
        # Лайк не обнаружен
        await callback.answer("❌ Комментарий не был написан. Попробуйте ещё раз.", show_alert=True)

# Обработчик нажатия на кнопку "2comment_"
@tasks.callback_query(F.data.startswith('2comment_'))
async def _(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    task_id = int(callback.data.split('_')[-1])  # Извлекаем ID задания из callback_data

    # Получаем данные задания
    task = await DB.get_task_by_id(task_id)
    if not task:
        await callback.answer("Задание не найдено.")
        return

    target_id = task[2]
    chat_id, message_id = map(int, target_id.split(":"))
    await callback.message.answer(
        '😞 Не получилось проверить комментарий автоматически?\n'
        '✌️ Нам жаль, что вы столкнулись с этой проблемой, а пока мы решаем её, вы можете попробовать ручную проверку.\n\n'
        '❗️ Чтобы сделать это, отправьте сюда скриншот того, как вы выполнили задание. Мы заметим это и в скором времени начислим вам награду!'
    )
    await state.set_state(CommentProof.waiting_for_screenshot)
    await state.update_data(task_id=task_id, target_id=target_id, chat_id=chat_id, message_id=message_id)

# Обработчик скриншота
@tasks.message(CommentProof.waiting_for_screenshot)
async def handle_screenshot(message: types.Message, state: FSMContext, bot: Bot):
    user_id = message.from_user.id
    data = await state.get_data()
    task_id = data.get('task_id')
    target_id = data.get('target_id')
    chat_id = data.get('chat_id')
    message_id = data.get('message_id')

    if not message.photo:
        await message.answer("❌ Пожалуйста, отправьте скриншот.")
        return

    screenshot_id = message.photo[-1].file_id  # Берём самое большое изображение

    # Добавляем задание в таблицу ожидания подтверждения
    await DB.add_pending_reaction_task( 
        user_id=user_id,
        task_id=task_id,
        target_id=target_id,
        post_id=chat_id,
        reaction=message_id,
        screenshot=screenshot_id
    )

    # Уведомляем пользователя
    kb = InlineKeyboardBuilder()
    kb.button(text='⏭ Далее', callback_data='work_comment')
    kb.button(text='🔙 Назад', callback_data='work_menu')
    await message.answer("✅ Скриншот отправлен на проверку. Ожидайте подтверждения.", reply_markup=kb.as_markup())

    chat: Chat = await bot.get_chat(chat_id)

    # Отправляем админу задание на проверку
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"confirm_comment_{task_id}_{user_id}"))
    builder.add(InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_comment_{task_id}_{user_id}"))
    builder.add(InlineKeyboardButton(text="🔗 Перейти к посту", url=f"https://t.me/{chat.username}/{message_id}"))
    builder.adjust(1)

    sent_message = await bot.send_photo(
        CHECK_CHAT_ID,
        photo=screenshot_id,
        caption=(
            f"#комментарий\n"
            f"📝 <b>Задание на комментарий</b>\n\n"
            f"👤 Пользователь: @{message.from_user.username} (ID: {user_id})\n"
            f"📌 Пост: https://t.me/{chat.username}/{message_id}\n"
            f"🆔 ID задания: {task_id}\n\n"
            f"Проверьте выполнение задания:"
        ),
        reply_markup=builder.as_markup()
    )

    # Сохраняем ID сообщения в state
    await state.update_data(admin_message_id=sent_message.message_id)

    # Запускаем фоновую задачу для автоматического подтверждения через 24 часа
    asyncio.create_task(auto_confirm_comment_task(task_id, user_id, bot, message.from_user.username, state))

    await state.clear()

# Функция для автоматического подтверждения через 24 часа
async def auto_confirm_comment_task(task_id, user_id, bot, username, state):
    await asyncio.sleep(24 * 3600)  # Ждем 24 часа
    pending_task = await DB.get_pending_reaction_task(task_id, user_id)
    if pending_task:
        await confirm_comment_handler(task_id, user_id, bot, username, state)

# Обработчик подтверждения задания админом
@tasks.callback_query(F.data.startswith('confirm_comment_'))
async def confirm_comment_handler(callback: types.CallbackQuery, bot: Bot, state: FSMContext):
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
    pending_id, user_id, task_id, target_id, chat_id, message_id, screenshot, status = pending_task

    # Добавляем задание в таблицу completed_tasks
    await DB.add_completed_task(
        user_id=user_id,
        task_id=task_id,
        target_id=target_id,
        task_sum=all_price["comment"],
        owner_id=user_id,
        status=0,
        other=0
    )

    # Удаляем задание из таблицы ожидания
    await DB.delete_pending_reaction_task(task_id, user_id)

    # Начисляем баланс пользователю
    await DB.add_balance(amount=all_price["comment"], user_id=user_id)

    task = await DB.get_task_by_id(task_id)
    if task:
        new_amount = task[3] - 1  # task[3] — это текущее количество выполнений
        await DB.update_task_amount2(task_id, new_amount)

    chat: Chat = await bot.get_chat(chat_id)

    # Уведомляем пользователя
    await bot.send_message(
        user_id,
        f"🎉 <b>Ваше задание на комментарий подтверждено!</b>\n\n"
        f"💸 Вам начислено: {all_price["comment"]} MITcoin\n"
        f"📌 Пост: https://t.me/{chat.username}/{message_id}\n"
        f"🆔 ID задания: {task_id}"
    )

    await update_dayly_and_weekly_tasks_statics(user_id)

    # Уведомляем создателя задания
    creator_id = user_id
    # await bot.send_message(
    #     creator_id,
    #     f"🎉 <b>Ваше задание на комментарий выполнено!</b>\n\n"
    #     f"👤 Пользователь: @{callback.from_user.username} (ID: {user_id})\n" 
    #     f"📌 Пост: https://t.me/{chat.username}/{message_id}\n"
    #     f"🆔 ID задания: {task_id}"
    # )

    # Удаляем сообщение с заданием
    data = await state.get_data()
    admin_message_id = data.get('admin_message_id')
    if admin_message_id:
        await bot.delete_message(CHECK_CHAT_ID, admin_message_id)

    await DB.increment_statistics(1, 'comments')
    await DB.increment_statistics(2, 'comments')
    await DB.increment_statistics(1, 'all_taasks')
    await DB.increment_statistics(2, 'all_taasks')

    await callback.answer("✅ Задание подтверждено.")

# Обработчик отклонения задания админом
@tasks.callback_query(F.data.startswith('reject_comment_'))
async def reject_comment_handler(callback: types.CallbackQuery, bot: Bot, state: FSMContext):
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
    pending_id, user_id, task_id, target_id, chat_id, message_id, screenshot, status = pending_task

    # Добавляем задание в список проваленных для пользователя
    await DB.add_failed_task(user_id, task_id)

    # Удаляем задание из таблицы ожидания
    await DB.delete_pending_reaction_task(task_id, user_id)

    chat: Chat = await bot.get_chat(chat_id)

    # Уведомляем пользователя
    await bot.send_message(
        user_id,
        f"❌ <b>Ваше задание на комментарий отклонено.</b>\n\n"
        f"📌 Пост: https://t.me/{chat.username}/{message_id}\n"
        f"🆔 ID задания: {task_id}\n\n"
        f"Пожалуйста, убедитесь, что вы выполнили задание правильно."
    )

    # Уведомляем админа
    await bot.send_message(
        CHECK_CHAT_ID,
        f"❌ <b>Задание на комментарий отклонено.</b>\n\n"
        f"👤 Пользователь: @{callback.from_user.username} (ID: {user_id})\n"
        f"📌 Пост: https://t.me/{chat.username}/{message_id}\n"
        f"🆔 ID задания: {task_id}"
    )

    # Удаляем сообщение с заданием
    data = await state.get_data()
    admin_message_id = data.get('admin_message_id')
    if admin_message_id:
        await bot.delete_message(CHECK_CHAT_ID, admin_message_id)

    await callback.answer("❌ Задание отклонено.")








@tasks.callback_query(F.data == 'work_comment')
async def works_like_handler(callback: types.CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    all_tasks = await DB.select_like_comment()

    if all_tasks:
        available_tasks = [
            task for task in all_tasks
            if not await DB.is_task_completed(user_id, task[0])
            and not await DB.is_task_failed(user_id, task[0])
            and not await DB.is_task_pending(user_id, task[0])
        ]
        
        if not available_tasks:
            await callback.message.edit_text(
                "На данный момент доступных заданий на комментарии нет, возвращайся позже 😉",
                reply_markup=back_work_menu_kb(user_id)
            )
            return 
        
        random_task = random.choice(available_tasks)
        task_id, target_id, amount = random_task[0], random_task[2], random_task[3]
        chat_id, message_id = map(int, target_id.split(":"))
        
        try:
            await bot.forward_message(chat_id=user_id, from_chat_id=chat_id, message_id=message_id)
            await callback.message.answer_sticker(
                'CAACAgIAAxkBAAENFeZnLS0EwvRiToR0f5njwCdjbSmWWwACTgEAAhZCawpt1RThO2pwgjYE')
            await asyncio.sleep(3)

            builder = InlineKeyboardBuilder()
            builder.add(InlineKeyboardButton(text="Проверить ✅", callback_data=f"comment_{task_id}"))
            builder.add(InlineKeyboardButton(text="✋Ручная проверка", callback_data=f"2comment_{task_id}"))
            builder.add(InlineKeyboardButton(text="⏭ Пропустить", callback_data=f"skip_task_{task_id}"))
            builder.add(InlineKeyboardButton(text="Репорт ⚠️", callback_data=f"report_comment_{task_id}"))
            builder.add(InlineKeyboardButton(text="🔙 Назад", callback_data="work_menu"))
            builder.adjust(2, 2, 1)

            await callback.message.answer(
                "💬 Напишите комментарий под постом и нажмите кнопку <b>Проверить</b>, чтобы подтвердить выполнение задания.\n\n"
                "<em>Комментарий не должен быть эмодзи, стикером, GIF или другим не текстовым содержимым.</em>\n"
                "<em>Комментарий должен содержать осмысленный текст, соответствующий теме поста.</em>\n"
                "<em>Комментарии, не соответствующие этим критериям, могут быть отклонены при проверке.</em>\n\n",
                reply_markup=builder.as_markup()
            )
        except Exception as e:
            print(f"Ошибка: {e}")
            await callback.message.edit_text(
                "Произошла ошибка при обработке задания. Попробуйте позже.",
                reply_markup=back_work_menu_kb(user_id))
    else:
        await callback.message.edit_text(
            "На данный момент заданий на комментарии нет, возвращайся позже 😉",
            reply_markup=back_work_menu_kb(user_id))
        







@tasks.callback_query(F.data == 'work_comment')
async def works_like_handler(callback: types.CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    all_tasks = await DB.select_like_comment()  # Получаем список всех заданий на комментарии

    if all_tasks:
        # Фильтруем задания, исключая выполненные, проваленные и находящиеся на проверке
        available_tasks = [
            task for task in all_tasks
            if not await DB.is_task_completed(user_id, task[0])  # Исключаем выполненные
            and not await DB.is_task_failed(user_id, task[0])  # Исключаем проваленные
            and not await DB.is_task_pending(user_id, task[0])  # Исключаем задания на проверке
        ]
        
        if not available_tasks:
            await callback.message.edit_text(
                "На данный момент доступных заданий на комментарии нет, возвращайся позже 😉",
                reply_markup=back_work_menu_kb(user_id)
            )
            return 
        
        # Выбираем случайное задание из списка доступных
        random_task = random.choice(available_tasks)
        task_id, target_id, amount = random_task[0], random_task[2], random_task[3]
        chat_id, message_id = map(int, target_id.split(":"))
        
        try:
            # Пересылаем пост пользователю
            await bot.forward_message(chat_id=user_id, from_chat_id=chat_id, message_id=message_id)
            await callback.message.answer_sticker(
                'CAACAgIAAxkBAAENFeZnLS0EwvRiToR0f5njwCdjbSmWWwACTgEAAhZCawpt1RThO2pwgjYE')
            await asyncio.sleep(3)

            # Создаем клавиатуру с кнопкой "Проверить"
            builder = InlineKeyboardBuilder()
            builder.add(InlineKeyboardButton(text="Проверить ✅", callback_data=f"comment_{task_id}"))
            builder.add(InlineKeyboardButton(text="✋Ручная проверка", callback_data=f"2comment_{task_id}"))
            builder.add(InlineKeyboardButton(text="⏭ Пропустить", callback_data=f"skip_task_{task_id}"))
            builder.add(InlineKeyboardButton(text="Репорт ⚠️", callback_data=f"report_comment_{task_id}"))
            builder.add(InlineKeyboardButton(text="🔙 Назад", callback_data="work_menu"))

            builder.adjust(2, 2, 1)

            await callback.message.answer(
                "💬 Напишите комментарий под постом и нажмите кнопку <b>Проверить</b>, чтобы подтвердить выполнение задания.\n"
                "<em>Комментарий не должен быть эмодзи, стикером, GIF или другим не текстовым содержимым.</em>\n"
                "<em>Комментарий должен содержать осмысленный текст, соответствующий теме поста.</em>\n"
                "<em>Комментарии, не соответствующие этим критериям, могут быть отклонены при проверке.</em>\n\n",
                reply_markup=builder.as_markup()
            )
        except Exception as e:
            print(f"Ошибка: {e}")
            await callback.message.edit_text(
                "Произошла ошибка при обработке задания. Попробуйте позже.",
                reply_markup=back_work_menu_kb(user_id)
            )
    else:
        await callback.message.edit_text(
            "На данный момент заданий на комментарии нет, возвращайся позже 😉",
            reply_markup=back_work_menu_kb(user_id)
        )

@tasks.callback_query(F.data.startswith('comment_'))
async def check_like_handler(callback: types.CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    task_id = int(callback.data.split('_')[-1])  # Извлекаем ID задания из callback_data

    # Получаем данные задания
    task = await DB.get_task_by_id(task_id)
    if not task:
        await callback.answer("Задание не найдено.")
        return

    target_id = task[2]
    chat_id, message_id = map(int, target_id.split(":"))

    # Проверяем, поставил ли пользователь лайк
    like_detected = None #await comment(user_id, chat_id, message_id)

    if like_detected:
        # # Лайк обнаружен
        await DB.increment_statistics(1, 'comments')
        await DB.increment_statistics(2, 'comments')
        await DB.increment_statistics(1, 'all_taasks')
        await DB.increment_statistics(2, 'all_taasks')

        await callback.message.answer(
            f"👍 <b>Комментарий засчитан! +{all_price["comment"]} MITcoin</b>\n\nНажмите кнопку для перехода к следующему заданию.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Дальше ⏭️", callback_data="work_comment")]]
            )
        ) 

        await DB.update_task_amount(task_id)
        updated_task = await DB.get_task_by_id(task_id)
        await DB.add_completed_task(user_id, task_id, target_id, all_price["comment"], task[1], status=0)
        await DB.add_balance(amount=all_price["comment"], user_id=user_id)

        if updated_task[3] == 0:
            delete_task = await DB.get_task_by_id(task_id)
            creator_id = delete_task[1]
            await DB.delete_task(task_id)
            await bot.send_message(creator_id, f"🎉 Одно из ваших заданий на комментарий было успешно выполнено!",
                                   reply_markup=back_menu_kb(user_id))
    else:
        # Лайк не обнаружен
        await callback.answer("❌ Комментарий не был написан. Попробуйте ещё раз.", show_alert=True)

# Состояние для ожидания скриншота
class CommentProof(StatesGroup):
    waiting_for_screenshot =State()

# Обработчик нажатия на кнопку "2comment_"
@tasks.callback_query(F.data.startswith('2comment_'))
async def _(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    task_id = int(callback.data.split('_')[-1])  # Извлекаем ID задания из callback_data

    # Получаем данные задания
    task = await DB.get_task_by_id(task_id)
    if not task:
        await callback.answer("Задание не найдено.")
        return

    target_id = task[2]
    chat_id, message_id = map(int, target_id.split(":"))
    await callback.message.answer(
        '😞 Не получилось проверить комментарий автоматически?\n'
        '✌️ Нам жаль, что вы столкнулись с этой проблемой, а пока мы решаем её, вы можете попробовать ручную проверку.\n\n'
        '❗️ Чтобы сделать это, отправьте сюда скриншот того, как вы выполнили задание. Мы заметим это и в скором времени начислим вам награду')
    await state.set_state(CommentProof.waiting_for_screenshot)                                                                          
    await state.update_data(task_id=task_id, target_id=target_id, chat_id=chat_id, message_id=message_id)

# Обработчик скриншота
@tasks.message(CommentProof.waiting_for_screenshot)
async def handle_screenshot(message: types.Message, state: FSMContext, bot: Bot):
    user_id = message.from_user.id
    data = await state.get_data()
    task_id = data.get('task_id')
    target_id = data.get('target_id')
    chat_id = data.get('chat_id')
    message_id = data.get('message_id')

    if not message.photo:
        await message.answer("❌ Пожалуйста, отправьте скриншот.")
        return

    screenshot_id = message.photo[-1].file_id  # Берём самое большое изображение

    # Добавляем задание в таблицу ожидания подтверждения
    await DB.add_pending_reaction_task( 
        user_id=user_id,
        task_id=task_id,
        target_id=target_id,
        post_id=chat_id,
        reaction=message_id,
        screenshot=screenshot_id
    )

    # Уведомляем пользователя
    kb = InlineKeyboardBuilder()
    kb.button(text='⏭ Далее', callback_data='work_comment')
    kb.button(text='🔙 Назад', callback_data='work_menu')
    await message.answer("✅ Скриншот отправлен на проверку. Ожидайте подтверждения.", reply_markup=kb.as_markup())

    chat: Chat = await bot.get_chat(chat_id)

    # Отправляем админу задание на проверку
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"confirm_comment_{task_id}_{user_id}"))
    builder.add(InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_comment_{task_id}_{user_id}"))
    builder.add(InlineKeyboardButton(text="🔗 Перейти к посту", url=f"https://t.me/{chat.username}/{message_id}"))
    builder.adjust(1)

    sent_message = await bot.send_photo(
        CHECK_CHAT_ID,
        photo=screenshot_id,
        caption=(
            f"#комментарий\n"
            f"📝 <b>Задание на комментарий</b>\n\n"
            f"👤 Пользователь: @{message.from_user.username} (ID: {user_id})\n"
            f"📌 Пост: https://t.me/{chat.username}/{message_id}\n"
            f"🆔 ID задания: {task_id}\n\n"
            f"Проверьте выполнение задания:"
        ),
        reply_markup=builder.as_markup()
    )

    # Сохраняем ID сообщения в state
    await state.update_data(admin_message_id=sent_message.message_id)

    # Запускаем фоновую задачу для автоматического подтверждения через 24 часа
    asyncio.create_task(auto_confirm_comment_task(task_id, user_id, bot, message.from_user.username, state))

    await state.clear()

# Функция для автоматического подтверждения через 24 часа
async def auto_confirm_comment_task(task_id, user_id, bot, username, state):
    await asyncio.sleep(24 * 3600)  # Ждем 24 часа
    pending_task = await DB.get_pending_reaction_task(task_id, user_id)
    if pending_task:
        await confirm_comment_handler(task_id, user_id, bot, username, state)

# Обработчик подтверждения задания админом
@tasks.callback_query(F.data.startswith('confirm_comment_'))
async def confirm_comment_handler(callback: types.CallbackQuery, bot: Bot, state: FSMContext):
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
    pending_id, user_id, task_id, target_id, chat_id, message_id, screenshot, status = pending_task

    # Добавляем задание в таблицу completed_tasks
    await DB.add_completed_task(
        user_id=user_id,
        task_id=task_id,
        target_id=target_id,
        task_sum=all_price["comment"],
        owner_id=user_id,
        status=0,
        other=0
    )

    # Удаляем задание из таблицы ожидания
    await DB.delete_pending_reaction_task(task_id, user_id)

    # Начисляем баланс пользователю
    await DB.add_balance(amount=all_price["comment"], user_id=user_id)

    task = await DB.get_task_by_id(task_id)
    if task:
        new_amount = task[3] - 1  # task[3] — это текущее количество выполнений
        await DB.update_task_amount2(task_id, new_amount)

    chat: Chat = await bot.get_chat(chat_id)
    # Уведомляем пользователя
    await bot.send_message(
        user_id,
        f"🎉 <b>Ваше задание на комментарий подтверждено!</b>\n\n"
        f"💸 Вам начислено: {all_price["comment"]} MITcoin\n"
        f"📌 Пост: https://t.me/{chat.username}/{message_id}\n"
        f"🆔 ID задания: {task_id}"
    )

    # Уведомляем создателя задания
    creator_id = user_id
    await bot.send_message(
        creator_id,
        f"🎉 <b>Ваше задание на комментарий выполнено!</b>\n\n"
        f"👤 Пользователь: @{callback.from_user.username} (ID: {user_id})\n" 
        f"📌 Пост: https://t.me/{chat.username}/{message_id}\n"
        f"🆔 ID задания: {task_id}"
    )

    # Удаляем сообщение с заданием
    data = await state.get_data()
    admin_message_id = data.get('admin_message_id')
    if admin_message_id:
        await bot.delete_message(CHECK_CHAT_ID, admin_message_id)

    await DB.increment_statistics(1, 'comments')
    await DB.increment_statistics(2, 'comments')
    await DB.increment_statistics(1, 'all_taasks')
    await DB.increment_statistics(2, 'all_taasks')

    await callback.answer("✅ Задание подтверждено.")

# Обработчик отклонения задания админом
@tasks.callback_query(F.data.startswith('reject_comment_'))
async def reject_comment_handler(callback: types.CallbackQuery, bot: Bot, state: FSMContext):
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
    pending_id, user_id, task_id, target_id, chat_id, message_id, screenshot, status = pending_task

    # Добавляем задание в список проваленных для пользователя
    await DB.add_failed_task(user_id, task_id)

    # Удаляем задание из таблицы ожидания
    await DB.delete_pending_reaction_task(task_id, user_id)

    chat: Chat = await bot.get_chat(chat_id)

    # Уведомляем пользователя
    await bot.send_message(
        user_id,
        f"❌ <b>Ваше задание на комментарий отклонено.</b>\n\n"
        f"📌 Пост: https://t.me/{chat.username}/{message_id}\n"
        f"🆔 ID задания: {task_id}\n\n"
        f"Пожалуйста, убедитесь, что вы выполнили задание правильно."
    )

    # Уведомляем админа
    await bot.send_message(
        CHECK_CHAT_ID,
        f"❌ <b>Задание на комментарий отклонено.</b>\n\n"
        f"👤 Пользователь: @{callback.from_user.username} (ID: {user_id})\n"
        f"📌 Пост: https://t.me/{chat.username}/{message_id}\n"
        f"🆔 ID задания: {task_id}"
    )

    # Удаляем сообщение с заданием
    data = await state.get_data()
    admin_message_id = data.get('admin_message_id')
    if admin_message_id:
        await bot.delete_message(CHECK_CHAT_ID, admin_message_id)

    await callback.answer("❌ Задание отклонено.")