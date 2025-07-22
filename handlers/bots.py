from utils.Imports import *
from threading import Lock
import string

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bots = Router()

task_cache = {}
task_cache_chat = {}

PRICE_MARKUP = 3  # 30% наценка


# Генерация уникального кода для TON транзакций
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

PREMIUM_SERVICES = {
    "➕ Подписчики": 31388,
    "➕ Подписчики+": 32281,
    "👁 Просмотры": 31621,
    "📊 Опросы": 787,
    "🤖 Боты": 26716
} 

REACTION_SERVICES = {
    "🔥": 31910,
    "👍 ❤️ 🔥 🎉": 31163,
    "🤩": 32038,
    "👍": 32023,
    "💩 🤡": 722,
    "🤮 😭": 734,
    "👎 💔": 27497,
    "🤬": 32053
}

SERVICE_DESCRIPTIONS = {
    31388: """
📌 Услуга #31388
🏷 Название: TG Подписчики [Канал/Группа | Дешевые
💵 Стоимость: 60 рублей за 1000 единиц
📊 Лимиты: 10 - 50000
🚀 Скорость: Моментально
🛡 Гарантия: Нет

📝 Описание:
ПРИМЕР ССЫЛКИ:https://t.me/***Старт: 0-1 час. Скорость: 3000-4000 в день. Списания: Возможны. Мы не гарантируем возврат средств, если количество участников упадет ниже стартового.
Нет гарантии выполнения на пустые каналы из-за риска увеличения бана.
""",
    32281: """
📌 Услуга #32281
🏷 Название: TG Подписчики [Канал/Группа | Без списания
💵 Стоимость: 150 рублей за 1000 единиц
📊 Лимиты: 1 - 50000
🚀 Скорость: Моментально
🛡 Гарантия: Нет

📝 Описание:
ПРИМЕР ССЫЛКИ: https://t.me/***
Старт: 0-1 час
Скорость: 50 тысяч в день
Качество: Высокое
ГЕО: Микс
Списания: Нет
Заказы на контент 18+ будут отменены
Делайте скриншоты с количеством подписчиков до оформления заказа.Мы не гарантируем возврат средств, если количество участников упадет ниже стартового.
Подписчики могу отображаться с задержкой до 3 часов
""",
    31621: """
📌 Услуга #31621
🏷 Название: TG Просмотры [Пост]
💵 Стоимость: 5 рублей за 1000 единиц
📊 Лимиты: 10 - 10000
🚀 Скорость: Моментально
🛡 Гарантия: Нет

📝 Описание:
ПРИМЕР ССЫЛКИ: https://t.me/***/123
Старт: 0-1 час
Скорость: до 10 тысяч в день
ГЕО: Микс
Списания: Нет
""",
    787: """
📌 Услуга #787
🏷 Название: TG Накрутка опросов [Канал]
💵 Стоимость: 50 рублей за 1000 единиц
📊 Лимиты: 1 - 10000
🚀 Скорость: Моментально
🛡 Гарантия: Нет

📝 Описание:
ПРИМЕР ССЫЛКИ: https://t.me/***
Старт: 0-1 час
Скорость: до 100 тысяч в день
Списания: Нет
Гарантия: Нет
ГЕО: Микс
Работает только для каналов. Если, хотите накрутить на опрос в чате, нужно сделать репост в любой открытый канал и сделать заказ уже на канал.
""",
    26716: """
📌 Услуга #26716
🏷 Название: TG Бот Старт [Быстрые]
💵 Стоимость: 100 рублей за 1000 единиц
📊 Лимиты: 100 - 1000000
🚀 Скорость: Моментально
🛡 Гарантия: Нет

📝 Описание:
ПРИМЕР ССЫЛКИ: https://t.me/name_bot
Старт: 0-1 час
Скорость: до 10000 в день
Списания: Возможно
Гарантия: Нет
Сервис активирует команду /Start.
""",
    # Реакции имеют одинаковый шаблон описания
    31910: """
📌 Услуга #31910
🏷 Название: TG Реакции [🔥 | 1 Пост]
💵 Стоимость: 10 рублей за 1000 единиц
📊 Лимиты: 1 - 100000
🚀 Скорость: Моментально
🛡 Гарантия: Нет

📝 Описание:
ПРИМЕР ССЫЛКИ: https://t.me/***
Старт: 0-2 часа
Скорость: до 10000 в день
Гарантия: Нет
Списания: Возможны
Канал должен быть открытым
Реакции должны быть доступны
Средства не возвращаются при использовании неправильной ссылки.
"""
}

