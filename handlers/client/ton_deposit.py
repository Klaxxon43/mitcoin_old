from .client import *
from confIg import *
from API.TonAPI import *
# Настройка логгирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_unique_code(length=8):
    """Генерация уникального кода для транзакции"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))


@router.callback_query(F.data == 'ton_deposit')
async def ton_deposit_handler(callback: types.CallbackQuery, state: FSMContext):
    """Обработчик пополнения через TON"""
    logger.info(f"Начало обработки TON депозита для user_id: {callback.from_user.id}")
    
    try:
        # Получаем курс TON к рублю
        ton_rate = await get_ton_rate()
        logger.info(f"Текущий курс TON: {ton_rate} RUB")
        
        await callback.message.edit_text(
            f"💎 <b>Пополнение через TON</b>\n\n"
            f"Текущий курс: 1 TON = {ton_rate:.2f}₽\n\n"
            "Введите сумму в рублях (от 10₽):",
            reply_markup=back_menu_kb(callback.from_user.id)
        )
        
        await state.set_state("waiting_ton_amount")
        await state.update_data(ton_rate=ton_rate)
        logger.info("Состояние установлено: waiting_ton_amount")
        
    except Exception as e:
        logger.error(f"Ошибка в ton_deposit_handler: {e}")
        await callback.answer("Произошла ошибка, попробуйте позже", show_alert=True)

async def get_ton_rate():
    """Получение курса TON к рублю"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://api.coingecko.com/api/v3/simple/price?ids=the-open-network&vs_currencies=rub",
                timeout=5
            ) as response:
                data = await response.json()
                return data['the-open-network']['rub']
    except Exception as e:
        logger.error(f"Ошибка при получении курса TON: {e}")
        return 200  # Курс по умолчанию

@router.message(F.text, StateFilter("waiting_ton_amount"))
async def process_ton_amount(message: types.Message, state: FSMContext):
    """Обработка суммы пополнения"""
    logger.info(f"Обработка суммы от user_id: {message.from_user.id}")
    
    try:
        rub_amount = float(message.text.strip())
        data = await state.get_data()
        
        # Получаем курс из state или запрашиваем новый, если отсутствует
        ton_rate = data.get('ton_rate')
        if not ton_rate:
            ton_rate = await get_ton_rate()
            await state.update_data(ton_rate=ton_rate)
        
        currency = data.get('deposit_currency', 'MICO')  # Получаем выбранную валюту

        ton_amount = round(rub_amount / ton_rate, 4)
        amount_nano = int(ton_amount * 10**9)
        unique_code = generate_unique_code()

        builder = InlineKeyboardBuilder()
        payment_links = [
            ("Ton Wallet", f"ton://transfer/{TON_WALLET}"),
            ("Tonkeeper", f"https://app.tonkeeper.com/transfer/{TON_WALLET}"),
            ("Tonhub", f"https://tonhub.com/transfer/{TON_WALLET}")
        ]
        
        for name, base_url in payment_links:
            builder.button(text=name, url=f"{base_url}?amount={amount_nano}&text={unique_code}")
            
        builder.button(text="✅ Проверить оплату", callback_data=f"check_ton:{unique_code}:{amount_nano}:{rub_amount}:{currency}")
        builder.button(text="✏️ Изменить сумму", callback_data="ton_deposit")
        builder.button(text="🔙 Назад", callback_data="select_deposit_menu")
        
        builder.adjust(2, 1, 1)
        
        await message.answer(
            f"💎 <b>Пополнение через TON</b>\n\n"
            f"▪ Сумма: <b>{ton_amount:.4f} TON</b> (~{rub_amount:.2f}₽)\n"
            f"▪ Валюта: {'RUB' if currency == 'RUB' else 'MICO'}\n"
            f"▪ Адрес: <code>{TON_WALLET}</code>\n"
            f"▪ Комментарий: <code>{unique_code}</code>\n\n"
            "После оплаты нажмите 'Проверить оплату'",
            reply_markup=builder.as_markup()
        )
        
        await state.update_data(
            amount_nano=str(amount_nano),
            unique_code=unique_code,
            rub_amount=rub_amount,
            currency=currency
        )
        logger.info(f"Сгенерирован запрос на оплату: {amount_nano} nanoTON, код: {unique_code}, валюта: {currency}")
        
    except ValueError:
        await message.answer("❌ Пожалуйста, введите корректную сумму (например: 100)")
        logger.warning("Некорректный ввод суммы")

@router.callback_query(F.data.startswith("check_ton:"))
async def check_payment_handler(callback: types.CallbackQuery, state: FSMContext):
    logger.info(f"Проверка платежа для user_id: {callback.from_user.id}")
    
    try:
        parts = callback.data.split(':')
        if len(parts) < 4:
            logger.error(f"Некорректный формат callback данных: {callback.data}")
            await callback.answer("Ошибка обработки платежа", show_alert=True)
            return
            
        code = parts[1]
        amount_nano = parts[2]
        rub_amount = parts[3]
        currency = parts[4] if len(parts) > 4 else 'MICO'  # Безопасное получение валюты
        print(parts, currency)
        
        logger.info(f"Проверка платежа: код={code}, сумма={amount_nano}, руб={rub_amount}, валюта={currency}")
        
        if await check_ton_payment(amount_nano, code):
            user_id = callback.from_user.id
            rub_amount = float(rub_amount)
            
            if currency == 'MICO':
                await DB.add_balance(user_id, rub_amount * 1000)  # Конвертируем в MICO
                success_msg = f"✅ <b>Платеж получен!</b>\nВаш MICO баланс пополнен на {rub_amount:.2f} $MICO"
            else:
                await DB.add_rub_balance(user_id, rub_amount)  # Зачисляем рубли напрямую
                success_msg = f"✅ <b>Платеж получен!</b>\nВаш рублевый баланс пополнен на {rub_amount:.2f}₽"
                
            await DB.add_transaction(
                user_id=user_id,
                amount=rub_amount,
                description=f"Пополнение TON ({currency})",
                additional_info=code
            )
            
            await callback.message.edit_text(
                success_msg,
                reply_markup=InlineKeyboardBuilder()
                    .button(text="👌 OK", callback_data="profile")
                    .as_markup()
            )
            await state.clear()
        else:
            await callback.answer("Платеж не найден. Попробуйте позже.", show_alert=True)
            
    except ValueError as e:
        logger.error(f"Ошибка преобразования данных: {e}")
        await callback.answer("Ошибка обработки суммы платежа", show_alert=True)
    except Exception as e:
        logger.error(f"Ошибка при проверке платежа: {e}", exc_info=True)
        await callback.answer("Произошла ошибка, попробуйте позже", show_alert=True)