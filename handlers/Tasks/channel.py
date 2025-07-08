from .tasks import *

@tasks.message(ChannelPromotionStates.awaiting_subscribers_count)
async def pr_chanel2(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    user = await DB.select_user(user_id)
    balance = user['balance']
    if balance is None:
        balance = 0
    try:
        uscount = int(message.text.strip())
        if uscount >= 1:
            price = 1500 * uscount
            await state.update_data(uscount=uscount, price=price, balance=balance)
            if balance >= price:
                builder = InlineKeyboardBuilder()
                builder.add(InlineKeyboardButton(text="✅ Продолжить", callback_data="pr_chanel_confirm"))
                builder.add(InlineKeyboardButton(text="🔙 Назад", callback_data="pr_menu_cancel"))
                await message.answer(
                    f'👥 <b>Количество: {uscount}</b>\n💰<b> Стоимость - {price} MITcoin</b>\n\n<em>Нажмите кнопку <b>Продолжить</b> или введите другое число...</em>',
                    reply_markup=builder.as_markup())
            else:
                builder = InlineKeyboardBuilder()
                builder.add(InlineKeyboardButton(text="Пополнить баланс", callback_data="cancel_all"))
                builder.add(InlineKeyboardButton(text="🔙 Назад", callback_data="pr_menu_cancel"))
                builder.adjust(1)
                await message.answer(
                    f'😢 <b>Недостаточно средств на балансе</b> \nВаш баланс: {balance} MITcoin\n<em>Пополните баланс или измените желаемое количество подписок...</em>',
                    reply_markup=builder.as_markup())
        else:
            await message.answer('<b>❗Минимальная покупка от 1 подписчика!</b>\nВведи корректное число...',
                                 reply_markup=pr_menu_canc())
    except ValueError:
        await message.answer('<b>Ошибка ввода</b>\nПопробуй ввести целое число...', reply_markup=pr_menu_canc())


@tasks.callback_query(F.data == 'chanel_pr_button')
async def pr_chanel_handler(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    user_id = callback.from_user.id
    user = await DB.select_user(user_id)
    balance = user['balance']
    if balance is None:
        balance = 0
    maxcount = balance // 1500
    await callback.message.edit_text(f'''
📢 Реклама канала

💹 1500 MITcoin = 1 подписчик

баланс: {balance}; Всего вы можете купить {maxcount} подписчиков

<b>Сколько нужно подписчиков</b>❓

<em>Что бы создать задание на вашем балансе должно быть не менее 1500 MitCoin</em>
    ''', reply_markup=pr_menu_canc())
    await state.set_state(ChannelPromotionStates.awaiting_subscribers_count)

@tasks.callback_query(F.data == 'pr_chanel_confirm')
async def pr_chanel3(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    data = await state.get_data()
    uscount = data.get('uscount')
    price = data.get('price')
    balance = data.get('balance')

    from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, KeyboardButtonRequestChat
    from aiogram.enums import ChatType

    kb = ReplyKeyboardMarkup(
        keyboard=[[
            KeyboardButton(
                text="📢 Выбрать канал",
                request_chat=KeyboardButtonRequestChat(
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

    await callback.message.answer(
        "📢 Пожалуйста, выбери канал, в который добавлен бот и у него есть права администратора.",
        reply_markup=kb
    )

    await state.set_state(ChannelPromotionStates.awaiting_channel_selection)
    await state.update_data(uscount=uscount, price=price, balance=balance)

@tasks.message(ChannelPromotionStates.awaiting_channel_selection)
async def handle_channel_selection(message: types.Message, state: FSMContext, bot: Bot):
    if not message.chat_shared:
        await message.answer("❗ Пожалуйста, выбери канал с помощью кнопки ниже.")
        return

    chat_id = message.chat_shared.chat_id
    user_id = message.from_user.id
    data = await state.get_data()
    price = data.get('price')
    amount = data.get('uscount')

    try:
        chat = await bot.get_chat(chat_id)
        bot_info = await bot.get_me()
        member = await bot.get_chat_member(chat_id, bot_info.id)

        # 🔒 Бот не админ или не может приглашать
        if member.status != "administrator" or not member.can_invite_users:
            await state.update_data(pending_channel_id=chat_id)

            invite_link = f"https://t.me/{bot_info.username}?startchannel&admin=invite_users+manage_chat"
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="➕ Добавить в админы", url=invite_link)],
                [InlineKeyboardButton(text="🔄 Проверить", callback_data="check_admin_rights")],
                [InlineKeyboardButton(text="❌ Отмена", callback_data="back_menu")]
            ])

            await message.answer(
                f"😕 Бот найден в канале <b>{chat.title}</b>, но ему <u>не выданы админ-права</u> или <u>он не может приглашать пользователей</u>.\n\n"
                f"🔧 Пожалуйста, добавьте бота в админы и нажмите <b>Проверить</b>.",
                reply_markup=keyboard
            )
            return

    except Exception as e:
        print("Ошибка при проверке канала:", e)
        await message.answer("❌ Ошибка при проверке канала. Убедитесь, что бот добавлен в канал с правами администратора.")
        return

    # ✅ Всё хорошо — создаём задание
    await DB.add_balance(user_id, -price)
    await DB.add_transaction(user_id=user_id, amount=price, description="создание задания на подписки", additional_info=None)
    task_id = await DB.add_task(user_id=user_id, target_id=chat_id, amount=amount, task_type=1)

    await message.answer(
        f"✅ Задание на канал <b>{chat.title}</b> создано успешно!",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Вернуться в меню", callback_data="back_menu")]
        ])
    )

    bot_username = (await bot.get_me()).username
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🎯 Выполнить задание", 
            url=f"https://t.me/{bot_username}?start=channel_{task_id}"
        )]
    ])

    await bot.send_message(
        TASKS_CHAT_ID,
        f'''
🔔 СОЗДАНО НОВОЕ ЗАДАНИЕ 🔔
⭕️ Тип задания: 📢 Канал
💬 Канал: {chat.title}
💸 Цена: {price // amount}
👥 Кол-во выполнений: {amount}
💰 Стоимость: {price}
    ''',
        reply_markup=keyboard
    )

