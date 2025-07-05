from untils.Imports import *
from .client import *
from .states import *

@router.message(F.text.startswith('/start'))
async def start_handler(message: types.Message, state: FSMContext, bot: Bot):
    user_id = message.from_user.id
    username = message.from_user.username
    
    # 1. Проверка на участие в конкурсе
    args = message.text.split()
    if len(args) > 1 and args[1].startswith('contest_'):
        contest_id = int(args[1].split('_')[1])
        await handle_contest_participation(message, bot, contest_id, user_id, username)
        return
    
    # 2. Проверка подписки на обязательные каналы
    not_subscribed = await check_channel_subscriptions(user_id, bot)
    if not_subscribed:
        await handle_not_subscribed(message, not_subscribed)
        return
    
    # 3. Очистка состояния и подготовка данных
    await state.clear()
    user = await DB.select_user(user_id)
    
    # 4. Обработка параметров команды /start
    referrer_id, check_uid, ref_user_id = parse_start_parameters(args)
    await state.update_data(reffer_id=ref_user_id) if ref_user_id else None
    
    # 5. Обработка личных сообщений
    if message.chat.type == 'private':
        # 5.1. Регистрация нового пользователя
        if not user:
            await register_new_user(message, bot, referrer_id, check_uid, ref_user_id)
        
        # 5.2. Обработка реферальной ссылки для чеков
        if ref_user_id and check_uid:
            await handle_check_referral(message, bot, check_uid, ref_user_id, state)
            return
        
        # 5.3. Активация чека
        if check_uid:
            await handle_check_activation(message, bot, check_uid, ref_user_id, state)
            return
        
        # 5.4. Основное меню
        await DB.update_user(user_id, username)
        await message.answer(
            "💎 <b>PR MIT</b> - <em>мощный и уникальный инструмент для рекламы ваших проектов</em>\n\n<b>Главное меню</b>",
            reply_markup=menu_kb(user_id))
    
    # 6. Обработка сообщений в группах
    elif message.chat.type in ['group', 'supergroup'] and not check_uid:
        await message.answer("Для получения информации используйте бота в личных сообщениях.")

# ===== Вспомогательные функции для конкурсов =====

