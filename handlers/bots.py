# Стандартные библиотеки
import os, asyncio, logging, random, uuid, sys, traceback, time, emoji, math
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple
import pytz, requests
from aiocryptopay import AioCryptoPay, Networks
from cachetools import TTLCache

# Aiogram основные компоненты
from aiogram import Bot, F, types, Router, Dispatcher
from aiogram.exceptions import TelegramBadRequest
from aiogram.enums import ChatMemberStatus, ChatType
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.enums.dice_emoji import DiceEmoji
from aiogram.types import (
    InlineQueryResultArticle, InputTextMessageContent,
    InlineKeyboardMarkup, InlineKeyboardButton,
    FSInputFile, InputMediaPhoto, ChatMemberUpdated,
    ContentType, LabeledPrice, PreCheckoutQuery,
    BufferedInputFile, Chat
)

# Локальные модули
from datebase.db import DB, Promo
from untils.kb import (
    menu_kb, back_menu_kb, profile_kb, pr_menu_kb,
    pr_menu_canc, work_menu_kb, back_work_menu_kb,
    back_profile_kb, select_deposit_menu_kb,
    back_dep_kb, cancel_all_kb
)
from config import CRYPTOBOT_TOKEN, ADMINS_ID, BotsAPI
from threading import Lock


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bots = Router()

task_cache = {}
task_cache_chat = {}

CHECK_CHAT_ID = -4792065005  # ID чата для проверки заданий
DB_CHAT_ID = -4683486408
INFO_ID = -4784146602
TASKS_CHAT_ID = -1002291978719
REPORT_CHAT_ID = -1002291978719

MOSCOW_TZ = pytz.timezone("Europe/Moscow")

# Добавим в начало файла
PREMIUM_SERVICES = {
    "Подписчики": 31388,
    "Подписчики+": 32281,
    "Просмотры": 31621,
    "Опросы": 787,
    "Боты": 26716
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
async def show_bots_menu(callback: types.CallbackQuery, state: FSMContext):
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
    builder.button(text="Реакции", callback_data="bots_reactions")
    builder.button(text='🔙 Назад', callback_data='back_menu')
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

@bots.callback_query(F.data.startswith("bots_srv_"))
async def show_service_details(callback: types.CallbackQuery):
    service_id = int(callback.data.replace("bots_srv_", ""))
    
    # Пытаемся получить данные из кэша
    service = None
    if service_id in PREMIUM_SERVICES.values() and SERVICES_CACHE['premium']:
        service = SERVICES_CACHE['premium'].get(service_id)
    elif service_id in REACTION_SERVICES.values() and SERVICES_CACHE['reactions']:
        service = SERVICES_CACHE['reactions'].get(service_id)
    
    # Если в кэше нет данных, запрашиваем из API
    if not service:
        try:
            service = await BotsAPI.get_service(service_id)
        except Exception as e:
            logger.error(f"Error getting service {service_id}: {e}")
            await callback.answer("⚠️ Ошибка при загрузке услуги")
            return
    
    if not service:
        await callback.answer("⚠️ Услуга не найдена")
        return
    
    description = SERVICE_DESCRIPTIONS.get(service_id, f"""
📌 Услуга #{service['service']}
🏷 Название: {service['name']}
💵 Стоимость: {service['rate']} за единицу
📊 Лимиты: {service['min']} - {service['max']}
🚀 Скорость: {'Моментально' if not service['dripfeed'] else 'Постепенно'}
🛡 Гарантия: {'Есть' if service['refill'] else 'Нет'}
""")
    
    builder = InlineKeyboardBuilder()
    builder.button(text="🛒 Купить", callback_data=f"buy_{service_id}")
    
    if service_id in REACTION_SERVICES.values():
        builder.button(text="🔙 Назад", callback_data="bots_reactions")
    else:
        builder.button(text="🔙 Назад", callback_data="bots_back_to_main")
    
    builder.adjust(2)
    
    await callback.message.edit_text(
        description,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await callback.answer()

# Обработчик возврата в главное меню
@bots.callback_query(F.data == "bots_back_to_main")
async def back_to_main_menu(callback: types.CallbackQuery):
    await show_bots_menu(callback, None)
    await callback.answer()

# Добавим новое состояние для оформления заказа
class OrderStates(StatesGroup):
    AWAITING_LINK = State()
    AWAITING_QUANTITY = State()
    VIEW_ORDERS = State()

# Обновим обработчик покупки
@bots.callback_query(F.data.startswith("buy_"))
async def start_order_process(callback: types.CallbackQuery, state: FSMContext):
    service_id = int(callback.data.replace("buy_", ""))
    
    # Получаем информацию об услуге
    service = await BotsAPI.get_service(service_id)
    if not service:
        await callback.answer("⚠️ Услуга временно недоступна")
        return
    
    await state.update_data(
        service_id=service_id,
        service_name=service['name'],
        min_quantity=int(service['min']),
        max_quantity=int(service['max']),
        rate=float(service['rate'])
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
        f"• Цена за 1000: {data['rate']} руб.",
        parse_mode="HTML"
    )
    
    await state.set_state(OrderStates.AWAITING_QUANTITY)

# Обработчик ввода количества
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
    
    # Рассчитываем стоимость
    cost = round(quantity * data['rate'] / 1000, 2)
    
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Подтвердить", callback_data="confirm_order")
    builder.button(text="❌ Отменить", callback_data="cancel_order")
    builder.adjust(2)
    
    await state.update_data(quantity=quantity, cost=cost)
    
    await message.answer(
        f"📝 <b>Подтвердите заказ:</b>\n\n"
        f"• Услуга: {data['service_name']}\n"
        f"• Ссылка: {data['link']}\n"
        f"• Количество: {quantity}\n"
        f"• Стоимость: {cost} руб.\n\n"
        f"После оплаты заказ начнет выполняться автоматически.",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )

# Обработчик отмены заказа
@bots.callback_query(F.data == "cancel_order", OrderStates.AWAITING_QUANTITY)
async def cancel_order(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("❌ Заказ отменен")
    await state.clear()
    await callback.answer()

# Обработчик команды /orders
@bots.message(Command("orders"))
async def show_orders(message: types.Message, state: FSMContext):
    # Здесь должна быть логика получения заказов пользователя из БД
    # Для примера будем использовать временное хранилище
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

# Обработчик возврата к списку заказов
@bots.callback_query(F.data == "back_to_orders")
async def back_to_orders_list(callback: types.CallbackQuery, state: FSMContext):
    await show_orders(callback.message, state)
    await callback.answer()

# Обновим метод создания заказа для сохранения в БД
@bots.callback_query(F.data == "confirm_order")
async def confirm_order(callback: types.CallbackQuery, state: FSMContext):
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
        cost=data['cost'],
        status='pending'  # Начальный статус
    )
    
    # Получаем информацию об услуге для красивого отображения
    service = await BotsAPI.get_service(data['service_id'])
    service_name = service['name'] if service else f"Услуга #{data['service_id']}"
    
    await callback.message.edit_text(
        f"✅ <b>Заказ #{order_id} успешно создан!</b>\n\n"
        f"• Услуга: {service_name}\n"
        f"• Ссылка: {data['link']}\n"
        f"• Количество: {data['quantity']}\n"
        f"• Стоимость: {data['cost']} руб.\n\n"
        f"Статус заказа можно проверить командой /orders",
        parse_mode="HTML"
    )
    
    await state.clear()
    await callback.answer()
    