# Для реакций используем тот же шаблон, подставляя только эмодзи и ID
for reaction_id in [31163, 32038, 32023, 722, 734, 27497, 32053]:
    SERVICE_DESCRIPTIONS[reaction_id] = SERVICE_DESCRIPTIONS[31910].replace("🔥", list(REACTION_SERVICES.keys())[list(REACTION_SERVICES.values()).index(reaction_id)])


# Глобальный кэш для сервисов
SERVICES_CACHE = {
    'premium': None,
    'reactions': None,
    'last_updated': None
}

async def update_services_cache():
    """Фоновая задача для обновления кэша сервисов"""
    global SERVICES_CACHE
    
    premium_services = {}
    reaction_services = {}
    
    try:
        # Загружаем все сервисы параллельно
        tasks = []
        for service_id in PREMIUM_SERVICES.values():
            tasks.append(BotsAPI.get_service(service_id))
        for service_id in REACTION_SERVICES.values():
            tasks.append(BotsAPI.get_service(service_id))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Обрабатываем результаты
        for i, service_id in enumerate(list(PREMIUM_SERVICES.values()) + list(REACTION_SERVICES.values())):
            if i < len(results) and not isinstance(results[i], Exception):
                service = results[i]
                if service_id in PREMIUM_SERVICES.values():
                    premium_services[service_id] = service
                else:
                    reaction_services[service_id] = service
    
        SERVICES_CACHE = {
            'premium': premium_services,
            'reactions': reaction_services,
            'last_updated': time.time()
        }
    except Exception as e:
        logger.error(f"Error updating services cache: {e}")

@bots.callback_query(F.data == "bots_menu")
async def show_bots_menu(callback: types.CallbackQuery, bot: Bot):
    user_id = callback.from_user.id

    from handlers.client.client import check_subs_op
    if not await check_subs_op(user_id, bot):
        return
    
    if await DB.get_break_status() and user_id not in ADMINS_ID:
        await callback.message.answer('🛠Идёт технический перерыв🛠\nПопробуйте снова позже')
        return
    
    # Сначала сразу показываем меню
    builder = InlineKeyboardBuilder()
    
    # Добавляем кнопки основных услуг (из кэша, если есть)
    if SERVICES_CACHE['premium']:
        for service_name, service_id in PREMIUM_SERVICES.items():
            if service_id in SERVICES_CACHE['premium']:
                builder.button(text=service_name, callback_data=f"bots_srv_{service_id}")
    else:
        # Если кэш пустой, показываем базовые кнопки
        for service_name in PREMIUM_SERVICES:
            builder.button(text=service_name, callback_data=f"bots_srv_{PREMIUM_SERVICES[service_name]}")
    
    # Кнопка реакций
    builder.button(text="❤️ Реакции", callback_data="bots_reactions")
    builder.button(text='🔙 Назад', callback_data='pr_menu')
    builder.adjust(1)
    
    await callback.message.edit_text(
        "🛒 <b>Выберите категорию услуг:</b>",
        reply_markup=builder.as_markup()
    )
    
    # Затем запускаем фоновое обновление кэша, если нужно
    need_update = (
        SERVICES_CACHE['last_updated'] is None or 
        (time.time() - SERVICES_CACHE['last_updated']) > 300
    )
    
    if need_update:
        asyncio.create_task(update_services_cache())