@tasks.callback_query(F.data == "check_admin_rights")
async def check_admin_rights(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    await callback.answer()
    data = await state.get_data()
    user_id = callback.from_user.id
    chat_id = data.get("pending_channel_id")
    price = data.get('price')
    amount = data.get('uscount')

    try:
        chat = await bot.get_chat(chat_id)
        bot_info = await bot.get_me()
        member = await bot.get_chat_member(chat_id, bot_info.id)

        if member.status != "administrator" or not member.can_invite_users:
            await callback.message.edit_text(
                f"⛔ Боту по-прежнему не выданы нужные права в канале <b>{chat.title}</b>.\n\n"
                f"🔧 Убедитесь, что он <b>админ</b> и может <b>приглашать пользователей</b>.",
                reply_markup=callback.message.reply_markup
            )
            return

        # ✅ Всё ок — создаём задание
        await DB.add_balance(user_id, -price)
        await DB.add_transaction(user_id=user_id, amount=price, description="создание задания на подписки", additional_info=None)
        task_id = await DB.add_task(user_id=user_id, target_id=chat_id, amount=amount, task_type=1)

        await callback.message.edit_text(
            f"✅ Задание на канал <b>{chat.title}</b> создано успешно!",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Вернуться в меню", callback_data="back_menu")]
            ])
        )

        bot_username = (await bot.get_me()).username
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="🎯 Выполнить задание", 
                url=f"https://t.me/{bot_username}?start=channel_{task_id}"
            )]
        ])

        await bot.send_message(
            TASKS_CHAT_ID,
            f'''
        🔔 СОЗДАНО НОВОЕ ЗАДАНИЕ 🔔
        ⭕️ Тип задания: 📢 Канал
        💬 Канал: {chat.title}
        💸 Цена: {price // amount}
        👥 Кол-во выполнений: {amount}
        💰 Стоимость: {price}
        ''',
            reply_markup=keyboard
        )

    except Exception as e:
        print("Ошибка в check_admin_rights:", e)
        await callback.message.edit_text("⚠ Произошла ошибка при повторной проверке. Попробуйте позже.")


