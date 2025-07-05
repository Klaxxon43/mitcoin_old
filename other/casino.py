from untils.Imports import *

casino = Router()

task_cache = {}
task_cache_chat = {}


# CHECK_CHAT_ID = -4792065005 # ID чата для проверки заданий
# DB_CHAT_ID = -4683486408
# INFO_ID = -4784146602
# TASKS_CHAT_ID = -1002291978719



# Обновленные константы коэффициентов
GAME_COEFFICIENTS = {
    'dice': {
        'even': 1.5,      # Чётное
        'odd': 1.5,       # Нечётное
        'greater': 1.5,    # Больше
        'less': 1.5,       # Меньше
        'exact': 3      # Конкретное число
    },
    'basketball': 1.5,    # Баскетбол
    'football': 1.5,      # Футбол
    'darts': {          # Дартс
        'bullseye': 3,   # Попадание в центр
        'outer': 0     # Попадание по краям
    }, 
    'casino': {         # Казино
        'three_7': 1,   # Три семерки
        'three_any': 3, # Три одинаковых (не 7)
        'two': 0       # Два одинаковых
    }
} 

class GameStates(StatesGroup):
    waiting_for_bet = State()
    waiting_for_exact_number = State()
    waiting_for_custom_bet = State()
    request_message_id=State()

@casino.callback_query(F.data == "game")
async def show_games_menu(callback: types.CallbackQuery):
    try:
        a = await DB.get_user_balance_game(callback.from_user.id)
    except:
        await DB.add_user_on_game(callback.from_user.id, callback.from_user.username)
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="💸 Баланс", callback_data="balance_game"),
        InlineKeyboardButton(text="🎲 Кубики", callback_data="game_dice"),
        InlineKeyboardButton(text="🏀 Баскетбол", callback_data="game_basketball"),
        # InlineKeyboardButton(text="⚽ Футбол", callback_data="game_football"),
        InlineKeyboardButton(text="🎯 Дартс", callback_data="game_darts"),
        InlineKeyboardButton(text="🎰 Казино", callback_data="game_casino"),
        InlineKeyboardButton(text="🎮 Игровая статистика", callback_data="gameStatics"),
        # InlineKeyboardButton(text="ℹ️ ИНФО", callback_data="gameInfo"),
        InlineKeyboardButton(text="🔙 В меню", callback_data="back_menu") 
    )
    builder.adjust(1, 2, 2, 1, repeat=True)
    
    await callback.message.edit_text(
        "🎮 <b>Игровой зал</b>\n\n"
        "Выберите игру, в которую хотите сыграть:",
        reply_markup=builder.as_markup()
    )


# @casino.callback_query(F.data == "game")
# async def _(callback: types.CallbackQuery):
#     await callback.message.edit_text('''
      
#                                      ''')

@casino.callback_query(F.data == 'gameStatics')
async def show_game_statistics(callback: types.CallbackQuery):
    kb = InlineKeyboardBuilder()
    kb.add(InlineKeyboardButton(text="🔙 В меню", callback_data="game"))

    try:
        stats = await DB.get_game_statics()
        stats_mico = await DB.get_game_financial_stats(currency='mico')
        stats_stars = await DB.get_game_financial_stats(currency='stars')
        
        if not stats or len(stats) < 2:
            await callback.message.answer(
                "❌ Статистика пока недоступна",
                reply_markup=kb.as_markup()
            )
            return

        total_stats = stats[0]  # Вся статистика
        today_stats = stats[1]  # Статистика за сегодня

        # Форматируем сообщение
        message_text = (
            "🎮 <b>Статистика игр</b>\n\n"
            "📊 <b>За все время:</b>\n"
            f"▪️ Всего ставок: {total_stats['game_wins'] + total_stats['game_losses']}\n"
            f"▪️ Побед: {total_stats['game_wins']}\n"
            f"▪️ Поражений: {total_stats['game_losses']}\n"
            f"▪️ Сыграно в кости: {total_stats['dice_played']}\n"
            f"▪️ Сыграно в баскетбол: {total_stats['basketball_played']}\n"
#            f"▪️ Сыграно в футбол: {total_stats['football_played']}\n"
            f"▪️ Сыграно в дартс: {total_stats['darts_played']}\n"
            f"▪️ Сыграно в казино: {total_stats['casino_played']}\n"
            f"▪️ Выведено средств: {total_stats['withdraw_from_game']} ⭐\n\n"
            
            "📅 <b>За сегодня:</b>\n"
            f"▪️ Всего ставок: {today_stats['game_wins'] + today_stats['game_losses']}\n"
            f"▪️ Побед: {today_stats['game_wins']}\n"
            f"▪️ Поражений: {today_stats['game_losses']}\n"
            f"▪️ Сыграно в кости: {today_stats['dice_played']}\n"
            f"▪️ Сыграно в баскетбол: {today_stats['basketball_played']}\n"
#            f"▪️ Сыграно в футбол: {today_stats['football_played']}\n"
            f"▪️ Сыграно в дартс: {today_stats['darts_played']}\n"
            f"▪️ Сыграно в казино: {today_stats['casino_played']}\n"
            f"▪️ Выведено средств: {today_stats['withdraw_from_game']} ⭐\n\n"
        )
        if callback.from_user.id in ADMINS_ID:
            message_text += (
            "💰 <b>Финансовая статистика (MICO):</b>\n"
            f"▪️ Всего поставлено: {stats_mico['total']['bet']:.2f}\n"
            f"▪️ Всего выиграно: {stats_mico['total']['win']:.2f}\n"
            f"▪️ Всего проиграно: {stats_mico['total']['loss']:.2f}\n"
            f"▪️ Чистая прибыль: {stats_mico['total']['profit']:.2f}\n\n"
            
            "🌟 <b>Финансовая статистика (STARS):</b>\n"
            f"▪️ Всего поставлено: {stats_stars['total']['bet']:.2f}\n"
            f"▪️ Всего выиграно: {stats_stars['total']['win']:.2f}\n"
            f"▪️ Всего проиграно: {stats_stars['total']['loss']:.2f}\n"
            f"▪️ Чистая прибыль: {stats_stars['total']['profit']:.2f}"
        )

        await callback.message.edit_text(
            message_text,
            reply_markup=kb.as_markup(),
            parse_mode='HTML'
        )

    except Exception as e:
        logger.error(f"Error showing game statistics: {e}", exc_info=True)
        await callback.message.answer(
            "❌ Произошла ошибка при загрузке статистики",
            reply_markup=kb.as_markup()
        )