async def handle_contest_participation(message: types.Message, bot: Bot, contest_id: int, user_id: int, username: str):
    """Обрабатывает участие в конкурсе из команды /start"""
    print(f"\n=== START HANDLE PARTICIPATION ===")
    print(f"contest_id: {contest_id}, user_id: {user_id}, username: {username}")
    
    try:
        # 1. Получаем данные о конкурсе
        print("\n[1] Получаем данные конкурса...")
        contest = await Contest.get_contest(contest_id)
        print(f"contest data: {contest}")
        
        if not contest:
            print("Конкурс не найден!")
            await message.answer("Конкурс не найден", reply_markup=back_menu_kb(user_id))
            return

        # 2. Извлекаем данные из кортежа
        print("\n[2] Извлекаем значения конкурса...")
        channel_url = contest[1]  # https://t.me/concest1
        message_id = contest[-2]  # ID сообщения
        contest_text = contest[-1]  # Текст сообщения
        channel_username = channel_url.replace("https://t.me/", "").replace("@", "")
        print(f"Канал: @{channel_username}, ID сообщения: {message_id}")

        # 3. Проверяем условия участия
        print("\n[3] Проверяем условия участия...")
        conditions = {}
        try:
            conditions = json.loads(contest[6]) if contest[6] else {}
        except json.JSONDecodeError as e:
            print(f"Ошибка парсинга условий: {e}")
        
        auto_conditions = conditions.get("auto_conditions", [])
        additional_channels = conditions.get("additional_channels", [])
        print(f"Условия: {auto_conditions}")
        print(f"Доп. каналы: {additional_channels}")

        # Проверка подписки на основной канал
        if "sub_channel" in auto_conditions:
            print("\n[3.1] Проверка подписки на основной канал...")
            try:
                chat_member = await bot.get_chat_member(
                    chat_id=f"@{channel_username}", 
                    user_id=user_id
                )
                print(f"Статус пользователя: {chat_member.status}")
                
                if chat_member.status not in ['member', 'administrator', 'creator']:
                    print("Пользователь не подписан")
                    await message.answer(
                        f"Для участия подпишитесь на канал: {channel_url}",
                        reply_markup=back_menu_kb(user_id)
                    )
                    return
            except Exception as e:
                print(f"Ошибка проверки подписки: {e}")
                await message.answer(
                    "Не удалось проверить подписку на основной канал",
                    reply_markup=back_menu_kb(user_id))
                return

        # Проверка подписки на дополнительные каналы
        if additional_channels:
            print("\n[3.2] Проверка подписки на дополнительные каналы...")
            for channel in additional_channels:
                channel_username2 = channel.replace("https://t.me/", "").replace("@", "")
                try:
                    chat_member = await bot.get_chat_member(
                        chat_id=f"@{channel_username2}", 
                        user_id=user_id
                    )
                    print(f"Статус пользователя в {channel_username2}: {chat_member.status}")
                    
                    if chat_member.status not in ['member', 'administrator', 'creator']:
                        print(f"Пользователь не подписан на {channel}")
                        await message.answer(
                            f"Для участия подпишитесь на канал: {channel}",
                            reply_markup=back_menu_kb(user_id))
                        return
                except Exception as e:
                    print(f"Ошибка проверки подписки на {channel}: {e}")
                    await message.answer(
                        f"Не удалось проверить подписку на канал: {channel}",
                        reply_markup=back_menu_kb(user_id))
                    return

        # if 'is_bot_user' in auto_conditions:
        #     # Проверка, что пользователь есть в базе бота
        #     if not await DB.select_user(user_id):
        #         await message.answer(
        #             "Вы не зарегистрированы в боте. Пожалуйста, начните с команды /start",
        #             reply_markup=back_menu_kb(user_id))
        #         return
                
        if 'is_active_user' in auto_conditions:
            count = (await DB.get_task_counts(user_id))[0]
            if count < 15:
                await message.answer(
                    'Вы не выполнили одно из условий. Для участия в конкурсе, вы должны быть активным пользователем бота\n\n'
                    '<b>Активным пользователем считается тот, кто за последние сутки выполнил более 15 заданий</b>',
                    reply_markup=back_menu_kb(user_id))
                return 
            

        # 4. Добавляем участника
        print("\n[4] Добавляем участника...")
        if not await Contest.add_participant(contest_id, user_id, username):
            print("Пользователь уже участвует")
            await message.answer(
                "Вы уже участвуете в этом конкурсе",
                reply_markup=back_menu_kb(user_id)
            )
            return

        # 5. Обновляем счетчик участников
        print("\n[5] Обновляем счетчик участников...")
        participants_count = await Contest.get_participants_count(contest_id)
        print(f"Текущее количество участников: {participants_count}")
        
        # 6. Обновляем текст конкурса
        print("\n[6] Обновляем текст конкурса...")
        if not contest_text:
            print("Текст конкурса пуст!")
            await message.answer(
                "Не удалось обновить конкурс: текст не найден",
                reply_markup=back_menu_kb(user_id))
            return

        # Обновляем строку с количеством участников
        updated_text = update_participants_count(contest_text, participants_count)
        print(f"Обновленный текст:\n{updated_text}")

        # 7. Обновляем сообщение в канале
        print("\n[7] Обновляем сообщение в канале...")
        try:
            if not updated_text.strip():
                raise ValueError("Текст сообщения пуст после обновления")
            
            # Создаем кнопку "Участвовать" (выносим это до попыток редактирования)
            bot_username = (await bot.get_me()).username
            participate_kb = InlineKeyboardBuilder()
            participate_kb.button(
                text="🎁 Участвовать", 
                url=f"https://t.me/{bot_username}?start=contest_{contest_id}"
            )
            
            try:
                # Пытаемся отредактировать текст сообщения с кнопкой
                await bot.edit_message_text(
                    chat_id=f"@{channel_username}",
                    message_id=message_id,
                    text=updated_text,
                    reply_markup=participate_kb.as_markup()  # Добавляем кнопку
                )
            except Exception as text_edit_error:
                print(f"Не удалось отредактировать текст: {text_edit_error}")
                try:
                    # Пытаемся отредактировать подпись (если это сообщение с фото)
                    await bot.edit_message_caption(
                        chat_id=f"@{channel_username}",
                        message_id=message_id,
                        caption=updated_text,
                        reply_markup=participate_kb.as_markup()  # Добавляем кнопку
                    )
                except Exception as caption_edit_error:
                    print(f"Не удалось отредактировать подпись: {caption_edit_error}")
                    try:
                        # Если не получилось редактировать, отправляем новое сообщение
                        if contest.get("image_path") and os.path.exists(contest["image_path"]):
                            with open(contest["image_path"], 'rb') as photo:
                                new_message = await bot.send_photo(
                                    chat_id=f"@{channel_username}",
                                    photo=types.BufferedInputFile(photo.read(), filename="contest.jpg"),
                                    caption=updated_text,
                                    reply_markup=participate_kb.as_markup()
                                )
                        else:
                            new_message = await bot.send_message(
                                chat_id=f"@{channel_username}",
                                text=updated_text,
                                reply_markup=participate_kb.as_markup()
                            )
                        
                        # Обновляем ID сообщения в базе данных
                        await Contest.update_contest_message_id(contest_id, new_message.message_id)
                        print("Создано новое сообщение с кнопкой")
                    except Exception as send_error:
                        print(f"Не удалось отправить новое сообщение: {send_error}")
                        raise Exception("Не удалось обновить сообщение в канале")

            await Contest.update_contest_message_text(contest_id, updated_text)
            print("Сообщение успешно обновлено с кнопкой!")
        except ValueError as e:
            print(f"Ошибка валидации: {e}")
            await message.answer(
                "Ошибка: недопустимый текст сообщения",
                reply_markup=back_menu_kb(user_id)
            )
        except Exception as e:
            print(f"Неизвестная ошибка при редактировании: {e}")
            await message.answer(
                "Не удалось обновить конкурс (техническая ошибка)",
                reply_markup=back_menu_kb(user_id))
            return

        # 8. Отправляем подтверждение
        print("\n[8] Отправляем подтверждение...")
        await message.answer(
            "🎉 Вы успешно зарегистрировались на конкурс!",
            reply_markup=back_menu_kb(user_id))
        print("=== УСПЕШНО ЗАВЕРШЕНО ===")
            
    except Exception as e:
        print(f"\n!!! ОШИБКА: {e}\n{traceback.format_exc()}")
        await message.answer(
            "Произошла ошибка при обработке вашего участия",
            reply_markup=back_menu_kb(user_id))