@tasks.message(ChannelPromotionStates.awaiting_members_count)
async def pr_chat2(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    user = await DB.select_user(user_id)
    balance = user['balance']
    if balance is None:
        balance = 0
    try:
        uscount = int(message.text.strip())
        if uscount >= 1:
            price = 1500 * uscount
            await state.update_data(uscount=uscount, price=price, balance=balance)
            if balance >= price:
                builder = InlineKeyboardBuilder()
                builder.add(InlineKeyboardButton(text="✅ Продолжить", callback_data="pr_chat_confirm"))
                builder.add(InlineKeyboardButton(text="🔙 Назад", callback_data="pr_menu_cancel"))
                await message.answer(
                    f'👥 <b>Количество: {uscount}</b>\n💰<b> Стоимость - {price} MITcoin</b>\n\n<em>Нажмите кнопку <b>Продолжить</b> или введите другое число...</em>',
                    reply_markup=builder.as_markup())
            else:
                builder = InlineKeyboardBuilder()
                builder.add(InlineKeyboardButton(text="Пополнить баланс", callback_data="cancel_all"))
                builder.add(InlineKeyboardButton(text="🔙 Назад", callback_data="pr_menu_cancel"))
                await message.answer(
                    f'😢 <b>Недостаточно средств на балансе</b> \nВаш баланс: {balance} MITcoin\n<em>Пополните баланс или измените желаемое количество участников...</em>',
                    reply_markup=builder.as_markup())
        else:
            await message.answer('<b>❗Минимальная покупка от 1 участника!</b>\nВведи корректное число...',
                                 reply_markup=pr_menu_canc())
    except ValueError:
        await message.answer('<b>Ошибка ввода</b>\nПопробуй ввести целое число...', reply_markup=pr_menu_canc())

@tasks.message(ChannelPromotionStates.awaiting_post_message)
async def pr_post4(message: types.Message, state: FSMContext, bot: Bot):
    async with task_creation_lock:  # Устанавливаем блокировку
        user_id = message.from_user.id
        data = await state.get_data()
        amount = data.get('uscount')
        price = data.get('price')
        balance = data.get('balance')
        if amount is None:
            amount = 1
        if balance is None:
            user = await DB.select_user(user_id)
            balance = user['balance']
        if price is None:
            price = 600

        if message.forward_from_chat:
            message_id = message.forward_from_message_id
            chat_id = message.forward_from_chat.id
            target_id_code = f'{chat_id}:{message_id}'

            try:
                await bot.forward_message(chat_id=user_id, from_chat_id=chat_id, message_id=message_id)
                task_type = 3  # пост
                new_balance = balance - price
                await DB.update_balance(user_id, balance=new_balance)
                await DB.add_task(user_id=user_id, target_id=target_id_code, amount=amount, task_type=task_type)

                builder = InlineKeyboardBuilder()
                builder.add(InlineKeyboardButton(text="🔙 Вернуться в меню", callback_data="my_works"))
                await message.answer(
                    "🥳 Задание создано! Оно будет размещено в разделе <b>Заработать</b>\n\nКогда задание будет выполнено - Вы получите уведомление 😉",
                    reply_markup=builder.as_markup())
                await DB.add_transaction(
                        user_id=user_id,
                        amount=price,
                        description="создание задания на просмотр",
                        additional_info= None
                    )
                
                
                await bot.send_message(TASKS_CHAT_ID, f'''
🔔 СОЗДАНО НОВОЕ ЗАДАНИЕ 🔔
⭕️ Тип задания: 👀 Пост
💸 Цена: 600
👥 Количество выполнений: {amount}
💰 Стоимость: {amount * 600} 
''')
                await state.clear()
            except:
                bot_username = (await bot.get_me()).username
                invite_link = f"http://t.me/{bot_username}?startchannel&admin=invite_users+manage_chat"
                add_button = InlineKeyboardButton(text="➕ Добавить бота в канал", url=invite_link)
                add_button1 = InlineKeyboardButton(text="❌ Отмена", callback_data='pr_menu_cancel')
                # Создаем клавиатуру и добавляем в нее кнопку
                keyboard = InlineKeyboardMarkup(inline_keyboard=[[add_button], [add_button1]])
                await message.answer(
                    '😶 Добавьте бота в канал с правами админа при помощи кнопки снизу и перешлите пост заново...',
                    reply_markup=keyboard)
                
semaphore = asyncio.Semaphore(2)  # Ограничение одновременных задач
@tasks.callback_query(F.data.startswith('work_chanel'))
async def taskss_handler(callback: types.CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    current_time = int(time.time())

    try:
        from handlers.client.client import get_available_tasks, task_cache
        all_tasks = task_cache.get('all_tasks', [])
        print(f'Все задания в кэше - {len(all_tasks)}')

        tasks = await get_available_tasks(user_id, all_tasks)
        print(f'Доступные задания для пользователя {user_id} - {len(tasks)}')

        if tasks:
            random.shuffle(tasks)
            keyboard = await generate_tasks_keyboard_chanel(tasks, bot, current_time)

            try:
                await callback.message.edit_text(
                    "📢 <b>Задания на каналы:</b>\n\n"
                    "🎢 Каналы в списке располагаются по количеству необходимых подписчиков\n\n"
                    "⚡<i>Запрещено отписываться от канала раньше чем через 7 дней, в случае нарушения возможен штраф!</i>\n\n"
                    f"📊 Доступно заданий: {len(tasks)}",
                    reply_markup=keyboard
                )
            except TelegramBadRequest as e:
                if "message is not modified" in str(e):
                    await callback.answer("Список заданий актуален")
                else:
                    raise
        else:
            await callback.message.edit_text(
                "На данный момент доступных заданий нет, возвращайся позже 😉",
                reply_markup=back_work_menu_kb(user_id)
            )
    except Exception as e:
        print(f"Ошибка в taskss_handler: {e}")
        markup = InlineKeyboardBuilder()
        markup.row(InlineKeyboardButton(
            text='🔄 Обновить',
            callback_data=f"work_chanel_{current_time}"
        ))
        await callback.message.edit_text(
            "Произошла ошибка при загрузке заданий. Попробуйте обновить страницу.",
            reply_markup=markup.as_markup()
        )


async def generate_tasks_keyboard_chanel(tasks, bot, timestamp=None):
    builder = InlineKeyboardBuilder()
    timestamp = timestamp or int(time.time())

    for task in tasks[:5]:
        try:
            chat = await bot.get_chat(task[2])
            button_text = f"{chat.title} | +1500"
            builder.row(InlineKeyboardButton(
                text=button_text,
                callback_data=f"chaneltask_{task[0]}_{timestamp}"
            ))
        except Exception as e:
            print(f"Ошибка при получении канала {task[2]}: {e}")
            continue

    builder.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data="work_menu"),
        InlineKeyboardButton(text="🔄 Обновить", callback_data=f"work_chanel_{timestamp}")
    )
    return builder.as_markup()


