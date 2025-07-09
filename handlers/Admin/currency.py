from aiogram import F, types
from aiogram.fsm.context import FSMContext
from utils.Imports import *
from .states import edit_sell_currency
from utils.kb import admin_kb
from .admin import admin

@admin.callback_query(F.data.startswith("editSellCurrency"))
async def edit_currency_handler(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(edit_sell_currency.amount)
    currency = await DB.get_stars_sell_currency()
    await callback.message.edit_text(f'Введите новый курс продажи звёзд\nТекущий курс: {currency[0]}')
    await callback.answer()

@admin.message(edit_sell_currency.amount)
async def process_edit_currency(message: types.Message, state: FSMContext):
    try:
        new_currency = float(message.text)
        if new_currency <= 0:
            raise ValueError
            
        await DB.update_buy_sell_currency(new_currency)
        await message.answer(f'✅ Курс успешно изменен на {new_currency}')
    except ValueError:
        await message.answer('❌ Неверное значение! Введите положительное число')
    except Exception as e:
        await message.answer(f'❌ Ошибка: {str(e)}')
    finally:
        await state.clear()