def update_participants_count(text: str, count: int) -> str:
    """Обновляет счетчик участников в тексте конкурса"""
    lines = text.split('\n')
    for i, line in enumerate(lines):
        if "Участников:" in line:
            parts = line.split("Участников:")
            if len(parts) > 1:
                lines[i] = f"{parts[0]}Участников: {count}"
                break
    return '\n'.join(lines)

# ===== Оригинальные вспомогательные функции =====

async def check_channel_subscriptions(user_id: int, bot: Bot) -> list:
    """Проверяет подписку пользователя на все обязательные каналы"""
    channels = await DB.all_channels_op()
    not_subscribed = []
    
    for channel in channels:
        channel_id = channel[0]
        try:
            chat_member = await bot.get_chat_member(chat_id=channel_id, user_id=user_id)
            if chat_member.status not in ['member', 'administrator', 'creator']:
                not_subscribed.append(channel)
        except Exception as e:
            print(f"Ошибка при проверке подписки: {e} \n\n {channel} \n\n ")
    
    return not_subscribed

async def handle_not_subscribed(message: types.Message, not_subscribed: list):
    """Обрабатывает случай, когда пользователь не подписан на каналы"""
    keyboard = InlineKeyboardBuilder()
    for channel in not_subscribed:
        keyboard.add(InlineKeyboardButton(
            text=f"📢 {channel[1]}",
            url=f"https://t.me/{channel[0].replace('@', '')}"
        ))
    keyboard.add(InlineKeyboardButton(
        text="✅ Я подписался",
        callback_data="op_proverka"
    ))
    keyboard.adjust(1)
    await message.answer(
        "Для использования бота подпишитесь на следующие каналы:",
        reply_markup=keyboard.as_markup()
    )

