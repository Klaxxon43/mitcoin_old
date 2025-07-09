from utils.Imports import *
from .states import AdminActions
from .admin import admin

@admin.callback_query(F.data == 'view_user_profile')
async def view_user_profile_handler(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer('Введите ID пользователя для просмотра его профиля', reply_markup=cancel_all_kb())
    await state.set_state(AdminActions.view_user_profile)
    await callback.answer()

@admin.message(AdminActions.view_user_profile)
async def get_user_profile(message: types.Message, state: FSMContext):
    user_id = message.text
    try:
        user = await DB.select_user(user_id)
        if user:
            balance = user['balance'] if user['balance'] is not None else 0
            rub_balance = user['rub_balance'] if user['rub_balance'] is not None else 0
            tasks = await DB.get_tasks_by_user_admin(user_id)

            chanel_tasks = [f"Канал | task_id - {task_id}" for task_id, type in tasks if type == 1]
            chat_tasks = [f"Чат | task_id - {task_id}" for task_id, type in tasks if type == 2]
            post_tasks = [f"Пост | task_id - {task_id}" for task_id, type in tasks if type == 3]

            donation_count = await DB.count_user_deposits(user_id)
            donation_sum = await DB.sum_user_deposits(user_id)
            referral_count = await DB.get_referred_users(user_id)
            referral_earnings = await DB.get_earned_from_referrals(user_id)
            completed_tasks_count = await DB.count_user_completed_tasks(user_id)
            approx_task_earnings = completed_tasks_count * 1700

            profile_text = f"""
🆔 ID - <code>{user_id}</code> / <a href='tg://user?id={user_id}'>КЛИК</a>

💵 MitCoin - {balance} $MICO
💵 Рубли - {rub_balance}₽

💼 Задания:

{chr(10).join(chanel_tasks)}
{chr(10).join(chat_tasks)}
{chr(10).join(post_tasks)}

Примерно заработано с заданий - {approx_task_earnings}

💰 Количество донатов - {donation_count}
🎰 Сумма донатов - {donation_sum}

👥 Количество приглашенных пользователей - {len(referral_count)}
💸Заработано с рефералов - {referral_earnings}
"""
            builder = InlineKeyboardBuilder()
            builder.add(types.InlineKeyboardButton(text="✏ Баланс", callback_data=f'update_balance:{user_id}'))
            builder.add(types.InlineKeyboardButton(text="✏ Руб Баланс", callback_data=f'update_rub_balance:{user_id}'))
            await message.answer(profile_text, reply_markup=builder.as_markup())
        else:
            await message.answer('Пользователь не найден 😓')
    except Exception as e:
        await message.answer(f"Произошла ошибка при получении профиля пользователя: {str(e)}")
        print(e)
    finally:
        await state.clear()

@admin.callback_query(lambda c: c.data.startswith('update_balance:'))
async def update_balance_handler(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.data.split(':')[1]
    await state.update_data(user_id=user_id)
    await callback.message.answer('Введите новый баланс пользователя:')
    await state.set_state(AdminActions.update_balance)
    await callback.answer()

@admin.message(AdminActions.update_balance)
async def set_new_balance(message: types.Message, state: FSMContext):
    data = await state.get_data()
    user_id = data['user_id']
    new_balance = int(message.text)
    await DB.update_balance(user_id, balance=new_balance)
    await message.answer(f"Баланс пользователя {user_id} обновлен до {new_balance}.")
    await state.clear()

@admin.callback_query(lambda c: c.data.startswith('update_rub_balance:'))
async def update_rub_balance_handler(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.data.split(':')[1]
    await state.update_data(user_id=user_id)
    await callback.message.answer('Введите новый баланс пользователя в рублях:')
    await state.set_state(AdminActions.update_rub_balance)
    await callback.answer()

@admin.message(AdminActions.update_rub_balance)
async def set_new_rub_balance(message: types.Message, state: FSMContext):
    data = await state.get_data()
    user_id = data['user_id']
    new_balance = int(message.text)
    await DB.update_rub_balance(user_id, rub_balance=new_balance)
    await message.answer(f"Баланс (Рубли) пользователя {user_id} обновлен до {new_balance}.")
    await state.clear()