@casino.callback_query(F.data.startswith("game_") & ~F.data.startswith("game_dice"))
async def start_game(callback: types.CallbackQuery):
    """Начало игры (общий обработчик для баскетбола, футбола, дартс, казино)"""
    try:

        game_type = callback.data.split('_')[1]
        user_id = callback.from_user.id
        current_bet = await DB.get_user_bet(user_id)
        current_currency = await DB.get_user_currency(user_id)
        currency_symbol = "🪙" if current_currency == "mico" else "⭐"
        
        game_names = {
            'basketball': "🏀 Баскетбол",
            'football': "⚽ Футбол",
            'darts': "🎯 Дартс",
            'casino': "🎰 Казино"
        }
        
        builder = InlineKeyboardBuilder()
        
        # Кнопка изменения ставки (теперь с функционалом указания своей ставки)
        builder.row(
            InlineKeyboardButton(text="➖", callback_data=f"decrease_bet_{game_type}"),
            InlineKeyboardButton(text=f"{current_bet} {currency_symbol}", callback_data=f"set_custom_bet_{game_type}"),
            InlineKeyboardButton(text="➕", callback_data=f"increase_bet_{game_type}")
        )
        
        # Кнопка смены валюты
        builder.row(InlineKeyboardButton(text=f"Сменить валюту ({currency_symbol})", callback_data=f"change_currency_{game_type}"))
        
        # Кнопка сделать ставку
        builder.row(InlineKeyboardButton(text="🎯 Сделать ставку", callback_data=f"play_{game_type}"))
        
        # Кнопка назад
        builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="game"))
        
        try:
            # Формируем текст с коэффициентами в зависимости от типа игры
            if game_type == 'darts':
                coefficients_text = (
                    f"🎯 Коэффициенты дартс:\n"
                    f"▪ Попадание в центр (🎯): x{GAME_COEFFICIENTS['darts']['bullseye']}\n"
                    f"▪ Попадание по краям: x{GAME_COEFFICIENTS['darts']['outer']}"
                )
            elif game_type == 'casino':
                coefficients_text = (
                    f"🎰 Коэффициенты казино:\n"
                    f"▪ Три 7️⃣7️⃣7️⃣: x{GAME_COEFFICIENTS['casino']['three_7']}\n"
                    f"▪ Три одинаковых: x{GAME_COEFFICIENTS['casino']['three_any']}\n"
                )
            else:
                # Для игр с простыми коэффициентами (футбол, баскетбол и т.д.)
                coefficients_text = f"▪ Коэффициент: x{GAME_COEFFICIENTS[game_type]}"

            await callback.message.edit_text(
                f"{game_names[game_type]} <b>Игра</b>\n\n"
                f"▪️ Текущая ставка: <b>{current_bet} {currency_symbol}</b>\n\n"
                f"{coefficients_text}\n\n"
                "Сделайте ставку и нажмите кнопку ниже:",
                reply_markup=builder.as_markup()
            )
        except Exception as e:
            logger.error(f"Error displaying game info: {e}")
            await callback.answer("Произошла ошибка при отображении информации об игре")

        except Exception as e:
            print(f"Error editing message: {e}")
            await callback.answer()
    except Exception as e:
        print(f"Error in start_game: {e}")


# Обработчик смены валюты
@casino.callback_query(F.data.startswith("change_currency_"))
async def change_currency_handler(callback: types.CallbackQuery, bot: Bot):
    """Изменение валюты для ставок"""
    try:
        game_type = callback.data.split('_')[2]
        user_id = callback.from_user.id
        current_currency = await DB.get_user_currency(user_id)
        
        # Меняем валюту на противоположную
        new_currency = 'stars' if current_currency == 'mico' else 'mico'
        await DB.update_user_currency(user_id, new_currency)
        
        # Создаем fake callback для повторного вызова меню
        class FakeCallback:
            def __init__(self, from_user, message):
                self.from_user = from_user 
                self.message = message
        
        fake_callback = FakeCallback(callback.from_user, callback.message)
        fake_callback.data = f"game_{game_type}"
        
        # Возвращаемся в меню игры
        if game_type == 'dice':
            await start_dice_game(fake_callback)
        else:
            await start_game(fake_callback)
            
        await callback.answer(f"Валюта изменена на {'Stars ⭐' if new_currency == 'stars' else '$MICO 🪙'}")
    except Exception as e:
        logger.error(f"Error in change_currency_handler: {e}")
        await callback.answer("Произошла ошибка, попробуйте позже")


# Обработчики изменения ставки для всех игр
@casino.callback_query(F.data.startswith("increase_bet_"))
async def increase_bet_handler(callback: types.CallbackQuery):
    """Увеличение ставки на 10% для любой игры"""
    try:
        game_type = callback.data.split('_')[2]
        user_id = callback.from_user.id
        current_bet = await DB.get_user_bet(user_id)
        
        # Увеличиваем ставку на 10% и округляем до 2 знаков
        new_bet = round(current_bet * 1.1, 2)
        
        # Обновляем ставку в базе
        await DB.update_user_bet(user_id, new_bet)
        
        # Обновляем интерфейс 
        if game_type == 'dice':
            await start_dice_game(callback)
        else:
            await start_game(callback) 
        await callback.answer(f"+10%")

    except Exception as e:
        logger.error(f"Error in increase_bet_handler: {e}", exc_info=True)
        await callback.answer("Произошла ошибка, попробуйте позже")

@casino.callback_query(F.data.startswith("decrease_bet_"))
async def decrease_bet_handler(callback: types.CallbackQuery):
    """Уменьшение ставки на 10% для любой игры"""
    try:
        game_type = callback.data.split('_')[2]
        user_id = callback.from_user.id
        current_bet = await DB.get_user_bet(user_id)
        
        # Уменьшаем ставку на 10% и округляем до 2 знаков
        new_bet = round(current_bet * 0.9, 2)
        
        # Минимальная ставка 0.01
        new_bet = max(0.01, new_bet)
        
        # Обновляем ставку в базе
        await DB.update_user_bet(user_id, new_bet)
        
        # Обновляем интерфейс
        if game_type == 'dice':
            await start_dice_game(callback)
        else:
            await start_game(callback)
        await callback.answer(f"-10%")

    except Exception as e:
        logger.error(f"Error in decrease_bet_handler: {e}", exc_info=True)
        await callback.answer("Произошла ошибка, попробуйте позже")

# Обработчики запроса пользовательской ставки для всех игр
@casino.callback_query(F.data.startswith("set_custom_bet_"))
async def ask_for_custom_bet(callback: types.CallbackQuery, state: FSMContext):
    """Запрос пользовательской ставки для любой игры"""
    try:
        game_type = callback.data.split('_')[3]
        await state.update_data(game_type=game_type,
                                request_message_id=callback.message.message_id)
        
        await callback.message.edit_text(
            "💰 Введите вашу новую ставку (минимальная ставка 1):",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data=f"game_{game_type}")]
            ])
        )
        await state.set_state(GameStates.waiting_for_custom_bet)
    except Exception as e:
        print(f"Error in ask_for_custom_bet: {e}")
        await callback.answer("Произошла ошибка, попробуйте позже")


@casino.message(GameStates.waiting_for_custom_bet)
async def set_custom_bet(message: types.Message, state: FSMContext, bot: Bot):
    """Установка пользовательской ставки с проверкой баланса"""
    try:
        user_id = message.from_user.id
        user_data = await state.get_data()
        game_type = user_data.get('game_type')
        
        # Получаем текущий баланс и валюту
        current_currency = await DB.get_user_currency(user_id)
        balance = await DB.get_user_balance_for_game(user_id)
        currency_symbol = "🪙" if current_currency == "mico" else "⭐"

        try:
            new_bet = int(message.text)
            if new_bet < 1:
                await message.answer("❌ Минимальная ставка 1!")
                return
                
            # Проверка на превышение баланса
            if new_bet > balance:
                await message.answer(f"❌ Недостаточно средств! Ваш баланс: {balance} {currency_symbol}")
                return
            
            # Сохраняем ставку как есть (без округления)
            await DB.update_user_bet(user_id, new_bet)
            
            # Удаляем сообщение с вводом ставки
            try:
                chat_id = message.chat.id
                request_message_id = user_data.get('request_message_id')
                await bot.delete_message(chat_id, message.message_id)  # Сообщение пользователя
                if request_message_id:
                    await bot.delete_message(chat_id, request_message_id)  # Наш запрос
            except Exception as e:
                print(f"Ошибка при удалении сообщений: {e}")
            
            # Отправляем подтверждение с кнопкой продолжить
            markup = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text="▶ Продолжить играть", 
                    callback_data=f"game_{game_type}"
                )]
            ])
            
            await message.answer(
                f"✅ Ставка успешно изменена на {new_bet} {currency_symbol}",
                reply_markup=markup
            )
            
        except ValueError:
            await message.answer("❌ Неверная сумма ставки! Введите целое число:")
            return
            
    except Exception as e:
        logger.error(f"Error in set_custom_bet: {e}")
        await message.answer("Произошла ошибка, попробуйте позже")
    finally:
        await state.clear()



