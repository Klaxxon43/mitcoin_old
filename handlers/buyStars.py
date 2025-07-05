# Стандартные библиотеки
import os, asyncio, logging, random, uuid, sys, traceback
from datetime import datetime
from pathlib import Path
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
from aiogram.types import InlineQueryResultArticle, InputTextMessageContent

# Aiogram типы
from aiogram.types import (
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
from config import CRYPTOBOT_TOKEN, ADMINS_ID
import API.usd as usd, time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BuyStars = Router()

STAR_PRICE_RUB = 1.6  # 1 звезда = 1.6 рубля
BUY_STARS_CHAT = -4891588772


class BuyStarsStates(StatesGroup):
    amount = State()
    payment_method = State()

@BuyStars.callback_query(F.data == 'BuyStars')
async def show_buy_stars_menu(callback: types.CallbackQuery, bot: Bot):
    try:
        current_currency = (await DB.get_stars_sell_currency())[0] 
        
        btn = InlineKeyboardBuilder()
        btn.add(InlineKeyboardButton(text='⭐️ Купить звёзды', callback_data='buy_stars_start'))
        btn.add(InlineKeyboardButton(text='◀️ Назад', callback_data='back_menu'))
        btn.adjust(1)
        
        await callback.message.edit_text(
            f"Тут вы можете купить звёзды\n"
            f"Минимальная сумма покупки: 50 звёзд\n"
            f"Цена: 1⭐️ = {current_currency}₽\n"
            f"Доступные способы оплаты:\n"
            f"- Рубли (переводом)\n"
            f"- USDT (через криптобота)\n\n"
            f"После оплаты в скорем времени вы получите свои звёзды",
            reply_markup=btn.as_markup()
        )
        
    except Exception as e:
        await callback.message.answer(f"Произошла ошибка: {e}")
        logger.error(f"Error in BuyStars: {e}")

@BuyStars.callback_query(F.data == 'buy_stars_start')
async def start_buy_stars(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    await state.set_state(BuyStarsStates.amount)
    await callback.message.edit_text(
        'Введите количество звёзд, которые хотите приобрести (мин. 50)',
        reply_markup=back_menu_kb(user_id)
    )

@BuyStars.message(BuyStarsStates.amount)
async def process_stars_amount(message: types.Message, state: FSMContext):
    try:
        current_currency = (await DB.get_stars_sell_currency())[0] 
        stars_amount = int(message.text)
        if stars_amount < 50:
            await message.answer("❌ Минимальная сумма покупки - 50 звёзд!")
            return
        
        amount_rub = stars_amount * current_currency
        await state.update_data(stars_amount=stars_amount, amount_rub=amount_rub)
        
        btn = InlineKeyboardBuilder()
        btn.add(InlineKeyboardButton(text='💳 Оплата рублями', callback_data='pay_rub'))
        btn.add(InlineKeyboardButton(text='💲 Оплата USDT', callback_data='pay_usd'))
        btn.add(InlineKeyboardButton(text='◀️ Назад', callback_data='BuyStars'))
        btn.adjust(1)
        
        await message.answer(
            f'Вы хотите купить {stars_amount}⭐ за {amount_rub:.2f}₽\n'
            'Выберите способ оплаты:',
            reply_markup=btn.as_markup()
        )
        await state.set_state(BuyStarsStates.payment_method)
        
    except ValueError:
        await message.answer("❌ Пожалуйста, введите целое число!")
    except Exception as e:
        logger.error(f"Error in process_stars_amount: {e}")
        await message.answer("❌ Произошла ошибка, попробуйте позже")

@BuyStars.callback_query(BuyStarsStates.payment_method, F.data == 'pay_rub')
async def pay_with_rub(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    stars_amount = data['stars_amount']
    amount_rub = data['amount_rub']
    
    btn = InlineKeyboardBuilder()
    btn.add(InlineKeyboardButton(text='💸 Оплатить', url='https://t.me/Coin_var'))
    btn.add(InlineKeyboardButton(text='◀️ Назад', callback_data='buy_stars_start'))
    btn.adjust(1)
    
    await callback.message.edit_text(
        f'Для покупки {stars_amount}⭐ за {amount_rub:.2f}₽:\n'
        '1. Напишите продавцу по кнопке ниже\n'
        '2. Оплатите звёзды по предоставленному им рекзвезитам\n'
        '3. В скорем времени вы получите свои звёзды\n\n'
        'Внимание! Обязательно пришлите скриншот перевода для подтверждения оплаты!',
        reply_markup=btn.as_markup()
    )
    await state.clear()

@BuyStars.callback_query(BuyStarsStates.payment_method, F.data == 'pay_usd')
async def pay_with_usd(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    user_id = callback.from_user.id
    data = await state.get_data()
    stars_amount = data['stars_amount']
    amount_rub = data['amount_rub']
    
    try:
        # Конвертируем рубли в доллары
        amount_usd = await convert_rub_to_usd(amount_rub)
        if amount_usd <= 0:
            raise ValueError("Неверный курс обмена")
        
        # Создаем счет в USDT
        invoice = await usd.create_invoice(amount_usd, purpose='BuyStars')
        if not invoice:
            raise ValueError("Ошибка создания счета")
            
        btn = InlineKeyboardBuilder()
        btn.add(InlineKeyboardButton(text='💲 Оплатить USDT', url=invoice['url']))
        btn.add(InlineKeyboardButton(text='◀️ Назад', callback_data='buy_stars_start'))
        btn.adjust(1)
        
        msg = await callback.message.answer(
            f'Для покупки {stars_amount}⭐ оплатите {amount_usd:.2f} USDT\n'
            'На оплату дается 3 минуты. После оплаты звёзды будут зачислены автоматически.',
            reply_markup=btn.as_markup()
        )
        
        # Ожидаем оплату
        ttime = 0
        while ttime < 180:  # 3 минуты
            result = await usd.check_payment_status(invoice['id'],purpose='BuyStars')
            if result:
                await callback.message.answer(
                    '✅ Оплата прошла успешно! Скоро звёзды будут зачислены ',
                    reply_markup=back_menu_kb(user_id)
                )
                
                # Уведомляем админа
                await bot.send_message(
                    chat_id=BUY_STARS_CHAT,
                    text=f'''
⭐️ Новая заявка на покупку звёзд! ⭐️
Пользователь: {callback.from_user.id} - @{callback.from_user.username}
Куплено: {stars_amount} ⭐️
Оплачено: {amount_usd:.2f} USDT ({amount_rub:.2f}₽)
Способ оплаты: USDT'''
                )
                break
                
            await asyncio.sleep(5)
            ttime += 5
        
        await state.clear()
        
    except Exception as e:
        logger.error(f"Error in pay_with_usd: {e}")
        await callback.message.answer(
            "❌ Произошла ошибка при создании счета. Попробуйте другой способ оплаты.",
            reply_markup=back_menu_kb(user_id)
        )
        await state.clear()

async def convert_rub_to_usd(amount_rub: float) -> float:
    """
    Конвертирует рубли в доллары по текущему курсу
    :param amount_rub: Сумма в рублях
    :return: Сумма в долларах
    """
    try:
        # Здесь можно использовать любой API для получения курса
        # В данном примере используем фиксированный курс 1 USD = 80 RUB
        # В реальном проекте лучше получать курс из API
        usd_rate = 80.0  # Пример: 1 USD = 80 RUB
        return amount_rub / usd_rate
    except Exception as e:
        print(f"Ошибка при конвертации: {e}")
        return 0.0