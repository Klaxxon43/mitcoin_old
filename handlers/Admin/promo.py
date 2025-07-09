from utils.Imports import *
from .states import PromoStates
from utils.kb import admin_kb
from datetime import datetime, timedelta
import random
import string
from .admin import admin

def generate_promo_code(length=8):
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

@admin.callback_query(F.data == "promocreate")
async def create_promo_start(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "Создание нового промокода:\n\nВведите сумму бонуса:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_menu")]
        ])
    )
    await state.set_state(PromoStates.waiting_amount)
    await state.update_data(creator_id=callback.from_user.id)

@admin.message(PromoStates.waiting_amount)
async def promo_get_amount(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text)
        if amount <= 0:
            raise ValueError
        await state.update_data(amount=amount)
        
        auto_promo = generate_promo_code()
        markup = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"🔢 {auto_promo}", callback_data=f"use_auto_promo:{auto_promo}")],
            [InlineKeyboardButton(text="✏ Ввести вручную", callback_data="enter_manually")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_menu")]
        ])
        
        await message.answer(
            "Выберите или введите название промокода:",
            reply_markup=markup
        )
        await state.set_state(PromoStates.waiting_name)
    except ValueError:
        await message.answer("❌ Неверная сумма! Введите число больше 0:")

@admin.callback_query(F.data.startswith("use_auto_promo:"), PromoStates.waiting_name)
async def use_auto_promo(callback: types.CallbackQuery, state: FSMContext):
    promo_name = callback.data.split(":")[1]
    await state.update_data(name=promo_name)
    await promo_select_where(callback.message, state)

@admin.callback_query(F.data == "enter_manually", PromoStates.waiting_name)
async def enter_promo_manually(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "Введите название промокода:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_menu")]
        ])
    )
    await state.set_state(PromoStates.waiting_name_manual)

@admin.message(PromoStates.waiting_name_manual)
async def promo_get_name_manual(message: types.Message, state: FSMContext):
    if len(message.text) < 3:
        await message.answer("❌ Слишком короткое название! Минимум 3 символа:")
        return
    
    await state.update_data(name=message.text.strip())
    await promo_select_where(message, state)

async def promo_select_where(message: Union[types.Message, types.CallbackQuery], state: FSMContext):
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="MICO", callback_data="where:def_bal")],
        [InlineKeyboardButton(text="RUB", callback_data="where:def_bal_rub")],
        [InlineKeyboardButton(text="Stars", callback_data="where:stars")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_menu")]
    ])
    
    if isinstance(message, types.CallbackQuery):
        await message.message.edit_text(
            "Выберите куда начислять бонус:",
            reply_markup=markup
        )
    else:
        await message.answer(
            "Выберите куда начислять бонус:",
            reply_markup=markup
        )
    await state.set_state(PromoStates.waiting_where)

@admin.callback_query(F.data.startswith("where:"), PromoStates.waiting_where)
async def promo_get_where(callback: types.CallbackQuery, state: FSMContext):
    where_to = callback.data.split(":")[1]
    await state.update_data(where_to=where_to)
    
    await callback.message.edit_text(
        "Введите количество активаций:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_menu")]
        ])
    )
    await state.set_state(PromoStates.waiting_count)

@admin.message(PromoStates.waiting_count)
async def promo_get_count(message: types.Message, state: FSMContext):
    try:
        count = int(message.text)
        if count <= 0:
            raise ValueError
            
        await state.update_data(count=count)
        
        await message.answer(
            "Введите срок действия в днях:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_menu")]
            ])
        )
        await state.set_state(PromoStates.waiting_days)
    except ValueError:
        await message.answer("❌ Неверное количество! Введите целое число больше 0:")

@admin.message(PromoStates.waiting_days)
async def promo_get_days(message: types.Message, state: FSMContext):
    try:
        days = int(message.text)
        if days <= 0:
            raise ValueError
            
        data = await state.get_data()
        
        await Promo.create(
            creator_id=data['creator_id'],
            name=data['name'],
            amount=data['amount'],
            where_to=data['where_to'],
            count=data['count'],
            days=days
        )
        
        await message.answer(
            f"✅ Промокод успешно создан!\n\n"
            f"🔢 Название: <code>{data['name']}</code>\n"
            f"💰 Сумма: {data['amount']}\n"
            f"📌 Тип: {data['where_to']}\n"
            f"🔢 Активаций: {data['count']}\n"
            f"📅 Срок действия: {days} дней",
            reply_markup=admin_kb()
        )
        await state.clear()
    except ValueError:
        await message.answer("❌ Неверное количество дней! Введите целое число больше 0:")