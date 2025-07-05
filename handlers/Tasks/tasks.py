from untils.Imports import *
from .states import *

task_cache = {}
task_cache_chat = {}



task_creation_lock = asyncio.Lock()
reaction_task_lock = asyncio.Lock()
available_reaction_tasks = [] # REACTIONS 

tasks = Router()


all_price = {
    "channel": 1500,
    "chat": 1500,
    "post": 250,
    "comment": 750,
    "reaction": 500,
    "link": 1500,
    "boost": 5000
}



@tasks.callback_query(F.data == 'pr_menu')
async def pr_menu_handler(callback: types.CallbackQuery, bot: Bot):
    user_id = callback.from_user.id

    # Проверяем, подписан ли пользователь на все каналы
    channels = await DB.all_channels_op()
    not_subscribed = []

    for channel in channels:
        channel_id = channel[0]
        try:
            chat_member = await bot.get_chat_member(chat_id=channel_id, user_id=user_id)
            if chat_member.status not in ['member', 'administrator', 'creator']:
                not_subscribed.append(channel)
        except Exception as e:
            print(f"Ошибка при проверке подписки: {e}") 

    if not_subscribed:
        print(f'https://t.me/{channel[0].replace("@", "")}')
        # Если пользователь не подписан на некоторые каналы
        keyboard = InlineKeyboardBuilder()
        for channel in not_subscribed:
            keyboard.add(InlineKeyboardButton(
                text=f"📢 {channel[1]}",
                url=f"https://t.me/{channel[0].replace('@', '')}"
            ))
        keyboard.add(InlineKeyboardButton(
            text="✅ Я подписался",
            callback_data="op_proverka"
        ))
        keyboard.adjust(1)
        await callback.message.answer(
            "Для использования бота подпишитесь на следующие каналы:",
            reply_markup=keyboard.as_markup()
        )
    else:

        await callback.answer()
        await callback.message.edit_text(
            "📋 <b>В данном разделе вы можете создать свои задания</b>\nЧто нужно рекламировать?", reply_markup=pr_menu_kb(user_id))

@tasks.callback_query(F.data == 'pr_menu_cancel')
async def cancel_pr(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    await state.clear()
    await pr_menu_handler(callback, bot)


async def auto_confirm_task(task_id: int, user_id: int, bot: Bot, username, state: FSMContext):
    # Ждем 24 часа
    await asyncio.sleep(24 * 60 * 60)  # 24 часа в секундах

    # Проверяем, находится ли заявка в ожидании
    pending_task = await DB.get_pending_reaction_task(task_id, user_id)
    if pending_task:
        # Если заявка всё ещё в ожидании, автоматически подтверждаем её
        pending_id, user_id, task_id, target_id, post_id, reaction, screenshot, status = pending_task

        # Разделяем target_id на channel_username и post_id
        channel_username, post_id = target_id.split(':')

        # Добавляем задание в таблицу completed_tasks
        await DB.add_completed_task(
            user_id=user_id,
            task_id=task_id,
            target_id=target_id,
            task_sum=all_price['reaction'],
            owner_id=user_id,
            status=0,
            other=0
        )

        # Удаляем задание из таблицы ожидания
        await DB.delete_pending_reaction_task(task_id, user_id)

        # Начисляем баланс пользователю
        await DB.add_balance(amount=all_price['reaction'], user_id=user_id)

        # Уменьшаем количество выполнений задания на 1
        task = await DB.get_task_by_id(task_id)
        if task:
            new_amount = task[3] - 1  # task[3] — это текущее количество выполнений
            await DB.update_task_amount2(task_id, new_amount)

        # Уведомляем пользователя
        await bot.send_message(
            user_id,
            f"🎉 <b>Ваше задание на реакцию автоматически подтверждено!</b>\n\n"
            f"💸 Вам начислено: {all_price['reaction']} MITcoin\n"
            f"📌 Пост: https://t.me/{channel_username}/{post_id}\n"
            f"🎯 Реакция: {reaction if reaction else 'Любая'}\n"
            f"🆔 ID задания: {task_id}"
        )

        # Уведомляем создателя задания
        creator_id = user_id
        await bot.send_message(
            creator_id,
            f"🎉 <b>Задание на реакцию автоматически выполнено!</b>\n\n"
            f"👤 Пользователь: @{username} (ID: {user_id})\n"
            f"📌 Пост: https://t.me/{channel_username}/{post_id}\n"
            f"🎯 Реакция: {reaction if reaction else 'Любая'}\n"
            f"🆔 ID задания: {task_id}"
        )

        # Удаляем сообщение с заданием
        data = await state.get_data()
        admin_message_id = data.get('admin_message_id')
        if admin_message_id:
            await bot.delete_message(CHECK_CHAT_ID, admin_message_id)


async def update_dayly_and_weekly_tasks_statics(user_id: int):
    """Обновляет дневную и недельную статистику задач"""
    try:
        # Обновляем дневные задачи
        await DB.increment_daily_completed_task_count(user_id)
        
        # Обновляем недельные задачи
        await DB.increment_weekly_completed_task_count(user_id)
        
        # Логируем успешное обновление
        print(f"Статистика задач обновлена для пользователя {user_id}")
        return True
    except Exception as e:
        print(f"Ошибка при обновлении статистики задач: {e}")
        return False

