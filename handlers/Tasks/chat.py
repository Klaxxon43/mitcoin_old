from .tasks import *
from handlers.Background.chat import check_admin_and_get_invite_link_chat

@tasks.callback_query(F.data == 'chat_pr_button')
async def pr_chat_handler(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    user_id = callback.from_user.id
    user = await DB.select_user(user_id)
    balance = user['balance']
    if balance is None:
        balance = 0
    maxcount = balance // 1500
    await callback.message.edit_text(f'''
👥 Реклама чата

💵 1500 $MICO = 1 участник

баланс: <b>{balance}</b>; Всего вы можете купить <b>{maxcount}</b> участников

<b>Сколько нужно участников</b>❓

<em>Что бы создать задание на вашем балансе должно быть не менее 1500 MITcoin</em>
    ''', reply_markup=pr_menu_canc())
    await state.set_state(ChatPromotionStates.awaiting_members_count)

@tasks.message(ChatPromotionStates.awaiting_members_count)
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

@tasks.callback_query(F.data == 'pr_chat_confirm')
async def pr_chat3(callback: types.CallbackQuery, state: FSMContext):
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
                text="💬 Выбрать чат",
                request_chat=KeyboardButtonRequestChat(
                    request_id=1,
                    chat_is_channel=False,
                    chat_is_group=True,
                    user_administrator_rights=types.ChatAdministratorRights(
                        is_anonymous=False,
                        can_manage_chat=True,
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
                        can_manage_chat=True,
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
        "💬 Пожалуйста, выбери чат, в который добавлен бот и у него есть права администратора.",
        reply_markup=kb
    )

    await state.set_state(ChatPromotionStates.awaiting_chat_selection)
    await state.update_data(uscount=uscount, price=price, balance=balance)

@tasks.message(ChatPromotionStates.awaiting_chat_selection)
async def handle_chat_selection(message: types.Message, state: FSMContext, bot: Bot):
    if not message.chat_shared:
        await message.answer("❗ Пожалуйста, выбери чат с помощью кнопки ниже.")
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

        # Проверка прав бота
        if member.status != "administrator" or not member.can_invite_users or not member.can_manage_chat:
            await state.update_data(pending_chat_id=chat_id)

            invite_link = f"https://t.me/{bot_info.username}?startgroup&admin=invite_users+manage_chat"
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="➕ Добавить в админы", url=invite_link)],
                [InlineKeyboardButton(text="🔄 Проверить", callback_data="check_chat_admin_rights")],
                [InlineKeyboardButton(text="❌ Отмена", callback_data="back_menu")]
            ])

            await message.answer(
                f"😕 Бот найден в чате <b>{chat.title}</b>, но ему <u>не выданы админ-права</u>\n\n"
                f"🔧 Пожалуйста, добавьте бота в админы и нажмите <b>Проверить</b>.",
                reply_markup=keyboard
            )
            return

    except Exception as e:
        print("Ошибка при проверке чата:", e)
        await message.answer("❌ Ошибка при проверке чата. Убедитесь, что бот добавлен в чат с правами администратора.")
        return

    # Создание задания
    await DB.add_balance(user_id, -price)
    await DB.add_transaction(user_id=user_id, amount=price, description="создание задания на вступление в чат", additional_info=None)
    await DB.add_task(user_id=user_id, target_id=chat_id, amount=amount, task_type=2)  # 2 - тип задания "чат"
    await RedisTasksManager.refresh_task_cache(bot, "chat")
    await RedisTasksManager.update_common_tasks_count(bot)

    await message.answer(
        f"✅ Задание на чат <b>{chat.title}</b> создано успешно!",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Вернуться в меню", callback_data="back_menu")]
        ])
    )

    await bot.send_message(TASKS_CHAT_ID, f'''
🔔 СОЗДАНО НОВОЕ ЗАДАНИЕ 🔔
⭕️ Тип задания: 💬 Чат
💬 Чат: {chat.title}
💸 Цена: {price // amount}
👥 Кол-во выполнений: {amount}
💰 Стоимость: {price}
''')

    await state.clear()