# Обновленный обработчик игры в футбол
@casino.callback_query(F.data == "play_football")
async def play_football_game(callback: types.CallbackQuery, bot: Bot):
    """Обработка игры в футбол с учетом выбранной валюты"""
    try:
        user_id = callback.from_user.id
        current_bet = await DB.get_user_bet(user_id)
        balance = await DB.get_user_balance_for_game(user_id)
        currency = await DB.get_user_currency(user_id)
        currency_symbol = "🪙" if currency == "mico" else "⭐"
        
        if current_bet > balance:
            builder = InlineKeyboardBuilder()
            builder.add(InlineKeyboardButton(text="Пополнить баланс", callback_data="top_up"))
            builder.add(InlineKeyboardButton(text="🔙 Назад", callback_data="game_football"))
            
            await callback.message.edit_text(
                f"❌ Недостаточно средств на балансе!\n"
                f"Ваш баланс: {balance:.2f} {currency_symbol}\n"
                f"Требуется: {current_bet:.2f} {currency_symbol}",
                reply_markup=builder.as_markup()
            )
            return
        
        football_message = await callback.message.answer_dice(emoji=DiceEmoji.FOOTBALL)
        football_result = football_message.dice.value
        
        is_goal = football_result in [3, 4, 5]
        coefficient = GAME_COEFFICIENTS['football']

        await DB.increment_statistics(1, 'football_played')
        await DB.increment_statistics(2, 'football_played')
        
        if is_goal:
            win_amount = current_bet * coefficient
            result_text = f"⚽ <b>ГОЛ!</b> Вы выиграли {win_amount:.2f} {currency_symbol}!"
            result_db = 'win'
            await DB.increment_statistics(1, 'game_wins')
            await DB.increment_statistics(2, 'game_wins')
        else:
            win_amount = -current_bet
            result_text = f"❌ Промах! Вы проиграли {current_bet:.2f} {currency_symbol}."
            result_db = 'loss'
            await DB.increment_statistics(1, 'game_losses')
            await DB.increment_statistics(2, 'game_losses')

        await update_game_stats(user_id, callback.from_user.username, current_bet, win_amount, result_db, 'football')
        new_balance = await DB.get_user_balance_for_game(user_id)
        
        result_message = (
            f"⚽ <b>Футбол - результат</b>\n\n"
            f"▪ Ваша ставка: <b>{current_bet:.2f} {currency_symbol}</b>\n"
            f"▪ Результат: <b>{'Гол!' if is_goal else 'Промах'}</b>\n"
            f"▪ Коэффициент: <b>x{coefficient if is_goal else 0}</b>\n\n"
            f"{result_text}\n\n"
            f"💰 Новый баланс: <b>{new_balance:.2f} {currency_symbol}</b>"
        )
        
        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(text="🔄 Играть снова", callback_data="play_football"))
        builder.add(InlineKeyboardButton(text="🎮 Другие игры", callback_data="game"))
        
        await asyncio.sleep(3)
        await callback.message.answer(result_message, reply_markup=builder.as_markup())
        
    except Exception as e:
        logger.error(f"Error in play_football_game: {e}", exc_info=True)
        await callback.answer("Произошла ошибка, попробуйте позже")

@casino.callback_query(F.data == "play_casino")
async def play_casino_game(callback: types.CallbackQuery, bot: Bot):
    try:
        user_id = callback.from_user.id
        current_bet = await DB.get_user_bet(user_id)
        balance = await DB.get_user_balance_for_game(user_id)
        currency = await DB.get_user_currency(user_id)
        currency_symbol = "🪙" if currency == "mico" else "⭐"
        
        if current_bet > balance:
            builder = InlineKeyboardBuilder()
            builder.add(InlineKeyboardButton(text="Пополнить баланс", callback_data="top_up"))
            builder.add(InlineKeyboardButton(text="🔙 Назад", callback_data="game_casino"))
            
            await callback.message.edit_text(
                f"❌ Недостаточно средств на балансе!\n"
                f"Ваш баланс: {balance:.2f} {currency_symbol}\n"
                f"Требуется: {current_bet:.2f} {currency_symbol}",
                reply_markup=builder.as_markup()
            )
            return
        
        await DB.increment_statistics(1, 'casino_played')
        await DB.increment_statistics(2, 'casino_played')
        
        # Показываем коэффициенты перед игрой
        coefficients_text = (
            "🎰 <b>Коэффициенты казино:</b>\n"
            f"▪ Три 7️⃣7️⃣7️⃣: x{GAME_COEFFICIENTS['casino']['three_7']}\n"
            f"▪ Три одинаковых: x{GAME_COEFFICIENTS['casino']['three_any']}\n"
        )
        
        #await callback.message.answer(coefficients_text)
        
        slot_message = await callback.message.answer_dice(emoji=DiceEmoji.SLOT_MACHINE)
        slot_result = slot_message.dice.value
        
        combo = get_combo_text(slot_result)
        
        if combo.count("семь") == 3:
            coefficient = GAME_COEFFICIENTS['casino']['three_7']
            result_type = "ДЖЕКПОТ! Три семерки!"
            result_db = 'big_win'
            await DB.increment_statistics(1, 'game_wins')
            await DB.increment_statistics(2, 'game_wins')
        elif len(set(combo)) == 1:
            coefficient = GAME_COEFFICIENTS['casino']['three_any']
            result_type = f"Три одинаковых символа ({combo[0]})!"
            result_db = 'win'
            await DB.increment_statistics(1, 'game_wins')
            await DB.increment_statistics(2, 'game_wins')

        elif len(set(combo)) == 2:
            coefficient = GAME_COEFFICIENTS['casino']['two']
            result_type = f"Два одинаковых символа ({max(set(combo), key=combo.count)})"
            result_db = 'loss'
            await DB.increment_statistics(1, 'game_losses')
            await DB.increment_statistics(2, 'game_losses')

        else:
            coefficient = 0
            result_type = "Неудача"
            result_db = 'loss'
            await DB.increment_statistics(1, 'game_losses')
            await DB.increment_statistics(2, 'game_losses')


        win_amount = round(current_bet * coefficient - current_bet, 2) if coefficient > 0 else -current_bet
        
        if coefficient > 0:
            result_text = f"🎰 <b>{result_type}</b> Вы выиграли {win_amount:.2f} {currency_symbol}!"
        else:
            result_text = f"❌ {result_type} Вы проиграли {current_bet:.2f} {currency_symbol}."
        
        await update_game_stats(user_id, callback.from_user.username, current_bet, win_amount, result_db, 'casino')
        new_balance = await DB.get_user_balance_for_game(user_id)
        
        result_message = (
            f"🎰 <b>Казино - результат</b>\n\n"
            f"▪ Ваша ставка: <b>{current_bet:.2f} {currency_symbol}</b>\n"
            f"▪ Комбинация: {' | '.join(combo)}\n"
            f"▪ {result_type}\n"
            f"▪ Коэффициент: <b>x{coefficient if coefficient > 0 else 0}</b>\n\n"
            f"{result_text}\n\n"
            f"💰 Новый баланс: <b>{new_balance:.2f} {currency_symbol}</b>"
        )
        
        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(text="🔄 Играть снова", callback_data="play_casino"))
        builder.add(InlineKeyboardButton(text="🎮 Другие игры", callback_data="game"))
        
        await asyncio.sleep(2)
        await callback.message.answer(result_message, reply_markup=builder.as_markup())
        
    except Exception as e:
        logger.error(f"Error in play_casino_game: {e}", exc_info=True)
        await callback.answer("Произошла ошибка, попробуйте позже")


