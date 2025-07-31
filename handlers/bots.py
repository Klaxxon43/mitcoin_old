from utils.Imports import *
from API.TonAPI import *

bots = Router()

PRICE_MARKUP = 3  # 30% наценка
CONFIG_FILE = Path("data/bots_config.json")

# Генерация уникального кода для TON транзакций
def generate_unique_code(length=8):
    """Генерация уникального кода для транзакции"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

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
    "🤬": 32053,
    # "Кастомные": 32860,
    "👾 😘 💘 🌚 🕊 🐳": 735,
    "💔": 32082,
    "🚀": 32083,
    "😈": 32084,
    # "👍 (Авто)": 32110,
    # "👎 (Авто)": 32111,
    # "👍 ❤️ 🔥 🎉 😁 (Авто)": 32114,
    # "👎 😱 💩 😢 🤮 (Авто)": 32115,
    "🐳 🍾 👻 🎃": 27957,
    "👎 😁 😢 💩 🤮 🤔 🤯 🤬": 27972,
    "😨 🤯 😱 🤮": 27955,
    "🕊 🦄 🍓 🎄": 27958,
    "❤️ 💯 🏆 🎉": 27966,
    "👎 💩 😱 😢": 27956,
    "💯 🤔": 720,
    "💋 💘": 24952,
    "🤣 👏": 733,
    "😱 😢": 721,
    "👍 🙏": 27965,
    "🤬 😨": 31166,
    "🤑": 24947,
    "😍": 24948,
    "🤨": 17067,
    "🥱": 736,
    "😴": 27499,
    "👨‍💻": 24953,
    "🙈": 24951,
    "😇": 24949,
    "🤷‍": 24950,
    "🙊": 27932,
    "🤣": 31911,
    "❤️": 31909,
    "👎": 32024,
    "🤝": 32025,
    "⚡️": 32026,
    "🥴": 32027,
    "🖕": 32028,
    "😐": 32030,
    "👀": 32031,
    "👏": 32032,
    "🍌": 32033,
    "🏆": 32034,
    "🦄": 32035,
    "👻": 32036,
    "😭": 32037,
    "🎄": 32039,
    "🎅": 32040,
    "☃️": 32041,
    "💩": 32042,
    "🎉": 32043,
    "🤮": 32044,
    "😁": 32045,
    "🗿": 32046,
    "🍾": 32047,
    "😢": 32048,
    "💊": 32049,
    "😱": 32050,
    "🙏": 32051,
    "👌": 32052,
    "🐳": 32054,
    "💯": 32055,
    "🕊": 32056,
    "🤡": 32057,
    "🥰": 32058,
    "🤔": 32059,
    "🤯": 32060,
    "🌚": 32061,
    "🌭": 32062,
    "🍓": 32063,
    "💋": 32064,
    "🤓": 32065,
    "🎃": 32067,
    "😨": 32068,
    "✍": 32069,
    "🤗": 32070,
    "💅": 32071,
    "🤪": 32072,
    "🆒": 32073,
    "💘": 32074,
    "🙉": 32075,
    "😘": 32076,
    "😎": 32077,
    "👾": 32078,
    "🤷": 32079,
    "😡": 32080
}

SERVICE_DESCRIPTIONS = {
    31388: """
<b>📌 Услуга #<code>31388</code></b>
<b>🏷 Название:</b> <code>TG Подписчики [Канал/Группа | Дешевые]</code>

<b>💵 Стоимость:</b> <code> 60 руб. за 1000 </code>
<b>📊 Лимиты:</b> <code> 10 - 50 000 </code>
<b>🚀 Скорость:</b> <code> Мгновенно </code>
<b>🛡 Гарантия:</b> <code> Нет </code>

<b>📝 Описание:</b>
Старт: <code> 0-1 час </code>
Скорость: <code> 3000-4000 в день </code>
Списания: <code> Возможны </code>

<b>⚠️ Важно:</b>
- Мы не гарантируем возврат средств, если количество участников упадет ниже стартового
- Нет гарантии выполнения на пустые каналы (риск бана)
""",

    32281: """
<b>📌 Услуга #<code>32281</code></b>
<b>🏷 Название:</b> <code>TG Подписчики [Канал/Группа | Премиум]</code>

<b>💵 Стоимость:</b> <code> 150 руб. за 1000 </code>
<b>📊 Лимиты:</b> <code> 1 - 50 000 </code>
<b>🚀 Скорость:</b> <code> Мгновенно </code>
<b>🛡 Гарантия:</b> <code> 60Д </code>

<b>📝 Описание:</b>
Старт: <code> 0-1 час </code>
Скорость: <code> до 50 000 в день </code>
Качество: <code> Высокое </code>
ГЕО: <code> Микс </code>
Списания: <code> Нет </code>

<b>⚠️ Важно:</b>
- Заказы на 18+ контент будут отменены
- Делайте скриншоты количества перед заказом
- Подписчики могут отображаться с задержкой до 3 часов
""",

    31621: """
<b>📌 Услуга #<code>31621</code></b>
<b>🏷 Название:</b> <code>TG Просмотры [Пост]</code>

<b>💵 Стоимость:</b> <code> 5 руб. за 1000 </code> 
<b>📊 Лимиты:</b> <code> 10 - 10 000 </code>
<b>🚀 Скорость:</b> <code> Мгновенно </code>
<b>🛡 Гарантия:</b> <code> Нет </code>

<b>📝 Описание:</b>
Старт: <code> 0-1 час </code>
Скорость: <code> до 10 000 в день </code>
ГЕО: <code> Микс </code> 
Списания: <code> Нет </code>
""",

    787: """
<b>📌 Услуга #<code>787 </code></b>
<b>🏷 Название:</b> <code>TG Опросы [Канал]</code>

<b>💵 Стоимость:</b> <code> 50 руб. за 1000 </code>
<b>📊 Лимиты:</b> <code> 1 - 10 000 </code>
<b>🚀 Скорость:</b> <code> Мгновенно </code>
<b>🛡 Гарантия:</b> <code> Нет </code>

