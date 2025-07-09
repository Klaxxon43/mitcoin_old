from aiogram import F, types
from aiogram.fsm.context import FSMContext
from utils.Imports import *
from .states import add_mining
from utils.kb import admin_kb
from .admin import admin

@admin.callback_query(F.data == 'adminMining')
async def mining_handler(callback: types.CallbackQuery):
    kb = InlineKeyboardBuilder()
    kb.add(InlineKeyboardButton(text='➕ Выдать майнинг', callback_data='add_mining'))
    kb.add(InlineKeyboardButton(text='➖ Забрать майнинг', callback_data='minus_mining'))
    kb.add(InlineKeyboardButton(text='🔙 Назад', callback_data='admin_kb'))
    kb.adjust(1)
    await callback.message.edit_text('Выберите действие:', reply_markup=kb.as_markup())

@admin.callback_query(F.data == 'add_mining')
async def add_mining_handler(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(add_mining.id)
    await callback.message.answer('Введите ID пользователя для выдачи майнинга:')
    await callback.answer()

@admin.callback_query(F.data == 'minus_mining')
async def remove_mining_handler(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(add_mining.id2)
    await callback.message.answer('Введите ID пользователя для отключения майнинга:')
    await callback.answer()

@admin.message(add_mining.id)
async def process_add_mining(message: types.Message, state: FSMContext, bot: Bot):
    user_id = message.text.strip()
    await state.update_data(id=user_id)
    data = await state.get_data()
    
    try:
        success = await DB.add_mining(data['id'])
        if success:
            await bot.send_message(data['id'], 'Вам выдан майнинг!')
            await message.answer(f'✅ Пользователю {data["id"]} успешно выдан майнинг')
        else:
            await message.answer('❌ У этого пользователя уже есть майнинг')
    except Exception as e:
        await message.answer(f'❌ Ошибка: {str(e)}')
    finally:
        await state.clear()

@admin.message(add_mining.id2)
async def process_remove_mining(message: types.Message, state: FSMContext):
    user_id = message.text.strip()
    await state.update_data(id2=user_id)
    data = await state.get_data()
    
    try:
        success = await DB.remove_mining(data['id2'])
        if success:
            await message.answer(f'✅ У пользователя {data["id2"]} отключен майнинг')
        else:
            await message.answer('❌ У этого пользователя нет майнинга')
    except Exception as e:
        await message.answer(f'❌ Ошибка: {str(e)}')
    finally:
        await state.clear()