def parse_start_parameters(args: list) -> tuple:
    """Анализирует параметры команды /start и возвращает (referrer_id, check_uid, ref_user_id)"""
    referrer_id = None
    check_uid = None
    ref_user_id = None
    
    if len(args) > 1:
        param = args[1]
        if param.startswith("check_"):
            check_uid = param[len("check_"):]
        elif param.startswith("ref_"):
            ref_parts = param.split("_")
            if len(ref_parts) == 3:
                check_uid = ref_parts[1]
                ref_user_id = int(ref_parts[2])
        else:
            referrer_id = int(param)
    
    return referrer_id, check_uid, ref_user_id

async def register_new_user(message: types.Message, bot: Bot, referrer_id: int, check_uid: str, ref_user_id: int):
    """Регистрирует нового пользователя и обрабатывает реферальные связи"""
    user_id = message.from_user.id
    username = message.from_user.username
    await DB.add_user(user_id, username)
    await DB.increment_all_users()
    
    # Проверяем, есть ли у пользователя Telegram Premium
    try:
        is_premium = False  # await check_premium(username, bot)
    except:
        is_premium = False
    
    # Обработка разных типов реферальных связей
    if check_uid and not ref_user_id:
        await handle_check_creator_referral(user_id, username, bot, check_uid, is_premium)
    elif referrer_id:
        await handle_regular_referral(user_id, username, bot, referrer_id, is_premium)
    elif ref_user_id:
        await handle_check_referral_registration(user_id, username, bot, ref_user_id, is_premium)

async def handle_check_creator_referral(user_id: int, username: str, bot: Bot, check_uid: str, is_premium: bool):
    """Обрабатывает регистрацию через чек (пользователь становится рефералом создателя чека)"""
    check = await DB.get_check_by_uid(check_uid)
    if check:
        creator_id = check[2]
        mit_reward = 500 * 2 if is_premium else 500
        await DB.update_user_referrer_id(user_id, creator_id)
        await DB.add_balance(creator_id, mit_reward)
        await DB.add_star(creator_id, 1)
        await DB.add_star(user_id, 1)
        await DB.record_referral_earnings(referrer_id=creator_id, referred_user_id=user_id, amount=mit_reward)
        
        await send_message_safe(bot, creator_id,
                            f"👤 <a href='t.me/{username}'>Пользователь</a> c ID {user_id} перешел по вашему чеку и стал вашим рефералом.\n\n"
                            f"💸 Вам начислено {mit_reward} MitCoin и 1⭐️ за привлечение нового пользователя."
                            f"{' 🎉 Вы пригласили премиум-пользователя!' if is_premium else ''}",
                            reply_markup=back_menu_kb(user_id))

async def handle_regular_referral(user_id: int, username: str, bot: Bot, referrer_id: int, is_premium: bool):
    """Обрабатывает обычную реферальную ссылку"""
    mit_reward = 500 * 2 if is_premium else 500
    await DB.update_user_referrer_id(user_id, referrer_id)
    await DB.add_balance(referrer_id, mit_reward)
    await DB.add_star(referrer_id, 1)
    await DB.add_star(user_id, 1)
    await DB.record_referral_earnings(referrer_id=referrer_id, referred_user_id=user_id, amount=mit_reward)
    
    await send_message_safe(bot, referrer_id,
                        f"👤 <a href='t.me/{username}'>Пользователь</a> c ID {user_id} перешел по вашему чеку и стал вашим рефералом.\n\n"
                        f"💸 Вам начислено {mit_reward} MitCoin и 1⭐️ за привлечение нового пользователя."
                        f"{' 🎉 Вы пригласили премиум-пользователя!' if is_premium else ''}",
                        reply_markup=back_menu_kb(user_id))

async def handle_check_referral_registration(user_id: int, username: str, bot: Bot, ref_user_id: int, is_premium: bool):
    """Обрабатывает регистрацию через реферальную ссылку для чеков"""
    mit_reward = 500 * 2 if is_premium else 500
    await DB.update_user_referrer_id(user_id, ref_user_id)
    await DB.add_balance(ref_user_id, mit_reward)
    await DB.add_star(ref_user_id, 1)
    await DB.add_star(user_id, 1)
    await DB.record_referral_earnings(referrer_id=ref_user_id, referred_user_id=user_id, amount=mit_reward)
    
    await send_message_safe(bot, ref_user_id,
                        f"👤 <a href='t.me/{username}'>Пользователь</a> c ID {user_id} перешел по вашему чеку и стал вашим рефералом.\n\n"
                        f"💸 Вам начислено {mit_reward} MitCoin и 1⭐️ за привлечение нового пользователя."
                        f"{' 🎉 Вы пригласили премиум-пользователя!' if is_premium else ''}",
                        reply_markup=back_menu_kb(user_id))