@tasks.callback_query(F.data == "check_chat_admin_rights")
async def check_chat_admin_rights(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    await callback.answer()
    data = await state.get_data()
    user_id = callback.from_user.id
    chat_id = data.get("pending_chat_id")
    price = data.get('price')
    amount = data.get('uscount')

    try:
        chat = await bot.get_chat(chat_id)
        bot_info = await bot.get_me()
        member = await bot.get_chat_member(chat_id, bot_info.id)

        if member.status != "administrator" or not member.can_invite_users or not member.can_manage_chat:
            await callback.message.edit_text(
                f"⛔ Боту по-прежнему не выданы нужные права в чате <b>{chat.title}</b>.\n\n"
                f"🔧 Убедитесь, что он <b>админ</b> и может <b>приглашать пользователей и управлять чатом</b>.",
                reply_markup=callback.message.reply_markup
            )
            return

        # Создание задания
        await DB.add_balance(user_id, -price)
        await DB.add_transaction(user_id=user_id, amount=price, description="создание задания на вступление в чат", additional_info=None)
        await DB.add_task(user_id=user_id, target_id=chat_id, amount=amount, task_type=2)
        await RedisTasksManager.refresh_task_cache(bot, "chat")
        await RedisTasksManager.update_common_tasks_count(bot)
        
        await callback.message.edit_text(
            f"✅ Задание на чат <b>{chat.title}</b> создано успешно!",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Вернуться в меню", callback_data="back_menu")]
            ])
        )

        await bot.send_message(TASKS_CHAT_ID, f'''
🔔 СОЗДАНО НОВОЕ ЗАДАНИЕ 🔔
⭕️ Тип задания: 💬 Чат
💬 Чат: {chat.title}
💸 Цена: {price // amount}
👥 Кол-во выполнений: {amount}
💰 Стоимость: {price}
''')

        await state.clear()

    except Exception as e:
        print("Ошибка в check_chat_admin_rights:", e)
        await callback.message.edit_text("⚠ Произошла ошибка при повторной проверке. Попробуйте позже.")
        


@tasks.callback_query(F.data == 'work_chat')
async def tasksschat_handler(callback: types.CallbackQuery, bot: Bot):
    user_id = callback.from_user.id

    try:
        # Получаем задания из Redis или БД
        all_tasks = await RedisTasksManager.get_cached_tasks('chat') or []
        if not all_tasks:
            await RedisTasksManager.refresh_task_cache(bot, 'chat')
            all_tasks = await RedisTasksManager.get_cached_tasks('chat') or []

        print("Задания для фильтрации:", all_tasks)

        filtered_tasks = []
        for task in all_tasks:
            print("Проверка задания:", task)
            try:
                task_id = task["id"]
                if not await DB.is_task_completed(user_id, task_id):
                    filtered_tasks.append(task)
            except Exception as inner_e:
                print(f"Ошибка при фильтрации задания {task}: {inner_e}")

        tasks = filtered_tasks


        if tasks:
            random.shuffle(tasks)
            keyboard = await generate_tasks_keyboard_chat(tasks, bot)

            await callback.message.edit_text(
                "👤 <b>Задания на чаты:</b>\n\n🎢 Чаты в списке располагаются по количеству необходимых участников\n\n⚡<i>Запрещено покидать чат раньше чем через 7 дней, в случае нарушения возможен штраф!</i>",
                reply_markup=keyboard
            )
        else:
            await callback.message.edit_text(
                "На данный момент доступных заданий нет, возвращайся позже 😉",
                reply_markup=back_work_menu_kb(user_id)
            )
    except Exception as e:
        print(f"Ошибка в tasksschat_handler: {e}")
        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(text="🔄 Обновить", callback_data="work_chat"))
        await callback.message.edit_text(
            "Произошла ошибка при загрузке заданий. Попробуйте обновить страницу.",
            reply_markup=builder.as_markup()
        )

        

async def generate_tasks_keyboard_chat(tasks, bot):
    builder = InlineKeyboardBuilder()

    # Выводим задания (по 5 на страницу)
    for task in tasks[:5]:  # Ограничиваем количество заданий на одной странице
        chat_id = task["target_id"]
        task_id = task["id"]
        try:
            chat = await bot.get_chat(chat_id)
            chat_title = chat.title
        except Exception:
            chat_title = "Неизвестный чат"

        button_text = f"{chat_title} | +1500"
        builder.row(InlineKeyboardButton(text=button_text, callback_data=f"chattask_{task_id}"))

    # Кнопка "Назад"
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="work_menu"))

    # Кнопка "Обновить"
    builder.row(InlineKeyboardButton(text="🔄 Обновить", callback_data="work_chat"))

    return builder.as_markup()


