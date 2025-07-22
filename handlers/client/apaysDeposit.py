# apaysDeposit.py
from .client import *
from .deposit import *
from API.APayAPI import APayAPI

@router.callback_query(F.data == 'deposit_apays')
async def deposit_apays_handler(callback: types.CallbackQuery, state: FSMContext):
    """Меню пополнения через APays"""
    data = await state.get_data()
    currency = data.get('deposit_currency', 'MICO')
    
    text = (
        f"💳 <b>Пополнение {currency} через APays</b>\n\n"
        "Введите сумму в рублях (мин. 100 ₽):"
    )
    
    await callback.message.edit_text(text, reply_markup=back_to_deposit_kb(currency))
    await state.set_state(DepositStates.waiting_apays_amount)
    await callback.answer()

@router.message(DepositStates.waiting_apays_amount)
async def process_apays_amount(message: types.Message, state: FSMContext):
    """Обработка ввода суммы"""
    data = await state.get_data()
    currency = data.get('deposit_currency', 'MICO')
    
    try:
        rub_amount = Decimal(message.text.replace(',', '.'))
        if rub_amount < 10:
            await message.answer("❌ Минимальная сумма - 100 ₽")
            return
            
        amount = int(rub_amount * 1000) if currency == 'MICO' else rub_amount
        amount_text = f"{amount} {'$MICO' if currency == 'MICO' else '₽'}"
        
        await message.answer(
            f"💎 <b>Детали пополнения:</b>\n\n"
            f"• Оплата: {rub_amount} ₽\n• Получите: {amount_text}\n"
            f"• Курс: 1 ₽ = {'1000 $MICO' if currency == 'MICO' else '1 ₽'}\n\n"
            "Для продолжения нажмите кнопку ниже 👇",
            reply_markup=confirm_apays_deposit_kb(amount, rub_amount, currency)
        )
    except (ValueError):
        await message.answer("❌ Введите корректную сумму (например: 100 или 150.5)")

@router.callback_query(F.data.startswith('confirm_apays_'))
async def confirm_apays_deposit(callback: types.CallbackQuery, state: FSMContext):
    """Создание платежа"""
    _, _, amount, rub_amount, currency = callback.data.split('_')
    user_id = callback.from_user.id
    order_id = f"apay_{int(time.time())}_{user_id}"
    
    try:
        invoice = await APayAPI.create_invoice(int(Decimal(rub_amount)*100), order_id)
        
        if not invoice.get('status'):
            error = invoice.get('error', 'Неизвестная ошибка')
            await callback.message.answer(f"❌ Ошибка: {error}")
            return
            
        await save_payment_data(
            user_id=user_id,
            amount=float(amount),
            currency=currency,
            order_id=order_id,
            status='created'
        )
        
        await callback.message.edit_text(
            f"🔗 <b>Платеж создан</b>\n\n"
            f"Сумма: {rub_amount} ₽\nК получению: {amount} {currency}\n\n"
            "Счет действителен 15 минут ⏳\n\n"
            f"❗️ Если на сайте не будет доступных способов оплаты, попробуйте подождать или увеличить сумму оплаты ❗️",
            reply_markup=payment_keyboard(invoice['url'], order_id, amount, currency)
        )
    except Exception as e:
        logger.error(f"APays error: {e}")
        await callback.message.answer("❌ Ошибка при создании платежа")
    finally:
        await callback.answer()

@router.callback_query(F.data.startswith('check_apays_'))
async def check_apays_payment(callback: types.CallbackQuery, bot: Bot):
    """Проверка статуса платежа"""
    parts = callback.data.split('_')

    if len(parts) < 4:
        await callback.answer("❌ Неверный формат данных", show_alert=True)
        return
    
    order_id = '_'.join(parts[2:-2])  # Собираем order_id из средних частей
    amount = parts[-2]
    currency = parts[-1]
    
    user_id = callback.from_user.id
    
    try:
        payment = await APayAPI.check_status(order_id)
        
        if payment.get('order_status') == 'approve':
            await process_successful_payment(
                user_id=user_id,
                amount=float(amount),
                currency=currency,
                order_id=order_id,
                bot=bot,
                callback=callback
            )
        elif payment.get('order_status') == 'pending':
            await callback.answer("ℹ️ Платеж еще не оплачен", show_alert=True)
        else:
            await callback.answer("❌ Платеж не найден", show_alert=True)
    except Exception as e:
        logger.error(f"Payment check error: {e}")
        await callback.answer("❌ Ошибка проверки", show_alert=True)

async def save_payment_data(user_id: int, amount: float, currency: str, order_id: str, status: str):
    """Сохранение данных платежа (замените на свою реализацию)"""
    payment_data = {
        'user_id': user_id,
        'amount': amount,
        'currency': currency,
        'order_id': order_id,
        'status': status,
        'created_at': datetime.now().isoformat()
    }
    # Реализуйте сохранение в вашу БД
    print(f"Saving payment: {payment_data}")

async def process_successful_payment(user_id: int, amount: float, currency: str, order_id: str, bot: Bot, callback: types.CallbackQuery):
    """Обработка успешного платежа"""
    if currency == 'MICO':
        await DB.add_balance(user_id, amount)
    else:
        await DB.add_rub_balance(user_id, amount)
    
    await DB.add_transaction(
        user_id=user_id,
        amount=amount,
        description=f"Пополнение {currency} через APays",
        additional_info=f"order_{order_id}"
    )

    await callback.message.edit_text(
        f"✅ Пополнение на {amount} {currency} успешно зачислено!",
        reply_markup=back_to_menu_kb()
    )

    await notify_admins(bot, user_id, amount, currency, order_id)

async def notify_admins(bot: Bot, user_id: int, amount: float, currency: str, order_id: str):
    """Уведомление администраторов"""
    message = (
        f"💰 Новое пополнение через APays\n"
        f"👤 ID: {user_id}\n💎 Сумма: {amount} {currency}\n"
        f"📝 Order ID: {order_id}"
    )
    
    for admin_id in ADMINS_ID:
        try:
            await bot.send_message(admin_id, message)
        except Exception as e:
            logger.error(f"Admin notify error: {e}")

def payment_keyboard(url: str, order_id: str, amount: float, currency: str):
    """Клавиатура для оплаты"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Оплатить", url=url)],
        [InlineKeyboardButton(
            text="🔄 Проверить оплату",
            callback_data=f"check_apays_{order_id}_{amount}_{currency}"
        )]
    ])

def confirm_apays_deposit_kb(amount: float, rub_amount: float, currency: str):
    """Клавиатура подтверждения"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="✅ Создать платеж",
            callback_data=f"confirm_apays_{amount}_{rub_amount}_{currency}"
        )],
        [InlineKeyboardButton(
            text="🔙 Назад",
            callback_data=f"deposit_currency_{currency}"
        )]
    ])