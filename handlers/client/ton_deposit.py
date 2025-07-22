from .client import *
from confIg import *
# Настройка логгирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_unique_code(length=8):
    """Генерация уникального кода для транзакции"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

async def check_ton_payment(expected_amount_nano: str, comment: str) -> bool:
    """Проверка платежа в сети TON с подробным логированием"""
    print(f"\n🔍 [Проверка платежа] Ожидаем: {expected_amount_nano} nanoTON, комментарий: '{comment}'")
    
    try:
        expected = int(expected_amount_nano)
        tolerance = max(int(expected * 0.01), 1000000)
        print(f"🔢 Допустимый диапазон: {expected - tolerance} - {expected + tolerance} nanoTON")
        
        params = {
            'address': str(TON_WALLET),
            'limit': 20,
            'api_key': str(TON_API_TOKEN),
            'archival': 'true'
        }
        
        print("🌐 Запрашиваем транзакции с параметрами:")
        print(f" - Адрес: {TON_WALLET}")
        print(f" - Лимит: 20")
        
        async with aiohttp.ClientSession() as session:
            try:
                response = await session.get(
                    f"{TON_API_BASE}getTransactions",
                    params=params,
                    timeout=20
                )
                
                print(f"📡 Ответ API: статус {response.status}")
                
                if response.status != 200:
                    print(f"❌ Ошибка API: HTTP {response.status}")
                    return False
                
                data = await response.json()
                print(f"📊 Получено транзакций: {len(data.get('result', []))}")
                
                if not data.get('ok', False):
                    error_msg = data.get('error', 'Неизвестная ошибка API')
                    print(f"❌ Ошибка API: {error_msg}")
                    return False
                
                for tx in data.get('result', []):
                    in_msg = tx.get('in_msg', {})
                    
                    # Обработка суммы
                    tx_value = 0
                    try:
                        value = in_msg.get('value')
                        if value is not None:
                            tx_value = int(float(value))
                    except (TypeError, ValueError):
                        continue
                    
                    # Обработка комментария
                    tx_comment = str(in_msg.get('message', '')).strip()
                    
                    print(f"\n🔎 Проверяем транзакцию:")
                    print(f" - Хэш: {tx.get('hash')}")
                    print(f" - Сумма: {tx_value} nanoTON")
                    print(f" - Комментарий: '{tx_comment}'")
                    print(f" - Дата: {tx.get('utime')}")
                    
                    # Проверка совпадения
                    amount_match = abs(tx_value - expected) <= tolerance
                    comment_match = tx_comment == comment.strip()
                    
                    print(f"🔹 Совпадение суммы: {'✅' if amount_match else '❌'}")
                    print(f"🔹 Совпадение комментария: {'✅' if comment_match else '❌'}")
                    
                    if amount_match and comment_match:
                        print(f"\n🎉 Найден подходящий платеж!")
                        print(f" - Получено: {tx_value} nanoTON")
                        print(f" - Ожидалось: {expected} nanoTON (±{tolerance})")
                        print(f" - Комментарий: '{tx_comment}'")
                        print(f" - Время: {tx.get('utime')}")
                        return True
                
                print("\n🔍 Подходящих платежей не найдено")
                return False
                
            except asyncio.TimeoutError:
                print("⏱️ Таймаут при запросе к TON API")
                return False
            except aiohttp.ClientError as e:
                print(f"🌐 Ошибка сети: {str(e)}")
                return False
    
    except Exception as e:
        print(f"💥 Критическая ошибка: {type(e).__name__}: {str(e)}")
        return False

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
        # if rub_amount < 10:
        #     await message.answer("Минимальная сумма - 10 рублей")
        #     return
            
        data = await state.get_data()
        ton_rate = data['ton_rate']
        
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
            
        builder.button(text="✅ Проверить оплату", callback_data=f"check_ton:{unique_code}:{amount_nano}:{rub_amount}")
        builder.button(text="✏️ Изменить сумму", callback_data="ton_deposit")
        builder.button(text="🔙 Назад", callback_data="select_deposit_menu")
        
        builder.adjust(2, 1, 1)
        
        await message.answer(
            f"💎 <b>Пополнение через TON</b>\n\n"
            f"▪ Сумма: <b>{ton_amount:.4f} TON</b> (~{rub_amount:.2f}₽)\n"
            f"▪ Адрес: <code>{TON_WALLET}</code>\n"
            f"▪ Комментарий: <code>{unique_code}</code>\n\n"
            "После оплаты нажмите 'Проверить оплату'",
            reply_markup=builder.as_markup()
        )
        
        await state.update_data(
            amount_nano=str(amount_nano),
            unique_code=unique_code,
            rub_amount=rub_amount
        )
        logger.info(f"Сгенерирован запрос на оплату: {amount_nano} nanoTON, код: {unique_code}")
        
    except ValueError:
        await message.answer("Введите число (например: 100)")
        logger.warning("Некорректный ввод суммы")

@router.callback_query(F.data.startswith("check_ton:"))
async def check_payment_handler(callback: types.CallbackQuery, state: FSMContext):
    """Проверка оплаты"""
    logger.info(f"Проверка платежа для user_id: {callback.from_user.id}")
    
    try:
        _, code, amount_nano, rub_amount = callback.data.split(':')
        
        if await check_ton_payment(amount_nano, code):
            user_id = callback.from_user.id
            rub_amount = float(rub_amount)
            
            await DB.add_balance(user_id, rub_amount* 1000)
            await DB.add_transaction(
                user_id=user_id,
                amount=rub_amount,
                description="Пополнение TON",
                additional_info=code
            )
            
            await callback.message.edit_text(
                f"✅ <b>Платеж получен!</b>\n"
                f"Ваш баланс пополнен на {rub_amount:.2f}₽",
                reply_markup=InlineKeyboardBuilder()
                    .button(text="👌 OK", callback_data="profile")
                    .as_markup()
            )
            await state.clear()
            logger.info(f"Платеж подтвержден для user_id: {user_id}")
        else:
            await callback.answer("Платеж не найден. Попробуйте через 30 секунд", show_alert=True)
            logger.warning(f"Платеж не найден для user_id: {callback.from_user.id}")
            
    except Exception as e:
        logger.error(f"Ошибка при проверке платежа: {e}")
        await callback.answer("Произошла ошибка, попробуйте позже", show_alert=True)