@tasks.callback_query(lambda c: c.data.startswith("chattask_"))
async def task_detail_handler(callback: types.CallbackQuery, bot: Bot):
    await callback.answer()
    task_id = int(callback.data.split('_')[1])
    task = await DB.get_task_by_id(task_id)

    amount = task[3]

    invite_link = await check_admin_and_get_invite_link_chat(bot, task[2])
    chat_id = task[2]
    chat = await bot.get_chat(chat_id)
    task_info = f"""
👤 {chat.title} | <i>{amount}</i>
<i>Вступите в чат и нажмите кнопку -</i> <b>Проверить</b> 🔄️

{invite_link}    
    """
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Проверить 🔄️", callback_data=f"chatcheck_{task_id}"))
    builder.add(InlineKeyboardButton(text="⏭ Пропустить", callback_data=f"skip_task_{task_id}"))
    builder.add(InlineKeyboardButton(text="Репорт ⚠️", callback_data=f"report_chat_{task_id}"))
    builder.add(InlineKeyboardButton(text="🔙 Назад", callback_data="work_chat"))
    builder.adjust(1, 2, 1)
    await callback.message.edit_text(task_info, reply_markup=builder.as_markup())


@tasks.callback_query(F.data.startswith('chatcheck_'))
async def check_subscription_chat(callback: types.CallbackQuery, bot: Bot):
    await callback.answer()
    task_id = int(callback.data.split('_')[1])
    task = await DB.get_task_by_id(task_id)
    if task is None:
        await callback.message.edit_text("❗ Задание не найдено или уже выполнено", reply_markup=back_menu_kb(user_id))
        await asyncio.sleep(1)
        return

    user_id = callback.from_user.id
    target_id = task[2]
    invite_link = await check_admin_and_get_invite_link_chat(bot, task[2])

    # Проверяем, подписан ли пользователь на чат
    try:
        bot_member = await bot.get_chat_member(target_id, callback.message.chat.id)
        if bot_member.status != "member":
            builder = InlineKeyboardBuilder()
            builder.add(InlineKeyboardButton(text="🔙 Назад", callback_data="work_chat"))
            builder.add(InlineKeyboardButton(text="Проверить 🔄️", callback_data=f"chatcheck_{task_id}"))
            await callback.message.edit_text(
                f"🚩 Пожалуйста, <b>вступите в чат</b> по ссылке {invite_link} и повторите попытку",
                reply_markup=builder.as_markup())
            return
    except Exception as e:
        print(f"Ошибка при проверке подписки: {e}")
        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(text="🔙 Назад", callback_data="work_chat"))
        builder.add(InlineKeyboardButton(text="Проверить 🔄️", callback_data=f"chatcheck_{task_id}"))

        await callback.message.edit_text(
            f"🚩 Пожалуйста, <b>вступите в чат</b> по ссылке {invite_link} и повторите попытку",
            reply_markup=builder.as_markup())
        return

    if not await DB.is_task_completed(user_id, task[0]):
        # Обновляем задание (вычитаем amount на 1)
        await DB.update_task_amount(task_id)
        await DB.add_completed_task(user_id, task_id, target_id, 1500, task[1], status=1)
        await DB.add_balance(amount=1500, user_id=user_id)

        # Проверяем, нужно ли удалить задание
        updated_task = await DB.get_task_by_id(task_id)
        if updated_task[3] == 0:
            delete_task = await DB.get_task_by_id(task_id)
            creator_id = delete_task[1]
            await DB.delete_task(task_id)
            await RedisTasksManager.refresh_task_cache(bot, "chat")
            await bot.send_message(creator_id, f"🎉 Одно из ваших заданий было успешно выполнено",
                                   reply_markup=back_menu_kb(user_id))


        await DB.increment_statistics(1, 'all_subs_groups')
        await DB.increment_statistics(2, 'all_subs_groups')
        await DB.increment_statistics(1, 'all_taasks')
        await DB.increment_statistics(2, 'all_taasks')
        await update_dayly_and_weekly_tasks_statics(user_id)
        await callback.message.edit_text("✅")
        await callback.answer("+1500")
        await asyncio.sleep(2)
    else:
        await callback.message.edit_text("‼ Вы уже выполнили это задание", reply_markup=back_menu_kb(user_id))
        await asyncio.sleep(3)

    # Обновляем список заданий после выполнения
    all_tasks = await RedisTasksManager.get_cached_tasks('chat') or []
    tasks = [
        task for task in all_tasks if not await DB.is_task_completed(user_id, task[0])
    ]

    if tasks:
        random.shuffle(tasks)
        keyboard = await generate_tasks_keyboard_chat(tasks, bot)
        await callback.message.edit_text(
            "👤 <b>Задания на чаты:</b>\n\n🎢 Чаты в списке располагаются по количеству необходимых участников\n\n⚡<i>Запрещено покидать чат раньше чем через 7 дней, в случае нарушения возможен штраф!</i>",
            reply_markup=keyboard
        )
    else:
        await callback.message.edit_text(
            "На данный момент доступных заданий нет, возвращайся позже 😉",
            reply_markup=back_work_menu_kb(user_id)
        )