<b>📝 Описание:</b>
Старт: <code> 0-1 час </code>
Скорость: <code> до 100 000 в день </code>
ГЕО: <code> Микс </code>
Списания: <code> Нет </code>

<b>ℹ️ Примечание:</b>
Работает только для каналов. Для чатов - сделайте репост опроса в канал.
""",

    26716: """
<b>📌 Услуга #<code>26716 </code></b>
<b>🏷 Название:</b> <code>TG Боты [Активация /Start]</code>

<b>💵 Стоимость:</b> <code> 100 руб. за 1000 </code>
<b>📊 Лимиты:</b> <code> 100 - 1 000 000 </code>
<b>🚀 Скорость:</b> <code> Мгновенно </code>
<b>🛡 Гарантия:</b> <code> Нет </code>

<b>📝 Описание:</b>
Старт: <code> 0-1 час </code>
Скорость: <code> до 10 000 в день </code>
Списания: <code> Возможны </code>

<b>⚙️ Особенности:</b>
- Активирует команду /start у пользователей
- Подходит для быстрого старта бота
""",

    31910: """
<b>📌 Услуга #<code>31910 </code></b>
<b>🏷 Название:</b> <code>TG Реакции [🔥]</code>

<b>💵 Стоимость:</b> <code> 10 руб. за 1000 </code>
<b>📊 Лимиты:</b> <code> 1 - 100 000 </code>
<b>🚀 Скорость:</b> <code> Мгновенно </code>
<b>🛡 Гарантия:</b> <code> Нет </code>

<b>📝 Описание:</b>
Старт: <code> 0-2 часа </code>
Скорость: <code> до 10 000 в день </code>
Списания: <code> Возможны </code>

<b>⚠️ Требования:</b>
- Канал должен быть открытым
- Реакции должны быть доступны
- Средства не возвращаются при ошибке в ссылке
"""
}

# Для реакций используем тот же шаблон, подставляя только эмодзи и ID
for reaction_id in REACTION_SERVICES.values():
    if reaction_id not in SERVICE_DESCRIPTIONS:
        emoji = list(REACTION_SERVICES.keys())[list(REACTION_SERVICES.values()).index(reaction_id)]
        SERVICE_DESCRIPTIONS[reaction_id] = f"""
<b>📌 Услуга #<code>{reaction_id}</code></b>
<b>🏷 Название:</b> <code>TG Реакции [{emoji}]</code>

<b>💵 Стоимость:</b> <code>1.79 руб. за 1000</code>
<b>📊 Лимиты:</b> <code>1 - 100 000</code>
<b>🚀 Скорость:</b> <code>Мгновенно</code>
<b>🛡 Гарантия:</b> <code>Нет</code>

<b>📝 Описание:</b>
Старт: <code>0-2 часа</code>
Скорость: <code>до 10 000 в день</code>
Списания: <code>Возможны</code>

