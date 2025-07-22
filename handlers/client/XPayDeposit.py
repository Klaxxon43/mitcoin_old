# xpay_deposit.py

from .client import *
from .deposit import *
from API.XPay import XPayClient

xpay = XPayClient()

@router.callback_query(F.data == 'deposit_xpay')
async def deposit_xpay_handler(callback: types.CallbackQuery, state: FSMContext):
    currency = (await state.get_data()).get('deposit_currency', 'MICO')
    text = (
        f"✪ <b>Пополнение {currency} через XPay</b>\n\n"
        "Введите сумму в рублях (min. 10 ₽):"
    )
    await callback.message.edit_text(text, reply_markup=back_to_deposit_kb(currency))
    await state.set_state(DepositStates.waiting_xpay_amount)
    await callback.answer()

@router.message(DepositStates.waiting_xpay_amount)
async def process_xpay_amount(message: types.Message, state: FSMContext):
    currency = (await state.get_data()).get('deposit_currency', 'MICO')

    try:
        rub_amount = Decimal(message.text.replace(',', '.'))
        if rub_amount < 10:
            return await message.answer("❌ Минимальная сумма — 10 ₽")

        amount = float(rub_amount * 1000) if currency == 'MICO' else float(rub_amount)

        await message.answer(
            f"💎 <b>Детали пополнения:</b>\n\n"
            f"• Оплата: {rub_amount} ₽\n• К получению: {amount} {currency}\n"
            f"• Курс: 1 ₽ = {'1000 $MICO' if currency == 'MICO' else '1 ₽'}\n\n"
            "Для продолжения нажмите кнопку ниже 👇",
            reply_markup=confirm_xpay_deposit_kb(amount, rub_amount, currency)
        )
    except ValueError:
        await message.answer("❌ Введите корректную сумму")

@router.callback_query(F.data.startswith('confirm_xpay_'))
async def confirm_xpay_deposit(callback: types.CallbackQuery, state: FSMContext):
    _, _, amount, rub_amount, currency = callback.data.split('_')
    user_id = callback.from_user.id

    try:
        invoice = await xpay.create_invoice(
            amount=float(rub_amount),
            description=f"Пополнение {currency}", 
            payload=str(user_id),
            user_id=user_id
        )

        await callback.message.edit_text(
            f"🔗 <b>Платеж создан</b>\n\n"
            f"Сумма: {rub_amount} ₽\nК получению: {amount} {currency}\n\n"
            "Счет действителен 15 минут ⏳",
            reply_markup=payment_keyboard(invoice['url'], invoice['unique_id'], amount, currency)
        )
    except Exception as e:
        logger.error(f"XPay error: {e}")
        await callback.message.answer("❌ Ошибка при создании платежа")
    finally:
        await callback.answer()

@router.callback_query(F.data.startswith('xpay_'))
async def check_xpay_payment(callback: types.CallbackQuery, bot: Bot):
    parts = callback.data.split('_')
    if len(parts) < 4:
        return await callback.answer("❌ Неверный формат данных", show_alert=True)

    unique_id = '_'.join(parts[2:-2])
    amount = parts[-2]
    currency = parts[-1]
    user_id = callback.from_user.id

    try:
        updated = await xpay.check_payment_status(unique_id)
        deposit = await DB.get_deposit(unique_id)

        if deposit and deposit['status'] == 'paid':
            await process_successful_payment(user_id, float(amount), currency, unique_id, bot, callback)
        elif not updated:
            await callback.answer("ℹ️ Платеж еще не оплачен", show_alert=True)
        else:
            await callback.answer("❌ Платеж не найден", show_alert=True)
    except Exception as e:
        logger.error(f"XPay payment check error: {e}")
        await callback.answer("❌ Ошибка при проверке платежа", show_alert=True)


def confirm_xpay_deposit_kb(amount: float, rub_amount, currency: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="✅ Создать платёж",
                callback_data=f"confirm_xpay_{amount}_{rub_amount}_{currency}"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔙 Назад",
                callback_data=f"deposit_currency_{currency}"
            )
        ]
    ])
def payment_keyboard(url: str, unique_id: str, amount: float, currency: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="💳 Оплатить",
                url=url
            )
        ],
        [
            InlineKeyboardButton(
                text="🔄 Проверить оплату",
                callback_data=f"xpay_{unique_id}_{amount}_{currency}"
            )
        ]
    ])

async def process_successful_payment(user_id: int, amount: float, currency: str, unique_id: str, bot: Bot, callback: types.CallbackQuery):
    if currency == 'MICO':
        await DB.add_balance(user_id, amount)
    else:
        await DB.add_rub_balance(user_id, amount)

    await DB.add_transaction(
        user_id=user_id,
        amount=amount,
        description=f"Пополнение {currency} через XPay",
        additional_info=f"unique_{unique_id}"
    )

    await callback.message.edit_text(
        f"✅ Пополнение на {amount} {currency} успешно зачислено!",
        reply_markup=back_to_menu_kb()
    )

    await notify_admins(bot, user_id, amount, currency, unique_id)

async def notify_admins(bot: Bot, user_id: int, amount: float, currency: str, unique_id: str):
    message = (
        f"💰 Новое пополнение через XPay\n"
        f"👤 ID: <code>{user_id}</code>\n"
        f"💸 Сумма: {amount} {currency}\n"
        f"🧾 ID платежа: <code>{unique_id}</code>"
    )
    for admin_id in ADMINS_ID:
        try:
            await bot.send_message(admin_id, message)
        except Exception as e:
            print(f"Ошибка отправки админу {admin_id}: {e}")