from utils.Imports import *
from .states import MailingStates
from utils.kb import admin_kb, back_menu_kb
from .admin import admin

@admin.callback_query(F.data == 'mailing')
async def mailing_handler(callback: types.CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.add(
        types.InlineKeyboardButton(text="Назад", callback_data='back_admin_not_clear'),
        types.InlineKeyboardButton(text="Остановить", callback_data='stop_mailing')
    )
    await callback.message.answer('Отправьте сообщение для рассылки', reply_markup=builder.as_markup())
    await state.set_state(MailingStates.message)
    await callback.answer()

@admin.message(MailingStates.message)
async def mailing_get_msg(message: types.Message, state: FSMContext, bot: Bot):
    text = message.text
    users = await DB.select_all()
    if not users:
        await message.answer("❌ Нет пользователей для рассылки.")
        await state.clear()
        return

    total_users = len(users)
    completed_users = 0
    dead_users = 0

    builder = InlineKeyboardBuilder()
    builder.add(
        types.InlineKeyboardButton(text="Назад", callback_data='admin_kb'),
        types.InlineKeyboardButton(text="Остановить", callback_data='stop_mailing')
    )

    progress_message = await message.answer(
        f"📤 <b>Рассылка началась</b>\n\n"
        f"Общее количество пользователей: {total_users}\n",
        reply_markup=builder.as_markup()
    )

    await state.set_state(MailingStates.progress)
    await state.update_data(stop_flag=False)

    async def update_progress():
        previous_text = None
        while True:
            data = await state.get_data()
            if data.get('stop_flag', False):
                break
            await asyncio.sleep(5)
            current_text = (
                f"📤 <b>Рассылка в процессе...</b>\n\n"
                f"Общее количество пользователей: {total_users}\n"
                f"✅ Успешно отправлено: {completed_users}\n"
                f"💀 Мертвые пользователи: {dead_users}"
            )
            if current_text != previous_text:
                try:
                    await progress_message.edit_text(
                        current_text,
                        reply_markup=builder.as_markup()
                    )
                    previous_text = current_text
                except TelegramBadRequest as e:
                    if "message is not modified" in str(e):
                        continue
                    raise

    asyncio.create_task(update_progress())

    for user in users:
        data = await state.get_data()
        if data.get('stop_flag', False):
            break
        try:
            user_id = message.from_user.id
            await bot.copy_message(
                chat_id=int(user['user_id']),
                from_chat_id=message.from_user.id,
                message_id=message.message_id,
                reply_markup=back_menu_kb(user_id)
            )
            completed_users += 1
            await asyncio.sleep(0.1)
        except TelegramForbiddenError:
            dead_users += 1
        except Exception as e:
            dead_users += 1
            print(f"Ошибка при отправке пользователю {user['user_id']}: {e}")

    await state.clear()
    await progress_message.answer(
        f"<b>Рассылка завершена</b>\n\n"
        f"Общее количество пользователей: {total_users}\n"
        f"✅ Успешно отправлено: {completed_users}\n"
        f"💀 Мертвые пользователи: {dead_users}",
        reply_markup=builder.as_markup()
    )

@admin.callback_query(F.data == 'stop_mailing')
async def stop_mailing(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(stop_flag=True)
    await callback.message.edit_text("❌ Рассылка остановлена")
    await callback.answer("Рассылка остановлена.")