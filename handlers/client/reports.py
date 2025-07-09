from utils.Imports import *
from .client import *
from .states import *

# ============ Репорты ============

@router.callback_query(F.data.startswith("report_"))
async def handle_report(callback: types.CallbackQuery, bot: Bot, state: FSMContext):
    parts = callback.data.split("_")

    if len(parts) == 3:
        # Первичная обработка — отображение причин
        task_type, task_id = parts[1], int(parts[2])

        buttons_by_type = {
            "channel": [
                ("Такого канала не существует", "channel|not|exist")
            ],
            "chat": [
                ("Такого чата не существует", "chat|not|exist")
            ],
            "reaction": [
                ("Такого канала не существует", "channel|not|exist"),
                ("Такого поста не существует", "post|not|exist"),
                ("Реакция недоступна", "reaction|unavailable")
            ],
            "link": [
                ("Бот не найден", "bot|not|found")
            ],
            "boost": [
                ("Канал не найден", "channel|not|found")
            ],
            "comment": [
                ("Такого канала не существует", "channel|not|exist"),
                ("Такого поста не существует", "post|not|exist")
            ]
        }

        builder = InlineKeyboardBuilder()
        for text, code in buttons_by_type.get(task_type, []):
            builder.add(InlineKeyboardButton(
                text=text,
                callback_data=f"report_{task_type}_{task_id}_reason_{code}"
            ))

        builder.add(InlineKeyboardButton(
            text="Другая причина",
            callback_data=f"report_{task_type}_{task_id}_other"
        ))
        builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data=f"chaneltask_{task_id}"))
        builder.adjust(1)

        await callback.message.edit_text("⚠️ Выберите причину репорта:", reply_markup=builder.as_markup())

    elif len(parts) == 5 and parts[3] == "reason":
        try:
            # Обработка выбранной причины
            task_type, task_id, reason_code = parts[1], int(parts[2]), parts[4]
            user_id = callback.from_user.id
            task = await DB.get_task_by_id(task_id)
            if not task:
                await callback.answer("Задание не найдено", show_alert=True)
                return

            reasons = {
                'channel|not|exist': "Такого канала не существует",
                'chat|not|exist': "Такого чата не существует",
                'post|not|exist': "Такого поста не существует",
                'reaction|unavailable': "Реакция недоступна",
                'bot|not|found': "Бот не найден",
                'channel|not_found': "Канал не найден"
            }
            reason_text = reasons.get(reason_code, "Неизвестная причина")

            try:
                chat = await bot.get_chat(task[2])
                title = chat.title
                link = chat.invite_link or f"https://t.me/{chat.username}" if chat.username else "Ссылка недоступна"
            except:
                title = "не удалось получить"
                link = "Ссылка недоступна"

            bonus = 1
            builder = InlineKeyboardBuilder()
            builder.add(
                InlineKeyboardButton(
                    text="✅ Принять и удалить",
                    callback_data=f"accept_report_{task_id}_{user_id}_{reason_code}_{bonus}"
                ))
            builder.add(
                InlineKeyboardButton(
                    text="❌ Отклонить",
                    callback_data=f"reject_report_{user_id}"
                )
            )
            builder.adjust(1)

            msg = (
                f"⚠️ <b>Новый репорт на задание</b>\n\n"
                f"<b>Тип задания:</b> {task_type}\n"
                f"<b>Причина:</b> {reason_text}\n"
                f"<b>ID задания:</b> {task_id}\n"
                f"<b>ID цели:</b> {task[2]}\n"
                f"<b>Ссылка:</b> {link}\n"
                f"<b>Название:</b> {title}\n"
                f"<b>От пользователя:</b> @{callback.from_user.username or '—'} (ID: {user_id})"
            )
            for admin in ADMINS_ID:
                try:
                    await bot.send_message(admin, msg, reply_markup=builder.as_markup())
                except Exception as e:
                    print(f"❌ Не удалось отправить сообщение админу {admin}: {e}")

            await callback.answer("Репорт отправлен администраторам", show_alert=True)
            await callback.message.delete()

            await DB.skip_task(user_id, task_id)
            all_tasks = task_cache.get('all_tasks', [])
            tasks = await get_available_tasks(user_id, all_tasks)

            if tasks:
                random.shuffle(tasks)
                kb = await generate_tasks_keyboard_chanel(tasks, bot)
                await callback.message.answer(
                    "📢 <b>Задания на каналы:</b>\n\n🎢 Каналы в списке располагаются по количеству необходимых подписчиков\n\n"
                    "⚡<i>Запрещено отписываться от канала раньше чем через 7 дней, в случае нарушения возможен штраф!</i>\n\n"
                    f"Доступно заданий: {len(tasks)}",
                    reply_markup=kb
                )
            else:
                await callback.message.answer(
                    "На данный момент доступных заданий нет, возвращайся позже 😉",
                    reply_markup=back_work_menu_kb(user_id)
                )
        except Exception as e:
            print(e)
            
    elif len(parts) == 4 and parts[3] == "other":
        await state.set_state(ReportStates.waiting_description)
        await state.update_data(task_id=int(parts[2]), task_type=parts[1])
        await callback.message.edit_text("Пожалуйста, опишите проблему:")