@tasks.callback_query(lambda c: c.data.startswith("chaneltask_"))
async def task_detail_handler(callback: types.CallbackQuery, bot: Bot):
    await callback.answer()
    try:
        parts = callback.data.split('_')
        task_id = int(parts[1])
        timestamp = parts[2] if len(parts) > 2 else None

        task = await DB.get_task_by_id(task_id)
        if not task:
            await callback.message.edit_text("Задание не найдено.")
            return

        amount = task[3]
        invite_link = await check_admin_and_get_invite_link_chanel(bot, task[2])
        chat = await bot.get_chat(task[2])

        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(text="Проверить 🔄️", callback_data=f"chanelcheck_{task_id}"))
        builder.add(InlineKeyboardButton(text="⏭ Пропустить", callback_data=f"skip_task_{task_id}"))
        builder.add(InlineKeyboardButton(text="Репорт ⚠️", callback_data=f"report_channel_{task_id}"))
        builder.add(InlineKeyboardButton(text="🔙 Назад", callback_data="work_chanel"))
        builder.adjust(1, 2, 1)

        task_info = (
            f"📢 {chat.title} | <i>{amount}</i>\n"
            f"<i>Подпишитесь на канал и нажмите кнопку -</i> <b>Проверить</b> 🔄️\n\n"
            f"{invite_link}"
        )
        await callback.message.edit_text(task_info, reply_markup=builder.as_markup())

    except Exception as e:
        print(f"Ошибка в task_detail_handler: {e}")