@bots.callback_query(F.data == "bots_reactions")
async def show_reactions_menu(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    
    # Используем кэш, если есть, иначе базовые данные
    if SERVICES_CACHE['reactions']:
        for emoji_text, service_id in REACTION_SERVICES.items():
            if service_id in SERVICES_CACHE['reactions']:
                builder.button(text=emoji_text, callback_data=f"bots_srv_{service_id}")
    else:
        for emoji_text in REACTION_SERVICES:
            builder.button(text=emoji_text, callback_data=f"bots_srv_{REACTION_SERVICES[emoji_text]}")
    
    builder.button(text="🔙 Назад", callback_data="bots_back_to_main")
    builder.adjust(2)
    
    await callback.message.edit_text(
        "🎭 <b>Выберите тип реакций:</b>",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await callback.answer()


# Добавим новое состояние для оформления заказа
class OrderStates(StatesGroup):
    AWAITING_LINK = State()
    AWAITING_QUANTITY = State()
    VIEW_ORDERS = State()
    PAYMENT_METHOD = State()
    AWAITING_PAYMENT = State()

@bots.callback_query(F.data.startswith("bots_srv_"))
async def show_service_details(callback: types.CallbackQuery):
    service_id = int(callback.data.replace("bots_srv_", ""))
    
    # Получаем данные услуги
    service = await BotsAPI.get_service(service_id)
    if not service:
        await callback.answer("⚠️ Услуга временно недоступна")
        return
    
    # Получаем описание из SERVICE_DESCRIPTIONS
    service_description = SERVICE_DESCRIPTIONS.get(service_id, "")
    
    # Извлекаем цену из описания
    price_line = next((line for line in service_description.split('\n') if line.startswith('💵 Стоимость:')), None)
    marked_up_price = float(price_line.split(': ')[1].split(' руб')[0]) if price_line else float(service['rate']) * PRICE_MARKUP
    
    # Используем описание из SERVICE_DESCRIPTIONS или генерируем его
    if service_description:
        description = service_description
    else:
        description = f"""
📌 Услуга #{service['service']}
🏷 Название: {service['name']}
💵 Стоимость: {marked_up_price:.2f} руб. за 1000 единиц
📊 Лимиты: {service['min']} - {service['max']}
🚀 Скорость: {'Моментально' if not service['dripfeed'] else 'Постепенно'}
🛡 Гарантия: {'Есть' if service['refill'] else 'Нет'}
""".strip()
    
    builder = InlineKeyboardBuilder()
    builder.button(text="🛒 Купить", callback_data=f"buy_{service_id}")
    
    if service_id in REACTION_SERVICES.values():
        builder.button(text="🔙 Назад", callback_data="bots_reactions")
    else:
        builder.button(text="🔙 Назад", callback_data="bots_back_to_main")
    
    builder.adjust(2)
    
    await callback.message.edit_text(
        description,
        reply_markup=builder.as_markup()
    )
    await callback.answer()


@bots.callback_query(F.data.startswith("buy_"))
async def start_order_process(callback: types.CallbackQuery, state: FSMContext):
    service_id = int(callback.data.replace("buy_", ""))
    
    # Получаем информацию об услуге
    service = await BotsAPI.get_service(service_id)
    if not service:
        await callback.answer("⚠️ Услуга временно недоступна")
        return
    
    # Получаем описание из SERVICE_DESCRIPTIONS
    service_description = SERVICE_DESCRIPTIONS.get(service_id, "")
    
    # Извлекаем цену из описания
    price_line = next((line for line in service_description.split('\n') if line.startswith('💵 Стоимость:')), None)
    marked_up_rate = float(price_line.split(': ')[1].split(' руб')[0]) if price_line else float(service['rate']) * PRICE_MARKUP
    
    await state.update_data(
        service_id=service_id,
        service_name=service['name'],
        min_quantity=int(service['min']),
        max_quantity=int(service['max']),
        original_rate=float(service['rate']),  # Оригинальная цена за 1000
        marked_up_rate=marked_up_rate  # Цена с наценкой за 1000 из SERVICE_DESCRIPTIONS
    )
    
    await callback.message.edit_text(
        "🔗 <b>Введите ссылку на канал/пост:</b>\n\n"
        "Примеры:\n"
        "• Для канала: https://t.me/channel_name\n"
        "• Для поста: https://t.me/channel_name/123",
        parse_mode="HTML"
    )
    
    await state.set_state(OrderStates.AWAITING_LINK)
    await callback.answer()

# Обработчик ввода ссылки
@bots.message(OrderStates.AWAITING_LINK)
async def process_link(message: types.Message, state: FSMContext):
    link = message.text.strip()
    
    # Простая валидация ссылки
    if not link.startswith(('https://t.me/', 't.me/')):
        await message.answer("❌ Неверный формат ссылки. Используйте ссылку на Telegram в формате https://t.me/...")
        return
    
    await state.update_data(link=link)
    
    data = await state.get_data()
    await message.answer(
        f"🔢 <b>Введите количество:</b>\n\n"
        f"• Минимум: {data['min_quantity']}\n"
        f"• Максимум: {data['max_quantity']}\n"
        f"• Цена за 1000: {data['marked_up_rate']} руб.",
        parse_mode="HTML"
    )
    
    await state.set_state(OrderStates.AWAITING_QUANTITY)

@bots.message(OrderStates.AWAITING_QUANTITY)
async def process_quantity(message: types.Message, state: FSMContext):
    try:
        quantity = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Введите число")
        return
    
    data = await state.get_data()
    
    if quantity < data['min_quantity'] or quantity > data['max_quantity']:
        await message.answer(
            f"❌ Количество должно быть от {data['min_quantity']} до {data['max_quantity']}"
        )
        return
    
    # Рассчитываем стоимость с наценкой
    cost = round(quantity * data['marked_up_rate'] / 1000, 2)
    original_cost = round(quantity * data['original_rate'] / 1000, 2)
    profit = cost - original_cost
    
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Подтвердить", callback_data="confirm_order")
    builder.button(text="❌ Отменить", callback_data="cancel_order")
    builder.adjust(2)
    
    await state.update_data(quantity=quantity, cost=cost, profit=profit)
    
    await message.answer(
        f"📝 <b>Подтвердите заказ:</b>\n\n"
        f"• Услуга: {data['service_name']}\n"
        f"• Ссылка: {data['link']}\n"
        f"• Количество: {quantity}\n"
        f"• Цена за 1000: {data['marked_up_rate']:.2f} руб.\n"
        # f"• Прибыль с продажи: {profit:.2f} руб.\n"
        f"• Стоимость: {cost:.2f} руб.\n\n"
        f"После оплаты заказ начнет выполняться автоматически.",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )

# Обработчик отмены заказа
@bots.callback_query(F.data == "cancel_order", OrderStates.AWAITING_QUANTITY)
async def cancel_order(callback: types.CallbackQuery, state: FSMContext):
    kb = InlineKeyboardBuilder()
    kb.button(text='🔙 Назад', callback_data='bots_menu')
    await callback.message.edit_text("❌ Заказ отменен", kb.as_markup())
    await state.clear()
    await callback.answer()

# Обработчик подтверждения заказа
@bots.callback_query(F.data == "confirm_order")
async def confirm_order(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    
    # Показываем меню выбора способа оплаты
    builder = InlineKeyboardBuilder()
    # builder.button(text="💳 CryptoBot (USDT)", callback_data="pay_cryptobot")
    # builder.button(text="💎 TON", callback_data="bots_pay_ton")
    builder.button(text="💎 Оплатить с баланса", callback_data="bot_pay_from_balance")
    builder.button(text="🔙 Назад", callback_data="back_to_order_confirmation")
    builder.adjust(1)
    
    await callback.message.edit_text(
        f"💳 <b>Выберите способ оплаты:</b>\n\n"
        f"Сумма к оплате: {data['cost']} руб.",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    
    await state.set_state(OrderStates.PAYMENT_METHOD)
    await callback.answer()


@bots.callback_query(F.data == "bot_pay_from_balance", OrderStates.PAYMENT_METHOD)
async def bot_pay_from_balance(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id 
    data = await state.get_data()
    
    # Рассчитываем стоимость с наценкой
    marked_up_cost = data['cost']  # Общая стоимость с наценкой
    original_cost = (data['original_rate'] * data['quantity']) / 1000  # Общая стоимость по базовой цене
    profit = marked_up_cost - original_cost  # Общая прибыль
    
    user_balance = await DB.get_user_rub_balance(user_id)
    
    if user_balance < marked_up_cost:
        btn = InlineKeyboardBuilder()
        btn.button(text='💸 К пополнению', callback_data='select_deposit_menu')
        btn.button(text='🔙 В меню', callback_data='back_menu')
        await callback.message.edit_text(
            f'❌ Недостаточно средств для оплаты услуги ❌\n'
            f'💰 Требуется: {marked_up_cost:.2f} руб.\n'
            f'💳 На балансе: {user_balance:.2f} руб.\n'
            f'Пополните баланс и возвращайтесь снова!', 
            reply_markup=btn.as_markup()
        )
        await callback.answer()
        return
    
    # Списываем деньги (уже с наценкой)
    await DB.add_rub_balance(user_id, -marked_up_cost)
    
    # Создаем заказ
    order_result = await BotsAPI.create_order(
        service_id=data['service_id'],
        link=data['link'],
        quantity=data['quantity']
    )
    
    if not order_result or 'order' not in order_result:
        # Возвращаем деньги при ошибке
        await DB.add_rub_balance(user_id, marked_up_cost)
        await callback.message.edit_text("❌ Ошибка при создании заказа. Попробуйте позже.")
        await state.clear()
        await callback.answer()
        return
    
    order_id = order_result['order']
    await DB.add_order(
        user_id=user_id,
        order_id=order_id,
        service_id=data['service_id'],
        link=data['link'],
        quantity=data['quantity'],
        cost=marked_up_cost,  # Сохраняем общую стоимость с наценкой
        status='pending',
    )
    
    # Получаем название услуги
    service = await BotsAPI.get_service(data['service_id'])
    service_name = service['name'] if service else f"Услуга #{data['service_id']}"
    
    # Отправляем уведомление админам
    admin_message = (
        f"💰 <b>Новый заказ #{order_id}</b>\n"
        f"👤 Пользователь: @{callback.from_user.username or 'нет'} (ID: {user_id})\n"
        f"📌 Услуга: {service_name}\n"
        f"🔗 Ссылка: {data['link']}\n"
        f"🔢 Количество: {data['quantity']}\n"
        f"💵 Цена из API: {original_cost:.2f} руб.\n"
        f"💰 Цена продажи: {marked_up_cost:.2f} руб.\n"
        f"💸 Прибыль: {profit:.2f} руб.\n"
    )
    
    for admin_id in ADMINS_ID:
        try:
            await callback.bot.send_message(
                chat_id=admin_id,
                text=admin_message,
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Не удалось отправить уведомление админу {admin_id}: {e}")
    
    # Отправляем сообщение пользователю
    await callback.message.edit_text(
        f"✅ <b>Заказ #{order_id} успешно создан!</b>\n\n"
        f"• Услуга: {service_name}\n"
        f"• Ссылка: {data['link']}\n"
        f"• Количество: {data['quantity']}\n"
        f"• Стоимость: {marked_up_cost:.2f} руб.\n\n"
        f"Статус заказа можно проверить командой /orders",
        parse_mode="HTML"
    )
    
    await state.clear()

# # Обработчик возврата к подтверждению заказа
# @bots.callback_query(F.data == "back_to_order_confirmation", OrderStates.PAYMENT_METHOD)
# async def back_to_order_confirmation(callback: types.CallbackQuery, state: FSMContext):
#     data = await state.get_data()
    
#     builder = InlineKeyboardBuilder()
#     builder.button(text="✅ Подтвердить", callback_data="confirm_order")
#     builder.button(text="❌ Отменить", callback_data="cancel_order")
#     builder.adjust(2)
    
#     await callback.message.edit_text(
#         f"📝 <b>Подтвердите заказ:</b>\n\n"
#         f"• Услуга: {data['service_name']}\n"
#         f"• Ссылка: {data['link']}\n"
#         f"• Количество: {data['quantity']}\n"
#         f"• Стоимость: {data['cost']} руб.\n\n"
#         f"После оплаты заказ начнет выполняться автоматически.",
#         reply_markup=builder.as_markup(),
#         parse_mode="HTML"
#     )
    
#     await state.set_state(OrderStates.AWAITING_QUANTITY)
#     await callback.answer()

# Обработчик выбора оплаты через CryptoBot
@bots.callback_query(F.data == "pay_cryptobot", OrderStates.PAYMENT_METHOD)
async def pay_with_cryptobot(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user_id = callback.from_user.id
    
    try:
        async with AioCryptoPay(token=CRYPTOBOT_TOKEN) as crypto:

            # Создаем счет в CryptoPay
            invoice = await crypto.create_invoice(
                asset='USDT',
                amount=data['cost'],
                description=f"Оплата заказа на {data['quantity']} {data['service_name']}",
                expires_in=1800  # 30 минут
            )
        
        # Сохраняем информацию о платеже
        await state.update_data(
            invoice_id=invoice.invoice_id,
            payment_method='cryptobot'
        )
        
        builder = InlineKeyboardBuilder()
        builder.button(text="💳 Оплатить", url=invoice.bot_invoice_url)
        builder.button(text="✅ Проверить оплату", callback_data="check_payment")
        builder.button(text="❌ Отменить", callback_data="cancel_payment")
        builder.adjust(1)
        
        await callback.message.edit_text(
            f"💳 <b>Оплата через CryptoBot</b>\n\n"
            f"Сумма к оплате: {data['cost']} USDT\n"
            f"Счет действителен в течение 30 минут\n\n"
            f"После оплаты нажмите кнопку 'Проверить оплату'",
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
        
        await state.set_state(OrderStates.AWAITING_PAYMENT)
    except Exception as e:
        logger.error(f"Error creating CryptoPay invoice: {e}")
        await callback.message.edit_text(
            "❌ Произошла ошибка при создании счета. Пожалуйста, попробуйте позже."
        )
        await state.clear()
    
    await callback.answer()

@bots.callback_query(F.data == "bots_pay_ton", OrderStates.PAYMENT_METHOD)
async def pay_with_ton(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user_id = callback.from_user.id
    
    try:
        # Получаем курс TON к рублю
        ton_rate = await get_ton_rate()
        
        # Конвертируем рубли в TON
        ton_amount = round(data['cost'] / ton_rate, 4)
        amount_nano = int(ton_amount * 1_000_000_000)  # Конвертация в нанотоны
        
        # Генерируем уникальный комментарий
        unique_code = generate_unique_code()
        
        builder = InlineKeyboardBuilder()
        
        # Добавляем кнопки для разных кошельков
        payment_links = [
            ("Ton Wallet", f"ton://transfer/{TON_WALLET}"),
            ("Tonkeeper", f"https://app.tonkeeper.com/transfer/{TON_WALLET}"),
            ("Tonhub", f"https://tonhub.com/transfer/{TON_WALLET}")
        ]
        
        for name, base_url in payment_links:
            builder.button(
                text=name, 
                url=f"{base_url}?amount={amount_nano}&text={unique_code}"
            )
            
        builder.button(
            text="✅ Проверить оплату", 
            callback_data=f"check_ton_payment:{unique_code}:{amount_nano}:{data['cost']}"
        )
        builder.button(
            text="❌ Отменить", 
            callback_data="cancel_payment"
        )
        builder.adjust(1)
        
        await callback.message.edit_text(
            f"💎 <b>Оплата через TON</b>\n\n"
            f"▪ Сумма: <b>{ton_amount:.4f} TON</b> (~{data['cost']:.2f}₽)\n"
            f"▪ Адрес: <code>{TON_WALLET}</code>\n"
            f"▪ Комментарий: <code>{unique_code}</code>\n\n"
            "После оплаты нажмите 'Проверить оплату'",
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
        
        await state.update_data(
            amount_nano=str(amount_nano),
            unique_code=unique_code,
            payment_method='ton'
        )
        
        await state.set_state(OrderStates.AWAITING_PAYMENT)
    except Exception as e:
        logger.error(f"Error creating TON payment: {e}")
        await callback.message.edit_text(
            "❌ Произошла ошибка при создании платежа. Пожалуйста, попробуйте позже."
        )
        await state.clear()
    
    await callback.answer()
    
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

# Обновленный обработчик проверки оплаты TON
@bots.callback_query(F.data.startswith("check_ton_payment:"), OrderStates.AWAITING_PAYMENT)
async def check_ton_payment_handler(callback: types.CallbackQuery, state: FSMContext):
    parts = callback.data.split(":")
    unique_code = parts[1]
    amount_nano = parts[2]
    rub_amount = float(parts[3])
    
    data = await state.get_data()
    
    # Проверяем, что это тот же заказ
    if data.get('unique_code') != unique_code or str(data.get('amount_nano')) != amount_nano:
        await callback.answer("❌ Неверные данные платежа", show_alert=True)
        return
    
    # Проверяем платеж с подробным логированием
    logger.info(f"Проверка платежа TON для заказа. Ожидаем: {amount_nano} nanoTON, комментарий: '{unique_code}'")
    
    try:
        expected = int(amount_nano)
        tolerance = max(int(expected * 0.01), 1000000)  # Допуск 1% или минимум 0.001 TON
        
        params = {
            'address': str(TON_WALLET),
            'limit': 20,
            'api_key': str(TON_API_TOKEN),
            'archival': 'true'
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                response = await session.get(
                    f"{TON_API_BASE}getTransactions",
                    params=params,
                    timeout=20
                )
                
                if response.status != 200:
                    logger.error(f"TON API error: HTTP {response.status}")
                    await callback.answer("Ошибка при проверке платежа", show_alert=True)
                    return
                
                data = await response.json()
                
                if not data.get('ok', False):
                    error_msg = data.get('error', 'Неизвестная ошибка API')
                    logger.error(f"TON API error: {error_msg}")
                    await callback.answer("Ошибка при проверке платежа", show_alert=True)
                    return
                
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
                    
                    # Проверка совпадения
                    amount_match = abs(tx_value - expected) <= tolerance
                    comment_match = tx_comment == unique_code.strip()
                    
                    if amount_match and comment_match:
                        logger.info(f"Найден подходящий платеж: {tx_value} nanoTON, комментарий: '{tx_comment}'")
                        # Если платеж подтвержден, создаем заказ
                        await create_order_after_payment(callback, state, rub_amount)
                        return
                
                logger.info("Подходящих платежей не найдено")
                await callback.answer(
                    "Платеж еще не получен. Пожалуйста, подождите и попробуйте снова через 30 секунд.",
                    show_alert=True
                )
                
            except asyncio.TimeoutError:
                logger.error("Timeout при запросе к TON API")
                await callback.answer("Таймаут при проверке платежа", show_alert=True)
            except aiohttp.ClientError as e:
                logger.error(f"Ошибка сети: {str(e)}")
                await callback.answer("Ошибка сети при проверке платежа", show_alert=True)
    
    except Exception as e:
        logger.error(f"Критическая ошибка при проверке платежа: {type(e).__name__}: {str(e)}")
        await callback.answer("Произошла ошибка при проверке платежа", show_alert=True)

# Обработчик проверки оплаты через CryptoBot
@bots.callback_query(F.data == "check_payment", OrderStates.AWAITING_PAYMENT)
async def check_cryptobot_payment(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    
    if 'invoice_id' not in data:
        await callback.answer("❌ Не найден счет для проверки", show_alert=True)
        return
    
    try:
        async with AioCryptoPay(token=CRYPTOBOT_TOKEN) as crypto:
            invoice = await crypto.get_invoices(invoice_ids=data['invoice_id'])
            
        if invoice.status == 'paid':
            # Если оплачено, создаем заказ
            await create_order_after_payment(callback, state, data['cost'])
        else:
            await callback.answer(
                "Платеж еще не получен. Пожалуйста, подождите и попробуйте снова через 10 секунд.",
                show_alert=True
            )
    except Exception as e:
        logger.error(f"Error checking CryptoPay invoice: {e}")
        await callback.answer(
            "Произошла ошибка при проверке платежа. Пожалуйста, попробуйте позже.",
            show_alert=True
        )
    
    await callback.answer()

# Общая функция для создания заказа после успешной оплаты
async def create_order_after_payment(callback: types.CallbackQuery, state: FSMContext, amount: float):
    data = await state.get_data()
    
    # Создаем заказ в API
    order_result = await BotsAPI.create_order(
        service_id=data['service_id'],
        link=data['link'],
        quantity=data['quantity']
    )
    
    if not order_result or 'order' not in order_result:
        await callback.message.edit_text("❌ Ошибка при создании заказа. Попробуйте позже.")
        await state.clear()
        return
    
    # Сохраняем заказ в БД
    order_id = order_result['order']
    await DB.add_order(
        user_id=callback.from_user.id,
        order_id=order_id,
        service_id=data['service_id'],
        link=data['link'],
        quantity=data['quantity'],
        cost=amount,
        status='pending',  # Начальный статус
    )
    
    # Получаем информацию об услуге для красивого отображения
    service = await BotsAPI.get_service(data['service_id'])
    service_name = service['name'] if service else f"Услуга #{data['service_id']}"
    
    await callback.message.edit_text(
        f"✅ <b>Заказ #{order_id} успешно создан!</b>\n\n"
        f"• Услуга: {service_name}\n"
        f"• Ссылка: {data['link']}\n"
        f"• Количество: {data['quantity']}\n"
        f"• Стоимость: {amount} руб.\n\n"
        f"Статус заказа можно проверить командой /orders",
        parse_mode="HTML"
    )
    
    await state.clear()

# Обработчик отмены платежа
@bots.callback_query(F.data == "cancel_payment", OrderStates.AWAITING_PAYMENT)
async def cancel_payment(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("❌ Оплата отменена")
    await state.clear()
    await callback.answer()

# Обработчик команды /orders
@bots.message(Command("orders"))
async def show_orders(message: types.Message, state: FSMContext):
    user_orders = await DB.get_user_orders(message.from_user.id)
    
    if not user_orders:
        await message.answer("📭 У вас пока нет заказов")
        return
    
    builder = InlineKeyboardBuilder()
    for order in user_orders[:10]:  # Ограничим показ 10 последними заказами
        builder.button(
            text=f"Заказ #{order['order_id']} - {order['status']}",
            callback_data=f"view_order_{order['order_id']}"
        )
    
    builder.adjust(1)
    await message.answer(
        "📋 <b>Ваши заказы:</b>",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await state.set_state(OrderStates.VIEW_ORDERS)

# Обработчик просмотра заказа
@bots.callback_query(F.data.startswith("view_order_"), OrderStates.VIEW_ORDERS)
async def view_order(callback: types.CallbackQuery):
    order_id = int(callback.data.replace("view_order_", ""))
    
    # Получаем заказ из БД
    order = await DB.get_order(order_id)
    if not order:
        await callback.answer("❌ Заказ не найден")
        return
    
    # Получаем статус из API
    status_data = await BotsAPI.get_order_status(order_id)
    
    if status_data and isinstance(status_data, dict) and 'status' in status_data:
        current_status = status_data['status']
        remains = status_data.get('remains', 'N/A')
        charge = status_data.get('charge', 'N/A')
        
        # Обновляем статус в БД
        await DB.update_order_status(order_id, current_status)
    else:
        current_status = order['status']
        remains = 'N/A'
        charge = 'N/A'
    
    service = await BotsAPI.get_service(order['service_id'])
    service_name = service['name'] if service else f"Услуга #{order['service_id']}"
    
    text = (
        f"📄 <b>Заказ #{order_id}</b>\n\n"
        f"• Услуга: {service_name}\n"
        f"• Ссылка: {order['link']}\n"
        f"• Количество: {order['quantity']}\n"
        f"• Стоимость: {order['cost']} руб.\n"
        # f"• Способ оплаты: {order.get('payment_method', 'не указан')}\n"
        f"• Статус: {current_status.upper()}\n"
        f"Дата: {order['created_at']}"
    )
    
    builder = InlineKeyboardBuilder()
    builder.button(text="🔄 Проверить статус", callback_data=f"refresh_order_{order_id}")
    builder.button(text="🔙 Назад", callback_data="back_to_orders")
    builder.adjust(1)
    
    await callback.message.edit_text(
        text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await callback.answer()

# Обработчик обновления статуса заказа
@bots.callback_query(F.data.startswith("refresh_order_"))
async def refresh_order_status(callback: types.CallbackQuery):
    order_id = int(callback.data.replace("refresh_order_", ""))
    
    # Получаем обновленный статус
    status_data = await BotsAPI.get_order_status(order_id)
    
    if not status_data or 'status' not in status_data:
        await callback.answer("⚠️ Не удалось проверить статус заказа", show_alert=True)
        return
    
    # Обновляем статус в БД
    await DB.update_order_status(order_id, status_data['status'])
    
    # Получаем данные заказа
    order = await DB.get_order(order_id)
    if not order:
        await callback.answer("❌ Заказ не найден")
        return
    
    service = await BotsAPI.get_service(order['service_id'])
    service_name = service['name'] if service else f"Услуга #{order['service_id']}"
    
    text = (
        f"📄 <b>Заказ #{order_id}</b> (обновлено)\n\n"
        f"• Услуга: {service_name}\n"
        f"• Ссылка: {order['link']}\n"
        f"• Количество: {order['quantity']}\n"
        f"• Стоимость: {order['cost']} руб.\n"
        # f"• Способ оплаты: {order.get('payment_method', 'не указан')}\n"
        f"• Статус: {status_data['status'].upper()}\n"
        f"Дата: {order['created_at']}"
    )
    
    builder = InlineKeyboardBuilder()
    builder.button(text="🔄 Проверить статус", callback_data=f"refresh_order_{order_id}")
    builder.button(text="🔙 Назад", callback_data="back_to_orders")
    builder.adjust(1)
    
    await callback.message.edit_text(
        text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await callback.answer("✅ Статус обновлен")

async def render_orders_list(user_id: int, state: FSMContext) -> types.Message | None:
    user_orders = await DB.get_user_orders(user_id)

    if not user_orders:
        return None

    builder = InlineKeyboardBuilder()
    for order in user_orders[:10]:
        builder.button(
            text=f"Заказ #{order['order_id']} - {order['status']}",
            callback_data=f"view_order_{order['order_id']}"
        )
    builder.adjust(1)
    return builder

@bots.callback_query(F.data == "back_to_orders")
async def back_to_orders_list(callback: types.CallbackQuery, state: FSMContext):
    builder = await render_orders_list(callback.from_user.id, state)
    if not builder:
        await callback.message.edit_text("📭 У вас пока нет заказов")
    else:
        await callback.message.edit_text(
            "📋 <b>Ваши заказы:</b>",
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
    await state.set_state(OrderStates.VIEW_ORDERS)
    await callback.answer()
 
@bots.message(Command('OrderStatus'))
async def _(message: types.Message):
    if message.from_user.id in ADMINS_ID:
        args = message.text.split()
        if len(args) > 1:
            argument = args[1] 
            status_data = await BotsAPI.get_order_status(argument)
            await message.answer(f'Status: <blockquote>{status_data}</blockquote>')
        else:
            await message.answer("Вы не указали аргумент.")
