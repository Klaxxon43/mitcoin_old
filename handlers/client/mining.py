from untils.Imports import *
import API.usd as usd, time

mining = Router()

# Константы майнинга
MINING_RATE_PER_HOUR = 1000  # 1000 монет в час
MAX_MINING_HOURS = 2         # Максимум 2 часа майнинга
MIN_MINIG_TIME_MINUTES = 5  # Минимальное время для сбора (60 минут)


@mining.callback_query(F.data == 'mining')
async def mining_menu(callback: types.CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    mining_data = await DB.search_mining(user_id)

    if mining_data:
        # Создаем клавиатуру для управления майнингом
        kb = InlineKeyboardBuilder()
        kb.button(text='🆙 Улучшить', callback_data='upgrade_mining')
        kb.button(text='💸 Собрать', callback_data='mining_collect')
        kb.button(text='ℹ️ Информация', callback_data='mining_info')
        kb.button(text='🔙 Назад', callback_data='back_menu')
        kb.adjust(2, 1, 1)

        # Получаем данные о майнинге
        time_str = await DB.get_last_collection_time(user_id)
        
        try:
            # Парсим время последнего сбора
            time_from_str = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
            current_time = datetime.now()
            time_diff = current_time - time_from_str
            
            # Рассчитываем прошедшее время в секундах
            total_seconds = time_diff.total_seconds()
            total_minutes = total_seconds / 60
            total_hours = total_minutes / 60
            
            # Рассчитываем сколько можно собрать (не более MAX_MINING_HOURS)
            effective_mining_hours = min(total_hours, MAX_MINING_HOURS)
            mined_amount = effective_mining_hours * MINING_RATE_PER_HOUR
            
            # Рассчитываем оставшееся время до сбора (если меньше часа)
            remaining_minutes = max(0, MIN_MINIG_TIME_MINUTES - total_minutes)
            
            # Форматируем время для отображения
            display_hours = int(total_hours)
            display_minutes = int(total_minutes % 60)
            
            # Формируем сообщение
            mining_info = (
                f"⛏️ Майнинг $MICO\n\n"
                f"💰 Ставка: {MINING_RATE_PER_HOUR} $MICO/час\n"
                f"⏳ Максимальное время: {MAX_MINING_HOURS} часа\n\n"
                f"💎 Доступно к сбору: {mined_amount:.2f} $MICO\n"
                f"🕒 Замайнено времени: {display_hours}ч {display_minutes}мин\n\n"
            )
            
            if total_minutes < MIN_MINIG_TIME_MINUTES:
                mining_info += (
                    f"⚠ Для сбора нужно минимум {MIN_MINIG_TIME_MINUTES} минут майнинга\n"
                    f"⏱ Осталось: {int(remaining_minutes)} минут"
                )
            else:
                mining_info += f"✅ Можно собрать {mined_amount:.2f} $MICO"
                
        except Exception as e:
            logger.error(f"Ошибка при обработке времени: {e}")
            mining_info = (
                f"⛏️ Майнинг $MICO\n\n"
                f"⚠ Произошла ошибка при расчете времени\n"
                f"Попробуйте позже или обратитесь в поддержку"
            )

        await callback.message.edit_text(mining_info, reply_markup=kb.as_markup())
    else: 
        # try:
        #     # Отправляем счет для активации майнинга
        #     await bot.send_invoice(
        #         chat_id=user_id,
        #         title="Оплата майнинга",
        #         description="Чтобы воспользоваться майнингом, оплатите счёт.",
        #         payload=f"user_{user_id}_stars_199",
        #         provider_token="YOUR_PROVIDER_TOKEN", 
        #         currency="XTR",  
        #         prices=[{"label": "Mining", "amount": 199}],
        #         start_parameter="stars_payment"
        #     )
            kb = InlineKeyboardBuilder()
            kb.button(text='💳 Купить', callback_data='mining_buy')
            kb.button(text='ℹ️ Узнать', callback_data='mining_info')
            kb.button(text='🔙 Назад', callback_data='back_menu') 
            kb.adjust(1)
            try:
                await callback.message.edit_text('Что такое майнинг?', reply_markup=kb.as_markup())
            except:
                await callback.message.answer('Что такое майнинг?', reply_markup=kb.as_markup())

        # except Exception as e:
        #     logger.error(f"Ошибка при отправке счета: {e}")
        #     await callback.answer("Произошла ошибка при создании платежа", show_alert=True)


@mining.callback_query(F.data == 'mining_buy')
async def collect_mining(callback: types.CallbackQuery, bot: Bot):
    kb = InlineKeyboardBuilder()
    kb.button(text='⭐️ Купить за звёзды', callback_data='mining_buyStars')
    kb.button(text='💳 Купить рублями', callback_data='mining_buyRub') 
    kb.button(text='💲 CryptoBot', callback_data='mining_buyUSD') 
    kb.button(text='🔙 Назад', callback_data='mining') 
    kb.adjust(1)
    try:
        await callback.message.edit_text('Выберите способ оплаты: ', reply_markup=kb.as_markup())
    except:
        await callback.message.answer('Выберите способ оплаты: ', reply_markup=kb.as_markup())


@mining.callback_query(F.data == 'mining_buyUSD')
async def collect_mining(callback: types.CallbackQuery, bot: Bot):
    try:
        user_id = callback.from_user.id
        invoice = await usd.create_invoice(4.5, purpose='mining')
        btn = InlineKeyboardBuilder()
        btn.add(InlineKeyboardButton(text='⭐️ Оплатить счёт', url=invoice['url']))
        btn.add(InlineKeyboardButton(text='◀️ Назад', callback_data='BuyStars'))
        btn.adjust(1)
        await callback.message.edit_text('''
Вы можете купить майнинг через @send
Цена: 4.5💲
Для покупки оплатите счёт ниже в течении 3х минут''', reply_markup=btn.as_markup())
        

        ttime = 0
        while True:
            result = await usd.check_payment_status(invoice['id'], purpose='mining')
            if result:
                try:
                    await DB.add_mining(callback.from_user.id, 1)
                    await callback.message.edit_text('''
Вы успешно оплатили счёт!
Майнинг уже доступен на вашем аккаунте''', reply_markup=back_menu_kb(user_id))
                except:

                    await callback.message.answer('''
Вы успешно оплатили счёт!
Майнинг уже доступен на вашем аккаунте''', reply_markup=back_menu_kb(user_id))

                return
                
            await asyncio.sleep(5)
            ttime += 5
            if ttime == 180:
                return
    except Exception as e:
        logger.error(f"Error in process_stars_purchase: {e}")
        await callback.message.answer("❌ Произошла ошибка, попробуйте позже")


@mining.callback_query(F.data == 'mining_buyRub')
async def collect_mining(callback: types.CallbackQuery, bot: Bot):

    kb = InlineKeyboardBuilder()
    kb.button(text='🔙 Назад', callback_data='mining_buy') 

    await callback.message.edit_text('''
🌚 Вы можете также купить майнинг рублями
💲 Стоимость 349 рублей единоразово
📨 Для приобретения писать @Coin_var
    ''', reply_markup=kb.as_markup())

@mining.callback_query(F.data == 'mining_buyStars')
async def collect_mining(callback: types.CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    mining_data = await DB.search_mining(user_id)

    try:
        # Удаляем последнее сообщение бота в этом чате
        await bot.delete_message(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id
        )
    except: pass

    if mining_data:
        pass
    else:
        try:
            # Отправляем счет для активации майнинга
            await bot.send_invoice(
                chat_id=user_id,
                title="Оплата майнинга",
                description="Чтобы воспользоваться майнингом, оплатите счёт.",
                payload=f"user_{user_id}_stars_199",
                provider_token="", 
                currency="XTR",  
                prices=[{"label": "Mining", "amount": 199}],
                start_parameter="stars_payment"
            )
        except Exception as e:
            logger.error(f"Ошибка при отправке счета: {e}")
            await callback.answer("Произошла ошибка при создании платежа", show_alert=True)

@mining.callback_query(F.data == 'mining_collect')
async def collect_mining(callback: types.CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    deposit = await DB.get_deposit_mining(user_id)
    dep = deposit[0][0] if deposit else 0

    if not dep:
        await callback.answer("Майнинг не активирован", show_alert=True)
        return

    try:
        # Получаем данные о майнинге
        last_collection_time_str = await DB.get_last_collection_time(user_id)
        last_collection_time = datetime.strptime(last_collection_time_str, "%Y-%m-%d %H:%M:%S")
        
        # Рассчитываем прошедшее время
        current_time = datetime.now()
        time_diff = current_time - last_collection_time
        total_seconds = time_diff.total_seconds()
        
        # Преобразуем время в читаемый формат
        days = int(total_seconds // 86400)
        hours = int((total_seconds % 86400) // 3600)
        minutes = int((total_seconds % 3600) // 60)
        
        # Форматируем строку времени
        time_parts = []
        if days > 0:
            time_parts.append(f"{days} {'день' if days == 1 else 'дня' if 1 < days < 5 else 'дней'}")
        if hours > 0:
            time_parts.append(f"{hours} {'час' if hours == 1 else 'часа' if 1 < hours < 5 else 'часов'}")
        if minutes > 0 or (days == 0 and hours == 0):
            time_parts.append(f"{minutes} {'минута' if minutes == 1 else 'минуты' if 1 < minutes < 5 else 'минут'}")
        
        mined_time_str = ", ".join(time_parts)
        
        # Рассчитываем доступные для сбора средства
        total_hours = total_seconds / 3600
        effective_mining_hours = min(total_hours, MAX_MINING_HOURS)
        mined_amount = effective_mining_hours * MINING_RATE_PER_HOUR
        
        # Проверяем минимальное время
        if total_seconds < MIN_MINIG_TIME_MINUTES * 60:
            remaining_seconds = MIN_MINIG_TIME_MINUTES * 60 - total_seconds
            remaining_minutes = int(remaining_seconds // 60)
            remaining_seconds = int(remaining_seconds % 60)
            
            await callback.answer(
                f"Для сбора нужно майнить хотя бы {MIN_MINIG_TIME_MINUTES} минут\n"
                f"Осталось: {remaining_minutes} мин {remaining_seconds} сек", 
                show_alert=True
            )
            return
            
        # Обновляем данные
        await DB.add_balance(user_id, mined_amount)
        await DB.update_last_collection_time(user_id, current_time)
        
        # Формируем сообщение о сборе
        message_text = (
            f"💸 Успешно собрано!\n"
            f"⏳ Замайнено: {mined_time_str}\n"
            f"💰 Сумма: {mined_amount:.2f} $MICO\n\n"
            f"🔄 Майнинг перезапущен"
        )

        await DB.add_mined_from_all_stats(user_id, mined_amount)
        
        try:
            await callback.message.edit_text(message_text)
        except:
            await callback.message.answer(message_text)
            
        # Обновляем меню майнинга
        await asyncio.sleep(3)
        await mining_menu(callback, bot)
        
    except Exception as e:
        logger.error(f"Ошибка при сборе майнинга: {e}")
        await callback.answer("Произошла ошибка при сборе майнинга", show_alert=True)


@mining.callback_query(F.data == 'mining_info')
async def _(callback: types.CallbackQuery):
    btn = InlineKeyboardBuilder()
    btn.button(text='🔙 Назад', callback_data='mining')

    mining_info = f"""
⛏️ Информация по майнингу $MICO:

💰 {MINING_RATE_PER_HOUR} $MICO в час
⏳ Максимальное время майнинга: {MAX_MINING_HOURS} часа
🕒 Минимальное время для сбора: 1 час
💎 Максимальная сумма за сбор: {MINING_RATE_PER_HOUR * MAX_MINING_HOURS} $MICO

🔹 Система работает по следующим правилам:
- Майнинг начинается после покупки
- Собрать можно только после 5 минут майнинга
- Максимальная награда за один сбор - за 2 часа
- После сбора таймер сбрасывается

💡 Советы:
1. Собирайте награду каждые 2 часа для максимальной выгоды. Чем чаще вы собираете, тем стабильнее доход
2. Улучшайте майнинг для большего дохода (Скоро будет доступно...) 
    """

    await callback.message.edit_text(mining_info, reply_markup=btn.as_markup())



@mining.callback_query(F.data == 'upgrade_mining')
async def _(callback: types.CallbackQuery):
    kb = InlineKeyboardBuilder()
    kb.button(text='Назад', callback_data='mining')
    await callback.message.edit_text('Скоро будет доступно...', reply_markup=kb.as_markup())