<b>⚠️ Требования:</b>
- Канал должен быть открытым
- Реакции должны быть доступны
- Средства не возвращаются при ошибке в ссылке
"""

# Глобальный кэш для сервисов
SERVICES_CACHE = {
    'premium': None,
    'reactions': None,
    'last_updated': None
}

async def load_config():
    """Загрузка конфигурации из файла"""
    if not CONFIG_FILE.exists():
        os.makedirs(CONFIG_FILE.parent, exist_ok=True)
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump({"orders": [], "stats": {"total_profit": 0, "total_orders": 0}}, f, ensure_ascii=False, indent=4)
        return {"orders": [], "stats": {"total_profit": 0, "total_orders": 0}}
    
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

async def save_config(config):
    """Сохранение конфигурации в файл"""
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=4)

async def update_stats(order_cost: float, profit: float):
    """Обновление статистики продаж"""
    config = await load_config()
    config["stats"]["total_profit"] += profit
    config["stats"]["total_orders"] += 1
    await save_config(config)

async def get_sales_stats():
    """Получение статистики продаж"""
    config = await load_config()
    return config["stats"]

async def add_order_to_config(order_data: dict):
    """Добавление заказа в конфиг"""
    config = await load_config()
    config["orders"].append(order_data)
    await save_config(config)

async def get_orders_from_config(limit: int = None, offset: int = 0):
    """Получение заказов из конфига"""
    config = await load_config()
    orders = config["orders"]
    if limit:
        return orders[offset:offset+limit]
    return orders

async def get_service_with_retry(service_id, max_retries=3, delay=1):
    """Получение информации о сервисе с повторными попытками"""
    for attempt in range(max_retries):
        try:
            service = await BotsAPI.get_service(service_id)
            if service:
                return service
            await asyncio.sleep(delay * (attempt + 1))  # Увеличиваем задержку с каждой попыткой
        except ClientError as e:
            logger.error(f"Attempt {attempt + 1} failed for service {service_id}: {str(e)}")
            await asyncio.sleep(delay * (attempt + 1))
    return None

async def update_services_cache():
    """Обновляет кэш сервисов с ограничением скорости"""
    global SERVICES_CACHE

    premium_services = {}
    reaction_services = {}
    
    # Ограничиваем количество одновременных запросов
    semaphore = asyncio.Semaphore(3)  # Не более 3 одновременных запросов
    delay_between_requests = 0.5  # Задержка между запросами в секундах

    async def get_and_store(service_id):
        async with semaphore:
            try:
                await asyncio.sleep(delay_between_requests)
                service = await get_service_with_retry(service_id)
                return (service_id, service)
            except Exception as e:
                logger.error(f"Error getting service {service_id}: {e}")
                return (service_id, None)

    # Собираем все ID
    all_ids = list(PREMIUM_SERVICES.values()) + list(REACTION_SERVICES.values())
    
    # Параллельно запрашиваем с ограничениями
    results = await asyncio.gather(*(get_and_store(sid) for sid in all_ids))

    # Обновляем кэш
    for service_id, service in results:
        if service:
            if service_id in PREMIUM_SERVICES.values():
                premium_services[service_id] = service
            else:
                reaction_services[service_id] = service

    SERVICES_CACHE = {
        'premium': premium_services,
        'reactions': reaction_services,
        'last_updated': time.time()
    }


@bots.callback_query(F.data == "bots_menu")
async def show_bots_main_menu(callback: types.CallbackQuery, bot: Bot):
    user_id = callback.from_user.id

    from handlers.client.client import check_subs_op
    if not await check_subs_op(user_id, bot):
        return
    
    if await DB.get_break_status() and user_id not in ADMINS_ID:
        await callback.message.answer('🛠Идёт технический перерыв🛠\nПопробуйте снова позже')
        return
    
    # Загружаем конфиг при первом входе
    await load_config()

    builder = InlineKeyboardBuilder()
    builder.button(text="🛒 Накрутить", callback_data="bots")
    builder.button(text="📋 Мои заказы", callback_data="my_orders")
    
    if user_id in ADMINS_ID:
        builder.button(text="💰 ПРОДАЖИ", callback_data="sales_stats")
    
    builder.button(text='🔙 Назад', callback_data='pr_menu')
    builder.adjust(2, 1)
    
    await callback.message.edit_text(
        "🤖 <b>Меню накрутки</b>\n\n"
        "Выберите действие:",
        reply_markup=builder.as_markup()
    )

@bots.callback_query(F.data == "bots")
async def show_bots_menu(callback: types.CallbackQuery, bot: Bot):
    user_id = callback.from_user.id

    from handlers.client.client import check_subs_op
    if not await check_subs_op(user_id, bot):
        return
    
    if await DB.get_break_status() and user_id not in ADMINS_ID:
        await callback.message.answer('🛠Идёт технический перерыв🛠\nПопробуйте снова позже')
        return
    
    builder = InlineKeyboardBuilder()
    
    if SERVICES_CACHE['premium']:
        for service_name, service_id in PREMIUM_SERVICES.items():
            if service_id in SERVICES_CACHE['premium']:
                builder.button(text=service_name, callback_data=f"bots_srv_{service_id}")
    else:
        for service_name in PREMIUM_SERVICES:
            builder.button(text=service_name, callback_data=f"bots_srv_{PREMIUM_SERVICES[service_name]}")
    
    builder.button(text="❤️ Реакции", callback_data="bots_reactions")
    builder.button(text='🔙 Назад', callback_data='bots_menu')
    builder.adjust(1)
    
    await callback.message.edit_text(
        "🛒 <b>Выберите категорию услуг:</b>",
        reply_markup=builder.as_markup()
    )
    
    need_update = (
        SERVICES_CACHE['last_updated'] is None or 
        (time.time() - SERVICES_CACHE['last_updated']) > 300
    )
    
    if need_update:
        asyncio.create_task(update_services_cache())

@bots.callback_query(F.data == "bots_reactions")
async def show_reactions_menu(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    
    if SERVICES_CACHE['reactions']:
        for emoji_text, service_id in REACTION_SERVICES.items():
            if service_id in SERVICES_CACHE['reactions']:
                builder.button(text=emoji_text, callback_data=f"bots_srv_{service_id}")
    else:
        for emoji_text in REACTION_SERVICES:
            builder.button(text=emoji_text, callback_data=f"bots_srv_{REACTION_SERVICES[emoji_text]}")
    
    builder.button(text="🔙 Назад", callback_data="bots_menu")
    builder.adjust(2)
    
    await callback.message.edit_text(
        "🎭 <b>Выберите тип реакций:</b>",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await callback.answer()

class OrderStates(StatesGroup):
    AWAITING_LINK = State()
    AWAITING_QUANTITY = State()
    VIEW_ORDERS = State()
    PAYMENT_METHOD = State()
    AWAITING_PAYMENT = State()

@bots.callback_query(F.data.startswith("bots_srv_"))
async def show_service_details(callback: types.CallbackQuery):
    service_id = int(callback.data.replace("bots_srv_", ""))
    
    # Проверяем, есть ли услуга в наших локальных данных
    if service_id not in SERVICE_DESCRIPTIONS:
        await callback.answer("⚠️ Услуга временно недоступна")
        return
    
    service_description = SERVICE_DESCRIPTIONS[service_id]
    
    builder = InlineKeyboardBuilder()
    builder.button(text="🛒 Купить", callback_data=f"buy_{service_id}")
    
    if service_id in REACTION_SERVICES.values():
        builder.button(text="🔙 Назад", callback_data="bots_reactions")
    else:
        builder.button(text="🔙 Назад", callback_data="bots")
    
    builder.adjust(1)
    
    await callback.message.edit_text(
        service_description,
        reply_markup=builder.as_markup()
    )
    await callback.answer()

@bots.callback_query(F.data.startswith("buy_"))
async def start_order_process(callback: types.CallbackQuery, state: FSMContext):
    service_id = int(callback.data.replace("buy_", ""))
    
    try:
        service = await BotsAPI.get_service(service_id)
        if not service:
            await callback.answer("⚠️ Услуга временно недоступна")
            return
        
        # Для сервиса просмотров используем фиксированную цену
        if service_id == 31621:
            marked_up_rate = 5.0  # 5 руб. за 1000 просмотров
            original_rate = marked_up_rate / PRICE_MARKUP
        else:
            # Для других сервисов используем цену из API с наценкой
            original_rate = float(service['rate'])
            marked_up_rate = original_rate * PRICE_MARKUP
        
        await state.update_data(
            service_id=service_id,
            service_name=service['name'],
            min_quantity=int(service['min']),
            max_quantity=int(service['max']),
            original_rate=original_rate,
            marked_up_rate=marked_up_rate
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
        
    except Exception as e:
        logger.error(f"Ошибка при проверке услуги: {e}")
        await callback.answer("⚠️ Ошибка при проверке услуги. Попробуйте позже.")
        
@bots.message(OrderStates.AWAITING_LINK)
async def process_link(message: types.Message, state: FSMContext):
    link = message.text.strip()
    
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
    
    # Для сервиса просмотров (ID 31621) используем фиксированную цену 5 руб. за 1000
    if data['service_id'] == 31621:
        marked_up_rate = 5.0  # Фиксированная цена за 1000 просмотров
        original_rate = marked_up_rate / PRICE_MARKUP  # Рассчитываем оригинальную цену
    else:
        # Для других сервисов используем стандартную логику
        marked_up_rate = data['marked_up_rate']
        original_rate = data['original_rate']
    
    try:
        balance_data = await BotsAPI.get_balance()
        api_balance = float(balance_data['balance']) if balance_data and 'balance' in balance_data else 0
    except Exception as e:
        logger.error(f"Ошибка при получении баланса API: {e}")
        api_balance = 0
    
    user_balance = await DB.get_user_rub_balance(message.from_user.id)
    
    max_by_api = int(api_balance / (original_rate / 1000)) if original_rate > 0 else 0
    max_by_api = min(max_by_api, data['max_quantity'])
    
    max_by_user = int(user_balance / (marked_up_rate / 1000)) if marked_up_rate > 0 else 0
    max_by_user = min(max_by_user, data['max_quantity'])
    
    max_available = min(max_by_api, max_by_user)
    
    if quantity < data['min_quantity'] or quantity > data['max_quantity']:
        error_msg = (
            f"❌ Количество должно быть от {data['min_quantity']} до {data['max_quantity']}\n\n"
            f"💡 На текущий момент вы можете заказать до {max_available} единиц\n"
        )
        await message.answer(error_msg)
        return
    
    if quantity > max_available:
        error_msg = (
            f"❌ Недостаточно средств для заказа {quantity} единиц данной услуги\n\n"
            f"💡 На текущий момент вы можете заказать до {max_available} единиц\n"
        )
        await message.answer(error_msg)
        return
    
    cost = round(quantity * marked_up_rate / 1000, 2)
    original_cost = round(quantity * original_rate / 1000, 2)
    profit = cost - original_cost
    
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Подтвердить", callback_data="confirm_order")
    builder.button(text="❌ Отменить", callback_data="cancel_order")
    builder.adjust(2)
    
    await state.update_data(
        quantity=quantity, 
        cost=cost, 
        profit=profit,
        marked_up_rate=marked_up_rate,
        original_rate=original_rate
    )
    
    confirmation_msg = (
        f"📝 <b>Подтвердите заказ:</b>\n\n"
        f"• Услуга: {data['service_name']}\n"
        f"• Ссылка: {data['link']}\n"
        f"• Количество: {quantity}\n"
        f"• Цена за 1000: {marked_up_rate:.2f} руб.\n"
        f"• Стоимость: {cost:.2f} руб.\n\n"
        f"💡 Доступно для заказа: до {max_available} единиц\n\n"
        f"После оплаты заказ начнет выполняться автоматически."
    )
    
    await message.answer(
        confirmation_msg,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )


@bots.callback_query(F.data == "cancel_order", OrderStates.AWAITING_QUANTITY)
async def cancel_order(callback: types.CallbackQuery, state: FSMContext):
    kb = InlineKeyboardBuilder()
    kb.button(text='🔙 Назад', callback_data='bots_menu')
    await callback.message.edit_text("❌ Заказ отменен", kb.as_markup())
    await state.clear()
    await callback.answer()

@bots.callback_query(F.data == "confirm_order")
async def confirm_order(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    
    builder = InlineKeyboardBuilder()
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
async def bot_pay_from_balance(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    MAX_RETRIES = 3
    RETRY_DELAY = 2  # секунды между попытками
    
    user_id = callback.from_user.id
    data = await state.get_data()
    
    logger.info(f"Начало обработки заказа для пользователя {user_id}. Данные: {data}")
    
    # Для просмотров используем фиксированную цену
    if data['service_id'] == 31621:
        marked_up_rate = 5.0  # 5 руб. за 1000 просмотров
        original_rate = marked_up_rate / PRICE_MARKUP
        marked_up_cost = round(data['quantity'] * marked_up_rate / 1000, 2)
        original_cost = round(data['quantity'] * original_rate / 1000, 2)
        logger.info(f"Заказ просмотров. Количество: {data['quantity']}, Стоимость: {marked_up_cost} руб.")
    else:
        marked_up_cost = data['cost']
        original_cost = (data['original_rate'] * data['quantity']) / 1000
    
    profit = marked_up_cost - original_cost
    
    async def refund_user():
        """Возврат средств пользователю"""
        await DB.add_rub_balance(user_id, marked_up_cost)
        logger.info(f"Возвращено {marked_up_cost:.2f} руб. на баланс пользователя")

    # 1. Проверка баланса пользователя
    user_balance = await DB.get_user_rub_balance(user_id)
    logger.info(f"Баланс пользователя: {user_balance} руб., требуется: {marked_up_cost} руб.")
    
    if user_balance < marked_up_cost:
        logger.warning("Недостаточно средств у пользователя")
        btn = InlineKeyboardBuilder()
        btn.button(text='💸 К пополнению', callback_data='select_deposit_menu')
        btn.button(text='🔙 В меню', callback_data='back_menu')
        btn.adjust(2)
        
        await callback.message.edit_text(
            f'❌ Недостаточно средств для оплаты услуги ❌\n'
            f'💰 Требуется: {marked_up_cost:.2f} руб.\n'
            f'💳 На балансе: {user_balance:.2f} руб.',
            reply_markup=btn.as_markup()
        )
        await callback.answer()
        return

    # 2. Проверка баланса API
    try:
        balance_data = await BotsAPI.get_balance()
        api_balance = float(balance_data['balance']) if balance_data and 'balance' in balance_data else 0
        logger.info(f"Баланс API: {api_balance} руб., требуется: {original_cost} руб.")
    except Exception as e:
        logger.error(f"Ошибка при проверке баланса API: {e}")
        await callback.message.edit_text(
            "❌ Ошибка при проверке баланса сервиса. Попробуйте позже."
        )
        await state.clear()
        return

    if api_balance < original_cost:
        logger.warning(f"Недостаточно средств в API. Нужно: {original_cost}, есть: {api_balance}")
        await callback.message.edit_text(
            "❌ В данный момент сервис недоступен из-за недостатка средств.\n"
            "Администраторы уже уведомлены о проблеме."
        )
        
        admin_message = (
            f"⚠️ НЕДОСТАТОК СРЕДСТВ В API!\n"
            f"👤 Пользователь: @{callback.from_user.username or 'нет'}\n"
            f"💵 Требуется: {original_cost:.2f} руб.\n"
            f"💰 Баланс API: {api_balance:.2f} руб."
        )
        
        for admin_id in ADMINS_ID:
            try:
                await callback.bot.send_message(admin_id, admin_message)
            except:
                pass
        
        await state.clear()
        return

    # 3. Создание заказа в API (попытки с повторами)
    order_created = False
    order_id = None
    api_error = None
    
    for attempt in range(MAX_RETRIES):
        try:
            # Для просмотров (ID 31621) нужно убедиться, что quantity передается как int
            quantity = int(data['quantity']) if data['service_id'] == 31621 else data['quantity']
            
            logger.info(f"Попытка {attempt+1} создания заказа. Сервис: {data['service_id']}, Ссылка: {data['link']}, Количество: {quantity}")
            
            order_result = await BotsAPI.create_order(
                service_id=data['service_id'],
                link=data['link'],
                quantity=quantity
            )
            
            logger.info(f"Ответ API на создание заказа: {order_result}")
            
            # Улучшенная проверка ответа API
            if not order_result:
                raise Exception("Пустой ответ от API")
                
            if isinstance(order_result, dict) and 'error' in order_result:
                api_error = order_result['error']
                raise Exception(f"API вернул ошибку: {api_error}")
                
            if isinstance(order_result, dict) and 'order' in order_result:
                order_id = str(order_result['order'])  # Преобразуем в строку на случай, если API возвращает число
                if order_id:  # Проверяем, что order_id не пустой
                    order_created = True
                    logger.info(f"Заказ успешно создан. ID: {order_id}")
                    break
                    
            await asyncio.sleep(RETRY_DELAY * (attempt + 1))
            
        except Exception as e:
            logger.error(f"Попытка {attempt + 1} не удалась: {str(e)}")
            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(RETRY_DELAY * (attempt + 1))
                continue
                
            error_msg = "❌ Не удалось создать заказ после нескольких попыток."
            if api_error:
                error_msg += f"\nПричина: {api_error}"
                
            await callback.message.edit_text(error_msg)
            await state.clear()
            return

    if not order_created:
        logger.error("Не удалось создать заказ после всех попыток")
        await callback.message.edit_text("❌ Ошибка при создании заказа.")
        await state.clear()
        return

    # 4. Только после успешного создания заказа списываем средства
    try:
        await DB.add_rub_balance(user_id, -marked_up_cost)
        logger.info(f"Списано {marked_up_cost} руб. с баланса пользователя")
    except Exception as e:
        logger.error(f"Ошибка при списании средств: {e}")
        # Пытаемся отменить заказ в API, если это возможно
        try:
            await BotsAPI.cancel_order(order_id)
            logger.info(f"Попытка отмены заказа {order_id} в API")
        except Exception as e:
            logger.error(f"Ошибка при отмене заказа: {e}")
            
        await refund_user()
        await callback.message.edit_text(
            "❌ Ошибка при обработке платежа. Средства не списаны, заказ не создан."
        )
        await state.clear()
        return

    # 5. Сохраняем заказ в базе данных
    try:
        await DB.add_order(
            user_id=user_id,
            order_id=order_id,
            service_id=data['service_id'],
            link=data['link'],
            quantity=data['quantity'],
            cost=marked_up_cost,
            status='pending',
        )
        logger.info(f"Заказ {order_id} сохранен в базе данных")

        await add_order_to_config({
            "order_id": order_id,
            "user_id": user_id,
            "service_id": data['service_id'],
            "service_name": data['service_name'],
            "link": data['link'],
            "quantity": data['quantity'],
            "cost": marked_up_cost,
            "profit": profit,
            "status": "pending",
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "payment_method": "balance"
        })

        await update_stats(marked_up_cost, profit)
    except Exception as e:
        logger.error(f"Ошибка при сохранении заказа: {e}")
        await refund_user()
        await callback.message.edit_text(
            "❌ Ошибка при сохранении заказа. Средства возвращены."
        )
        await state.clear()
        return

    # 6. Уведомление пользователя и администраторов
    try:
        service = await BotsAPI.get_service(data['service_id'])
        service_name = service['name'] if service else f"Услуга #{data['service_id']}"

        kb = InlineKeyboardBuilder()
        kb.button(text='🔙 В "Мои заказы"', callback_data='my_orders')
        
        await callback.message.edit_text(
            f"✅ <b>Заказ #{order_id} успешно создан!</b>\n\n"
            f"• Услуга: {service_name}\n"
            f"• Ссылка: {data['link']}\n"
            f"• Количество: {data['quantity']}\n"
            f"• Стоимость: {marked_up_cost:.2f} руб.\n\n"
            f"Статус заказа можно проверить в разделе <b>Мои заказы</b>",
            reply_markup=kb.as_markup(),
            parse_mode="HTML"
        )
        
        # Уведомление администраторов
        old_api_balance = api_balance
        new_api_balance = (await BotsAPI.get_balance())['balance']
        
        admin_msg = f'''НОВЫЙ ЗАКАЗ
• Услуга: {service_name}
• Ссылка: {data['link']}
• Количество: {data['quantity']}
• Стоимость: {marked_up_cost:.2f} руб.
• Покупатель: @{callback.from_user.username} | {callback.from_user.id}
• Баланс API: {new_api_balance} Р
• Баланс API перед покупкой: {old_api_balance:.2f} Р
• Потраченная сумма из API на заказ: {float(old_api_balance) - float(new_api_balance):.2f} Р'''
        
        logger.info(f"Отправка уведомления администраторам: {admin_msg}")
        
        for admin_id in ADMINS_ID:
            try:
                await bot.send_message(admin_id, admin_msg)
            except Exception as e:
                logger.error(f"Ошибка при уведомлении администратора {admin_id}: {e}")
                
    except Exception as e:
        logger.error(f"Ошибка при завершении заказа: {e}")
    
    await state.clear()

@bots.callback_query(F.data == "my_orders")
async def show_my_orders(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    user_orders = list(await DB.get_user_orders(user_id))  # Преобразуем генератор в список
    
    if not user_orders:
        builder = InlineKeyboardBuilder()
        builder.button(text="🛒 Сделать заказ", callback_data="bots")
        builder.button(text="🔙 Назад", callback_data="bots_menu")
        builder.adjust(1)
        
        await callback.message.edit_text(
            "📭 <b>У вас пока нет заказов</b>\n\n"
            "Вы можете оформить новый заказ, нажав на кнопку ниже",
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
        return
    
    # Сохраняем заказы в state для пагинации
    await state.update_data(all_orders=user_orders, current_page=1)
    
    # Проверяем есть ли активные заказы (статус 'pending')
    active_orders = [o for o in user_orders if o['status'] == 'pending']
    has_active = bool(active_orders)
    
    if has_active:
        await show_filtered_orders(callback, state, "active")
    else:
        # Если нет активных, проверяем есть ли завершенные
        completed_orders = [o for o in user_orders if o['status'] != 'pending']
        if completed_orders:
            await show_filtered_orders(callback, state, "completed")
        else:
            builder = InlineKeyboardBuilder()
            builder.button(text="🛒 Сделать заказ", callback_data="bots")
            builder.button(text="🔙 Назад", callback_data="bots_menu")
            builder.adjust(1)
            
            await callback.message.edit_text(
                "📭 <b>У вас пока нет заказов</b>\n\n"
                "Вы можете оформить новый заказ, нажав на кнопку ниже",
                reply_markup=builder.as_markup(),
                parse_mode="HTML"
            )
    
    await callback.answer()

async def show_filtered_orders(callback: types.CallbackQuery, state: FSMContext, filter_type: str):
    data = await state.get_data()
    user_orders = data.get('all_orders', [])
    current_page = data.get('current_page', 1)
    
    if filter_type == "active":
        filtered_orders = [o for o in user_orders if o['status'] == 'pending']
        title = "📋 <b>Активные заказы</b>"
    else:
        filtered_orders = [o for o in user_orders if o['status'] != 'pending']
        title = "📋 <b>Завершённые заказы</b>"

    # Пагинация
    orders_per_page = 5
    total_pages = (len(filtered_orders) + orders_per_page - 1) // orders_per_page
    start_index = (current_page - 1) * orders_per_page
    end_index = start_index + orders_per_page
    page_orders = filtered_orders[start_index:end_index]

    builder = InlineKeyboardBuilder()

    # Если заказов нет
    if not page_orders:
        builder.button(text="🔄 Активные", callback_data="filter_orders:active")
        builder.button(text="✅ Завершённые", callback_data="filter_orders:completed")
        # builder.adjust(1)
        builder.button(text="🔙 Назад", callback_data="bots_menu")
        builder.adjust(2, 1)

        status_text = "активных" if filter_type == "active" else "завершённых"
        await callback.message.edit_text(
            f"📭 <b>Нет {status_text} заказов</b>",
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
        return

    # Кнопки фильтров в первой строке
    builder.row(
        InlineKeyboardButton(text="🔄 Активные", callback_data="filter_orders:active"),
        InlineKeyboardButton(text="✅ Завершённые", callback_data="filter_orders:completed")
    )

    # Кнопки заказов (по одной в ряд)
    for order in page_orders:
        status_text = {
            'pending': '🔄 ВЫПОЛНЯЕТСЯ',
            'completed': '✅ ВЫПОЛНЕНО',
            'canceled': '❌ ОТМЕНЕН',
            'failed': '⚠️ ОШИБКА'
        }.get(order['status'], order['status'])
        
        builder.button(
            text=f"{status_text} | Заказ #{order['order_id']}",
            callback_data=f"view_order_{order['order_id']}"
        )
    # builder.adjust(2, 1)

    # Пагинация
    pagination_row = []
    if current_page > 1:
        pagination_row.append(InlineKeyboardButton(text="<", callback_data=f"orders_page:{current_page-1}:{filter_type}"))
    
    pagination_row.append(InlineKeyboardButton(text=f"{current_page}/{total_pages}", callback_data="no_action"))
    
    if current_page < total_pages:
        pagination_row.append(InlineKeyboardButton(text=">", callback_data=f"orders_page:{current_page+1}:{filter_type}"))
    
    if pagination_row:
        builder.row(*pagination_row)

    # Кнопка назад
    builder.button(text="🔙 Назад", callback_data="bots_menu")
    builder.adjust(2, 1)

    await callback.message.edit_text(
        title,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )

@bots.callback_query(F.data.startswith("filter_orders:"))
async def filter_orders_handler(callback: types.CallbackQuery, state: FSMContext):
    filter_type = callback.data.split(":")[1]
    await state.update_data(current_page=1)  # Сбрасываем на первую страницу при смене фильтра
    await show_filtered_orders(callback, state, filter_type)
    await callback.answer()

@bots.callback_query(F.data.startswith("orders_page:"))
async def change_orders_page(callback: types.CallbackQuery, state: FSMContext):
    _, page, filter_type = callback.data.split(":")
    await state.update_data(current_page=int(page))
    await show_filtered_orders(callback, state, filter_type)
    await callback.answer()

@bots.callback_query(F.data == "no_action")
async def no_action(callback: types.CallbackQuery):
    await callback.answer()

@bots.callback_query(F.data.startswith("view_order_"))
async def view_order(callback: types.CallbackQuery):
    order_id = int(callback.data.replace("view_order_", ""))
    
    order = await DB.get_order(order_id)
    if not order:
        await callback.answer("❌ Заказ не найден")
        return
    
    status_data = await BotsAPI.get_order_status(order_id)
    
    if status_data and isinstance(status_data, dict) and 'status' in status_data:
        current_status = status_data['status']
        remains = status_data.get('remains', 'N/A')
        charge = status_data.get('charge', 'N/A')
        
        await DB.update_order_status(order_id, current_status)
    else:
        current_status = order['status']
        remains = 'N/A'
        charge = 'N/A'
    
    service = await BotsAPI.get_service(order['service_id'])
    service_name = service['name'] if service else f"Услуга #{order['service_id']}"
    
    status_emoji = {
        'pending': '🟡',
        'processing': '🔄',
        'completed': '✅',
        'canceled': '❌',
        'error': '⚠️'
    }.get(current_status, '❓')
    
    text = (
        f"{status_emoji} <b>Заказ #{order_id}</b>\n\n"
        f"📌 <b>Услуга:</b> {service_name}\n"
        f"🔗 <b>Ссылка:</b> {order['link']}\n"
        f"🔢 <b>Количество:</b> {order['quantity']}\n"
        f"💰 <b>Стоимость:</b> {order['cost']:.2f} руб.\n"
        f"📊 <b>Статус:</b> {current_status.upper()}\n"
        f"🕒 <b>Дата:</b> {order['created_at']}\n"
    )
    
    builder = InlineKeyboardBuilder()
    builder.button(text="🔄 Проверить статус", callback_data=f"refresh_order_{order_id}")
    builder.button(text="🔙 Назад", callback_data="my_orders")
    builder.adjust(1)
    
    await callback.message.edit_text(
        text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await callback.answer()

@bots.callback_query(F.data.startswith("refresh_order_"))
async def refresh_order_status(callback: types.CallbackQuery):
    order_id = int(callback.data.replace("refresh_order_", ""))
    
    status_data = await BotsAPI.get_order_status(order_id)
    
    if not status_data or 'status' not in status_data:
        await callback.answer("⚠️ Не удалось проверить статус заказа", show_alert=True)
        return
    
    await DB.update_order_status(order_id, status_data['status'])
    
    order = await DB.get_order(order_id)
    if not order:
        await callback.answer("❌ Заказ не найден")
        return
    
    service = await BotsAPI.get_service(order['service_id'])
    service_name = service['name'] if service else f"Услуга #{order['service_id']}"
    
    status_emoji = {
        'pending': '🟡',
        'processing': '🔄',
        'completed': '✅',
        'canceled': '❌',
        'error': '⚠️'
    }.get(status_data['status'], '❓')
    
    text = (
        f"{status_emoji} <b>Заказ #{order_id}</b> (обновлено)\n\n"
        f"📌 <b>Услуга:</b> {service_name}\n"
        f"🔗 <b>Ссылка:</b> {order['link']}\n"
        f"🔢 <b>Количество:</b> {order['quantity']}\n"
        f"💰 <b>Стоимость:</b> {order['cost']:.2f} руб.\n"
        f"📊 <b>Статус:</b> {status_data['status'].upper()}\n"
        f"🕒 <b>Дата:</b> {order['created_at']}\n"
    )
    
    builder = InlineKeyboardBuilder()
    builder.button(text="🔄 Проверить статус", callback_data=f"refresh_order_{order_id}")
    builder.button(text="🔙 Назад", callback_data="my_orders")
    builder.adjust(1)
    
    await callback.message.edit_text(
        text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await callback.answer("✅ Статус обновлен")

@bots.callback_query(F.data == "sales_stats")
async def show_sales_stats(callback: types.CallbackQuery):
    if callback.from_user.id not in ADMINS_ID:
        await callback.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    # Создаем шаблон сообщения с загрузкой
    loading_text = (
        "📊 <b>Статистика продаж</b>\n\n"
        "💰 <b>Общая прибыль:</b> загрузка...\n"
        "📦 <b>Всего заказов:</b> загрузка...\n"
        "📈 <b>Средний чек:</b> загрузка...\n"
        "💳 <b>Баланс API:</b> загрузка...\n\n"
        "🏆 <b>Самый популярный товар:</b>\n"
        "📌 загрузка...\n"
        "🛒 Продано: загрузка...\n"
    )
    
    builder = InlineKeyboardBuilder()
    builder.button(text="📋 Список заказов", callback_data="orders_list:1")
    builder.button(text="🔄 Обновить", callback_data="sales_stats")
    builder.button(text="🔙 Назад", callback_data="bots_menu")
    builder.adjust(1)
    
    message = await callback.message.edit_text(
        loading_text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    
    # Постепенно загружаем данные
    try:
        # Шаг 1: Получаем базовую статистику
        stats = await get_sales_stats()
        text = loading_text.replace(
            "💰 <b>Общая прибыль:</b> загрузка...", 
            f"💰 <b>Общая прибыль:</b> <code>{stats['total_profit']:.2f}</code> руб."
        ).replace(
            "📦 <b>Всего заказов:</b> загрузка...", 
            f"📦 <b>Всего заказов:</b> <code>{stats['total_orders']}</code>"
        )
        await message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
        
        # Шаг 2: Получаем баланс API
        balance_data = await BotsAPI.get_balance()
        api_balance = float(balance_data['balance']) if balance_data and 'balance' in balance_data else 0
        text = text.replace(
            "💳 <b>Баланс API:</b> загрузка...", 
            f"💳 <b>Баланс API:</b> <code>{api_balance:.2f}</code> руб."
        )
        await message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
        
        # Шаг 3: Рассчитываем средний чек
        avg_order = stats['total_profit'] / stats['total_orders'] if stats['total_orders'] > 0 else 0
        text = text.replace(
            "📈 <b>Средний чек:</b> загрузка...", 
            f"📈 <b>Средний чек:</b> <code>{avg_order:.2f}</code> руб."
        )
        await message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
        
        # Шаг 4: Получаем самый популярный товар
        all_orders = await get_orders_from_config()
        service_counts = {}
        for order in all_orders:
            service_id = order['service_id']
            service_counts[service_id] = service_counts.get(service_id, 0) + 1
        
        most_popular = max(service_counts.items(), key=lambda x: x[1]) if service_counts else (None, 0)
        
        if most_popular[0]:
            popular_service = await BotsAPI.get_service(most_popular[0])
            service_name = popular_service['name'] if popular_service else f"Услуга #{most_popular[0]}"
            text = text.replace(
                "🏆 <b>Самый популярный товар:</b>\n📌 загрузка...\n🛒 Продано: загрузка...", 
                f"🏆 <b>Самый популярный товар:</b>\n📌 <code>{service_name}</code>\n🛒 Продано: <code>{most_popular[1]}</code> раз"
            )
        else:
            text = text.replace(
                "🏆 <b>Самый популярный товар:</b>\n📌 загрузка...\n🛒 Продано: загрузка...", 
                "🏆 <b>Самый популярный товар:</b>\nНет данных"
            )
        
        await message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Ошибка при загрузке статистики: {e}")
        await message.edit_text(
            "❌ Произошла ошибка при загрузке статистики",
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
    
    await callback.answer()

@bots.callback_query(F.data.startswith("orders_list:"))
async def show_orders_list(callback: types.CallbackQuery):
    if callback.from_user.id not in ADMINS_ID:
        await callback.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    page = int(callback.data.split(":")[1])
    per_page = 5
    
    # Создаем шаблон сообщения с загрузкой
    loading_text = (
        "📋 <b>Список заказов</b>\n\n"
        "🔄 Загрузка данных...\n\n"
        "📄 Страница загрузка..."
    )
    
    builder = InlineKeyboardBuilder()
    builder.button(text="📊 Статистика", callback_data="sales_stats")
    builder.button(text="🔙 Назад", callback_data="bots_menu")
    builder.adjust(1)
    
    try:
        message = await callback.message.edit_text(
            loading_text,
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Ошибка при начальном редактировании: {e}")
        await callback.answer()
        return
    
    try:
        # Шаг 1: Получаем заказы
        all_orders = (await get_orders_from_config())[::-1]
        total_pages = (len(all_orders) + per_page - 1) // per_page
        offset = (page - 1) * per_page
        orders = all_orders[offset:offset+per_page]
        
        if not orders:
            try:
                await message.edit_text(
                    "📋 <b>Список заказов</b>\n\n"
                    "❌ Нет заказов для отображения\n\n"
                    f"📄 Страница {page} из {total_pages}",
                    reply_markup=builder.as_markup(),
                    parse_mode="HTML"
                )
            except:
                pass
            await callback.answer()
            return
        
        # Шаг 2: Формируем текст с заказами
        text = "📋 <b>Список заказов</b>\n\n"
        for order in orders:
            status_emoji = {
                'pending': '🟡',
                'processing': '🔄',
                'completed': '✅',
                'canceled': '❌',
                'error': '⚠️'
            }.get(order['status'], '❓')
            
            text += (
                f"""<blockquote>{status_emoji} <b>Заказ #<code>{order['order_id']}</code></b>\n"""
                f"""👤 Пользователь: <code>{order['user_id']}</code>\n"""
                f"""📌 Услуга: загрузка...\n"""
                f"""💰 Сумма: <code>{order['cost']:.2f}</code> руб.\n"""
                f"""📊 Статус: <code>{order['status']}</code>\n"""
                f"""🕒 Дата: <code>{order['created_at']}</code></blockquote>\n\n"""
            )
        
        text += f"📄 Страница {page} из {total_pages}"
        
        try:
            await message.edit_text(
                text,
                reply_markup=builder.as_markup(),
                parse_mode="HTML"
            )
        except:
            pass
        
        # Шаг 3: Постепенно загружаем названия услуг
        updated_text = "📋 <b>Список заказов</b>\n\n"
        for order in orders:
            status_emoji = {
                'pending': '🟡',
                'processing': '🔄',
                'completed': '✅',
                'canceled': '❌',
                'error': '⚠️'
            }.get(order['status'], '❓')
            
            service = await BotsAPI.get_service(order['service_id'])
            service_name = service['name'] if service else f"Услуга #{order['service_id']}"
            
            updated_text += (
                f"""<blockquote>{status_emoji} <b>Заказ #<code>{order['order_id']}</code></b>\n"""
                f"""👤 Пользователь: <code>{order['user_id']}</code>\n"""
                f"""📌 Услуга: <code>{service_name}</code>\n"""
                f"""💰 Сумма: <code>{order['cost']:.2f}</code> руб.\n"""
                f"""📊 Статус: <code>{order['status']}</code>\n"""
                f"""🕒 Дата: <code>{order['created_at']}</code></blockquote>\n\n"""
            )
        
        updated_text += f"📄 Страница {page} из {total_pages}"
        
        # Обновляем кнопки пагинации
        new_builder = InlineKeyboardBuilder()
        
        if page > 1:
            new_builder.button(text="⬅️ Назад", callback_data=f"orders_list:{page-1}")
        
        if page < total_pages:
            new_builder.button(text="Вперед ➡️", callback_data=f"orders_list:{page+1}")
        
        new_builder.button(text="📊 Статистика", callback_data="sales_stats")
        new_builder.button(text="🔙 Назад", callback_data="bots_menu")
        new_builder.adjust(2, 1)
        
        # Финальное обновление сообщения с проверкой изменений
        try:
            current_text = message.html_text if hasattr(message, 'html_text') else message.text
            current_markup = message.reply_markup
            
            if (current_text != updated_text or 
                str(current_markup) != str(new_builder.as_markup())):
                await message.edit_text(
                    updated_text,
                    reply_markup=new_builder.as_markup(),
                    parse_mode="HTML"
                )
        except Exception as e:
            logger.error(f"Ошибка при финальном редактировании: {e}")
        
    except Exception as e:
        logger.error(f"Ошибка при загрузке списка заказов: {e}")
        try:
            await message.edit_text(
                "❌ Произошла ошибка при загрузке списка заказов",
                reply_markup=builder.as_markup(),
                parse_mode="HTML"
            )
        except:
            pass
    
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