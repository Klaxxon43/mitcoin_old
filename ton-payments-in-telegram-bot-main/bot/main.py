# main.py
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.enums.parse_mode import ParseMode
from aiogram.client.default import DefaultBotProperties
import random
import string
import json
import db
import api

# Конфигурация
with open('config.json', 'r') as f:
    config = json.load(f)
    BOT_TOKEN = config['BOT_TOKEN']
    MAINNET_WALLET = config['MAINNET_WALLET']
    TESTNET_WALLET = config['TESTNET_WALLET']
    WORK_MODE = config['WORK_MODE']

WALLET = MAINNET_WALLET if WORK_MODE == "mainnet" else TESTNET_WALLET

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация бота
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# Состояния FSM
class OrderStates(StatesGroup):
    choosing_air = State()
    entering_amount = State()
    waiting_payment = State()

def generate_unique_code(length=8):
    """Генерация уникального кода для транзакции"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

# Обработчики команд
@dp.message(Command("start"))
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    is_existing = db.check_user(
        message.from_user.id, 
        message.from_user.username, 
        message.from_user.first_name
    )
    
    welcome_text = (
        f"РЕЖИМ РАБОТЫ: {WORK_MODE}\n\n"
        f"{'С возвращением' if is_existing else 'Добро пожаловать'}, "
        f"{message.from_user.first_name}!\n\n"
        "Для покупки воздуха отправьте /buy"
    )
    
    await message.answer(welcome_text)

@dp.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    """Отмена текущего действия"""
    await state.clear()
    await message.answer("Операция отменена\n/start для перезапуска")

@dp.message(Command("me"))
async def cmd_me(message: Message):
    """Показать историю транзакций"""
    transactions = db.get_user_payments(message.from_user.id)
    
    if not transactions:
        await message.answer("У вас пока нет транзакций")
        return
    
    response = ["Ваши транзакции:"]
    for tx in transactions:
        amount = int(tx['value']) / 1_000_000_000  # Конвертация из нанотонов
        response.append(f"{amount} TON - {tx['comment']} (статус: {tx['status']})")
    
    await message.answer("\n".join(response))

@dp.message(Command("buy"))
async def cmd_buy(message: Message, state: FSMContext):
    """Начать процесс покупки"""
    builder = ReplyKeyboardBuilder()
    air_types = [
        ('Чистый воздух 🌫', 'pure'),
        ('Лесной воздух 🌲', 'forest'),
        ('Морской бриз 🌊', 'sea'),
        ('Запах асфальта 🛣', 'asphalt')
    ]
    
    for text, callback_data in air_types:
        builder.add(KeyboardButton(text=text))
    
    builder.adjust(2)  # 2 кнопки в ряд
    
    await message.answer(
        "Выберите тип воздуха (или /cancel для отмены):",
        reply_markup=builder.as_markup(resize_keyboard=True, one_time_keyboard=True)
    )
    await state.set_state(OrderStates.choosing_air)

# Обработчики состояний
@dp.message(OrderStates.choosing_air)
async def process_air_type(message: Message, state: FSMContext):
    """Обработка выбора типа воздуха"""
    air_mapping = {
        'Чистый воздух 🌫': 'pure',
        'Лесной воздух 🌲': 'forest',
        'Морской бриз 🌊': 'sea',
        'Запах асфальта 🛣': 'asphalt'
    }
    
    if message.text not in air_mapping:
        await message.answer("Пожалуйста, выберите один из предложенных вариантов")
        return
    
    await state.update_data(air_type=message.text, air_code=air_mapping[message.text])
    await message.answer("Введите сумму TON, которую вы хотите отправить (например: 0.5)")
    await state.set_state(OrderStates.entering_amount)

@dp.message(OrderStates.entering_amount)
async def process_amount(message: Message, state: FSMContext):
    """Обработка ввода суммы"""
    try:
        amount = float(message.text.strip())
        if amount <= 0:
            raise ValueError("Сумма должна быть больше нуля")
        
        amount_nano = int(amount * 1_000_000_000)  # Конвертация в нанотоны
        
        # Генерируем уникальный код
        unique_code = generate_unique_code()
        
        data = await state.get_data()
        air_type = data['air_type']
        
        # Сохраняем платеж в БД
        db.save_pending_payment(
            user_id=message.from_user.id,
            amount=str(amount_nano),
            comment_code=unique_code
        )
        
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(
                text="Ton Wallet",
                url=f"ton://transfer/{WALLET}?amount={amount_nano}&text={unique_code}"
            ),
            InlineKeyboardButton(
                text="Tonkeeper",
                url=f"https://app.tonkeeper.com/transfer/{WALLET}?amount={amount_nano}&text={unique_code}"
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="Tonhub",
                url=f"https://tonhub.com/transfer/{WALLET}?amount={amount_nano}&text={unique_code}"
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="✅ Проверить оплату",
                callback_data=f"check_payment:{unique_code}"
            )
        )

        await message.answer(
            f"💨 Вы выбрали: <b>{air_type}</b>\n\n"
            f"Пожалуйста, отправьте <b>{amount} TON</b> на адрес:\n"
            f"<code>{WALLET}</code>\n\n"
            f"С комментарием:\n<code>{unique_code}</code>\n\n"
            "После оплаты нажмите кнопку 'Проверить оплату'",
            reply_markup=builder.as_markup()
        )

        await state.update_data(amount_nano=str(amount_nano), unique_code=unique_code)
        await state.set_state(OrderStates.waiting_payment)
    except ValueError as e:
        await message.answer(f"Некорректная сумма. Пожалуйста, введите число больше нуля (например: 0.5). Ошибка: {str(e)}")

@dp.callback_query(F.data.startswith("check_payment:"), OrderStates.waiting_payment)
async def check_payment(callback: CallbackQuery, state: FSMContext):
    """Проверка платежа"""
    unique_code = callback.data.split(":")[1]
    data = await state.get_data()
    
    result = api.find_transaction(
        value=data['amount_nano'],
        comment=unique_code
    )

    if not result:
        await callback.answer(
            "Платеж еще не получен. Пожалуйста, подождите и попробуйте снова через 10 секунд.",
            show_alert=True
        )
        return
    
    # Обновляем статус платежа в БД
    db.update_payment_status(unique_code, "completed")
    
    await callback.message.edit_text(
        "✅ <b>Платеж подтвержден!</b>\n\n"
        f"Спасибо за покупку {data['air_type']}\n\n"
        "/start для нового заказа",
    )
    await state.clear()

if __name__ == '__main__':
    dp.run_polling(bot, skip_updates=True)  