@casino.callback_query(F.data == "play_darts")
async def play_darts_game(callback: types.CallbackQuery, bot: Bot):
    try:
        user_id = callback.from_user.id
        current_bet = await DB.get_user_bet(user_id)
        balance = await DB.get_user_balance_for_game(user_id)
        currency = await DB.get_user_currency(user_id)
        currency_symbol = "🪙" if currency == "mico" else "⭐"
        
        if current_bet > balance:
            builder = InlineKeyboardBuilder()
            builder.add(InlineKeyboardButton(text="Пополнить баланс", callback_data="top_up"))
            builder.add(InlineKeyboardButton(text="🔙 Назад", callback_data="game_darts"))
            
            await callback.message.edit_text(
                f"❌ Недостаточно средств на балансе!\n"
                f"Ваш баланс: {balance:.2f} {currency_symbol}\n"
                f"Требуется: {current_bet:.2f} {currency_symbol}",
                reply_markup=builder.as_markup()
            )
            return
        
        await DB.increment_statistics(1, 'darts_played')
        await DB.increment_statistics(2, 'darts_played')

        # Показываем коэффициенты перед игрой
        coefficients_text = (
            "🎯 <b>Коэффициенты дартс:</b>\n"
            f"▪ Попадание в центр (🎯): x{GAME_COEFFICIENTS['darts']['bullseye']}\n"
        )
        
        #await callback.message.answer(coefficients_text)
        
        darts_message = await callback.message.answer_dice(emoji=DiceEmoji.DART)
        darts_result = darts_message.dice.value
        
        if darts_result == 6:
            coefficient = GAME_COEFFICIENTS['darts']['bullseye']
            result_type = "Попадание в центр!"
            result_db = 'win'
            await DB.increment_statistics(1, 'game_wins')
            await DB.increment_statistics(2, 'game_wins')
        else:
            coefficient = 0
            result_type = "Промах!"
            result_db = 'loss'
            await DB.increment_statistics(1, 'game_losses')
            await DB.increment_statistics(2, 'game_losses')
        
        win_amount = round(current_bet * coefficient - current_bet, 2) if coefficient > 0 else -current_bet
        
        if coefficient > 0:
            result_text = f"🎯 <b>{result_type}</b> Вы выиграли {win_amount:.2f} {currency_symbol}!"
        else:
            result_text = f"❌ {result_type} Вы проиграли {current_bet:.2f} {currency_symbol}."
        
        await update_game_stats(user_id, callback.from_user.username, current_bet, win_amount, result_db, 'darts')
        new_balance = await DB.get_user_balance_for_game(user_id)
        
        result_message = (
            f"🎯 <b>Дартс - результат</b>\n\n"
            f"▪ Ваша ставка: <b>{current_bet:.2f} {currency_symbol}</b>\n"
            f"▪ Результат броска: <b>{darts_result}</b>\n"
            f"▪ {result_type}\n"
            f"▪ Коэффициент: <b>x{coefficient if int(coefficient) > 0 else 0}</b>\n\n"
            f"{result_text}\n\n"
            f"💰 Новый баланс: <b>{new_balance:.2f} {currency_symbol}</b>"
        )
        
        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(text="🔄 Играть снова", callback_data="play_darts"))
        builder.add(InlineKeyboardButton(text="🎮 Другие игры", callback_data="game"))
        
        await asyncio.sleep(2)
        await callback.message.answer(result_message, reply_markup=builder.as_markup())
        
    except Exception as e:
        logger.error(f"Error in play_darts_game: {e}", exc_info=True)
        await callback.answer("Произошла ошибка, попробуйте позже")

def get_combo_text(dice_value: int):
    """
    Возвращает то, что было на конкретном дайсе-казино
    :param dice_value: значение дайса (число)
    :return: массив строк, содержащий все выпавшие элементы в виде текста

    Альтернативный вариант (ещё раз спасибо t.me/svinerus):
        return [casino[(dice_value - 1) // i % 4]for i in (1, 4, 16)]
    """
    #           0       1         2        3
    values = ["BAR", "виноград", "лимон", "семь"]

    dice_value -= 1
    result = []
    for _ in range(3):
        result.append(values[dice_value % 4])
        dice_value //= 4
    return result

@casino.callback_query(F.data == "play_basketball")
async def play_basketball_game(callback: types.CallbackQuery, bot: Bot):
    try:
        user_id = callback.from_user.id
        current_bet = await DB.get_user_bet(user_id)
        balance = await DB.get_user_balance_for_game(user_id)
        currency = await DB.get_user_currency(user_id)
        currency_symbol = "🪙" if currency == "mico" else "⭐"
        
        if current_bet > balance:
            builder = InlineKeyboardBuilder()
            builder.add(InlineKeyboardButton(text="Пополнить баланс", callback_data="top_up"))
            builder.add(InlineKeyboardButton(text="🔙 Назад", callback_data="game_basketball"))
            
            await callback.message.edit_text(
                f"❌ Недостаточно средств на балансе!\n"
                f"Ваш баланс: {balance:.2f} {currency_symbol}\n"
                f"Требуется: {current_bet:.2f} {currency_symbol}",
                reply_markup=builder.as_markup()
            )
            return
        
        await DB.increment_statistics(1, 'basketball_played')
        await DB.increment_statistics(2, 'basketball_played')
        basketball_message = await callback.message.answer_dice(emoji=DiceEmoji.BASKETBALL)
        basketball_result = basketball_message.dice.value
        
        is_basket = basketball_result in [4, 5]
        coefficient = GAME_COEFFICIENTS['basketball']
        
        if is_basket:
            win_amount = current_bet * coefficient
            result_text = f"🏀 <b>ПОПАДАНИЕ!</b> Вы выиграли {win_amount:.2f} {currency_symbol}!"
            result_db = 'win'
            await DB.increment_statistics(1, 'game_wins')
            await DB.increment_statistics(2, 'game_wins')
        else:
            win_amount = -current_bet
            result_text = f"❌ Промах! Вы проиграли {current_bet:.2f} {currency_symbol}."
            result_db = 'loss'
            await DB.increment_statistics(1, 'game_losses')
            await DB.increment_statistics(2, 'game_losses')
        
        await update_game_stats(user_id, callback.from_user.username, current_bet, win_amount, result_db, 'basketball')
        new_balance = await DB.get_user_balance_for_game(user_id)
        
        result_message = (
            f"🏀 <b>Баскетбол - результат</b>\n\n"
            f"▪ Ваша ставка: <b>{current_bet:.2f} {currency_symbol}</b>\n"
            f"▪ Результат броска: <b>{'Попадание' if is_basket else 'Промах'}</b>\n"
            f"▪ Коэффициент: <b>x{coefficient if is_basket else 0}</b>\n\n"
            f"{result_text}\n\n"
            f"💰 Новый баланс: <b>{new_balance:.2f} {currency_symbol}</b>"
        )
        
        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(text="🔄 Играть снова", callback_data="play_basketball"))
        builder.add(InlineKeyboardButton(text="🎮 Другие игры", callback_data="game"))
        
        await asyncio.sleep(2)
        await callback.message.answer(result_message, reply_markup=builder.as_markup())
        
    except Exception as e:
        logger.error(f"Error in play_basketball_game: {e}", exc_info=True)
        await callback.answer("Произошла ошибка, попробуйте позже")


