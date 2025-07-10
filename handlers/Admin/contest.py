from datetime import datetime
from aiogram import F, types
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from utils.Imports import *
from .admin import admin
from .states import CreateContest



@admin.callback_query(F.data == 'admin_contest')
async def admin_contest_menu(callback: types.CallbackQuery):
    kb = InlineKeyboardBuilder()
    kb.button(text='ДА', callback_data='admin_contest_yes')
    kb.button(text='НЕТ', callback_data='admin_kb')
    kb.adjust(1)
    await callback.message.edit_text('Вы хотите запустить конкурс?', reply_markup=kb.as_markup())

@admin.callback_query(F.data == 'admin_contest_yes')
async def admin_contest_start(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text('В каком канале будет конкурс? Отправьте ссылку или юзернейм')
    await state.set_state(CreateContest.channel_url)

@admin.message(CreateContest.channel_url)
async def process_channel_url(message: types.Message, state: FSMContext):
    await state.update_data(channel_url=message.text)
    await message.answer('Сколько будет победителей? Введите число:')
    await state.set_state(CreateContest.winners_count)

@admin.message(CreateContest.winners_count)
async def process_winners_count(message: types.Message, state: FSMContext):
    try:
        winners_count = int(message.text)
        if winners_count <= 0:
            raise ValueError
        await state.update_data(winners_count=winners_count)
        
        # Создаем клавиатуру для выбора наград
        kb = InlineKeyboardBuilder()
        for i in range(1, winners_count + 1):
            kb.button(text=f"{i} место - MICO", callback_data=f"set_prize_{i}")
        kb.adjust(2)
        
        await message.answer(
            "Установите награды для каждого места. Нажмите на кнопку, чтобы изменить:",
            reply_markup=kb.as_markup()
        )
        await state.set_state(CreateContest.set_prizes)
    except ValueError:
        await message.answer("Пожалуйста, введите корректное положительное число!")

@admin.callback_query(F.data.startswith("set_prize_"), CreateContest.set_prizes)
async def set_prize_type(callback: types.CallbackQuery, state: FSMContext):
    place = int(callback.data.split("_")[2])
    await state.update_data(current_place=place)
    
    kb = InlineKeyboardBuilder()
    prize_types = ["MICO", "RUB", "MINING", "OTHER"]
    for prize in prize_types:
        kb.button(text=prize, callback_data=f"prize_type_{prize}")
    kb.adjust(2)
    
    await callback.message.edit_text(
        f"Выберите тип награды для {place} места:",
        reply_markup=kb.as_markup()
    )

@admin.callback_query(F.data.startswith("prize_type_"), CreateContest.set_prizes)
async def set_prize_amount(callback: types.CallbackQuery, state: FSMContext):
    prize_type = callback.data.split("_")[2]
    data = await state.get_data()
    place = data["current_place"]
    
    # Сохраняем выбранный тип награды
    prizes = data.get("prizes", {})
    prizes[str(place)] = {"type": prize_type}
    await state.update_data(prizes=prizes)
    
    await callback.message.edit_text(
        f"Введите количество награды для {place} места (тип: {prize_type}):\n"
        f"Для MINING можно только 1"
    )
    await state.set_state(CreateContest.set_prize_amounts)

@admin.message(CreateContest.set_prize_amounts)
async def process_prize_amount(message: types.Message, state: FSMContext):
    try:
        data = await state.get_data()
        place = data["current_place"]
        prize_type = data["prizes"][str(place)]["type"]
        
        if prize_type == "MINING":
            amount = 1
        else:
            amount = float(message.text)
            if amount <= 0:
                raise ValueError
        
        # Обновляем количество награды
        prizes = data["prizes"]
        prizes[str(place)]["amount"] = amount
        await state.update_data(prizes=prizes)
        
        # Проверяем, все ли награды установлены
        if len(prizes) == data["winners_count"]:
            await ask_contest_frequency(message, state)  # Изменено с ask_start_date
        else:
            # Продолжаем устанавливать награды
            kb = InlineKeyboardBuilder()
            for i in range(1, data["winners_count"] + 1):
                prize = prizes.get(str(i), {"type": "не выбрано"})
                kb.button(text=f"{i} место - {prize['type']}", callback_data=f"set_prize_{i}")
            kb.adjust(2)
            
            await message.answer(
                "Продолжите установку наград. Нажмите на кнопку, чтобы изменить:",
                reply_markup=kb.as_markup()
            )
            await state.set_state(CreateContest.set_prizes)
            
    except ValueError:
        await message.answer("Пожалуйста, введите корректное положительное число!")

async def ask_start_date(message: types.Message, state: FSMContext):
    kb = InlineKeyboardBuilder()
    kb.button(text="Сейчас", callback_data="start_now")
    kb.button(text="Запланировать", callback_data="schedule_start")
    kb.adjust(1)
    
    await message.answer(
        "Когда должен начаться конкурс?",
        reply_markup=kb.as_markup()
    )
    await state.set_state(CreateContest.start_date_choice)

@admin.callback_query(F.data == "start_now", CreateContest.start_date_choice)
async def start_now(callback: types.CallbackQuery, state: FSMContext):
    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    await state.update_data(start_date=now)
    await callback.message.edit_text(
        "Введите дату и время окончания конкурса в формате ДД.ММ.ГГГГ ЧЧ:ММ\n"
        "Например: 01.07.2025 15:00"
    )
    await state.set_state(CreateContest.end_date)

@admin.callback_query(F.data == "schedule_start", CreateContest.start_date_choice)
async def schedule_start(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "Введите дату и время начала конкурса в формате ДД.ММ.ГГГГ ЧЧ:ММ\n"
        "Например: 01.07.2025 15:00"
    )
    await state.set_state(CreateContest.start_date_input)

@admin.message(CreateContest.start_date_input)
async def process_start_date(message: types.Message, state: FSMContext):
    try:
        datetime.strptime(message.text, "%d.%m.%Y %H:%M")
        await state.update_data(start_date=message.text)
        await message.answer(
            "Введите дату и время окончания конкурса в формате ДД.ММ.ГГГГ ЧЧ:ММ\n"
            "Например: 01.07.2025 15:00"
        )
        await state.set_state(CreateContest.end_date)
    except ValueError:
        await message.answer("Неверный формат даты. Пожалуйста, используйте формат ДД.ММ.ГГГГ ЧЧ:ММ")

@admin.message(CreateContest.end_date)
async def process_end_date(message: types.Message, state: FSMContext):
    try:
        datetime.strptime(message.text, "%d.%m.%Y %H:%M")
        await state.update_data(end_date=message.text)
        await ask_conditions(message, state)
    except ValueError:
        await message.answer("Неверный формат даты. Пожалуйста, используйте формат ДД.ММ.ГГГГ ЧЧ:ММ")

async def ask_conditions(message: types.Message, state: FSMContext):
    data = await state.get_data()
    
    kb = InlineKeyboardBuilder()
    
    # Получаем текущие значения условий (по умолчанию False)
    sub_channel = data.get("sub_channel", False)
    is_bot_user = data.get("is_bot_user", False)
    is_active_user = data.get("is_active_user", False)
    
    # Кнопки с галочками ✓
    kb.button(
        text=f"{'✓ ' if sub_channel else ''}Подписаться на канал", 
        callback_data="set_condition_sub_channel"
    )
    kb.button(
        text=f"{'✓ ' if is_bot_user else ''}Быть пользователем бота", 
        callback_data="set_condition_is_bot_user"
    )
    kb.button(
        text=f"{'✓ ' if is_active_user else ''}Быть активным пользователем", 
        callback_data="set_condition_is_active_user"
    )
    
    kb.button(text="✅ Готово", callback_data="conditions_done")
    kb.adjust(1)
    
    # Устанавливаем общее состояние для выбора условий
    await state.set_state(CreateContest.conditions)
    
    await message.answer(
        "Выберите условия участия (✓ — выбрано):",
        reply_markup=kb.as_markup()
    )

# Обработчики теперь работают в общем состоянии условий
@admin.callback_query(F.data == "set_condition_sub_channel", CreateContest.conditions)
async def toggle_sub_channel(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    current_value = data.get("sub_channel", False)
    
    if not current_value:
        # Если включаем подписку на канал, запрашиваем ссылку
        await callback.message.edit_text(
            "Введите ссылку или юзернейм канала для подписки (например, @channel или https://t.me/channel):"
        )
        await state.set_state(CreateContest.channel_sub_input)
        await state.update_data(editing_condition="sub_channel")
    else:
        # Если выключаем подписку на канал
        await state.update_data(sub_channel=False, channel_url=None)
        await ask_conditions(callback.message, state)
    await callback.answer()

@admin.message(CreateContest.channel_sub_input)
async def process_channel_sub(message: types.Message, state: FSMContext):
    channel_url = message.text.strip()
    data = await state.get_data()
    condition = data.get("editing_condition")
    
    if condition == "sub_channel":
        await state.update_data(
            sub_channel=True,
            channel_url=channel_url
        )
    elif condition == "additional_channel":
        additional_channels = data.get("additional_channels", [])
        additional_channels.append(channel_url)
        await state.update_data(
            additional_channels=additional_channels
        )
    
    await ask_conditions(message, state)

@admin.callback_query(F.data == "set_condition_additional_channel", CreateContest.conditions)
async def add_additional_channel(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "Введите ссылку или юзернейм дополнительного канала для подписки:"
    )
    await state.set_state(CreateContest.channel_sub_input)
    await state.update_data(editing_condition="additional_channel")
    await callback.answer()

async def ask_conditions(message: types.Message, state: FSMContext):
    data = await state.get_data()
    
    kb = InlineKeyboardBuilder()
    
    # Основные условия
    sub_channel = data.get("sub_channel", False)
    channel_url = data.get("channel_url", "")
    is_bot_user = data.get("is_bot_user", False)
    is_active_user = data.get("is_active_user", False)
    
    # Дополнительные каналы
    additional_channels = data.get("additional_channels", [])
    
    # Кнопки с галочками ✓
    kb.button(
        text=f"{'✓ ' if sub_channel else ''}Подписаться на канал", 
        callback_data="set_condition_sub_channel"
    )
    
    # Кнопки для дополнительных каналов
    for i, channel in enumerate(additional_channels, 1):
        kb.button(
            text=f"✓ Доп. канал {i}",
            callback_data=f"edit_additional_channel_{i}"
        )
    
    kb.button(
        text="➕ Добавить канал", 
        callback_data="set_condition_additional_channel"
    )
    
    kb.button(
        text=f"{'✓ ' if is_bot_user else ''}Быть пользователем бота", 
        callback_data="set_condition_is_bot_user"
    )
    kb.button(
        text=f"{'✓ ' if is_active_user else ''}Быть активным пользователем", 
        callback_data="set_condition_is_active_user"
    )
    
    kb.button(text="✅ Готово", callback_data="conditions_done")
    kb.adjust(1)
    
    # Формируем текст с текущими каналами
    channels_text = ""
    if sub_channel:
        channels_text += f"\n\nОсновной канал: {channel_url}"
    if additional_channels:
        channels_text += "\nДополнительные каналы:"
        for i, channel in enumerate(additional_channels, 1):
            channels_text += f"\n{i}. {channel}"
    
    await message.answer(
        f"Выберите условия участия (✓ — выбрано):{channels_text}",
        reply_markup=kb.as_markup()
    )
    await state.set_state(CreateContest.conditions)

@admin.callback_query(F.data.startswith("edit_additional_channel_"), CreateContest.conditions)
async def edit_additional_channel(callback: types.CallbackQuery, state: FSMContext):
    channel_index = int(callback.data.split("_")[-1]) - 1
    data = await state.get_data()
    additional_channels = data.get("additional_channels", [])
    
    if 0 <= channel_index < len(additional_channels):
        # Удаляем выбранный канал
        additional_channels.pop(channel_index)
        await state.update_data(additional_channels=additional_channels)
    
    await ask_conditions(callback.message, state)
    await callback.answer()


@admin.callback_query(F.data == "set_condition_is_bot_user", CreateContest.conditions)
async def toggle_is_bot_user(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    current_value = data.get("is_bot_user", False)
    await state.update_data(is_bot_user=not current_value)
    
    await ask_conditions(callback.message, state)
    await callback.answer()

@admin.callback_query(F.data == "set_condition_is_active_user", CreateContest.conditions)
async def toggle_is_active_user(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    current_value = data.get("is_active_user", False)
    await state.update_data(is_active_user=not current_value)
    
    await ask_conditions(callback.message, state)
    await callback.answer()

@admin.callback_query(F.data == "conditions_done", CreateContest.conditions)
async def conditions_done(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    
    # Формируем список выбранных условий
    selected_conditions = []
    if data.get("sub_channel"):
        selected_conditions.append("sub_channel")
    if data.get("is_bot_user"):
        selected_conditions.append("is_bot_user")
    if data.get("is_active_user"):
        selected_conditions.append("is_active_user")
    
    # Сохраняем дополнительные каналы
    additional_channels = data.get("additional_channels", [])
    
    await state.update_data(
        conditions=selected_conditions,
        additional_channels=additional_channels
    )
    
    await callback.message.edit_text(
        "Введите дополнительные условия (или '-' чтобы пропустить):"
    )
    await state.set_state(CreateContest.additional_conditions)


@admin.message(CreateContest.additional_conditions)
async def process_additional_conditions(message: types.Message, state: FSMContext):
    additional = message.text if message.text != "-" else ""
    await state.update_data(additional_conditions=additional)
    await ask_contest_content(message, state)

async def ask_contest_content(message: types.Message, state: FSMContext):
    kb = InlineKeyboardBuilder()
    kb.button(text="Использовать contest.png", callback_data="use_default_image")
    kb.button(text="Пропустить", callback_data="skip_image")
    kb.adjust(1)
    
    await message.answer(
        "Отправьте текст конкурса и/или изображение:\n"
        "Вы можете использовать стандартное изображение или пропустить этот шаг",
        reply_markup=kb.as_markup()
    )
    await state.set_state(CreateContest.contest_content)

@admin.callback_query(F.data == "use_default_image", CreateContest.contest_content)
async def use_default_image(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(image_path="contest.png")
    await callback.message.edit_text(
        "Отправьте текст конкурса (или '-' чтобы пропустить):"
    )
    await state.set_state(CreateContest.contest_text)

@admin.callback_query(F.data == "skip_image", CreateContest.contest_content)
async def skip_image(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(image_path=None)
    await callback.message.edit_text(
        "Отправьте текст конкурса (или '-' чтобы пропустить):"
    )
    await state.set_state(CreateContest.contest_text)

@admin.message(CreateContest.contest_content)
async def process_contest_content(message: types.Message, state: FSMContext):
    if message.photo:
        # Сохраняем фото (здесь нужно реализовать сохранение файла)
        file_id = message.photo[-1].file_id
        # Здесь должен быть код для сохранения файла и получения пути
        image_path = f"contests/{file_id}.jpg"
        await state.update_data(image_path=image_path)
    
    if message.text and message.text != "-":
        await state.update_data(contest_text=message.text)
    
    data = await state.get_data()
    if "contest_text" not in data:
        await message.answer("Отправьте текст конкурса (или '-' чтобы пропустить):")
        await state.set_state(CreateContest.contest_text)
    else:
        await confirm_contest(message, state)

@admin.message(CreateContest.contest_text)
async def process_contest_text(message: types.Message, state: FSMContext):
    text = message.text if message.text != "-" else None
    await state.update_data(contest_text=text)
    await confirm_contest(message, state)

async def confirm_contest(message: types.Message, state: FSMContext):
    data = await state.get_data()
    
    # Форматируем даты
    start_date = data.get('start_date', 'сразу')
    if start_date != 'сразу':
        start_date = datetime.strptime(start_date, "%d.%m.%Y %H:%M").strftime("%H:%M, %d.%m.%Y MSK")
    
    end_date = datetime.strptime(data['end_date'], "%d.%m.%Y %H:%M").strftime("%H:%M, %d.%m.%Y MSK")
    
    # Формируем текст подтверждения в новом формате
    text = "🎉 Проверьте данные конкурса 🎉\n\n"
    text += f"📢 Канал: {data['channel_url']}\n"
    text += f"🏆 Количество победителей: {data['winners_count']}\n\n"
    text += "💰 Призы:\n"
    
    # Сортируем призы по местам
    for place, prize in sorted(data.get("prizes", {}).items(), key=lambda x: int(x[0])):
        text += f"  {place} место: {prize['amount']} {prize['type']}\n"
    
    text += f"\n⏳ Начало: {start_date}\n"
    text += f"⏰ Окончание: {end_date}\n\n"
    
    # Формируем условия участия
    conditions = data.get("conditions", [])
    additional_conditions = data.get('additional_conditions', '')
    
    if conditions or additional_conditions:
        text += "📌 Условия участия:\n\n"
        condition_num = 1
        
        if "sub_channel" in conditions:
            text += f"{condition_num}. ✅ Подписаться на канал ({data['channel_url']})\n"
            condition_num += 1
        if "is_bot_user" in conditions:
            text += f"{condition_num}. 📲 Быть активным пользователем нашего бота\n"
            condition_num += 1
        if "is_active_user" in conditions:
            text += f"{condition_num}. 🔥 Быть активным участником сообщества\n"
            condition_num += 1
        if additional_conditions and additional_conditions != '-':
            text += f"{condition_num}. 📌 {additional_conditions}\n"
    
    text += "\n⚠️ Проверьте все данные перед подтверждением!"
    
    # Создаем клавиатуру
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Подтвердить", callback_data="confirm_contest")
    kb.button(text="❌ Отменить", callback_data="cancel_contest")
    kb.adjust(1)
    
    try:
        if data.get("image_path"):
            if os.path.exists(data["image_path"]):
                with open(data["image_path"], 'rb') as photo:
                    await message.answer_photo(
                        photo=types.BufferedInputFile(photo.read(), filename="contest.jpg"),
                        caption=text,
                        reply_markup=kb.as_markup()
                    )
            else:
                await message.answer(
                    "⚠️ Файл изображения не найден\n\n" + text,
                    reply_markup=kb.as_markup()
                )
        else:
            await message.answer(
                text,
                reply_markup=kb.as_markup()
            )
    except Exception as e:
        await message.answer(
            f"⚠️ Произошла ошибка:\n{str(e)}\n\n{text}",
            reply_markup=kb.as_markup()
        )

@admin.callback_query(F.data == "confirm_contest")
async def save_contest(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    
    try:
        # Подготавливаем данные для сохранения
        conditions = {
            "auto_conditions": data.get("conditions", []),
            "additional": data.get("additional_conditions", ""),
            "additional_channels": data.get("additional_channels", [])
        }
        
        # Определяем статус конкурса
        start_date = data.get("start_date")
        frequency = data.get("frequency", "once")
        
        if frequency == "once":
            if start_date == "сразу" or start_date == datetime.now().strftime("%d.%m.%Y %H:%M"):
                status = "active"
            else:
                status = "waiting"
        else:
            status = "recurring"
        
        # Формируем данные конкурса
        contest_data = {
            "channel_url": data["channel_url"],
            "winners_count": data["winners_count"],
            "prizes": data["prizes"],
            "start_date": data.get("start_date", datetime.now().strftime("%d.%m.%Y %H:%M")),
            "end_date": data["end_date"],
            "conditions": json.dumps(conditions, ensure_ascii=False),
            "contest_text": data.get("contest_text", ""),
            "image_path": data.get("image_path"),
            "status": status,
            "frequency": frequency,
            "selected_days": list(data.get("selected_days", [])),
            "total_occurrences": data.get("total_occurrences", 1),
            "current_occurrence": 1
        }

        # Сохраняем конкурс в базу данных
        contest_id = await Contest.create_recurring_contest(**contest_data)
        
        # Если конкурс активный - публикуем сразу
        if status == "active":
            try:
                # Формируем текст конкурса
                contest_text = await generate_contest_text(contest_data, conditions)
                
                # Создаем кнопку "Участвовать"
                bot_username = (await bot.get_me()).username
                participate_kb = InlineKeyboardBuilder()
                participate_kb.button(
                    text="🎁 Участвовать", 
                    url=f"https://t.me/{bot_username}?start=contest_{contest_id}"
                )
                
                # Получаем username канала
                channel_url = contest_data["channel_url"]
                channel_username = channel_url.replace("@", "").replace("https://t.me/", "")
                
                # Проверяем наличие изображения
                image_path = contest_data.get("image_path")
                
                if image_path and os.path.exists(image_path):
                    with open(image_path, 'rb') as photo:
                        # Отправляем сообщение с фото
                        message = await bot.send_photo(
                            chat_id=f"@{channel_username}",
                            photo=types.BufferedInputFile(photo.read(), filename="contest.jpg"),
                            caption=contest_text,
                            reply_markup=participate_kb.as_markup(),
                            parse_mode="HTML"
                        )
                else:
                    # Отправляем текстовое сообщение
                    message = await bot.send_message(
                        chat_id=f"@{channel_username}",
                        text=contest_text,
                        reply_markup=participate_kb.as_markup(),
                        parse_mode="HTML"
                    )
                
                # Сохраняем данные сообщения
                await Contest.update_contest_message_id(contest_id, message.message_id)
                await Contest.update_contest_message_text(contest_id, contest_text)
                
                await callback.answer("✅ Конкурс успешно создан и опубликован в канале!", show_alert=True)

            except Exception as e:
                error_msg = f"❌ Ошибка при публикации: {str(e)}"
                print(error_msg)
                await callback.answer(error_msg, show_alert=True)
        else:
            if frequency == "once":
                await callback.answer(
                    f"⏳ Конкурс запланирован на {contest_data['start_date']}. "
                    "Он будет автоматически опубликован в указанное время.",
                    show_alert=True
                )
            else:
                await callback.answer(
                    "✅ Регулярный конкурс успешно создан! "
                    "Он будет автоматически публиковаться по расписанию.",
                    show_alert=True
                )
                
    except Exception as e:
        error_msg = f"❌ Критическая ошибка при создании конкурса: {str(e)}"
        print(error_msg)
        await callback.answer(error_msg, show_alert=True)
    finally:
        await state.clear()
        

async def generate_contest_text(contest_data, conditions):
    from datetime import datetime

    # 1. Форматируем дату окончания
    end_date = datetime.strptime(contest_data["end_date"], "%d.%m.%Y %H:%M")
    formatted_end_date = end_date.strftime("%H:%M, %d.%m.%Y MSK")
    
    # 2. Формируем список призов
    prizes_text = []
    for place, prize in sorted(contest_data["prizes"].items(), key=lambda x: int(x[0])):
        prizes_text.append(f"{place} место: {prize['amount']} {prize['type']}")
    
    # 3. Формируем условия участия
    conditions_text = ""
    condition_number = 1
    
    auto_conditions = conditions.get("auto_conditions", [])
    
    # 3.1 Подписка на основной канал
    if "sub_channel" in auto_conditions:
        conditions_text += (
            f'{condition_number}. ✅ Подписаться на <a href="{contest_data["channel_url"]}">канал</a>\n'
        )
        condition_number += 1
    
    # 3.2 Подписка на дополнительные каналы
    additional_channels = conditions.get("additional_channels", [])
    for channel in additional_channels:
        conditions_text += (
            f'{condition_number}. ✅ Подписаться на <a href="{channel}">канал</a>\n'
        )
        condition_number += 1
    
    # 3.3 Быть пользователем бота
    if "is_bot_user" in auto_conditions:
        conditions_text += (
            f"{condition_number}. 📲 Быть пользователем нашего бота\n"
        )
        condition_number += 1

    # 3.4 Быть активным пользователем
    if "is_active_user" in auto_conditions:
        conditions_text += (
            f"{condition_number}. 🔥 Быть активным участником сообщества\n"
        )
        condition_number += 1

    # 3.5 Дополнительные условия
    additional_conditions = conditions.get("additional", "")
    if additional_conditions and additional_conditions != "-":
        # Пробуем декодировать Unicode-последовательности
        if "\\u" in additional_conditions:
            try:
                additional_conditions = additional_conditions.encode().decode("unicode-escape")
            except Exception:
                pass
        conditions_text += f"{condition_number}. 📌 {additional_conditions}\n"

    # 4. Формируем финальный текст конкурса
    return (
        f"🎉 Конкурс для всех участников! 🎉\n\n"
        f"Призы:\n" + "\n".join(prizes_text) + "\n\n"
        f"Условия участия:\n\n"
        f"{conditions_text.strip()}\n\n"
        f"📅 Итоги конкурса будут объявлены {formatted_end_date}. Не упустите свой шанс!\n\n"
        f"✨ За каждого приглашенного друга вы увеличиваете свои шансы на победу! "
        f"Делитесь информацией и побеждайте вместе с нами! 🍀\n\n"
        f"Удачи всем участникам! 💪💰\n\n"
        f"Участников: 0\n"
        f"Призовых мест: {contest_data['winners_count']}\n"
        f"Дата розыгрыша: {formatted_end_date}"
    )


async def check_finished_contests(bot: Bot):
    """Проверяет и завершает конкурсы с истекшим сроком"""
    current_time = datetime.now()
    print(f"Проверка конкурсов в {current_time} (check_finished_contests)")
    
    # Получаем активные конкурсы с истекшим сроком
    print("Получение активных конкурсов...")
    contests = await Contest.get_active_contests_before(current_time)
    print(f"Найдено {len(contests)} конкурсов для проверки")
    
    for contest in contests:
        print(contest['id'])
        print(f"Обработка конкурса ID: {contest['id']}")
        try:
            await finish_contest(contest['id'], bot)
        except Exception as e:
            print(f"Ошибка при завершении конкурса {contest['id']} (check_finished_contests): {e}")
            import traceback
            traceback.print_exc()

async def finish_contest(contest_id: int, bot: Bot):
    """Завершает конкурс и выбирает победителей"""
    print(f"Начало завершения конкурса {contest_id} (finish_contest)")
    contest = await Contest.get_contest2(contest_id)
    if not contest:
        print(f"Конкурс {contest_id} не найден")
        return
    
    if contest.get('status') == 'finished':
        print(f"Конкурс {contest_id} уже завершен")
        return
    
    print(f"Завершение конкурса {contest_id} (finish_contest)")
    
    # 1. Получаем участников
    print("Получение участников...")
    participants = await Contest.get_participants(contest_id)
    print(f"Найдено {len(participants)} участников")
    
    if not participants:
        print("Нет участников, обработка пустого конкурса")
        await handle_no_participants(contest, bot)
        return
    
    # 2. Выбираем победителей
    print("Выбор победителей...")
    winners_count = contest['winners_count']
    winners = select_winners(participants, winners_count)
    print(f"Выбрано {len(winners)} победителей")
    
    # 3. Награждаем победителей
    winners_info = []
    prizes = json.loads(contest['prizes'])
    print(f"Призы для конкурса: {prizes}")
    
    for place, (user_id, username) in enumerate(winners, start=1):
        print(f"Обработка победителя {username} (место {place})")
        prize = prizes.get(str(place), {})
        if not prize:
            print(f"Нет приза для места {place}")
            continue
            
        # Сохраняем победителя
        print("Сохранение победителя в БД...")
        await Contest.add_winner(
            contest_id=contest_id,
            user_id=user_id,
            place=place,
            prize_type=prize['type'],
            prize_amount=prize['amount']
        )
        
        # Начисляем награду
        print(f"Начисление награды: {prize['type']} {prize['amount']}")
        await award_winner(user_id, prize['type'], prize['amount'])
        
        # Формируем информацию о победителе
        winners_info.append({
            'place': place,
            'username': username,
            'prize': prize
        })
        
        # Уведомляем победителя
        print("Отправка уведомления победителю...")
        await notify_winner(bot, user_id, place, prize)
    
    # 4. Обновляем статус конкурса
    print("Обновление статуса конкурса...")
    await Contest.update_contest_status(contest_id, 'finished')
    
    # 5. Публикуем результаты
    print("Публикация результатов...")
    await publish_results(bot, contest, winners_info)

def select_winners(participants: list, winners_count: int) -> list:
    """Выбирает случайных победителей"""
    print(f"Выбор {winners_count} победителей из {len(participants)} участников")
    if winners_count >= len(participants):
        print("Все участники становятся победителями")
        return participants
    
    return random.sample(participants, winners_count)

async def award_winner(user_id: int, prize_type: str, amount: float):
    """Начисляет награду победителю"""
    print(f"Начисление награды пользователю {user_id}: {amount} {prize_type}")
    if prize_type == 'MICO':
        await DB.add_balance(user_id, amount)
    elif prize_type == 'RUB':
        await DB.add_rub_balance(user_id, amount)
    elif prize_type == 'MINING':
        await DB.add_mining(user_id)
    else:
        print(f"Неизвестный тип приза: {prize_type}")

async def notify_winner(bot: Bot, user_id: int, place: int, prize: dict):
    """Отправляет уведомление победителю"""
    print(f"Попытка уведомить пользователя {user_id} о победе")
    try:
        await bot.send_message(
            chat_id=user_id,
            text=f"🎉 Поздравляем! Вы заняли {place} место в конкурсе!\n\n"
                 f"Ваш приз: {prize['amount']} {prize['type']} уже на вашем счету!"
        )
        print("Уведомление успешно отправлено")
    except Exception as e:
        print(f"Не удалось уведомить победителя {user_id}: {e}")
        import traceback
        traceback.print_exc()

async def publish_results(bot: Bot, contest: dict, winners: list):
    """Публикует результаты конкурса в канале и выдает награды победителям"""
    print(f"Публикация результатов конкурса {contest['id']}")
    
    try:
        # Выдача наград победителям
        await award_winners(winners, contest['prizes'])
        
        channel_username = contest['channel_url'].replace('https://t.me/', '').replace('@', '')
        message_id = contest['message_id']
        print(f"Канал для публикации: {channel_username}, message_id: {message_id}")
        
        # Получаем текущий текст сообщения
        try:
            message = str(contest['message_text'])
            original_text = message
        except Exception as e:
            print(f"Не удалось получить исходное сообщение: {e}")
            original_text = None
        
        if original_text:
            updated_text = original_text
            
            # Добавляем пометку о завершении конкурса
            if "(завершён)" not in updated_text:
                updated_text = updated_text.replace(
                    f"Дата розыгрыша: {contest['end_date']} MSK",
                    f"Дата розыгрыша: {contest['end_date']} MSK <b>(завершён)</b>"
                )
            
            # Добавляем информацию о победителях
            winners_section = "\n\n🏆 Победители розыгрыша:\n"
            for winner in winners:
                winners_section += f"{winner['place']}. <a href='@{winner['username']}'>{winner['username']}</a>\n"
            
            winners_section += "\n🎁 Награды выданы победителям!"
            updated_text += winners_section
            
            print(f"Обновленный текст сообщения:\n{updated_text}")
            
            try:
                await bot.edit_message_text(
                    chat_id=f"@{channel_username}",
                    message_id=message_id,
                    text=updated_text,
                    parse_mode="HTML"
                )
            except Exception as e:
                print(f"Не удалось отредактировать текст сообщения (попытка редактирования подписи): {e}")
                try:
                    await bot.edit_message_caption(
                        chat_id=f"@{channel_username}",
                        message_id=message_id,
                        caption=updated_text,
                        parse_mode="HTML"
                    )
                except Exception as e:
                    print(f"Не удалось отредактировать подпись сообщения: {e}")
                    raise
        else:
            print("Не удалось получить исходный текст сообщения для редактирования")
            raise Exception("Original message text not found")
        
    except Exception as e:
        print(f"Не удалось опубликовать результаты (publish_results): {e}")
        import traceback
        traceback.print_exc()
        # В случае ошибки публикуем результаты как новое сообщение
        await publish_results_as_new_message(bot, contest, winners)


async def award_winners(winners: list, prizes: str):
    """Выдает награды победителям конкурса"""
    print("Начало выдачи наград победителям...")
    
    try:
        # Преобразуем строку с призами в словарь
        if isinstance(prizes, str):
            prizes = json.loads(prizes)
            
        for winner in winners:
            print(winner)
            place = winner['place']
            username = winner['username']
            user_id = str(await DB.get_id_from_username(username)).replace("(", "").replace(")", "").replace(",","")
            
            try:
                # Определяем тип награды и выдаем соответствующий приз
                print(f"Призы: {prizes}")
                
                # Получаем приз для текущего места (формат: {"1": {"type": "MICO", "amount": 111111.0}})
                prize_info = prizes.get(str(place))
                if not prize_info:
                    print(f"Для места {place} не указан приз!")
                    continue
                    
                prize_type = prize_info.get('type')
                prize_amount = prize_info.get('amount')
                
                if not prize_type or not prize_amount:
                    print(f"Для места {place} не указан тип или количество приза!")
                    continue
                
                print(f"Выдача награды пользователю {username}: {prize_amount} {prize_type}")
                
                # Приводим prize_amount к float на случай, если он пришел как строка
                prize_amount = float(prize_amount)
                
                if prize_type.upper() == 'MICO':
                    await DB.add_balance(user_id, prize_amount)
                elif prize_type.upper() == 'MINING':
                    await DB.add_mining(user_id, int(prize_amount))  # mining обычно целое число
                elif prize_type.upper() == 'RUB':
                    await DB.add_rub_balance(user_id, prize_amount)
                else:
                    print(f"Неизвестный тип награды: {prize_type}")
                    
                print(f"Успешно выдана награда для места {place} пользователю {username}")
                
            except Exception as e:
                print(f"Ошибка при выдаче награды пользователю {username} (ID: {user_id}): {e}")
                import traceback
                traceback.print_exc()
                continue
                
    except json.JSONDecodeError:
        print("Ошибка декодирования JSON призов")
    except Exception as e:
        print(f"Общая ошибка в award_winners: {e}")
        import traceback
        traceback.print_exc()

async def publish_results_as_new_message(bot: Bot, contest: dict, winners: list):
    """Публикует результаты как новое сообщение, если не удалось отредактировать исходное"""
    try:
        channel_username = contest['channel_url'].replace('https://t.me/', '').replace('@', '')
        end_date = datetime.strptime(contest['end_date'], '%d.%m.%Y %H:%M').strftime('%H:%M, %d.%m.%Y')
        
        text = (
            f"🏆 Конкурс завершен! Результаты 🏆\n\n"
            f"Дата окончания: {end_date}\n"
            f"Всего участников: {len(await Contest.get_participants(contest['id']))}\n\n"
            f"Победители:\n"
        )
        
        for winner in winners:
            text += (
                f"{winner['place']}. <a href=@{winner['username']}'>"
                f"{winner['username']}</a> - "
                f"{winner['prize']['amount']} {winner['prize']['type']}\n"
            )
        
        text += "\nПоздравляем победителей! 🎉\nПризы уже начислены на счета."
        
        await bot.send_message(
            chat_id=f"@{channel_username}",
            text=text,
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"Не удалось опубликовать результаты как новое сообщение: {e}")

async def handle_no_participants(contest: dict, bot: Bot):
    """Обрабатывает случай, когда нет участников"""
    print(f"Обработка конкурса без участников {contest['id']}")
    await Contest.update_contest_status(contest['id'], 'finished')
    channel_username = contest['channel_url'].replace('https://t.me/', '').replace('@', '')
    
    try:
        print(f"Отправка сообщения об отсутствии участников в канал {channel_username}")
        await bot.send_message(
            chat_id=f"@{channel_username}",
            text="Конкурс завершен, но не было участников 😢"
        )
    except Exception as e:
        print(f"Не удалось отправить сообщение о завершении (handle_no_participants): {e}")
        import traceback
        traceback.print_exc()

# В функции on_startup (при запуске бота)
async def on_startup(bot: Bot):
    """Запускает фоновые задачи при старте бота"""
    print("Запуск фоновой задачи проверки конкурсов")
    asyncio.create_task(run_contest_checker(bot))

@admin.callback_query(F.data == "cancel_contest")
async def cancel_contest(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Создание конкурса отменено")
    await state.clear()


async def run_contest_checker(bot: Bot):
    """Запускает периодическую проверку конкурсов"""
    print("Запуск проверки конкурсов (run_contest_checker)")
    while True:
        try:
            print("Начало новой итерации проверки конкурсов")
            await check_waiting_contests(bot)  # Сначала проверяем ожидающие конкурсы
            await check_finished_contests(bot)  # Затем проверяем завершенные
        except Exception as e:
            print(f"Ошибка в проверке конкурсов (run_contest_checker): {e}")
            import traceback
            traceback.print_exc()
        await asyncio.sleep(60)  # Проверка каждую минуту
        print("Ожидание 60 секунд до следующей проверки")

async def check_waiting_contests(bot: Bot):
    """Проверяет и активирует запланированные конкурсы"""
    current_time = datetime.now()
    print(f"Проверка запланированных конкурсов в {current_time}")
    
    # Получаем ожидающие конкурсы, которые должны начаться
    contests = await Contest.get_waiting_contests_before(current_time)
    print(f"Найдено {len(contests)} ожидающих конкурсов для активации")
    
    for contest in contests:
        print(f"Активация конкурса ID: {contest['id']}")
        try:
            await activate_contest(contest, bot)
        except Exception as e:
            print(f"Ошибка при активации конкурса {contest['id']}: {e}")
            import traceback
            traceback.print_exc()

async def activate_contest(contest: dict, bot: Bot):
    """Активирует запланированный конкурс"""
    print(f"Активация конкурса {contest['id']}")
    
    try:
        # Обновляем статус конкурса
        await Contest.update_contest_status(contest['id'], 'active')
        
        # Получаем данные конкурса
        try:
            conditions = json.loads(contest['conditions'])
        except json.JSONDecodeError:
            conditions = {}
            
        additional_channels = conditions.get('additional_channels', [])
        
        # Формируем текст конкурса
        contest_text = await generate_contest_text({
            'channel_url': contest['channel_url'],
            'winners_count': contest['winners_count'],
            'prizes': json.loads(contest['prizes']),
            'start_date': contest['start_date'],
            'end_date': contest['end_date'],
            'conditions': contest['conditions'],
            'contest_text': contest['contest_text']
        }, conditions)
        
        # Проверяем HTML-разметку
        from aiogram.utils.text_decorations import html_decoration as hd
        try:
            safe_text =(contest_text)
        except Exception as e:
            print(f"Ошибка при экранировании текста: {e}")
            safe_text = contest_text  # Используем оригинальный текст, если не удалось экранировать
        
        # Создаем кнопку "Участвовать"
        bot_username = (await bot.get_me()).username
        participate_kb = InlineKeyboardBuilder()
        participate_kb.button(
            text="🎁 Участвовать", 
            url=f"https://t.me/{bot_username}?start=contest_{contest['id']}"
        )
        
        # Получаем username канала
        channel_url = contest['channel_url']
        channel_username = channel_url.replace("@", "").replace("https://t.me/", "")
        
        try:
            # Проверяем права бота в канале
            chat_member = await bot.get_chat_member(
                chat_id=f"@{channel_username}",
                user_id=(await bot.get_me()).id
            )
            if chat_member.status not in ['administrator', 'creator']:
                raise Exception("Bot is not admin in the channel")
                
            # Проверяем наличие изображения
            image_path = contest.get("image_path")
            
            if image_path and os.path.exists(image_path):
                with open(image_path, 'rb') as photo:
                    # Отправляем сообщение с фото
                    message = await bot.send_photo(
                        chat_id=f"@{channel_username}",
                        photo=types.BufferedInputFile(photo.read(), filename="contest.jpg"),
                        caption=safe_text,
                        reply_markup=participate_kb.as_markup(),
                        parse_mode="HTML"
                    )
            else:
                # Отправляем текстовое сообщение
                message = await bot.send_message(
                    chat_id=f"@{channel_username}",
                    text=safe_text,
                    reply_markup=participate_kb.as_markup(),
                    parse_mode="HTML"
                )
            
            # Сохраняем данные сообщения
            await Contest.update_contest_message_id(contest['id'], message.message_id)
            await Contest.update_contest_message_text(contest['id'], contest_text)
            
            print(f"Конкурс {contest['id']} успешно активирован и опубликован")
            
        except Exception as e:
            print(f"Ошибка при публикации конкурса {contest['id']}: {e}")
            # Возвращаем статус waiting для повторной попытки
            await Contest.update_contest_status(contest['id'], 'waiting')
            raise
            
    except json.JSONDecodeError as e:
        print(f"Ошибка декодирования JSON для конкурса {contest['id']}: {e}")
        await Contest.update_contest_status(contest['id'], 'error')
    except Exception as e:
        print(f"Неизвестная ошибка при активации конкурса {contest['id']}: {e}")
        await Contest.update_contest_status(contest['id'], 'error')







async def ask_contest_frequency(message: types.Message, state: FSMContext):
    kb = InlineKeyboardBuilder()
    kb.button(text="Одноразовый", callback_data="frequency_once")
    kb.button(text="Ежедневный", callback_data="frequency_daily")
    kb.button(text="Еженедельный", callback_data="frequency_weekly")
    kb.adjust(1)
    
    await message.answer(
        "Выберите частоту проведения конкурса:",
        reply_markup=kb.as_markup()
    )
    await state.set_state(CreateContest.contest_frequency)

@admin.callback_query(F.data.startswith("frequency_"), CreateContest.contest_frequency)
async def process_frequency(callback: types.CallbackQuery, state: FSMContext):
    frequency = callback.data.split("_")[1]
    await state.update_data(frequency=frequency)
    
    if frequency == "once":
        await ask_start_date(callback.message, state)
    elif frequency == "daily":
        await callback.message.answer(
            "Введите количество дней, в течение которых будет повторяться конкурс:"
        )
        await state.set_state(CreateContest.total_occurrences)
    elif frequency == "weekly":
        await ask_days_of_week(callback.message, state)

async def ask_days_of_week(message: types.Message, state: FSMContext):
    kb = InlineKeyboardBuilder()
    days = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    for i, day in enumerate(days, 1):
        kb.button(text=day, callback_data=f"day_{i}")
    kb.button(text="✅ Готово", callback_data="days_done")
    kb.adjust(7)
    
    await message.answer(
        "Выберите дни недели для проведения конкурса:",
        reply_markup=kb.as_markup()
    )
    await state.set_state(CreateContest.days_of_week)

@admin.callback_query(F.data.startswith("day_"), CreateContest.days_of_week)
async def toggle_day(callback: types.CallbackQuery, state: FSMContext):
    day_num = int(callback.data.split("_")[1])
    data = await state.get_data()
    selected_days = data.get("selected_days", set())
    
    if day_num in selected_days:
        selected_days.remove(day_num)
    else:
        selected_days.add(day_num)
    
    await state.update_data(selected_days=selected_days)
    await callback.answer(f"День {day_num} {'добавлен' if day_num in selected_days else 'удален'}")

@admin.callback_query(F.data == "days_done", CreateContest.days_of_week)
async def days_selected(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if not data.get("selected_days"):
        await callback.answer("Выберите хотя бы один день", show_alert=True)
        return
    
    await callback.message.answer(
        "Введите количество недель, в течение которых будет повторяться конкурс:"
    )
    await state.set_state(CreateContest.total_occurrences)

@admin.message(CreateContest.total_occurrences)
async def process_total_occurrences(message: types.Message, state: FSMContext):
    try:
        occurrences = int(message.text)
        if occurrences <= 0:
            raise ValueError
        await state.update_data(total_occurrences=occurrences)
        await ask_start_date(message, state)
    except ValueError:
        await message.answer("Пожалуйста, введите корректное положительное число!")


async def check_recurring_contests(bot: Bot):
    """Проверяет и запускает регулярные конкурсы по расписанию"""
    while True:
        try:
            now = datetime.now()
            current_time = now.strftime("%H:%M")
            current_weekday = now.weekday() + 1  # 1-7, где 1-пн, 7-вс
            
            # Получаем активные регулярные конкурсы
            recurring_contests = await Contest.get_active_recurring_contests()
            
            for contest in recurring_contests:
                contest_id = contest['id']
                frequency = contest['frequency']
                start_time = contest['start_time']  # В формате "HH:MM"
                selected_days = contest['selected_days'] or []
                last_run = contest['last_run']
                current_occurrence = contest['current_occurrence']
                total_occurrences = contest['total_occurrences']
                
                # Проверяем, нужно ли запускать конкурс сегодня
                should_run = False
                
                if frequency == "daily":
                    # Для ежедневных - проверяем время
                    should_run = current_time == start_time
                    
                elif frequency == "weekly":
                    # Для еженедельных - проверяем день недели и время
                    should_run = (current_weekday in selected_days and 
                                current_time == start_time)
                
                # Проверяем, не превышено ли количество запусков
                if current_occurrence >= total_occurrences:
                    await Contest.update_contest_status(contest_id, "finished")
                    continue
                
                # Проверяем, не запускали ли уже сегодня
                if last_run and last_run.date() == now.date():
                    continue
                
                if should_run:
                    try:
                        # Клонируем конкурс для нового запуска
                        new_contest_id = await Contest.clone_contest_for_recurring_run(contest_id)
                        
                        # Публикуем конкурс
                        await publish_recurring_contest(bot, contest, new_contest_id)
                        
                        # Обновляем данные оригинального конкурса
                        await Contest.update_recurring_contest_after_run(
                            contest_id, 
                            current_occurrence + 1,
                            now
                        )
                        
                    except Exception as e:
                        print(f"Ошибка при запуске регулярного конкурса {contest_id}: {e}")
            
            await asyncio.sleep(60)  # Проверяем каждую минуту
            
        except Exception as e:
            print(f"Критическая ошибка в check_recurring_contests: {e}")
            await asyncio.sleep(300)  # При ошибке ждем 5 минут

async def publish_recurring_contest(bot: Bot, contest_data: dict, contest_id: int):
    """Публикует регулярный конкурс в канале"""
    try:
        # Формируем текст конкурса
        conditions = json.loads(contest_data['conditions'])
        contest_text = await generate_contest_text(contest_data, conditions)
        
        # Создаем кнопку "Участвовать"
        bot_username = (await bot.get_me()).username
        participate_kb = InlineKeyboardBuilder()
        participate_kb.button(
            text="🎁 Участвовать", 
            url=f"https://t.me/{bot_username}?start=contest_{contest_id}"
        )
        
        # Получаем username канала
        channel_url = contest_data['channel_url']
        channel_username = channel_url.replace("@", "").replace("https://t.me/", "")
        
        # Проверяем наличие изображения
        image_path = contest_data.get('image_path')
        
        if image_path and os.path.exists(image_path):
            with open(image_path, 'rb') as photo:
                # Отправляем сообщение с фото
                message = await bot.send_photo(
                    chat_id=f"@{channel_username}",
                    photo=types.BufferedInputFile(photo.read(), filename="contest.jpg"),
                    caption=contest_text,
                    reply_markup=participate_kb.as_markup(),
                    parse_mode="HTML"
                )
        else:
            # Отправляем текстовое сообщение
            message = await bot.send_message(
                chat_id=f"@{channel_username}",
                text=contest_text,
                reply_markup=participate_kb.as_markup(),
                parse_mode="HTML"
            )
        
        # Сохраняем данные сообщения
        await Contest.update_contest_message_id(contest_id, message.message_id)
        await Contest.update_contest_message_text(contest_id, contest_text)
        await Contest.update_contest_status(contest_id, "active")
        
    except Exception as e:
        print(f"Ошибка при публикации регулярного конкурса: {e}")
        await Contest.update_contest_status(contest_id, "error")