@router.message(ReportStates.waiting_description)
async def report_other_description(message: types.Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    task_id = data.get("task_id")
    task_type = data.get("task_type")
    user_id = message.from_user.id
    description = message.text

    task = await DB.get_task_by_id(task_id)
    if not task:
        await message.answer("Задание не найдено")
        await state.clear()
        return

    try:
        chat = await bot.get_chat(task[2])
        title = chat.title
        link = chat.invite_link or f"https://t.me/{chat.username}" if chat.username else "Ссылка недоступна"
    except:
        title = "не удалось получить"
        link = "Ссылка недоступна"

    bonus = 0
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="✅ Принять и удалить",
            callback_data=f"accept_report_{task_id}_{user_id}_custom_{bonus}"
        ),
        InlineKeyboardButton(
            text="❌ Отклонить",
            callback_data=f"reject_report_{user_id}"
        )
    )

    msg = (
        f"⚠️ <b>Новый репорт на задание</b>\n\n"
        f"<b>Тип задания:</b> {task_type}\n"
        f"<b>Причина:</b> {description}\n"
        f"<b>ID задания:</b> {task_id}\n"
        f"<b>ID цели:</b> {task[2]}\n"
        f"<b>Ссылка:</b> {link}\n"
        f"<b>Название:</b> {title}\n"
        f"<b>От пользователя:</b> @{message.from_user.username or '—'} (ID: {user_id})"
    )

    for admin in ADMINS_ID:
        try:
            await bot.send_message(admin, msg, reply_markup=builder.as_markup())
        except Exception as e:
            print(f"❌ Не удалось отправить сообщение админу {admin}: {e}")    
    await message.answer("Репорт успешно отправлен. Спасибо!")
    await DB.skip_task(user_id, task_id)
    await state.clear()


@router.callback_query(F.data.startswith("accept_report_"))
async def accept_report_handler(callback: types.CallbackQuery, bot: Bot):
    parts = callback.data.split("_")
    task_id = int(parts[2])
    user_id = int(parts[3])
    reason_code = parts[4]
    bonus = int(parts[5])

    task = await DB.get_task_by_id(task_id)
    if not task:
        await callback.answer("Задание не найдено")
        return

    creator_id = task[1]
    await DB.delete_task(task_id)

    reason_text = {
        'channel_not_exist': "Такого канала не существует",
        'chat_not_exist': "Такого чата не существует",
        'post_not_exist': "Такого поста не существует",
        'reaction_unavailable': "Реакция недоступна",
        'bot_not_found': "Бот не найден",
        'channel_not_found': "Канал не найден",
        'custom': "Указанная пользователем причина"
    }.get(reason_code, "Неизвестная причина")

    try:
        if bonus == 1:
            await DB.add_balance(user_id, 1000)
            await bot.send_message(user_id, f"✅ Ваш репорт принят\nЗадание удалено\nНачислено +1000 на баланс.")
        else:
            await bot.send_message(user_id, "✅ Ваш репорт принят\nЗадание удалено.")

        await bot.send_message(creator_id, f"❌ Ваше задание (ID {task_id}) было удалено\nПричина: {reason_text}")
    except Exception as e:
        print(f"Ошибка при отправке уведомлений: {e}")

    await callback.message.delete()
    await callback.answer("Репорт обработан")


@router.callback_query(F.data.startswith("reject_report_"))
async def reject_report_handler(callback: types.CallbackQuery, bot: Bot):
    user_id = int(callback.data.split("_")[2])
    try:
        await bot.send_message(user_id, "❌ Ваш репорт был отклонён\nСпасибо за участие.")
    except:
        pass
    await callback.message.delete()
    await callback.answer("Репорт отклонён")