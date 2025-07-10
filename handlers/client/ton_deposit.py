from .client import *
from config import *

# Добавь эту функцию в client.py (можно рядом с другими функциями)
def generate_unique_code(length=8):
    """Генерация уникального кода для транзакции"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

async def check_ton_payment(expected_amount_nano: str, comment: str) -> bool:
    """Проверка платежа в сети TON с учетом возможного округления"""
    print(f"\n🔍 Starting TON payment check for amount: {expected_amount_nano}, comment: '{comment}'")
    
    try:
        response = requests.get(
            f"{TON_API_BASE}getTransactions",
            params={
                'address': TON_WALLET,
                'limit': 100,
                'api_key': TON_API_TOKEN,
                'archival': True
            },
            timeout=10
        )
        
        data = response.json()
        if not data.get('ok', False):
            return False

        expected = int(expected_amount_nano)
        tolerance = 1000000  # Допустимое отклонение ±0.001 TON (1,000,000 нанотонов)
        
        for tx in data.get('result', []):
            in_msg = tx.get('in_msg', {})
            tx_value = int(in_msg.get('value', 0))
            tx_comment = in_msg.get('message', '').strip()
            
            print(f"Checking: {tx_value} vs {expected} (±{tolerance}), comment: '{tx_comment}'")
            
            if (abs(tx_value - expected) <= tolerance and 
                tx_comment == comment.strip()):
                return True

        return False
    except Exception as e:
        print(f"TON payment check error: {e}")
        return False

# Добавь этот обработчик в router (можно рядом с другими обработчиками пополнения)
@router.callback_query(F.data == 'ton_deposit')
async def ton_deposit_handler(callback: types.CallbackQuery, state: FSMContext):
    """Обработчик выбора пополнения через TON"""
    user_id = callback.from_user.id
    
    # Получаем курс TON к рублю (можно использовать любой API)
    try:
        response = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=the-open-network&vs_currencies=rub")
        ton_rate = response.json()['the-open-network']['rub']
    except:
        ton_rate = 200  # Значение по умолчанию если API не доступен
    
    await callback.message.edit_text(
        f"💎 <b>Пополнение через TON</b>\n\n"
        f"Текущий курс: 1 TON = {ton_rate:.2f}₽\n\n"
        "Введите сумму в рублях, которую вы хотите пополнить:",
        reply_markup=back_menu_kb(user_id)
    )
    
    await state.set_state("waiting_ton_amount")
    await state.update_data(ton_rate=ton_rate)


@router.message(F.text, StateFilter("waiting_ton_amount"))
async def process_ton_amount(message: types.Message, state: FSMContext):
    """Обработка ввода суммы для пополнения через TON"""
    user_id = message.from_user.id
    try:
        rub_amount = float(message.text.strip())
        if rub_amount < 10:
            await message.answer("Минимальная сумма пополнения - 10 рублей")
            return
        
        data = await state.get_data()
        ton_rate = data['ton_rate']
        
        # Конвертируем рубли в TON
        ton_amount = (rub_amount / ton_rate, 4)
        amount_nano = int(ton_amount * 1_000_000_000)  # Конвертация в нанотоны
        
        # Генерируем уникальный комментарий
        unique_code = generate_unique_code()
        
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(
                text="Ton Wallet",
                url=f"ton://transfer/{TON_WALLET}?amount={amount_nano}&text={unique_code}"
            ),
            InlineKeyboardButton(
                text="Tonkeeper",
                url=f"https://app.tonkeeper.com/transfer/{TON_WALLET}?amount={amount_nano}&text={unique_code}"
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="Tonhub",
                url=f"https://tonhub.com/transfer/{TON_WALLET}?amount={amount_nano}&text={unique_code}"
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="✅ Проверить оплату",
                callback_data=f"check_ton_payment:{unique_code}:{amount_nano}:{rub_amount}"
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="✏️ Изменить сумму",
                callback_data="ton_deposit"
            ),
            InlineKeyboardButton(
                text="🔙 Назад",
                callback_data="select_deposit_menu"
            )
        )

        await message.answer(
            f"💎 <b>Пополнение через TON</b>\n\n"
            f"Сумма к оплате: <b>{ton_amount:.4f} TON</b> (~{rub_amount:.2f}₽)\n\n"
            f"Пожалуйста, отправьте <b>{ton_amount:.4f} TON</b> на адрес:\n"
            f"<code>{TON_WALLET}</code>\n\n"
            f"С комментарием:\n<code>{unique_code}</code>\n\n"
            "После оплаты нажмите кнопку 'Проверить оплату'",
            reply_markup=builder.as_markup()
        )
        
        await state.update_data(
            amount_nano=str(amount_nano),
            unique_code=unique_code,
            rub_amount=rub_amount
        )
    except ValueError:
        await message.answer("Пожалуйста, введите корректную сумму в рублях (например: 100)")

@router.callback_query(F.data.startswith("check_ton_payment:"))
async def check_ton_payment_callback(callback: types.CallbackQuery, state: FSMContext):
    """Проверка платежа TON"""
    parts = callback.data.split(":")
    unique_code = parts[1]
    amount_nano = parts[2]
    rub_amount = float(parts[3])
    
    result = await check_ton_payment(amount_nano, unique_code)
    
    if not result:
        await callback.answer(
            "Платеж еще не получен. Пожалуйста, подождите и попробуйте снова через 10 секунд.",
            show_alert=True
        )
        return
    
    user_id = callback.from_user.id
    
    # Зачисляем рубли на баланс
    await DB.add_rub_balance(user_id, rub_amount)
    await DB.add_transaction(
        user_id=user_id,
        amount=rub_amount,
        description="пополнение TON",
        additional_info=None
    )
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data="profile")
    )
    
    await callback.message.edit_text(
        f"✅ <b>Платеж подтвержден!</b>\n\n"
        f"Ваш баланс пополнен на {rub_amount:.2f}₽\n\n"
        "Спасибо за использование нашего сервиса!",
        reply_markup=builder.as_markup()
    )
    await state.clear()