async def handle_check_referral(message: types.Message, bot: Bot, check_uid: str, ref_user_id: int, state: FSMContext):
    """Обрабатывает активацию чека по реферальной ссылке"""
    user_id = message.from_user.id
    check = await DB.get_check_by_uid(check_uid)
    if not check:
        await message.answer("❌ Чек не найден.", reply_markup=back_menu_kb(user_id))
        return
    
    # Извлекаем данные чека
    check_id, uid, creator_id, check_type, check_sum, check_amount, check_description, \
    locked_for_user, password, OP_id, max_amount, ref_bonus, ref_fund, OP_name = check
    
    # Проверяем реферальный фонд
    if ref_fund <= 0:
        await message.answer("❌ Реферальный фонд для этого чека закончился.", reply_markup=back_menu_kb(user_id))
        return
    
    # Проверка подписки на канал
    if OP_id:
        try:
            chat = await bot.get_chat(OP_id)
            user_channel_status = await bot.get_chat_member(chat_id=OP_id, user_id=user_id)
            if user_channel_status.status not in ['member', 'administrator', 'creator']:
                await message.answer(f"💸 <b>Для активации этого чека необходимо подписаться на канал:</b> {OP_id}\n\n<i>После подписки повторите попытку</i>", reply_markup=back_menu_kb(user_id))
                return
        except Exception as e:
            logger.error(f'Ошибка при проверке подписки на канал - {e}')
            await message.answer(f'😢 <b>В данный момент невозможно проверить подписку, повторите попытку позже</b>\n', reply_markup=back_menu_kb(user_id))
            return
    
    # Проверка пароля
    if password:
        await message.answer("🔑 <b>Для получения чека необходимо ввести пароль:</b>", reply_markup=back_menu_kb(user_id))
        await state.set_state(checks.check_password1)
        await state.update_data(check_uid=check_uid)
        return
    
    # Проверяем, есть ли у пользователя Telegram Premium
    is_premium = False  # await check_premium(message.from_user.username, bot)
    
    # Активация чека
    await DB.add_balance(user_id, check_sum)
    await DB.process_check_activation(check_uid)
    await DB.add_activated_check(user_id, check_uid)
    await DB.check_fund_minus(check_id)
    
    # Начисляем реферальный бонус
    referral_amount = (check_sum * ref_bonus) // 100
    if is_premium:
        referral_amount *= 2
    
    await DB.add_balance(ref_user_id, referral_amount)
    
    # Сообщение активатору чека
    bot_username = (await bot.get_me()).username
    referral_link = f"https://t.me/{bot_username}?start=ref_{check_uid}_{user_id}"
    await message.answer(
        f"🥳 <b>Вы успешно активировали реферальный чек на {check_sum} MitCoin!</b>\n\n"
        f"🔗 <b>Ваша реферальная ссылка:</b>\n{referral_link}\n\n"
        f"💸 <b>Распространяйте эту ссылку и получайте {ref_bonus}% от суммы чека за каждого привлеченного пользователя!</b>",
        reply_markup=back_menu_kb(user_id)
    )
    
    # Сообщение рефереру
    await send_message_safe(
        bot,
        ref_user_id,
        f"💸 <b>Пользователь c ID {user_id} активировал ваш реферальный чек!</b>\n\n"
        f"💰 <b>Вам начислено {referral_amount} MitCoin за активацию чека.</b>"
        f"{' 🎉 Вы пригласили премиум-пользователя!' if is_premium else ''}",
        reply_markup=back_menu_kb(user_id)
    )
    
    # Уведомление создателю чека при исчерпании фонда
    if ref_fund - 1 == 0:
        await send_message_safe(
            bot,
            creator_id,
            f"⚠️ <b>Реферальный фонд для чека {check_uid} закончился.</b>\n\n"
            f"💵 Вы можете пополнить реферальный фонд, чтобы продолжить привлекать пользователей.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="Пополнить реферальный фонд", callback_data=f'refill_ref_fund_{check_id}')
            ]])
        )