async def update_game_stats(user_id: int, username: str, bet: float, win_amount: float, result_type: str, game_mode: str):
    """Обновление статистики игры с учетом выбранной валюты"""
    currency = await DB.get_user_currency(user_id)
    
    # Обновляем баланс в выбранной валюте
    await DB.update_user_balance_for_game(user_id, win_amount)

    currency = await DB.get_user_currency(user_id)
    
    # Обновляем статистику
    await DB.update_game_stats(user_id, stat_type='bet')
    await DB.update_game_stats(user_id, stat_type=result_type)
    await DB.add_game_history(
        user_id=user_id,
        amount=bet,
        result=result_type,
        game_mode=game_mode,
        currency=currency
    )
    
    await DB.update_game_mode_stats(
        user_id=user_id,
        game_mode=game_mode,
        result=result_type
    )


@casino.callback_query(F.data == "game_dice")
async def start_dice_game(callback: types.CallbackQuery):
    """Начало игры в кубики с отображением текущей ставки и валюты"""
    try:
        user_id = callback.from_user.id
        current_bet = await DB.get_user_bet(user_id)
        current_currency = await DB.get_user_currency(user_id)
        currency_symbol = "🪙" if current_currency == "mico" else "⭐"
        
        builder = InlineKeyboardBuilder()
        
        # Кнопки изменения ставки
        builder.row(
            InlineKeyboardButton(text="➖", callback_data="decrease_bet_dice"),
            InlineKeyboardButton(text=f"{current_bet} {currency_symbol}", callback_data="set_custom_bet_dice"),
            InlineKeyboardButton(text="➕", callback_data="increase_bet_dice")
        )
        
        # Кнопка смены валюты
        builder.row(InlineKeyboardButton(text=f"Сменить валюту ({currency_symbol})", callback_data="change_currency_dice"))
        
        # Кнопки выбора типа ставки
        builder.row(
            InlineKeyboardButton(text="2️⃣4️⃣6️⃣ Чётное (x2)", callback_data="dice_even"),
            InlineKeyboardButton(text="1️⃣3️⃣5️⃣ Нечётное (x2)", callback_data="dice_odd")
        )
        builder.row(
            InlineKeyboardButton(text="1️⃣2️⃣3️⃣ Меньше (x2)", callback_data="dice_less"),
            InlineKeyboardButton(text="4️⃣5️⃣6️⃣ Больше (x2)", callback_data="dice_greater")
        )
        builder.row(
            InlineKeyboardButton(text="🎯 Конкретное число (x6)", callback_data="dice_exact")
        )
        builder.row(
            InlineKeyboardButton(text="🔙 Назад", callback_data="game")
        )
        
        try:
            await callback.message.edit_text(
                f"🎲 <b>Игра в кубики</b>\n\n"
                f"▪ Текущая ставка: <b>{current_bet} {currency_symbol}</b>\n\n"
                "Выберите тип ставки:",
                reply_markup=builder.as_markup()
            )
        except Exception as e:
            print(f"Error editing message: {e}")
            await callback.answer()
    except Exception as e:
        print(f"Error in start_dice_game: {e}")


@casino.callback_query(F.data == "change_currency_dice")
async def change_currency_dice_handler(callback: types.CallbackQuery, bot: Bot):
    """Изменение валюты для игры в кубики"""
    try:
        user_id = callback.from_user.id
        current_currency = await DB.get_user_currency(user_id)
        
        # Меняем валюту на противоположную
        new_currency = 'stars' if current_currency == 'mico' else 'mico'
        await DB.update_user_currency(user_id, new_currency)
        
        # Возвращаемся в меню игры
        await start_dice_game(callback)
            
        await callback.answer(f"Валюта изменена на {'Stars ⭐' if new_currency == 'stars' else '$MICO 🪙'}")
    except Exception as e:
        logger.error(f"Error in change_currency_dice_handler: {e}")
        await callback.answer("Произошла ошибка, попробуйте позже")


@casino.callback_query(F.data == "increase_bet_dice")
async def increase_bet_handler(callback: types.CallbackQuery):
    """Увеличение ставки на 10% для кубиков"""
    try:
        user_id = callback.from_user.id
        current_bet = await DB.get_user_bet(user_id)
        
        # Увеличиваем ставку на 10% и округляем до 2 знаков
        new_bet = round(current_bet * 1.1, 2)
        
        # Обновляем ставку в базе
        await DB.update_user_bet(user_id, new_bet)
        
        # Обновляем интерфейс
        await start_dice_game(callback)
        await callback.answer(f"+10%")

    except Exception as e:
        logger.error(f"Error in increase_bet_handler: {e}", exc_info=True)
        await callback.answer("Произошла ошибка, попробуйте позже")

@casino.callback_query(F.data == "decrease_bet_dice")
async def decrease_bet_handler(callback: types.CallbackQuery):
    """Уменьшение ставки на 10% для кубиков"""
    try:
        user_id = callback.from_user.id
        current_bet = await DB.get_user_bet(user_id)
        
        # Уменьшаем ставку на 10% и округляем до 2 знаков
        new_bet = round(current_bet * 0.9, 2)
        
        # Минимальная ставка 0.01
        new_bet = max(0.01, new_bet)
        
        # Обновляем ставку в базе
        await DB.update_user_bet(user_id, new_bet)
        
        # Обновляем интерфейс
        await start_dice_game(callback)
        await callback.answer(f"-10%")

    except Exception as e:
        logger.error(f"Error in decrease_bet_handler: {e}", exc_info=True)
        await callback.answer("Произошла ошибка, попробуйте позже")

@casino.callback_query(F.data == "set_custom_bet_dice")
async def ask_for_custom_bet(callback: types.CallbackQuery, state: FSMContext):
    """Запрос пользовательской ставки для кубиков"""
    try:
        await state.set_state(GameStates.waiting_for_custom_bet)
        await state.update_data(game_type='dice')
        
        await callback.message.edit_text(
            "💰 Введите вашу новую ставку (минимальная ставка 1):",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data="game_dice")]
            ])
        )
    except Exception as e:
        print(f"Error in ask_for_custom_bet: {e}")
        await callback.answer("Произошла ошибка, попробуйте позже")