@tasks.callback_query(F.data.startswith('chanelcheck_'))
async def check_subscription_chanel(callback: types.CallbackQuery, bot: Bot):
    await callback.answer()
    task_id = int(callback.data.split('_')[1])
    task = await DB.get_task_by_id(task_id)
    if task is None:
        await callback.message.edit_text("❗ Задание не найдено или уже выполнено", reply_markup=back_menu_kb(callback.from_user.id))
        await asyncio.sleep(1)
        return

    user_id = callback.from_user.id
    target_id = task[2]
    invite_link = await check_admin_and_get_invite_link_chanel(bot, task[2])

    # Проверяем подписку на канал
    try: 
        chat_member = await bot.get_chat_member(target_id, user_id)
        if chat_member.status not in ["member", "administrator", "creator"]:
            builder = InlineKeyboardBuilder()
            builder.add(InlineKeyboardButton(text="🔙 Назад", callback_data="work_chanel"))
            builder.add(InlineKeyboardButton(text="Проверить 🔄️", callback_data=f"chanelcheck_{task_id}"))
            await callback.message.edit_text(
                f"🚩 Пожалуйста, <b>подпишитесь на канал</b> по ссылке {invite_link} и повторите попытку",
                reply_markup=builder.as_markup())
            return
    except Exception as e:
        print(f"Ошибка при проверке подписки: {e}")
        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(text="🔙 Назад", callback_data="work_chanel"))
        builder.add(InlineKeyboardButton(text="Проверить 🔄️", callback_data=f"chanelcheck_{task_id}"))
        await callback.message.edit_text(
            f"🚩 Пожалуйста, <b>подпишитесь на канал</b> по ссылке {invite_link} и повторите попытку",
            reply_markup=builder.as_markup())
        return

    if not await DB.is_task_completed(user_id, task[0]):
        # Уменьшаем количество выполнений на 1
        new_amount = task[3] - 1
        await DB.update_task_amount(task_id, new_amount)
        
        await DB.add_completed_task(user_id, task_id, target_id, 1500, task[1], status=1)
        await DB.add_balance(amount=1500, user_id=user_id)

        # Проверяем нужно ли удалить задание
        if new_amount <= 0:
            creator_id = task[1]
            await DB.delete_task(task_id)
            await bot.send_message(
                creator_id, 
                "🎉 Одно из ваших заданий было успешно выполнено",
                reply_markup=back_menu_kb(creator_id)
            )

        await DB.increment_statistics(1, 'all_subs_chanel')
        await DB.increment_statistics(2, 'all_subs_chanel')
        await DB.increment_statistics(1, 'all_taasks')
        await DB.increment_statistics(2, 'all_taasks')
        await update_dayly_and_weekly_tasks_statics(user_id)
        
        # Показываем уведомление об успешном выполнении
        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(
            text="Дальше ⏭️", 
            callback_data="work_chanel"
        ))
        await callback.message.edit_text(
            "✅ Задание успешно выполнено! +1500 MITcoin",
            reply_markup=builder.as_markup()
        )
    else:
        await callback.message.edit_text(
            "‼ Вы уже выполнили это задание", 
            reply_markup=back_menu_kb(user_id))

async def check_admin_and_get_invite_link_chanel(bot: Bot, target_id: int):
    try:
        chat_info = await bot.get_chat(target_id)
        return chat_info.invite_link or f"https://t.me/{chat_info.username}"
    except Exception as e:
        print(e)
        return "Ссылка недоступна"
    

@tasks.callback_query(F.data.startswith('skip_task_'))
async def skip_task_handler(callback: types.CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    try:
        task_id = int(callback.data.split('_')[2])
        await DB.skip_task(user_id, task_id)
        await callback.answer("Задание пропущено")

        all_tasks = task_cache.get('all_tasks', [])
        from ..client.client import get_available_tasks
        tasks = await get_available_tasks(user_id, all_tasks)

        if tasks:
            random.shuffle(tasks)
            keyboard = await generate_tasks_keyboard_chanel(tasks, bot)
            await callback.message.edit_text(
                "📢 <b>Задания на каналы:</b>\n\n🎢 Каналы в списке располагаются по количеству необходимых подписчиков\n\n"
                "⚡<i>Запрещено отписываться от канала раньше чем через 7 дней, в случае нарушения возможен штраф!</i>\n\n"
                f"Доступно заданий: {len(tasks)}",
                reply_markup=keyboard
            )
        else:
            await callback.message.edit_text(
                "На данный момент доступных заданий нет, возвращайся позже 😉",
                reply_markup=back_work_menu_kb(user_id)
            )

    except Exception as e:
        print(f"Ошибка в skip_task_handler: {e}")
        await callback.answer("Ошибка при пропуске задания", show_alert=True)