async def handle_check_activation(message: types.Message, bot: Bot, check_uid: str, ref_user_id: int, state: FSMContext):
    """Обрабатывает активацию чека"""
    user_id = message.from_user.id
    username = message.from_user.username
    name = message.from_user.full_name
    usname = f'@{username}' if username else name
    
    check = await DB.get_check_by_uid(check_uid)
    if not check or await DB.is_check_activated(user_id, check_uid) or check[2] == user_id:
        await message.answer("❌ <b>Данный чек не может быть активирован по следующим возможным причинам:</b>\n\n<i>1) Этот чек был создан Вами\n2) Вы уже активировали данный чек\n3) Чек не существует, либо произошла ошибка</i>", reply_markup=back_menu_kb(user_id))
        return
    
    # Извлекаем данные чека
    check_id, uid, creator_id, check_type, check_sum, check_amount, check_description, \
    locked_for_user, password, OP_id, max_amount, ref_bonus, ref_fund, OP_name = check
    
    # Отправляем информацию о чеке
    check_info = f"💎 <b>Информация о чеке:</b>\n\n" \
                f"💸 Сумма: {check_sum} MitCoin\n" \
                f"📝 Описание: {check_description if check_description else 'Отсутствует'}\n\n"
    
    if OP_id:
        try:
            chat = await bot.get_chat(OP_id) 
            check_info += f"🔗 Подписка на канал: <a href='https://t.me/{chat.username}'>{chat.title}</a>\n"
        except Exception as e:
            logger.error(f'Ошибка при получении информации о канале: {e}')
            check_info += "🔗 Подписка на канал: Недоступно\n"
    
    if password:
        check_info += f"🔑 Пароль: Требуется\n"
    
    await message.answer(check_info, reply_markup=back_menu_kb(user_id))
    
    # Проверка чека для конкретного пользователя
    if check_description and check_description[0] == '@' and check_description != f'@{usname}':
        await message.answer("❌ <b>Этот чек предназначен для другого пользователя</b>", reply_markup=back_menu_kb(user_id))
        return
    elif check_description and check_description != user_id:
        await message.answer("❌ <b>Этот чек предназначен для другого пользователя</b>", reply_markup=back_menu_kb(user_id))
        return
    
    # Проверка подписки на канал
    if OP_id:
        try:
            chat = await bot.get_chat(OP_id)
            user_channel_status = await bot.get_chat_member(chat_id=OP_id, user_id=user_id)
            if user_channel_status.status not in ['member', 'administrator', 'creator']:
                kb = InlineKeyboardBuilder()
                kb.row(InlineKeyboardButton(text='Подписаться на канал', url=f'https://t.me/{chat.username}'))
                kb.row(InlineKeyboardButton(text='Назад', callback_data='back_menu'))
                kb.adjust(2)
                await message.answer(
                    f"💸 <b>Для активации этого чека необходимо подписаться на канал: @{chat.username}\n\n"
                    "<i>После подписки повторите попытку</i>",
                    reply_markup=kb.as_markup()
                )
                return
        except Exception as e:
            logger.error(f'Ошибка при проверке подписки на канал - {e}')
            await message.answer('😢 <b>В данный момент невозможно проверить подписку, повторите попытку позже</b>', reply_markup=back_menu_kb(user_id))
            return
    
    # Проверка пароля
    if password:
        await message.answer("🔑 <b>Для получения чека необходимо ввести пароль:</b>", reply_markup=back_menu_kb(user_id))
        await state.set_state(checks.check_password1)
        await state.update_data(check_uid=check_uid)
        return
    
    # Активация чека
    await DB.add_balance(user_id, check_sum)
    await DB.process_check_activation(check_uid)
    await DB.add_activated_check(user_id, check_uid)
    
    # Обработка реферального бонуса
    if ref_user_id and ref_bonus:
        referral_amount = (check_sum * ref_bonus) // 100
        await DB.add_balance(ref_user_id, referral_amount)
        await send_message_safe(bot, ref_user_id, f"💸 Вы получили {referral_amount} MitCoin за реферальную активацию чека.")
    
    # Уведомление создателю чека
    await send_message_safe(bot, creator_id, f"💸 Ваш чек на {check_sum} MitCoin был активирован пользователем {usname}.")
    
    # Создание реферальной ссылки (для мульти-чеков)
    if check_type == 2 and ref_bonus and not ref_user_id:
        bot_username = (await bot.get_me()).username
        referral_link = f"https://t.me/{bot_username}?start=ref_{check_uid}_{user_id}"
        await message.answer(
            f"🔗 <b>Ваша реферальная ссылка:</b>\n{referral_link}\n\n"
            f"💸 <b>Распространяйте эту ссылку и получайте {ref_bonus}% от суммы чека за каждого привлеченного пользователя!</b>",
            reply_markup=back_menu_kb(user_id)
        ) 
    
    await message.answer(f"🥳 <b>Вы успешно активировали чек на {check_sum} MitCoin</b>", reply_markup=back_menu_kb(user_id))