@casino.callback_query(F.data.startswith("dice_num_"))
async def process_exact_number(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    """Обработка выбора конкретного числа в игре в кубики"""
    try:
        exact_number = int(callback.data.split('_')[2])
        user_id = callback.from_user.id
        current_bet = await DB.get_user_bet(user_id)
        balance = await DB.get_user_balance_for_game(user_id)
        currency = await DB.get_user_currency(user_id)
        currency_symbol = "🪙" if currency == "mico" else "⭐"
        
        await state.update_data(exact_number=exact_number)
        
        if current_bet > balance:
            builder = InlineKeyboardBuilder()
            builder.add(InlineKeyboardButton(text="Пополнить баланс", callback_data="top_up"))
            builder.add(InlineKeyboardButton(text="🔙 Назад", callback_data="game_dice"))
            
            await callback.message.edit_text(
                f"❌ Недостаточно средств на балансе!\n"
                f"Ваш баланс: {balance:.2f} {currency_symbol}\n"
                f"Требуется: {current_bet:.2f} {currency_symbol}",
                reply_markup=builder.as_markup()
            )
            return
        
        await DB.increment_statistics(1, 'dice_played')
        await DB.increment_statistics(2, 'dice_played')
        
        dice_message = await callback.message.answer_dice(emoji=DiceEmoji.DICE)
        dice_roll = dice_message.dice.value
        
        win = dice_roll == exact_number
        coefficient = GAME_COEFFICIENTS['dice']['exact']
        
        if win:
            win_amount = current_bet * coefficient
            result_text = f"🎉 Поздравляем! Вы угадали число и выиграли {win_amount:.2f} {currency_symbol}!"
            result_db = 'win'
            await DB.increment_statistics(1, 'game_wins')
            await DB.increment_statistics(2, 'game_wins')
        else:
            win_amount = -current_bet
            result_text = f"😢 К сожалению, выпало {dice_roll}, а не {exact_number}. Вы проиграли {current_bet:.2f} {currency_symbol}."
            result_db = 'loss'
            await DB.increment_statistics(1, 'game_losses')
            await DB.increment_statistics(2, 'game_losses')
        
        await update_game_stats(user_id, callback.from_user.username, current_bet, win_amount, result_db, 'dice')
        new_balance = await DB.get_user_balance_for_game(user_id)
        
        result_message = (
            f"🎲 <b>Результат игры в кубики</b>\n\n"
            f"▪ Ваша ставка: <b>{current_bet:.2f} {currency_symbol}</b>\n"
            f"▪ Тип ставки: <b>конкретное число {exact_number}</b>\n"
            f"▪ Выпало: <b>{dice_roll}</b>\n\n"
            f"{result_text}\n\n"
            f"💰 Новый баланс: <b>{new_balance:.2f} {currency_symbol}</b>\n\n"
            f"🎰 Попробуйте ещё раз!"
        )
        
        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(text="🎲 Играть снова", callback_data="dice_exact"))
        builder.add(InlineKeyboardButton(text="🎮 Другие игры", callback_data="game"))
        builder.adjust(1)
        
        await asyncio.sleep(2)
        await callback.message.answer(result_message, reply_markup=builder.as_markup())
        await state.clear()
        
    except Exception as e:
        logger.error(f"Error in process_exact_number: {e}", exc_info=True)
        await callback.answer("Произошла ошибка, попробуйте позже")

@casino.callback_query(F.data.startswith("dice_") & ~F.data.startswith("dice_num_"))
async def start_dice_game_immediately(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    try:
        bet_type = callback.data.split('_')[1]
        user_id = callback.from_user.id
        current_bet = await DB.get_user_bet(user_id)
        balance = await DB.get_user_balance_for_game(user_id)
        currency = await DB.get_user_currency(user_id)
        currency_symbol = "🪙" if currency == "mico" else "⭐"
        
        if bet_type == 'exact':
            builder = InlineKeyboardBuilder()
            for num in range(1, 7):
                builder.add(InlineKeyboardButton(text=str(num), callback_data=f"dice_num_{num}"))
            builder.add(InlineKeyboardButton(text="🔙 Назад", callback_data="game_dice"))
            builder.adjust(6, 1, repeat=True)
            
            await state.set_state(GameStates.waiting_for_exact_number)
            await callback.message.edit_text(
                "🎯 Выберите число от 1 до 6:",
                reply_markup=builder.as_markup()
            )
            return
        
        await state.update_data(bet_type=bet_type)
        
        if current_bet > balance:
            builder = InlineKeyboardBuilder()
            builder.add(InlineKeyboardButton(text="Пополнить баланс", callback_data="top_up"))
            builder.add(InlineKeyboardButton(text="🔙 Назад", callback_data="game_dice"))
            
            await callback.message.edit_text(
                f"❌ Недостаточно средств на балансе!\n"
                f"Ваш баланс: {balance:.2f} {currency_symbol}\n"
                f"Требуется: {current_bet:.2f} {currency_symbol}",
                reply_markup=builder.as_markup()
            )
            return
        
        await DB.increment_statistics(1, 'dice_played')
        await DB.increment_statistics(2, 'dice_played')
        
        dice_message = await callback.message.answer_dice(emoji=DiceEmoji.DICE)
        dice_roll = dice_message.dice.value
        
        win = False
        coefficient = GAME_COEFFICIENTS['dice'][bet_type]
        
        if bet_type == 'even':
            win = dice_roll % 2 == 0
        elif bet_type == 'odd':
            win = dice_roll % 2 != 0
        elif bet_type == 'greater':
            win = dice_roll in [4, 5, 6]  # Победа при 4,5,6
        elif bet_type == 'less':
            win = dice_roll in [1, 2, 3]  # Победа при 1,2,3
        
        if win:
            win_amount = current_bet * coefficient
            result_text = f"🎉 Поздравляем! Вы выиграли {win_amount:.2f} {currency_symbol}!"
            result_db = 'win'
            await DB.increment_statistics(1, 'game_wins')
            await DB.increment_statistics(2, 'game_wins')
        else:
            win_amount = -current_bet
            result_text = f"😢 К сожалению, вы проиграли {current_bet:.2f} {currency_symbol}."
            result_db = 'loss'
            await DB.increment_statistics(1, 'game_losses')
            await DB.increment_statistics(2, 'game_losses')
        
        await update_game_stats(user_id, callback.from_user.username, current_bet, win_amount, result_db, 'dice')
        new_balance = await DB.get_user_balance_for_game(user_id)
        
        bet_type_names = {
            'even': 'чётное',
            'odd': 'нечётное',
            'greater': 'больше (4-6)',
            'less': 'меньше (1-3)'
        }
        
        result_message = (
            f"🎲 <b>Результат игры в кубики</b>\n\n"
            f"▪ Ваша ставка: <b>{current_bet:.2f} {currency_symbol}</b>\n"
            f"▪ Тип ставки: <b>{bet_type_names[bet_type]}</b>\n"
            f"▪ Выпало: <b>{dice_roll}</b>\n\n"
            f"{result_text}\n\n"
            f"💰 Новый баланс: <b>{new_balance:.2f} {currency_symbol}</b>\n\n"
            f"🎰 Попробуйте ещё раз!"
        )
        
        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(text="🎲 Играть снова", callback_data=f"dice_{bet_type}"))
        builder.add(InlineKeyboardButton(text="🎮 Другие игры", callback_data="game"))
        builder.adjust(1)

        await asyncio.sleep(2)
        await callback.message.answer(result_message, reply_markup=builder.as_markup())
        await state.clear()
        
    except Exception as e:
        logger.error(f"Error in start_dice_game_immediately: {e}", exc_info=True)
        await callback.answer("Произошла ошибка, попробуйте позже")