class ChatReport(StatesGroup):
    desc = State()

@tasks.callback_query(F.data.startswith('chatreport_'))
async def request_chat_report_description(callback: types.CallbackQuery, bot: Bot, state: FSMContext):
    await callback.answer()
    task_id = int(callback.data.split('_')[1])
    task = await DB.get_task_by_id(task_id)
    target_id = task[2]

    # Сохраняем task_id в состояние пользователя
    await state.update_data(task_id=task_id, target_id=target_id)

    # Запрашиваем описание проблемы
    await callback.message.edit_text("⚠️ Пожалуйста, опишите проблему с этим чатом. Например, чат не соответствует правилам или содержит недопустимый контент.")
    await state.set_state(ChatReport.desc)

@tasks.message(ChatReport.desc)
async def save_chat_report_description(message: types.Message, bot: Bot, state: FSMContext):
    user_id = message.from_user.id
    description = message.text

    # Получаем task_id и target_id из состояния
    data = await state.get_data()
    task_id = data.get("task_id")
    target_id = data.get("target_id")

    if task_id and target_id:
        # Добавляем репорт в базу данных
        await DB.add_report(task_id=task_id, chat_id=target_id, user_id=user_id, description=description)

        # Отправляем подтверждение
        chat = await bot.get_chat(target_id)
        await message.answer(f'⚠️ Жалоба на чат <b>{chat.title}</b> отправлена!')
        await asyncio.sleep(1)

        # Возвращаем пользователя к списку заданий
        all_tasks = await RedisTasksManager.get_cached_tasks('chat') or []
        tasks = [task for task in all_tasks if not await DB.is_task_completed(user_id, task[0])]

        if tasks:
            random.shuffle(tasks)
            chatpage = 1
            keyboard = await generate_tasks_keyboard_chat(tasks, bot)
            await message.answer(
                "👤 <b>Задания на чаты:</b>\n\n🎢 Чаты в списке располагаются по количеству необходимых участников\n\n⚡<i>Запрещено покидать чат раньше чем через 7 дней, в случае нарушения возможен штраф!</i>",
                reply_markup=keyboard)
        else:
            await message.answer("На данный момент доступных заданий нет, возвращайся позже 😉",
                                 reply_markup=back_work_menu_kb(user_id))
    else:
        await message.answer("Ошибка: не удалось получить данные о задании.")

    # Сбрасываем состояние
    await state.clear()


# Функция для проверки прав админа и генерации ссылки
async def check_admin_and_get_invite_link_chating(bot, chat_id):
    try:
        chat_administrators = await bot.get_chat_administrators(chat_id)
        # Проверяем, является ли бот администратором
        for admin in chat_administrators:
            if admin.user.id == bot.id:
                # Если бот админ, генерируем ссылку-приглашение
                invite_link = await bot.export_chat_invite_link(chat_id)
                return invite_link
        # Если бот не админ
        return "😑 Ошибка, приходите позже..."
    except:
        return "😑 Ошибка, приходите позже..."
    














