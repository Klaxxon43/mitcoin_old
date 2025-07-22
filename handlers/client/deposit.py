from .client import *
from decimal import Decimal, getcontext, InvalidOperation
from API.usd import create_check as CryptoPayCreateCheck, create_invoice as CryptoPayCreateInvoice


# Настройка точности Decimal
getcontext().prec = 6

async def get_usd_to_rub_rate() -> Decimal:
    """Получаем текущий курс USD к RUB"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get('https://api.exchangerate-api.com/v4/latest/USD') as resp:
                data = await resp.json()
                return Decimal(str(data['rates']['RUB']))
    except Exception as e:
        logger.error(f"Ошибка получения курса USD: {e}")
        return Decimal("93.6")  # Значение по умолчанию

@router.callback_query(F.data == 'select_deposit_menu')
async def select_deposit_handler(callback: types.CallbackQuery):
    """Меню выбора валюты для пополнения"""
    await callback.answer()
    await callback.message.edit_text(
        "💰 <b>Выберите валюту для пополнения:</b>",
        reply_markup=select_currency_kb()
    )

@router.callback_query(F.data.startswith('deposit_currency_'))
async def select_deposit_currency_handler(callback: types.CallbackQuery, state: FSMContext):
    """Обработка выбора валюты для пополнения"""
    currency = callback.data.split('_')[2]  # MICO или RUB
    await state.update_data(deposit_currency=currency)
    
    await callback.answer()
    await callback.message.edit_text(
        f"💰 <b>Выберите способ пополнения {currency}:</b>",
        reply_markup=deposit_methods_kb(currency)
    )

@router.callback_query(F.data == 'deposit_stars')
async def deposit_stars_handler(callback: types.CallbackQuery, state: FSMContext):
    """Обработка выбора пополнения через Stars"""
    data = await state.get_data()
    currency = data.get('deposit_currency', 'MICO')
    
    await callback.answer()
    await callback.message.edit_text(
        f"⭐ <b>Пополнение {currency} через Telegram Stars</b>\n\n"
        "Введите количество Stars, которое хотите оплатить:\n"
        "(1 ⭐ = 2000 $MICO)\n\n",
        reply_markup=back_to_deposit_kb(currency)
    )
    await state.set_state(DepositStates.waiting_stars_amount)

@router.message(DepositStates.waiting_stars_amount)
async def process_stars_amount(message: types.Message, state: FSMContext, bot: Bot):
    """Обработка введенного количества Stars"""
    data = await state.get_data()
    currency = data.get('deposit_currency', 'MICO')
    
    if not message.text:
        await message.answer("❌ Пожалуйста, введите количество Stars")
        return
    
    try:
        stars_amount = Decimal(message.text.replace(',', '.'))
        if stars_amount < 1:
            await message.answer("❌ Минимальная сумма - 1 ⭐")
            return
            
        amount_mico = int(stars_amount * 2000)  # 1 ⭐ = 2000 MICO
        
        text = (
            f"💎 <b>Детали пополнения:</b>\n\n"
            f"• Оплата: {stars_amount.normalize()} ⭐\n"
        )
        
        if currency == 'MICO':
            text += f"• Получите: {amount_mico} $MICO\n"
        else:
            rub_amount = stars_amount * Decimal('20')  # Примерный курс 1 ⭐ = 20 ₽
            text += f"• Получите: {rub_amount.normalize()} ₽\n"
            
        text += f"• Курс: 1 ⭐ = 2000 $MICO\n\n"
        text += "Для продолжения нажмите кнопку ниже 👇"
        
        await message.answer(
            text,
            reply_markup=confirm_stars_deposit_kb(amount_mico, stars_amount, currency)
        )
        await state.clear()
        
    except (ValueError, InvalidOperation):
        await message.answer("❌ Пожалуйста, введите корректное число (например: 5 или 5.5)")

@router.callback_query(F.data.startswith('confirm_stars_'))
async def confirm_stars_deposit(callback: types.CallbackQuery, bot: Bot, state: FSMContext):
    """Подтверждение и создание счета на оплату Stars"""
    try:
        data = callback.data.split('_')
        amount_mico = int(data[2])
        stars_amount = Decimal(data[3])
        currency = data[4] if len(data) > 4 else 'MICO'
        
        prices = [LabeledPrice(
            label=f"{stars_amount.normalize()} Stars → {amount_mico if currency == 'MICO' else stars_amount * Decimal('20')} {currency}",
            amount=int(stars_amount)  # 1 звезда = 100 копеек
        )]
        
        await bot.send_invoice(
            chat_id=callback.from_user.id,
            title=f"Пополнение на {amount_mico if currency == 'MICO' else stars_amount * Decimal('20')} {currency}",
            description=f"Оплата {stars_amount.normalize()} Stars",
            payload=f"stars_{callback.from_user.id}_{amount_mico}_{currency}",
            provider_token="",
            currency="XTR",
            prices=prices,
            start_parameter="stars_deposit"
        )
        
    except Exception as e:
        logger.error(f"Ошибка при создании счета Stars: {e}")
        await callback.message.answer("❌ Ошибка при создании счета. Попробуйте позже.")
    finally:
        await callback.answer()

@router.callback_query(F.data == 'deposit_cryptobot')
async def deposit_cryptobot_handler(callback: types.CallbackQuery, state: FSMContext):
    """Обработка выбора пополнения через CryptoBot"""
    data = await state.get_data()
    currency = data.get('deposit_currency', 'MICO')
    usd_rate = await get_usd_to_rub_rate()
    
    if currency == 'MICO':
        mico_per_usdt = int(usd_rate * 1000)  # 1 USDT = X RUB * 1000 MICO
        rate_text = f"1 USDT = {mico_per_usdt} $MICO\n(1 USD = {usd_rate.normalize()} RUB → 1 RUB = 1000 $MICO)"
    else:
        mico_per_usdt = usd_rate  # 1 USDT = X RUB
        rate_text = f"1 USDT = {usd_rate.normalize()} ₽"

    await callback.answer()
    await callback.message.edit_text(
        f"💵 <b>Пополнение {currency} через USDT (CryptoBot)</b>\n\n"
        f"Текущий курс: {rate_text}\n\n"
        "Введите сумму в USDT, которую хотите оплатить:\n"
        "<i>Минимальная сумма: 0.03 USDT</i>",
        reply_markup=back_to_deposit_kb(currency)
    )
    await state.set_state(DepositStates.waiting_crypto_amount)

@router.message(DepositStates.waiting_crypto_amount)
async def process_crypto_amount(message: types.Message, state: FSMContext):
    """Обработка введенной суммы USDT"""
    data = await state.get_data()
    currency = data.get('deposit_currency', 'MICO')
    
    if not message.text:
        await message.answer("❌ Пожалуйста, введите сумму в USDT")
        return
    
    try:
        usdt_amount = Decimal(message.text.replace(',', '.'))
        if usdt_amount < Decimal('0.03'):
            await message.answer("❌ Минимальная сумма - 0.03 USDT")
            return
            
        usd_rate = await get_usd_to_rub_rate()
        
        if currency == 'MICO':
            amount = int(usdt_amount * usd_rate * 1000)  # USDT * курс * 1000
            amount_text = f"{amount} $MICO"
            rate_text = f"1 USDT = {int(usd_rate * 1000)} $MICO"
        else:
            amount = usdt_amount * usd_rate
            amount_text = f"{amount.normalize()} ₽"
            rate_text = f"1 USDT = {usd_rate.normalize()} ₽"
        
        await message.answer(
            f"💳 <b>Детали пополнения:</b>\n\n"
            f"• Оплата: {usdt_amount.normalize()} USDT\n"
            f"• Получите: {amount_text}\n"
            f"• Курс: {rate_text}\n\n"
            "Для создания счета нажмите кнопку ниже 👇",
            reply_markup=confirm_crypto_deposit_kb(amount, usdt_amount, currency)
        )
        
    except (ValueError, InvalidOperation):
        await message.answer("❌ Пожалуйста, введите корректное число (например: 0.5 или 1)")

@router.callback_query(F.data.startswith('confirm_crypto_'))
async def confirm_crypto_deposit(callback: types.CallbackQuery, state: FSMContext):
    """Создание счета на оплату через CryptoPay"""
    data = callback.data.split('_')
    amount = Decimal(data[2]) if '.' in data[2] else int(data[2])
    usdt_amount = Decimal(data[3])
    currency = data[4] if len(data) > 4 else 'MICO'
    user_id = callback.from_user.id
    
    try:
        # Создаем счет в CryptoPay
        invoice = await CryptoPayCreateInvoice(
            amount=float(usdt_amount),
            asset='USDT',
            purpose=f'Пополнение {currency} баланса {user_id}'
        )
        
        # Сохраняем данные платежа
        payment_data = {
            'user_id': user_id,
            'amount': float(amount),
            'currency': currency,
            'invoice_id': invoice['id'],
            'status': 'created',
            'created_at': int(time.time())
        }
        
        # Отправляем пользователю ссылку на оплату
        await callback.message.edit_text(
            f"🔗 <b>Счет на оплату создан</b>\n\n"
            f"Сумма: {usdt_amount.normalize()} USDT\n"
            f"К получению: {amount} {currency}\n\n"
            "Для оплаты нажмите кнопку ниже 👇\n"
            "Счет действителен 5 минут",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="💳 Оплатить USDT", url=invoice['url'])],
                [InlineKeyboardButton(text="🔄 Проверить оплату", callback_data=f"check_pay_{invoice['id']}_{amount}_{currency}")]
            ])
        )
        
    except Exception as e:
        logger.error(f"Ошибка создания счета CryptoPay: {e}")
        await callback.message.answer("❌ Ошибка при создании счета. Попробуйте позже.")
    finally:
        await callback.answer()
        
@router.callback_query(F.data.startswith('check_pay_'))
async def check_payment_status(callback: types.CallbackQuery, bot: Bot):
    """Проверка статуса оплаты"""
    data = callback.data.split('_')
    invoice_id = int(data[2])
    amount = Decimal(data[3]) if '.' in data[3] else int(data[3])
    currency = data[4] if len(data) > 4 else 'MICO'
    user_id = callback.from_user.id

    try:
        async with AioCryptoPay(token=CRYPTOBOT_TOKEN) as crypto:
            invoice = await crypto.get_invoices(invoice_ids=invoice_id)

        if invoice.status == 'paid':
            # Зачисляем средства
            if currency == 'MICO':
                await DB.add_balance(user_id, amount)
            else:
                await DB.add_rub_balance(user_id, float(amount))
                
            await DB.add_transaction(
                user_id=user_id,
                amount=float(amount),
                description=f"Пополнение {currency} USDT",
                additional_info=f"invoice_{invoice_id}"
            )

            await callback.message.edit_text(
                f"✅ Пополнение на {amount} {currency} успешно зачислено!",
                reply_markup=back_to_menu_kb()
            )

            # Уведомление админам
            for admin_id in ADMINS_ID:
                try:
                    await bot.send_message(
                        admin_id,
                        f"💰 Новое пополнение USDT\n"
                        f"👤 ID: {user_id}\n"
                        f"💎 Сумма: {amount} {currency}\n"
                        f"📝 Invoice ID: {invoice_id}"
                    )
                except Exception as e:
                    logger.error(f"Ошибка уведомления админа {admin_id}: {e}")

        elif invoice.status == 'active':
            await callback.answer("ℹ️ Счет еще не оплачен", show_alert=True)
        else:
            await callback.answer("❌ Счет просрочен или отменен", show_alert=True)

    except Exception as e:
        logger.error(f"Ошибка проверки платежа: {e}")
        await callback.answer("❌ Ошибка при проверке платежа", show_alert=True)

@router.callback_query(F.data == 'deposit_rub')
async def deposit_rub_handler(callback: types.CallbackQuery, state: FSMContext):
    """Обработка выбора пополнения рублями"""
    data = await state.get_data()
    currency = data.get('deposit_currency', 'MICO')
    
    await callback.answer()
    await callback.message.edit_text(
        f"₽ <b>Пополнение {currency} рублями</b>\n\n"
        "Введите сумму в рублях, которую хотите оплатить:\n"
        f"Курс: 1 ₽ = {1000 if currency == 'MICO' else 1} {currency}\n\n"
        "<i>Пример: 100 или 150.5</i>",
        reply_markup=back_to_deposit_kb(currency)
    )
    await state.set_state(DepositStates.waiting_rub_amount)

@router.message(DepositStates.waiting_rub_amount)
async def process_rub_amount(message: types.Message, state: FSMContext):
    """Обработка введенной суммы рублей"""
    data = await state.get_data()
    currency = data.get('deposit_currency', 'MICO')
    
    if not message.text:
        await message.answer("❌ Пожалуйста, введите сумму в рублях")
        return
    
    try:
        rub_amount = Decimal(message.text.replace(',', '.'))
        if rub_amount < 10:
            await message.answer("❌ Минимальная сумма - 10 ₽")
            return
            
        if currency == 'MICO':
            amount = int(rub_amount * 1000)  # 1 RUB = 1000 MICO
            amount_text = f"{amount} $MICO"
            rate_text = "1 ₽ = 1000 $MICO"
        else:
            amount = rub_amount
            amount_text = f"{amount.normalize()} ₽"
            rate_text = "1 ₽ = 1 ₽"
        
        await message.answer(
            f"💎 <b>Детали пополнения:</b>\n\n"
            f"• Оплата: {rub_amount.normalize()} ₽\n"
            f"• Получите: {amount_text}\n"
            f"• Курс: {rate_text}\n\n"
            "Для оплаты свяжитесь с оператором @Coin_var\n\n"
            "Укажите ваш ID и сумму пополнения:"
            f"\n<code>{message.from_user.id} - {rub_amount.normalize()} ₽ → {amount_text}</code>",
            reply_markup=contact_operator_kb(currency)
        )
        
    except (ValueError, InvalidOperation):
        await message.answer("❌ Пожалуйста, введите корректное число (например: 100 или 150.5)")

@router.pre_checkout_query()
async def pre_checkout_handler(pre_checkout_query: PreCheckoutQuery, bot: Bot):
    """Подтверждение платежа"""
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

@router.message(F.successful_payment)
async def successful_payment_handler(message: types.Message, bot: Bot):
    """Обработка успешных платежей (Stars и майнинг)"""
    try:
        payload = message.successful_payment.invoice_payload
        user_id = message.from_user.id
        
        # Обработка пополнения баланса через Stars
        if payload.startswith('stars_'):
            parts = payload.split('_')
            payload_user_id = parts[1]
            amount = int(parts[2])
            currency = parts[3] if len(parts) > 3 else 'MICO'
            
            # Проверка соответствия user_id
            if int(payload_user_id) != user_id:
                await message.answer("❌ Ошибка: несоответствие ID пользователя")
                return
                
            # Зачисляем средства
            if currency == 'MICO':
                await DB.add_balance(user_id, amount)
            else:
                rub_amount = amount / 2000 * 20  # Конвертируем MICO обратно в RUB по примерному курсу
                await DB.add_rub_balance(user_id, float(rub_amount))
                
            await DB.add_transaction(
                user_id=user_id,
                amount=float(amount),
                description=f"Пополнение Stars ({currency})",
                additional_info=payload
            )
            
            await message.answer(
                f"✅ Пополнение на {amount} {currency} успешно зачислено!\n\n"
                "Спасибо за использование нашего сервиса!",
                reply_markup=back_to_menu_kb()
            )
            
            # Уведомление админам
            for admin_id in ADMINS_ID:
                try:
                    await bot.send_message(
                        admin_id,
                        f"💰 Новое пополнение через Stars\n"
                        f"👤 ID: {user_id}\n"
                        f"💎 Сумма: {amount} {currency}"
                    )
                except Exception as e:
                    logger.error(f"Ошибка уведомления админа {admin_id}: {e}")
        
        # Обработка оплаты майнинга
        elif payload.startswith(f"user_{user_id}_stars_199"):
            await DB.add_mining(user_id, 1)
            kb = InlineKeyboardBuilder()
            kb.button(text='🚀 Майнинг', callback_data='mining')
            await message.answer(
                "🚀 Майнинг активирован! Теперь вы можете зарабатывать $MICO автоматически.\n"
                "Заходите в меню майнинга, чтобы следить за доходом!",
                reply_markup=kb.as_markup()
            )
            
            # Уведомление админам
            for admin_id in ADMINS_ID:
                try:
                    await bot.send_message(
                        admin_id,
                        f"⛏️ Активирован майнинг\n"
                        f"👤 ID: {user_id}"
                    )
                except Exception as e:
                    logger.error(f"Ошибка уведомления админа {admin_id}: {e}")
        
        # Неизвестный тип платежа
        else:
            logger.warning(f"Неизвестный тип платежа: {payload}")
            await message.answer("⚠️ Получен неизвестный тип платежа")
            
    except Exception as e:
        logger.error(f"Ошибка обработки платежа: {e}")
        error_code = hash(str(e)) % 10000
        await message.answer(
            "❌ Произошла ошибка при обработке платежа.\n"
            f"Код ошибки: PAY-{error_code}\n"
            "Пожалуйста, обратитесь в поддержку."
        )
        
        # Отправка лога админам
        for admin_id in ADMINS_ID:
            try:
                await bot.send_message(
                    admin_id,
                    f"🔥 Ошибка обработки платежа\n"
                    f"👤 ID: {user_id}\n"
                    f"📝 Payload: {payload}\n"
                    f"🚨 Ошибка: {str(e)}\n"
                    f"🛠 Код: PAY-{error_code}"
                )
            except Exception as e:
                logger.error(f"Не удалось отправить лог админу: {e}")

# Клавиатуры
def select_currency_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="💎 $MICO", callback_data="deposit_currency_MICO")
    kb.button(text="₽ Рубли", callback_data="deposit_currency_RUB")
    kb.button(text="🔙 Назад", callback_data="back_menu")
    kb.adjust(2, 1)
    return kb.as_markup()

def deposit_methods_kb(currency: str):
    kb = InlineKeyboardBuilder()
    if currency == 'MICO':
        kb.button(text="⭐️ Telegram Stars", callback_data="deposit_stars")
    kb.button(text="💵 USDT (CryptoBot)", callback_data="deposit_cryptobot")
    kb.button(text="APay", callback_data="deposit_apays")  #deposit_rub
    # kb.button(text="XPAY", callback_data="deposit_xpay")  #deposit_rub
    kb.button(text="💎 TON", callback_data="ton_deposit")
    kb.button(text="🔙 Назад", callback_data="select_deposit_menu")
    if currency == 'MICO':
        kb.adjust(2, 2, 1)
    else:
        kb.adjust(1, 2, 1)
    return kb.as_markup()

def back_to_deposit_kb(currency: str):
    kb = [[InlineKeyboardButton(text="🔙 Назад", callback_data=f"deposit_currency_{currency}")]]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def confirm_stars_deposit_kb(amount_mico: int, stars_amount: Decimal, currency: str):
    kb = [
        [InlineKeyboardButton(
            text=f"✅ Оплатить {stars_amount.normalize()} Stars", 
            callback_data=f"confirm_stars_{amount_mico}_{stars_amount}_{currency}"
        )],
        [InlineKeyboardButton(text="🔙 Назад", callback_data=f"deposit_currency_{currency}")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def confirm_crypto_deposit_kb(amount: Decimal, usdt_amount: Decimal, currency: str):
    kb = [
        [InlineKeyboardButton(
            text=f"✅ Подтвердить", 
            callback_data=f"confirm_crypto_{amount}_{usdt_amount}_{currency}"
        )],
        [InlineKeyboardButton(text="🔙 Назад", callback_data=f"deposit_currency_{currency}")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def contact_operator_kb(currency: str):
    kb = [
        [InlineKeyboardButton(text="📞 Написать оператору", url="https://t.me/Coin_var")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data=f"deposit_currency_{currency}")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def back_to_menu_kb():
    kb = [[InlineKeyboardButton(text="🔙 В меню", callback_data="back_menu")]]
    return InlineKeyboardMarkup(inline_keyboard=kb)