@casino.message(GameStates.waiting_for_bet)
async def process_bet(message: types.Message, state: FSMContext, bot: Bot):
    """Обработка ставки и проведение игры с реальными кубиками Telegram"""
    user_id = message.from_user.id
    current_bet = await DB.get_user_bet(user_id)
    
    user_data = await state.get_data()
    bet_type = user_data.get('bet_type')
    exact_number = user_data.get('exact_number')
    
    # Проверка баланса пользователя
    user = await DB.select_user(user_id)
    if not user:
        await message.answer("❌ Ошибка: пользователь не найден!")
        return
    
    if current_bet > DB.get_user_balance_game(user_id):
        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(text="Пополнить баланс", callback_data="top_up"))
        builder.add(InlineKeyboardButton(text="🔙 Назад", callback_data="game_dice"))
        
        await message.answer(
            f"❌ Недостаточно средств на балансе!\n"
            f"Ваш баланс: {DB.get_user_balance_game(user_id):.2f}\n"
            f"Требуется: {current_bet:.2f}",
            reply_markup=builder.as_markup()
        )
        return
    
    # Отправляем кубик и получаем результат
    dice_message = await message.answer_dice(emoji=DiceEmoji.DICE)
    dice_roll = dice_message.dice.value
    
    # Определяем результат
    win = False
    coefficient = GAME_COEFFICIENTS['dice'][bet_type]
    
    if bet_type == 'even':
        win = dice_roll % 2 == 0
    elif bet_type == 'odd':
        win = dice_roll % 2 != 0
    elif bet_type == 'greater':
        win = dice_roll > 4
    elif bet_type == 'less':
        win = dice_roll < 4
    elif bet_type == 'exact':
        win = dice_roll == exact_number

    await DB.increment_statistics(1, 'dice_played')
    await DB.increment_statistics(2, 'dice_played')
    
    # Рассчитываем выигрыш
    if win:
        win_amount = current_bet * coefficient
        result_text = f"🎉 Поздравляем! Вы выиграли {win_amount:.2f}!"
        result_db = 'win'
        await DB.increment_statistics(1, 'game_wins')
        await DB.increment_statistics(2, 'game_wins')
    else:
        win_amount = -current_bet
        result_text = f"😢 К сожалению, вы проиграли {current_bet:.2f}."
        result_db = 'loss'
        await DB.increment_statistics(1, 'game_losses')
        await DB.increment_statistics(2, 'game_losses')
    
    # Обновляем баланс пользователя
    await DB.add_game_balance( # проблема
        user_id=user_id,
        username=message.from_user.username,
        bal_change=win_amount
    )
    
    # Обновляем статистику ставок
    await DB.update_game_stats(
        user_id=user_id,
        stat_type='bet'
    )
    
    # Обновляем статистику выигрышей/проигрышей
    await DB.update_game_stats(
        user_id=user_id,
        stat_type=result_db
    )
    
    # Добавляем запись в историю игр
    await DB.add_game_history(
        user_id=user_id,
        amount=current_bet,
        result=result_db,
        game_mode='dice'
    )
    
    # Обновляем статистику по режимам игры
    await DB.update_game_mode_stats(
        user_id=user_id,
        game_mode='dice',
        result=result_db
    )
    
    # Получаем обновленный баланс
    updated_user = await DB.select_user(user_id)
    new_balance = updated_user['balance']
    
    # Формируем текст результата
    bet_type_names = {
        'even': 'чётное',
        'odd': 'нечётное',
        'greater': 'больше 4',
        'less': 'меньше 4',
        'exact': f'число {exact_number}'
    }
    
    result_message = (
        f"🎲 <b>Результат игры в кубики</b>\n\n"
        f"▪ Ваша ставка: <b>{current_bet:.2f}</b>\n"
        f"▪ Тип ставки: <b>{bet_type_names[bet_type]}</b>\n"
        f"▪ Выпало: <b>{dice_roll}</b>\n\n"
        f"{result_text}\n\n"
        f"💰 Новый баланс: <b>{new_balance:.2f}</b>\n\n"
        f"🎰 Попробуйте ещё раз!"
    )
    
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="🎲 Играть снова", callback_data=f"dice_{bet_type}"))
    builder.add(InlineKeyboardButton(text="🎮 Другие игры", callback_data="game"))
    builder.adjust(1)


    # Ждем завершения анимации кубика (примерно 2 секунды)
    await asyncio.sleep(2)
    await message.answer(result_message, reply_markup=builder.as_markup())
    await state.clear()


# Добавляем в начало файла новый State для состояний
class BalanceStates(StatesGroup):
    waiting_for_deposit_amount = State()
    waiting_for_withdraw_amount = State()
    waiting_for_stars_amount = State()

# Обработчик кнопки "Баланс"
@casino.callback_query(F.data == "balance_game")
async def game_balance_handler(callback: types.CallbackQuery):
    """Меню управления балансом в игре"""
    user_id = callback.from_user.id
    game_balance = await DB.get_user_balance_game(user_id)
    stars_balance = await DB.get_user_balance_stars_game(user_id)
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="💰 Пополнить", callback_data="dep_game"),
        InlineKeyboardButton(text="💸 Вывести", callback_data="withdraw_game")
    )
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="game"))
    
    await callback.message.edit_text(
        f"🎮 <b>Игровой баланс</b>\n\n"
        f"💰 Баланс $MICO: <b>{game_balance:.2f}</b>\n\n" 
        f"⭐ Баланс Stars: <b>{stars_balance:.2f}</b>\n\n"
        "Выберите действие:",
        reply_markup=builder.as_markup()
    )

# Меню пополнения
@casino.callback_query(F.data == "dep_game")
async def deposit_menu_handler(callback: types.CallbackQuery):
    """Меню выбора способа пополнения"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="⭐ Stars", callback_data="dep_stars"),
        InlineKeyboardButton(text="🪙 $MICO", callback_data="dep_mico")
    )
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="balance_game"))
    
    await callback.message.edit_text(
        "💳 <b>Пополнение игрового баланса</b>\n\n"
        "Выберите способ пополнения:",
        reply_markup=builder.as_markup()
    )

# Меню вывода
@casino.callback_query(F.data == "withdraw_game")
async def withdraw_menu_handler(callback: types.CallbackQuery):
    """Меню выбора способа вывода"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🪙 $MICO", callback_data="withdraw_mico"),
        InlineKeyboardButton(text="⭐️ Stars", callback_data="withdraw_stars"),
    ) 
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="balance_game"))
    
    await callback.message.edit_text(
        "💸 <b>Вывод средств</b>\n\n"
        "Выберите способ вывода:",
        reply_markup=builder.as_markup()
    )

class withdraw_stars(StatesGroup):
    amount = State()