@router.message(checks.check_password1)
async def handle_check_password(message: types.Message, state: FSMContext, bot: Bot):
    user_data = await state.get_data()
    check_uid = user_data.get("check_uid")
    data = await state.get_data()
    ref_user_id = data.get("reffer_id")
    name = message.from_user.full_name
    usname = message.from_user.username
    if usname is None:
        usname = name
    else:
        usname = f'@{usname}'

    if not check_uid:
        await message.answer("❌ <i>Возникла ошибка. Повторите попытку позже...</i>", reply_markup=back_menu_kb(user_id))
        await state.clear()
        return

    check = await DB.get_check_by_uid(check_uid)
    if not check:
        await message.answer("❌ Чек не найден или уже был активирован.", reply_markup=back_menu_kb(user_id))
        await state.clear()
        return
    check_id = check[0]  # check_id (INTEGER)
    uid = check[1]  # uid (TEXT)
    user_id = check[2]  # user_id (INTEGER)
    check_type = check[3]  # type (INTEGER)
    check_sum = check[4]  # sum (INTEGER)
    check_amount = check[5]  # amount (INTEGER)
    check_description = check[6]  # description (TEXT)
    locked_for_user = check[7]  # locked_for_user (INTEGER)
    password = check[8]  # password (TEXT)
    OP_id = check[9]  # OP_id (TEXT)
    max_amount = check[10]  # max_amount (INTEGER)
    ref_bonus = check[11]  # ref_bonus (INTEGER)
    ref_fund = check[12]  # ref_fund (INTEGER)
    OP_name = check[13]  # OP_name (TEXT)

    if message.text == password:  # Проверка пароля
        await DB.add_balance(message.from_user.id, check_sum)
        await DB.process_check_activation(check_uid)
        await DB.add_activated_check(user_id=message.from_user.id, uid=check_uid)

        # Если чек активирован по реферальной ссылке, начисляем награду рефереру
        if ref_user_id and ref_bonus:
            referral_bonus = ref_bonus  # Получаем процент реферала из столбца ref_bonus
            referral_amount = (check_sum * referral_bonus) // 100
            await DB.add_balance(ref_user_id, referral_amount)
            await send_message_safe(bot, ref_user_id, f"💸 Вы получили {referral_amount} MitCoin за реферальную активацию чека.")

            # Уведомление создателю чека
            await send_message_safe(bot, user_id, f"💸 Ваш чек на {check[4]} MitCoin был активирован пользователем {usname}.")

            # Создаем реферальную ссылку для текущего пользователя
            bot_username = (await bot.get_me()).username
            referral_link = f"https://t.me/{bot_username}?start=ref_{check_uid}_{message.from_user.id}"
            await message.answer(
                f"🔗 <b>Ваша реферальная ссылка:</b>\n{referral_link}\n\n"
                f"💸 <b>Распространяйте эту ссылку и получайте {referral_bonus}% от суммы чека за каждого привлеченного пользователя!</b>",
                reply_markup=back_menu_kb(user_id)
            )

        await message.answer(f"🥳 <b>Вы успешно активировали чек на {check_sum} MitCoin</b>", reply_markup=back_menu_kb(user_id))
        await state.clear()
    else:
        await message.answer("❌ <b>Неверный пароль</b>", reply_markup=back_menu_kb(user_id))
        return 
