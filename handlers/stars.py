from utils.Imports import *

stars = Router()

class BalanceStates(StatesGroup):
    waiting_for_deposit_amount = State()
    waiting_for_withdraw_amount = State()
    waiting_for_stars_amount = State()

class withdraw_stars(StatesGroup):
    amount = State()

@stars.callback_query(F.data == "withdraw_stars")
async def withdraw_stars_handler(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(withdraw_stars.amount)
    kb = InlineKeyboardBuilder()
    kb.add(InlineKeyboardButton(text='Назад', callback_data='balance_game'))
    stars = await DB.get_stars(callback.from_user.id)
    await callback.message.edit_text(
        '❓ Сколько звёзд вы хотите вывести?\n'
        '❗️ Минимальная сумма: 50 звёзд\n'
        f'Ваш баланс: {stars}'
        '✍️ Введите количество звёзд, которые хотите вывести',
        reply_markup=kb.as_markup()
    )

@stars.message(withdraw_stars.amount)
async def process_withdraw_amount(message: types.Message, state: FSMContext, bot: Bot):
    try:
        # Пытаемся преобразовать введенный текст в число
        amount = float(message.text)
        
        # Проверяем минимальную сумму
        if amount < 50:
            kb = InlineKeyboardBuilder()
            kb.add(InlineKeyboardButton(text='Назад', callback_data='withdraw_game'))
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
            kb.add(InlineKeyboardButton(text='Назад', callback_data='withdraw_game'))
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
        await DB.update_user_balance_stars_game(user_id, -amount)
        
        # Отправляем подтверждение пользователю
        kb = InlineKeyboardBuilder()
        kb.add(InlineKeyboardButton(text='Назад', callback_data='withdraw_game'))
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
@stars.callback_query(F.data == "dep_stars")
async def deposit_stars_handler(callback: types.CallbackQuery, state: FSMContext):
    """Обработчик пополнения через Stars"""
    await callback.message.edit_text(
        "<b>⭐Вы можете пополнить свой баланс звёзд</b>\n"
        "<b>⭐Введите количество Stars, которое вы хотите пополнить:</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="dep_game")]
        ])
    )
    await state.set_state(BalanceStates.waiting_for_stars_amount)

@stars.pre_checkout_query()
async def pre_checkout_handler(pre_checkout_query: types.PreCheckoutQuery, bot: Bot):
    try:
        await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)
    except Exception as e:
        logger.error(f"Error in pre_checkout_handler: {e}")
        await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=False, error_message="Ошибка обработки платежа")

@stars.message(BalanceStates.waiting_for_stars_amount)
async def process_stars_amount(message: types.Message, state: FSMContext, bot: Bot):
    try:
        stars_amount = int(message.text)
        if stars_amount <= 0:
            await message.answer("❌ Введите положительное число!")
            return
            
        # Конвертируем в копейки (минимальные единицы валюты)
        amount_kopecks = stars_amount * 100  # 1 звезда = 1 рубль (100 копеек)
        
        # Создаем инвойс для оплаты Stars
        prices = [LabeledPrice(label=f"{stars_amount} Stars", amount=amount_kopecks)]
        
        await bot.send_invoice(
            chat_id=message.chat.id,
            title=f"Пополнение на {stars_amount} Stars",
            description=f"Покупка {stars_amount} ⭐ для игрового баланса",
            provider_token='',  # Ваш токен платежной системы
            currency="RUB",  # Валюта платежа (рубли)
            prices=prices,
            payload=f"user_{message.from_user.id}_stars_{stars_amount}",
            start_parameter="stars_deposit",
            need_name=False,
            need_phone_number=False,
            need_email=False,
            need_shipping_address=False,
            is_flexible=False
        )

        await state.clear()
    except ValueError:
        await message.answer("❌ Пожалуйста, введите целое число!")
    except Exception as e:
        logger.error(f"Error in process_stars_amount: {e}")
        await message.answer("❌ Произошла ошибка, попробуйте позже")

@stars.message(F.successful_payment)
async def successful_payment_handler(message: types.Message):
    try:
        user_id = message.from_user.id
        payload = message.successful_payment.invoice_payload
        
        # Извлекаем количество Stars из payload
        parts = payload.split('_')
        if len(parts) != 4:
            raise ValueError("Invalid payload format")
            
        stars_amount = int(parts[3])
        
        # Пополняем игровой баланс
        await DB.update_user_balance_stars_game(user_id, stars_amount)

        kb = InlineKeyboardBuilder()
        kb.add(InlineKeyboardButton(text='Назад', callback_data='game'))
        
        await message.answer(
            f"✅ Платеж успешно завершен!\n\n"
            f"⭐ Получено: <b>{stars_amount} Stars</b>\n"
            f"💰 Новый баланс: <b>{await DB.get_user_balance_stars_game(user_id):.2f}⭐</b>",
            reply_markup=kb.as_markup()
        )
        
    except Exception as e:
        logger.error(f"Error processing stars payment: {e}")
        await message.answer("❌ Ошибка при зачислении средств, обратитесь в поддержку")