@casino.callback_query(F.data == "withdraw_stars")
async def withdraw_stars_handler(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(withdraw_stars.amount)
    kb = InlineKeyboardBuilder()
    kb.add(InlineKeyboardButton(text='Назад', callback_data='balance_game'))
    stars = await DB.get_stars(callback.from_user.id)
    await callback.message.edit_text(
        '❓ Сколько звёзд вы хотите вывести?\n'
        '❗️ Минимальная сумма: 50 звёзд\n'
        f'⭐️ Ваш баланс: {stars} Stars\n'
        '✍️ Введите количество звёзд, которые хотите вывести',
        reply_markup=kb.as_markup()
    )

@casino.message(withdraw_stars.amount)
async def process_withdraw_amount(message: types.Message, state: FSMContext, bot: Bot):
    try:
        # Пытаемся преобразовать введенный текст в число
        amount = float(message.text)
        
        # Проверяем минимальную сумму
        if amount < 50:
            kb = InlineKeyboardBuilder()
            kb.add(InlineKeyboardButton(text='Назад', callback_data='profile'))
            await message.answer(
                '❌ Минимальная сумма вывода - 50 ⭐',
                reply_markup=kb.as_markup()
            )
            return
        
        # Получаем текущий баланс пользователя
        user_id = message.from_user.id
        current_balance = await DB.get_stars(user_id)
        
        # Проверяем, достаточно ли средств
        if amount > current_balance:
            kb = InlineKeyboardBuilder()
            kb.add(InlineKeyboardButton(text='Назад', callback_data='profile'))
            await message.answer(
                f'❌ Недостаточно звёзд на балансе ❌\n'
                f'Ваш баланс: {current_balance} ⭐\n'
                f'Запрошено: {amount} ⭐',
                reply_markup=kb.as_markup()
            )
            return
        
        await DB.increment_statistics_withdraw_from_game(1, amount)
        await DB.increment_statistics_withdraw_from_game(2, amount)
        
        # Отправляем заявку в чат для вывода
        await bot.send_message(
            WITHDRAW_CHAT,
            text=f'''
🚀 ЗАЯВКА НА ВЫВОД ЗВЁЗД
👤 Пользователь: @{message.from_user.username}
🔢 ID: {message.from_user.id}
💰 Сумма: {amount} ⭐
            '''
        )
        
        # Обновляем баланс пользователя (вычитаем сумму вывода)
        new_balance = current_balance - amount
        await DB.add_star(user_id, -amount)
        
        # Отправляем подтверждение пользователю
        kb = InlineKeyboardBuilder()
        kb.add(InlineKeyboardButton(text='Назад', callback_data='profile'))
        await message.answer(
            f'✅ Заявка на вывод {amount} ⭐ успешно создана!\n'
            f'💰 Ваш новый баланс: {new_balance} ⭐ \n'
            '👑 Администратор обработает её в ближайшее время.',
            reply_markup=kb.as_markup()
        )
        
    except ValueError:
        kb = InlineKeyboardBuilder()
        kb.add(InlineKeyboardButton(text='Назад', callback_data='withdraw_game'))
        await message.answer(
            '❌ Пожалуйста, введите корректное число (например: 50 или 100) ❌',
            reply_markup=kb.as_markup()
        )
    finally:
        await state.clear()


# Пополнение через Stars
@casino.callback_query(F.data == "dep_stars")
async def deposit_stars_handler(callback: types.CallbackQuery, state: FSMContext):
    """Обработчик пополнения через Stars"""
    await callback.message.edit_text(
        "<b>Вы можете обменять свои Telegram Stars на игровую валюту по курсу:</b>\n\n"
        "1⭐ = 1\n\n"
        "<b>Введите количество Stars, которое вы хотите обменять:</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="dep_game")]
        ])
    )
    await state.set_state(BalanceStates.waiting_for_stars_amount)

# Обработчик ввода суммы Stars
@casino.message(BalanceStates.waiting_for_stars_amount)
async def process_stars_amount(message: types.Message, state: FSMContext, bot: Bot):
    try:
        stars_amount = int(message.text)
        if stars_amount <= 0:
            await message.answer("❌ Введите положительное число!")
            return
            
        # Создаем инвойс для оплаты Stars (1 звезда = 1 монета)
        prices = [LabeledPrice(label=f"{stars_amount} Stars", amount=stars_amount)]  # В копейках
        
        await bot.send_invoice(
            chat_id=message.chat.id,
            title=f"Пополнение на {stars_amount} монет",
            description=f"Обмен {stars_amount} Stars на игровую валюту",
            payload=f"user_{message.from_user.id}_stars_{stars_amount}",
            provider_token="",  # Убедитесь, что токен установлен
            currency="XTR",
            prices=prices,
            start_parameter="stars_deposit"
        )

        await state.clear()
    except ValueError:
        await message.answer("❌ Пожалуйста, введите целое число!")
    except Exception as e:
        logger.error(f"Error in process_stars_amount: {e}")
        await message.answer("❌ Произошла ошибка, попробуйте позже")

# Пополнение через MICO
@casino.callback_query(F.data == "dep_mico")
async def deposit_mico_handler(callback: types.CallbackQuery, state: FSMContext):
    """Обработчик пополнения через MICO"""
    user_id = callback.from_user.id
    mico_balance = await DB.get_user_balance(user_id)
    
    await callback.message.edit_text(
        f"🪙 <b>Пополнение игрового баланса</b>\n\n"
        f"▪ Ваш баланс $MICO: <b>{mico_balance:.2f}</b>\n\n"
        "Введите сумму для перевода в игровой баланс:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="dep_game")]
        ])
    )
    await state.set_state(BalanceStates.waiting_for_deposit_amount)

# Обработчик ввода суммы MICO для пополнения
@casino.message(BalanceStates.waiting_for_deposit_amount)
async def process_mico_deposit(message: types.Message, state: FSMContext):
    try:
        user_id = message.from_user.id
        amount = float(message.text)
        
        if amount <= 0:
            await message.answer("❌ Введите положительное число!")
            return
            
        mico_balance = await DB.get_user_balance(user_id)
        
        if amount > mico_balance:
            await message.answer(f"❌ Недостаточно средств! Ваш баланс: {mico_balance:.2f} $MICO")
            return
            
        # Списание с основного баланса и пополнение игрового
        await DB.add_balance(user_id, -amount)
        await DB.update_user_balance_game(user_id, amount)
        
        new_balance = await DB.get_user_balance_game(user_id)
        
        kb = InlineKeyboardBuilder()
        kb.add(InlineKeyboardButton(text='Назад', callback_data='game'))
            
        await message.answer(
            f"✅ Успешно переведено <b>{amount:.2f}</b> $MICO на игровой баланс!\n\n"
            f"💰 Новый игровой баланс: <b>{new_balance:.2f}</b>",
            reply_markup=kb.as_markup()
        )
        
        await state.clear()
    except ValueError:
        await message.answer("❌ Пожалуйста, введите число!")
    except Exception as e:
        logger.error(f"Error in process_mico_deposit: {e}")
        await message.answer("❌ Произошла ошибка, попробуйте позже")

# Вывод через MICO
@casino.callback_query(F.data == "withdraw_mico")
async def withdraw_mico_handler(callback: types.CallbackQuery, state: FSMContext):
    """Обработчик вывода через MICO"""
    user_id = callback.from_user.id
    game_balance = await DB.get_user_balance_game(user_id)
    
    await callback.message.edit_text(
        f"💸 <b>Вывод средств из игры</b>\n\n"
        f"▪ Ваш игровой баланс: <b>{game_balance:.2f}</b>\n\n"
        "Введите сумму для вывода в $MICO:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="withdraw_game")]
        ])
    )
    await state.set_state(BalanceStates.waiting_for_withdraw_amount)

# Обработчик ввода суммы MICO для вывода
@casino.message(BalanceStates.waiting_for_withdraw_amount)
async def process_mico_withdraw(message: types.Message, state: FSMContext):
    try:
        user_id = message.from_user.id
        amount = float(message.text)
        
        if amount <= 0:
            await message.answer("❌ Введите положительное число!")
            return
            
        game_balance = await DB.get_user_balance_game(user_id)
        
        if amount > game_balance:
            await message.answer(f"❌ Недостаточно средств! Ваш игровой баланс: {game_balance:.2f}")
            return
            
        # Списание с игрового баланса и пополнение основного
        await DB.update_user_balance_game(user_id, -amount)
        await DB.add_balance(user_id, amount)
        
        new_balance = await DB.get_user_balance(user_id)
        

        kb = InlineKeyboardBuilder()
        kb.add(InlineKeyboardButton(text='Назад', callback_data='game'))
            

        await message.answer(
            f"✅ Успешно выведено <b>{amount:.2f}</b> $MICO с игрового баланса!\n\n"
            f"💰 Новый баланс $MICO: <b>{new_balance:.2f}</b>",
            reply_markup=kb.as_markup()
        )
        
        await state.clear()
    except ValueError:
        await message.answer("❌ Пожалуйста, введите число!")
    except Exception as e:
        logger.error(f"Error in process_mico_withdraw: {e}")
        await message.answer("❌ Произошла ошибка, попробуйте позже")