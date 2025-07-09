from .tasks import *

active_tasks={}

@tasks.callback_query(F.data == 'post_pr_button')
async def pr_post_handler(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    user_id = callback.from_user.id
    user = await DB.select_user(user_id)
    balance = user['balance']
    if balance is None:
        balance = 0
    maxcount = balance // 300
    await callback.message.edit_text(f'''
👀 Реклама поста

💵 300 MITcoin = 1 просмотр

баланс: <b>{balance}</b>; Всего вы можете купить <b>{maxcount}</b> просмотров

<b>Сколько нужно просмотров</b>❓

<em>Что бы создать задание на вашем балансе должно быть не менее 300 MITcoin</em>
    ''', reply_markup=pr_menu_canc())
    await state.set_state(PostPromotionStates.awaiting_views_count)

@tasks.message(PostPromotionStates.awaiting_views_count)
async def pr_post2(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    user = await DB.select_user(user_id)
    balance = user['balance']
    if balance is None:
        balance = 0
    try:
        uscount = int(message.text.strip())
        if uscount >= 1:
            price = 300 * uscount
            await state.update_data(uscount=uscount, price=price, balance=balance)
            if balance >= price:
                builder = InlineKeyboardBuilder()
                builder.add(InlineKeyboardButton(text="✅ Продолжить", callback_data="pr_post_confirm"))
                builder.add(InlineKeyboardButton(text="🔙 Назад", callback_data="pr_menu_cancel"))
                await message.answer(
                    f'👀 <b>Количество: {uscount}</b>\n💰<b> Стоимость - {price} MITcoin</b>\n\n<em>Нажмите кнопку <b>Продолжить</b> или введите другое число...</em>',
                    reply_markup=builder.as_markup())
            else:
                builder = InlineKeyboardBuilder()
                builder.add(InlineKeyboardButton(text="Пополнить баланс", callback_data="cancel_all"))
                builder.add(InlineKeyboardButton(text="🔙 Назад", callback_data="pr_menu_cancel"))
                await message.answer( 
                    f'😢 <b>Недостаточно средств на балансе</b> \nВаш баланс: {balance} MITcoin\n<em>Пополните баланс или измените желаемое количество просмотров...</em>',
                    reply_markup=builder.as_markup())
        else:
            await message.answer('<b>❗Минимальная покупка от 1 просмотра!</b>\nВведи корректное число...',
                                 reply_markup=pr_menu_canc())
    except ValueError:
        await message.answer('<b>Ошибка ввода</b>\nПопробуй ввести целое число...', reply_markup=pr_menu_canc())

@tasks.callback_query(F.data == 'pr_post_confirm')
async def pr_post3(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    uscount = data.get('uscount')
    price = data.get('price')
    balance = data.get('balance')
    await state.clear()
    await callback.message.edit_text(f'''
👾 Теперь перешли ОДИН пост (‼ если пост с несколькими картинками - перешлите ОДНУ картинку, просмотры на пост будут засчитаны), который нужно рекламировать. Я жду...
    ''', reply_markup=pr_menu_canc())
    await state.set_state(PostPromotionStates.awaiting_post_message)
    await state.update_data(uscount=uscount, price=price, balance=balance)

@tasks.message(PostPromotionStates.awaiting_post_message)
async def pr_post4(message: types.Message, state: FSMContext, bot: Bot):
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
                    additional_info=None
                )
                
                await bot.send_message(TASKS_CHAT_ID, f'''
🔔 СОЗДАНО НОВОЕ ЗАДАНИЕ 🔔
⭕️ Тип задания: 👀 Пост
💸 Цена: 600
👥 Количество выполнений: {amount}
💰 Стоимость: {amount * 600} 
''')
                await state.clear()
                # После создания задания
                await RedisTasksManager.refresh_task_cache(bot, "post")
                await RedisTasksManager.update_common_tasks_count(bot)

            except:
                bot_username = (await bot.get_me()).username
                invite_link = f"http://t.me/{bot_username}?startchannel&admin=invite_users+manage_chat"
                add_button = InlineKeyboardButton(text="➕ Добавить бота в канал", url=invite_link)
                add_button1 = InlineKeyboardButton(text="❌ Отмена", callback_data='pr_menu_cancel')
                keyboard = InlineKeyboardMarkup(inline_keyboard=[[add_button], [add_button1]])
                await message.answer(
                    '😶 Добавьте бота в канал с правами админа при помощи кнопки снизу и перешлите пост заново...',
                    reply_markup=keyboard)
                


@tasks.callback_query(F.data == 'work_post')
async def works_post_handler(callback: types.CallbackQuery, bot: Bot, state: FSMContext):
    user_id = callback.from_user.id

    try:
        # 1. Получаем задания из кэша или БД
        cached_tasks = await RedisTasksManager.get_cached_tasks('post')
        if not cached_tasks:
            db_tasks = await DB.select_post_tasks()
            if db_tasks:
                await RedisTasksManager.cache_tasks('post', db_tasks)
                cached_tasks = db_tasks

        if not cached_tasks:
            await callback.message.edit_text(
                "⛔ Нет доступных заданий на посты",
                reply_markup=back_work_menu_kb(user_id)
            )
            return

        # 2. Фильтруем доступные задания
        available_tasks = []
        for task in cached_tasks:
            try:
                # Если task в виде tuple (из БД), конвертируем в словарь
                if isinstance(task, (list, tuple)):
                    task = {
                        'id': task[0],
                        'user_id': task[1],
                        'target_id': task[2],
                        'amount': task[3],
                        'type': task[4],
                        'status': task[5]
                    }

                if await DB.is_task_completed(user_id, task['id']):
                    continue

                task_data = {
                    'id': task['id'],
                    'user_id': task['user_id'],
                    'link': task['target_id'],
                    'amount': task['amount'],
                    'type': task['type'],
                    'status': task['status'],
                }

                if not task_data['link'] or ':' not in task_data['link']:
                    print(f"⚠️ Некорректный формат ссылки: {task_data['link']}")
                    continue

                channel_id, message_id_str = task_data['link'].split(':', 1)
                message_id = int(message_id_str)

                try:
                    chat = await bot.get_chat(chat_id=channel_id)
                    if not chat:
                        print(f"❌ Канал {channel_id} не найден")
                        continue

                    try:
                        member = await bot.get_chat_member(channel_id, bot.id)
                        if not member.can_post_messages:
                            print(f"⚠️ Бот не имеет прав в канале {channel_id}")
                            continue
                    except:
                        print(f"⚠️ Бот не состоит в канале {channel_id}")
                        continue

                    try:
                        await bot.forward_message(chat_id=INFO_ID, from_chat_id=channel_id, message_id=message_id)
                        task_data['channel_accessible'] = True
                        task_data['post_accessible'] = True
                        available_tasks.append(task_data)
                    except Exception as e:
                        print(f"❌ Ошибка проверки поста {message_id}: {str(e)}")
                        continue

                except Exception as e:
                    print(f"❌ Ошибка проверки канала {channel_id}: {str(e)}")
                    continue

            except Exception as e:
                print(f"⚠️ Ошибка обработки задания: {str(e)}")
                continue

        if not available_tasks:
            await callback.message.edit_text(
                "⛔ Нет доступных заданий",
                reply_markup=back_work_menu_kb(user_id)
            )
            return

        # 3. Обрабатываем первое доступное задание
        task = available_tasks[0]

        try:
            channel_id, message_id_str = task['link'].split(':', 1)
            message_id = int(message_id_str)

            await bot.forward_message(
                chat_id=user_id,
                from_chat_id=channel_id,
                message_id=message_id
            )

            keyboard = InlineKeyboardBuilder()
            keyboard.add(InlineKeyboardButton(text="🔙 Назад", callback_data="work_menu"))
            keyboard.add(InlineKeyboardButton(text="Дальше ⏭️", callback_data="work_post"))
            keyboard.add(InlineKeyboardButton(text="Репорт ⚠️", callback_data=f"postreport_{task['id']}"))

            await callback.message.answer_sticker(
                'CAACAgIAAxkBAAENFeZnLS0EwvRiToR0f5njwCdjbSmWWwACTgEAAhZCawpt1RThO2pwgjYE'
            )
            await asyncio.sleep(3)

            await DB.add_balance(amount=250, user_id=user_id)
            await DB.add_completed_task(
                user_id=user_id,
                task_id=task['id'],
                target_id=message_id,
                task_sum=250,
                owner_id=task['user_id'],
                status=0
            )

            await callback.message.answer(
                "👀 <b>Вы просмотрели пост! +250 MITcoin</b>",
                reply_markup=keyboard.as_markup()
            )

            await DB.update_task_amount(task['id'], int(task['amount'])-1)
            updated_task = await DB.get_task_by_id(task['id'])

            if updated_task[3] == 0:
                await DB.delete_task(task['id'])
                await RedisTasksManager.invalidate_cache('post')
                await bot.send_message(
                    updated_task[1],
                    "🎉 Ваше задание выполнено!",
                    reply_markup=back_menu_kb(updated_task[1])
                )
            await RedisTasksManager.refresh_task_cache(bot, "post")
            await RedisTasksManager.update_common_tasks_count(bot)

        except Exception as e:
            print(f"⚠️ Ошибка обработки поста: {str(e)}")
            await callback.message.answer(
                "⛔ Произошла ошибка при обработке поста",
                reply_markup=back_work_menu_kb(user_id)
            )

    except Exception as e:
        print(f"⚠️ Критическая ошибка в обработчике: {str(e)}")
        await callback.message.edit_text(
            "⛔ Произошла системная ошибка. Попробуйте позже.",
            reply_markup=back_work_menu_kb(user_id)
        )

# # Глобальный словарь для хранения активных заданий пользователей
# active_tasks = {} 

# @tasks.callback_query(F.data == 'work_post')
# async def works_post_handler(callback: types.CallbackQuery, bot: Bot, state: FSMContext):
#     user_id = callback.from_user.id

#     # Используем глобальный список обработанных заданий
#     from handlers.client.client import processed_tasks

#     # Проверяем, есть ли активное задание для пользователя
#     if user_id in active_tasks:
#         await callback.answer("Вы уже выполняете задание. Дождитесь его завершения.", show_alert=True)
#         return

#     if processed_tasks:
#         # Фильтруем задания, которые пользователь еще не выполнил
#         available_tasks = [task for task in processed_tasks if not await DB.is_task_completed(user_id, task[0])]

#         if not available_tasks:
#             await callback.message.edit_text("На данный момент доступных заданий нет, возвращайся позже 😉",
#                                              reply_markup=back_work_menu_kb(user_id))
#             return

#         # Выбираем первое доступное задание
#         task = available_tasks[0]
#         task_id, target_id, amount = task[0], task[2], task[3]
#         chat_id, message_id = map(int, target_id.split(":"))

#         # Сохраняем активное задание для пользователя
#         active_tasks[user_id] = task_id

#         try:
#             builder = InlineKeyboardBuilder()
#             builder.add(InlineKeyboardButton(text="🔙 Назад", callback_data="work_menu"))
#             builder.add(InlineKeyboardButton(text="Дальше ⏭️", callback_data=f"work_post"))
#             # builder.add(InlineKeyboardButton(text="Репорт ⚠️", callback_data=f"report_post_{task_id}"))

#             # Пересылаем пост пользователю
#             await bot.forward_message(chat_id=user_id, from_chat_id=chat_id, message_id=message_id)

#             # Отправляем стикер и сообщение
#             await callback.message.answer_sticker(
#                 'CAACAgIAAxkBAAENFeZnLS0EwvRiToR0f5njwCdjbSmWWwACTgEAAhZCawpt1RThO2pwgjYE')
#             await asyncio.sleep(3)

#             # Начисляем награду сразу после просмотра поста
#             await DB.add_balance(amount=250, user_id=user_id)
#             await DB.add_completed_task(user_id, task_id, target_id, 250, task[1], status=0)

#             # Обновляем статистику
#             await DB.increment_statistics(1, 'all_see')
#             await DB.increment_statistics(2, 'all_see')
#             await DB.increment_statistics(1, 'all_taasks')
#             await DB.increment_statistics(2, 'all_taasks')
#             await update_dayly_and_weekly_tasks_statics(user_id)

#             # Отправляем сообщение с кнопками
#             await callback.message.answer(
#                 f"👀 <b>Вы просмотрели пост! +250 MITcoin</b>\n\nНажмите кнопку для просмотра следующего поста",
#                 reply_markup=builder.as_markup())

#             # Обновляем задание в базе данных
#             await DB.update_task_amount(task_id)
#             updated_task = await DB.get_task_by_id(task_id)

#             # Если задание выполнено, удаляем его
#             if updated_task[3] == 0:
#                 delete_task = await DB.get_task_by_id(task_id)
#                 creator_id = delete_task[1]
#                 await DB.delete_task(task_id)
#                 await bot.send_message(creator_id, f"🎉 Одно из ваших заданий на пост было успешно выполнено!",
#                                        reply_markup=back_menu_kb(user_id))

#         except Exception as e:
#             print(f"Ошибка: {e}")
#             await callback.message.edit_text("Произошла ошибка при обработке задания. Попробуйте еще раз.",
#                                              reply_markup=back_work_menu_kb(user_id))
#         finally:
#             # Удаляем активное задание для пользователя
#             if user_id in active_tasks:
#                 del active_tasks[user_id]
#     else:
#         await callback.message.edit_text("На данный момент заданий на посты нет, возвращайся позже 😉",
#                                          reply_markup=back_work_menu_kb(user_id))



# class PostReport(StatesGroup):
#     desc = State()

# @tasks.callback_query(F.data.startswith('postreport_'))
# async def request_post_report_description(callback: types.CallbackQuery, bot: Bot, state: FSMContext):
#     task_id = int(callback.data.split('_')[1])
#     await callback.answer()

#     # Сохраняем task_id в состояние пользователя
#     await state.update_data(task_id=task_id)

#     # Запрашиваем описание проблемы
#     await callback.message.edit_text(
#         "⚠️ Пожалуйста, опишите проблему с этим постом. Например, пост не соответствует правилам или содержит недопустимый контент."
#     )
#     await state.set_state(PostReport.desc)

# @tasks.message(PostReport.desc)
# async def save_post_report_description(message: types.Message, bot: Bot, state: FSMContext):
#     user_id = message.from_user.id
#     description = message.text

#     # Получаем task_id из состояния
#     data = await state.get_data()
#     task_id = data.get("task_id")

#     if task_id:
#         task = await DB.get_task_by_id(task_id)
#         if task:
#             target_id = task[2]

#             # Добавляем репорт в базу данных
#             await DB.add_report(task_id=task_id, chat_id=target_id, user_id=user_id, description=description)

#             # Отправляем подтверждение
#             await message.answer("⚠️ Жалоба на пост отправлена!")
#             await asyncio.sleep(1)

#             # Возвращаем пользователя к списку заданий
#             all_tasks = await DB.select_post_tasks()
#             if all_tasks:
#                 available_tasks = [task for task in all_tasks if not await DB.is_task_completed(user_id, task[0])]
#                 if not available_tasks:
#                     await message.answer("На данный момент доступных заданий нет, возвращайся позже 😉",
#                                          reply_markup=back_work_menu_kb(user_id))
#                     return

#                 for task in available_tasks:
#                     task_id, target_id, amount = task[0], task[2], task[3]
#                     chat_id, message_id = map(int, target_id.split(":"))
#                     try:
#                         builder = InlineKeyboardBuilder()
#                         builder.add(InlineKeyboardButton(text="🔙 Назад", callback_data="work_menu"))
#                         builder.add(InlineKeyboardButton(text="Дальше ⏭️", callback_data=f"work_post"))
#                         builder.add(InlineKeyboardButton(text="Репорт ⚠️", callback_data=f"postreport_{task_id}"))
#                         await bot.forward_message(chat_id=user_id, from_chat_id=chat_id, message_id=message_id)
#                         await message.answer_sticker(
#                             'CAACAgIAAxkBAAENFeZnLS0EwvRiToR0f5njwCdjbSmWWwACTgEAAhZCawpt1RThO2pwgjYE')
#                         await asyncio.sleep(5)

#                         await message.answer(
#                             f"👀 <b>Просмотрели пост! +250 MITcoin</b>\n\nНажмите кнопку для просмотра следующего поста",
#                             reply_markup=builder.as_markup())

#                         await DB.update_task_amount(task_id)
#                         updated_task = await DB.get_task_by_id(task_id)

#                         await DB.add_completed_task(user_id, task_id, target_id, 250, task[1], status=0)
#                         await DB.add_balance(amount=250, user_id=user_id)

#                         if updated_task[3] == 0:
#                             delete_task = await DB.get_task_by_id(task_id)
#                             creator_id = delete_task[1]
#                             await DB.delete_task(task_id)
#                             await DB.increment_all_see()
#                             await DB.increment_all_taasks()
#                             await bot.send_message(creator_id, f"🎉 Одно из ваших заданий на пост было успешно выполнено!",
#                                                    reply_markup=back_menu_kb(user_id))

#                         return
#                     except Exception as e:
#                         print(f"Ошибка: {e}")
#                         continue

#                 # Если все задания были пропущены
#                 await message.answer("На данный момент доступных заданий нет, возвращайся позже 😉",
#                                      reply_markup=back_work_menu_kb(user_id))
#             else:
#                 await message.answer("На данный момент заданий на посты нет, возвращайся позже 😉",
#                                      reply_markup=back_work_menu_kb(user_id))
#         else:
#             await message.answer("Задание не найдено.")
#     else:
#         await message.answer("Ошибка: не удалось получить данные о задании.")

#     # Сбрасываем состояние
#     await state.clear()












async def process_tasks_periodically(bot: Bot):
    """Обновление постовых заданий с сохранением доступности"""
    while True:
        try:
            all_tasks = await DB.select_post_tasks()
            random.shuffle(all_tasks)
            
            new_processed_tasks = []
            for task in all_tasks:
                try:
                    channel_id, post_id = map(int, task[2].split(':'))
                    await bot.forward_message(chat_id=INFO_ID, from_chat_id=channel_id, message_id=post_id)
                    new_processed_tasks.append(task)
                except Exception as e:
                    print(f"Ошибка при проверке поста {task[2]}: {e}")
                    continue
            from handlers.Background.bg_tasks import post_cache_lock
            with post_cache_lock:
                global processed_tasks
                # Сохраняем старые задания, если новые не прошли проверку
                processed_tasks = new_processed_tasks if new_processed_tasks else processed_tasks
                print(f"Постовые задания обновлены. Доступно: {len(processed_tasks)}")

        except Exception as e:
            print(f"Критическая ошибка в process_tasks_periodically: {e}")

        await asyncio.sleep(600)