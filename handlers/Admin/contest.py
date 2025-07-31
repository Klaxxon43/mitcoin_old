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
            await ask_start_date(message, state)
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
    
    # Получаем текущие значения условий
    sub_channel = data.get("sub_channel", False)
    channel_url = data.get("channel_url", "")
    is_bot_user = data.get("is_bot_user", False)
    is_active_user = data.get("is_active_user", False)
    required_refs = data.get("required_refs", 0)
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
    
    # Кнопки для управления количеством рефералов
    kb.button(text="-", callback_data="decrease_refs")
    kb.button(
        text=f"{required_refs} рефералов" if required_refs > 0 else "Пригласить рефералов", 
        callback_data="set_refs_count"
    )
    kb.button(text="+", callback_data="increase_refs")
    
    kb.button(text="✅ Готово", callback_data="conditions_done")
    
    kb.adjust(1, 1, 1, 1, 3, 1)
    
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


@admin.callback_query(F.data == "increase_refs", CreateContest.conditions)
async def increase_refs(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    current_refs = data.get("required_refs", 0)
    await state.update_data(required_refs=current_refs + 1)
    await ask_conditions(callback.message, state)
    await callback.answer()

@admin.callback_query(F.data == "decrease_refs", CreateContest.conditions)
async def decrease_refs(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    current_refs = data.get("required_refs", 0)
    new_refs = max(0, current_refs - 1)  # Не позволяем уходить ниже 0
    await state.update_data(required_refs=new_refs)
    await ask_conditions(callback.message, state)
    await callback.answer()

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
    
    # Сохраняем дополнительные каналы и количество рефералов
    additional_channels = data.get("additional_channels", [])
    required_refs = data.get("required_refs", 0)
    
    await state.update_data(
        conditions=selected_conditions,
        additional_channels=additional_channels,
        required_refs=required_refs
    )
    
    # Создаем клавиатуру для выбора типа текста конкурса
    kb = InlineKeyboardBuilder()
    kb.button(text="Автоматически сгенерировать текст", callback_data="generate_contest_text")
    kb.button(text="Ввести текст вручную", callback_data="enter_contest_text")
    kb.adjust(1)
    
    await callback.message.edit_text(
        "Выберите способ создания текста конкурса:",
        reply_markup=kb.as_markup()
    )

@admin.callback_query(F.data == "generate_contest_text")
async def generate_contest_text_handler(callback: types.CallbackQuery, state: FSMContext):
    await ask_contest_content(callback.message, state)

@admin.callback_query(F.data == "enter_contest_text")
async def enter_contest_text_handler(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "Введите текст конкурса (обязательно включите строку с 'Участников: 0'):"
    )
    await state.set_state(CreateContest.contest_text_input)

@admin.message(CreateContest.contest_text_input)
async def process_contest_text_input(message: types.Message, state: FSMContext):
    # Проверяем, содержит ли текст обязательную строку
    if "Участников: 0" not in message.text:
        await message.answer("Текст конкурса должен содержать строку 'Участников: 0'. Пожалуйста, добавьте ее и отправьте текст снова.")
        return
    
    await state.update_data(contest_text=message.text)
    await ask_contest_content(message, state)

@admin.message(CreateContest.additional_conditions)
async def process_additional_conditions(message: types.Message, state: FSMContext):
    additional = message.text if message.text != "-" else ""
    await state.update_data(additional_conditions=additional)
    await ask_contest_content(message, state)

async def ask_contest_content(message: types.Message, state: FSMContext):
    data = await state.get_data()
    
    # Если текст уже есть (введен вручную), пропускаем запрос текста
    if data.get("contest_text"):
        await confirm_contest(message, state)
        return
    
    kb = InlineKeyboardBuilder()
    kb.button(text="Использовать contest.png", callback_data="use_default_image")
    kb.button(text="Пропустить", callback_data="skip_image")
    kb.adjust(1)
    
    await message.answer(
        "Отправьте изображение для конкурса (если нужно):\n"
        "Вы можете использовать стандартное изображение или пропустить этот шаг",
        reply_markup=kb.as_markup()
    )
    await state.set_state(CreateContest.contest_content)

@admin.callback_query(F.data == "use_default_image", CreateContest.contest_content)
async def use_default_image(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(image_path="contest.png")
    await confirm_contest(callback.message, state)

@admin.callback_query(F.data == "skip_image", CreateContest.contest_content)
async def skip_image(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(image_path=None)
    await confirm_contest(callback.message, state)

@admin.message(CreateContest.contest_content)
async def process_contest_content(message: types.Message, state: FSMContext):
    if message.photo:
        # Сохраняем фото (здесь нужно реализовать сохранение файла)
        file_id = message.photo[-1].file_id
        # Здесь должен быть код для сохранения файла и получения пути
        image_path = f"contests/{file_id}.jpg"
        await state.update_data(image_path=image_path)
    
    await confirm_contest(message, state)

async def confirm_contest(message: types.Message, state: FSMContext):
    data = await state.get_data()
    
    # Форматируем даты
    start_date = data.get('start_date', 'сразу')
    if start_date != 'сразу':
        start_date = datetime.strptime(start_date, "%d.%m.%Y %H:%M").strftime("%H:%M, %d.%m.%Y MSK")
    
    end_date = datetime.strptime(data['end_date'], "%d.%m.%Y %H:%M").strftime("%H:%M, %d.%m.%Y MSK")
    
    # Если текст был введен вручную, используем его без изменений
    if data.get("contest_text"):
        text = data["contest_text"]
    else:
        # Формируем текст автоматически
        text = await generate_contest_text(data, {
            "auto_conditions": data.get("conditions", []),
            "additional_channels": data.get("additional_channels", []),
            "required_refs": data.get("required_refs", 0),
            "additional": data.get("additional_conditions", "")
        })
    
    # Добавляем строку проверки
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

@admin.message(CreateContest.contest_text)
async def process_contest_text(message: types.Message, state: FSMContext):
    text = message.text if message.text != "-" else None
    await state.update_data(contest_text=text)
    await confirm_contest(message, state)


@admin.callback_query(F.data == "confirm_contest")
async def save_contest(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    
    try:
        # Подготавливаем данные для сохранения
        conditions = {
            "auto_conditions": data.get("conditions", []),
            "additional": data.get("additional_conditions", ""),
            "additional_channels": data.get("additional_channels", []),
            "required_refs": data.get("required_refs", 0)
        }
        
        # Определяем статус конкурса
        start_date = data.get("start_date")
        if start_date == "сразу" or start_date == datetime.now().strftime("%d.%m.%Y %H:%M"):
            status = "active"
        else:
            status = "waiting"
        
        # Формируем данные конкурса - используем введенный текст, если он есть
        contest_text = data.get("contest_text")
        logger.warning(f"contest_text: {contest_text}")
        if contest_text is None:
            contest_text = await generate_contest_text({
                "channel_url": data["channel_url"],
                "winners_count": data["winners_count"],
                "prizes": data["prizes"],
                "end_date": data["end_date"]
            }, conditions)
        
        contest_data = {
            "channel_url": data["channel_url"],
            "winners_count": data["winners_count"],
            "prizes": data["prizes"],
            "start_date": data.get("start_date", datetime.now().strftime("%d.%m.%Y %H:%M")),
            "end_date": data["end_date"],
            "conditions": json.dumps(conditions, ensure_ascii=False),
            "contest_text": contest_text,  # Используем подготовленный текст
            "image_path": data.get("image_path"),
            "status": status
        }

        # Сохраняем конкурс в базу данных
        contest_id = await Contest.create_contest(
            channel_url=contest_data["channel_url"],
            winners_count=contest_data["winners_count"],
            prizes=json.dumps(contest_data["prizes"], ensure_ascii=False),
            start_date=contest_data["start_date"],
            end_date=contest_data["end_date"],
            conditions=contest_data["conditions"],
            contest_text=contest_data["contest_text"],  # Сохраняем именно тот текст, который показали пользователю
            image_path=contest_data["image_path"],
            status=contest_data["status"]
        )
        
        # Если конкурс активный - публикуем сразу
        if status == "active":
            try:
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
                            caption=contest_data["contest_text"],  # Используем сохраненный текст
                            reply_markup=participate_kb.as_markup(),
                            parse_mode="HTML"
                        )
                else:
                    # Отправляем текстовое сообщение
                    message = await bot.send_message(
                        chat_id=f"@{channel_username}",
                        text=contest_data["contest_text"],  # Используем сохраненный текст
                        reply_markup=participate_kb.as_markup(),
                        parse_mode="HTML"
                    )
                
                # Сохраняем данные сообщения
                await Contest.update_contest_message_id(contest_id, message.message_id)
                await Contest.update_contest_message_text(contest_id, contest_data["contest_text"])
                
                await callback.answer("✅ Конкурс успешно создан и опубликован в канале!", show_alert=True)

            except Exception as e:
                error_msg = f"❌ Ошибка при публикации: {str(e)}"
                logger.error(error_msg)
                await callback.answer(error_msg, show_alert=True)
        else:
            await callback.answer(
                f"⏳ Конкурс запланирован на {contest_data['start_date']}. "
                "Он будет автоматически опубликован в указанное время.",
                show_alert=True
            )
            
    except Exception as e:
        error_msg = f"❌ Критическая ошибка при создании конкурса: {str(e)}"
        logger.error(error_msg)
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
    required_refs = conditions.get("required_refs", 0)
    
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
        
    # 3.5 Пригласить рефералов
    if required_refs > 0:
        conditions_text += (
            f"{condition_number}. 👥 Пригласить {required_refs} друзей\n"
        )
        condition_number += 1

    # 3.6 Дополнительные условия
    additional_conditions = conditions.get("additional", "")
    if additional_conditions and additional_conditions != '-':
        conditions_text += f"{condition_number}. 📌 {additional_conditions}\n"

    # 4. Формируем финальный текст конкурса с обязательной строкой
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
    """Проверяет конкурсы с учетом часового пояса"""
    from datetime import timezone
    current_time = datetime.now(timezone.utc)
    logger.info(f"[CONTEST] Текущее время (UTC): {current_time}")
    
    contests = await Contest.get_active_contests_before(current_time)
    
    for contest in contests:
        try:
            end_date = datetime.strptime(contest['end_date'], "%d.%m.%Y %H:%M")
            end_date_utc = end_date.replace(tzinfo=timezone.utc)
            
            if current_time < end_date_utc:
                logger.info(f"Конкурс {contest['id']} активен до {end_date_utc}")
                continue
                
            await finish_contest(contest['id'], bot)
        except Exception as e:
            logger.error(f"Ошибка обработки конкурса {contest['id']}: {e}")

async def finish_contest(contest_id: int, bot: Bot):
    """Завершает конкурс и выбирает победителей"""
    logger.info(f"[CONTEST] Начало завершения конкурса {contest_id} (finish_contest)")
    contest = await Contest.get_contest2(contest_id)
    if not contest:
        logger.info(f"[CONTEST] Конкурс {contest_id} не найден")
        return
    
    if contest.get('status') == 'finished':
        logger.info(f"[CONTEST] Конкурс {contest_id} уже завершен")
        return
    
    logger.info(f"[CONTEST] Завершение конкурса {contest_id} (finish_contest)")
    
    # 1. Получаем участников
    logger.info("[CONTEST] Получение участников...")
    participants = await Contest.get_participants(contest_id)
    logger.info(f"[CONTEST] Найдено {len(participants)} участников")
    
    if not participants:
        logger.info("[CONTEST] Нет участников, обработка пустого конкурса")
        await handle_no_participants(contest, bot)
        return
    
    # 2. Выбираем победителей
    logger.info("[CONTEST] Выбор победителей...")
    winners_count = contest['winners_count']
    winners = select_winners(participants, winners_count)
    logger.info(f"[CONTEST] Выбрано {len(winners)} победителей")
    
    # 3. Награждаем победителей
    winners_info = []
    prizes = json.loads(contest['prizes'])
    logger.info(f"[CONTEST] Призы для конкурса: {prizes}")
    
    for place, (user_id, username) in enumerate(winners, start=1):
        logger.info(f"[CONTEST] Обработка победителя {username} (место {place})")
        prize = prizes.get(str(place), {})
        if not prize:
            logger.info(f"[CONTEST] Нет приза для места {place}")
            continue
            
        # Сохраняем победителя
        logger.info("[CONTEST] Сохранение победителя в БД...")
        await Contest.add_winner(
            contest_id=contest_id,
            user_id=user_id,
            place=place,
            prize_type=prize['type'],
            prize_amount=prize['amount']
        )
        
        # Начисляем награду
        logger.info(f"[CONTEST] Начисление награды: {prize['type']} {prize['amount']}")
        await award_winner(user_id, prize['type'], prize['amount'])
        
        # Формируем информацию о победителе
        winners_info.append({
            'place': place,
            'username': username,
            'prize': prize
        })
        
        # Уведомляем победителя
        logger.info("[CONTEST] Отправка уведомления победителю...")
        await notify_winner(bot, user_id, place, prize)
    
    # 4. Обновляем статус конкурса
    logger.info("[CONTEST] Обновление статуса конкурса...")
    await Contest.update_contest_status(contest_id, 'finished')
    
    # 5. Публикуем результаты
    logger.info("[CONTEST] Публикация результатов...")
    await publish_results(bot, contest, winners_info)

def select_winners(participants: list, winners_count: int) -> list:
    """Выбирает случайных победителей"""
    logger.info(f"[CONTEST] Выбор {winners_count} победителей из {len(participants)} участников")
    if winners_count >= len(participants):
        logger.info("Все участники становятся победителями")
        return participants
    
    return random.sample(participants, winners_count)

async def award_winner(user_id: int, prize_type: str, amount: float):
    """Начисляет награду победителю"""
    logger.info(f"[CONTEST] Начисление награды пользователю {user_id}: {amount} {prize_type}")
    if prize_type == 'MICO':
        await DB.add_balance(user_id, amount)
    elif prize_type == 'RUB':
        await DB.add_rub_balance(user_id, amount)
    elif prize_type == 'MINING':
        mining = await DB.search_mining(user_id)
        if not mining:
            await DB.add_mining(user_id)
        else:
            await DB.add_rub_balance(user_id, 299)
    else:
        logger.error(f"Неизвестный тип приза: {prize_type}")

async def notify_winner(bot: Bot, user_id: int, place: int, prize: dict):
    """Отправляет уведомление победителю"""
    logger.info(f"[CONTEST] Попытка уведомить пользователя {user_id} о победе")
    try:
        await bot.send_message(
            chat_id=user_id,
            text=f"🎉 Поздравляем! Вы заняли {place} место в конкурсе!\n\n"
                 f"Ваш приз: {prize['amount']} {prize['type']} уже на вашем счету!"
        )
        logger.info("[CONTEST] Уведомление успешно отправлено")
    except Exception as e:
        logger.error(f"Не удалось уведомить победителя {user_id}: {e}")
        import traceback
        traceback.print_exc()

async def publish_results(bot: Bot, contest: dict, winners: list):
    """Публикует результаты конкурса в канале и выдает награды победителям"""
    logger.info(f"[CONTEST] Публикация результатов конкурса {contest['id']}")
    
    try:
        # Выдача наград победителям
        await award_winners(winners, contest['prizes'])
        
        channel_username = contest['channel_url'].replace('https://t.me/', '').replace('@', '')
        message_id = contest['message_id']
        logger.info(f"[CONTEST] Канал для публикации: {channel_username}, message_id: {message_id}")
        
        # Получаем текущий текст сообщения
        try:
            message = str(contest['message_text'])
            original_text = message
        except Exception as e:
            logger.error(f"Не удалось получить исходное сообщение: {e}")
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
            
            logger.info(f"[CONTEST] Обновленный текст сообщения:\n{updated_text}")
            
            try:
                await bot.edit_message_text(
                    chat_id=f"@{channel_username}",
                    message_id=message_id,
                    text=updated_text,
                    parse_mode="HTML"
                )
            except Exception as e:
                logger.error(f"[CONTEST] Не удалось отредактировать текст сообщения (попытка редактирования подписи): {e}")
                try:
                    await bot.edit_message_caption(
                        chat_id=f"@{channel_username}",
                        message_id=message_id,
                        caption=updated_text,
                        parse_mode="HTML"
                    )
                except Exception as e:
                    logger.error(f"[CONTEST] Не удалось отредактировать подпись сообщения: {e}")
                    raise
        else:
            logger.error("[CONTEST] Не удалось получить исходный текст сообщения для редактирования")
            raise Exception("Original message text not found")
        
    except Exception as e:
        logger.error(f"[CONTEST] Не удалось опубликовать результаты (publish_results): {e}")
        import traceback
        traceback.print_exc()
        # В случае ошибки публикуем результаты как новое сообщение
        await publish_results_as_new_message(bot, contest, winners)


async def award_winners(winners: list, prizes: str):
    """Выдает награды победителям конкурса"""
    logger.info("[CONTEST] Начало выдачи наград победителям...")
    
    try:
        # Преобразуем строку с призами в словарь
        if isinstance(prizes, str):
            prizes = json.loads(prizes)
            
        for winner in winners:
            place = winner['place']
            username = winner['username']
            user_id = str(await DB.get_id_from_username(username)).replace("(", "").replace(")", "").replace(",","")
            
            try:
                # Определяем тип награды и выдаем соответствующий приз
                logger.info(f"[CONTEST] Призы: {prizes}")
                
                # Получаем приз для текущего места (формат: {"1": {"type": "MICO", "amount": 111111.0}})
                prize_info = prizes.get(str(place))
                if not prize_info:
                    logger.error(f"[CONTEST] Для места {place} не указан приз!")
                    continue
                    
                prize_type = prize_info.get('type')
                prize_amount = prize_info.get('amount')
                
                if not prize_type or not prize_amount:
                    logger.error(f"[CONTEST] Для места {place} не указан тип или количество приза!")
                    continue
                
                logger.info(f"[CONTEST] Выдача награды пользователю {username}: {prize_amount} {prize_type}")
                
                # Приводим prize_amount к float на случай, если он пришел как строка
                prize_amount = float(prize_amount)
                
                if prize_type.upper() == 'MICO':
                    await DB.add_balance(user_id, prize_amount)
                elif prize_type.upper() == 'MINING':
                    await DB.add_mining(user_id, int(prize_amount))  # mining обычно целое число
                elif prize_type.upper() == 'RUB':
                    await DB.add_rub_balance(user_id, prize_amount)
                else:
                    logger.error(f"[CONTEST] Неизвестный тип награды: {prize_type}")
                    
                logger.info(f"[CONTEST] Успешно выдана награда для места {place} пользователю {username}")
                
            except Exception as e:
                logger.error(f"[CONTEST] Ошибка при выдаче награды пользователю {username} (ID: {user_id}): {e}")
                import traceback
                traceback.print_exc()
                continue
                
    except json.JSONDecodeError:
        logger.error("[CONTEST] Ошибка декодирования JSON призов")
    except Exception as e:
        logger.error(f"[CONTEST] Общая ошибка в award_winners: {e}")
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
        logger.error(f"[CONTEST] Не удалось опубликовать результаты как новое сообщение: {e}")

async def handle_no_participants(contest: dict, bot: Bot):
    """Обрабатывает случай, когда нет участников"""
    logger.info(f"[CONTEST] Обработка конкурса без участников {contest['id']}")
    await Contest.update_contest_status(contest['id'], 'finished')
    channel_username = contest['channel_url'].replace('https://t.me/', '').replace('@', '')
    
    try:
        logger.info(f"[CONTEST] Отправка сообщения об отсутствии участников в канал {channel_username}")
        await bot.send_message(
            chat_id=f"@{channel_username}",
            text="Конкурс завершен, но не было участников 😢"
        )
    except Exception as e:
        logger.error(f"[CONTEST] Не удалось отправить сообщение о завершении (handle_no_participants): {e}")
        import traceback
        traceback.print_exc()

# В функции on_startup (при запуске бота)
async def on_startup(bot: Bot):
    """Запускает фоновые задачи при старте бота"""
    logger.info("[CONTEST] Запуск фоновой задачи проверки конкурсов")
    asyncio.create_task(run_contest_checker(bot))

@admin.callback_query(F.data == "cancel_contest")
async def cancel_contest(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Создание конкурса отменено")
    await state.clear()


async def run_contest_checker(bot: Bot):
    """Запускает периодическую проверку конкурсов"""
    logger.info("[CONTEST] Запуск проверки конкурсов (run_contest_checker)")
    while True:
        try:
            logger.info("[CONTEST] Начало новой итерации проверки конкурсов")
            await check_waiting_contests(bot)  # Сначала проверяем ожидающие конкурсы
            await check_finished_contests(bot)  # Затем проверяем завершенные
        except Exception as e:
            logger.error(f"[CONTEST] Ошибка в проверке конкурсов (run_contest_checker): {e}")
            import traceback
            traceback.print_exc()
        await asyncio.sleep(60)  # Проверка каждую минуту
        logger.info("[CONTEST] Ожидание 60 секунд до следующей проверки")

async def check_waiting_contests(bot: Bot):
    """Проверяет и активирует запланированные конкурсы"""
    current_time = datetime.now()
    logger.info(f"[CONTEST] Проверка запланированных конкурсов в {current_time}")
    
    # Получаем ожидающие конкурсы, которые должны начаться
    contests = await Contest.get_waiting_contests_before(current_time)
    logger.info(f"[CONTEST] Найдено {len(contests)} ожидающих конкурсов для активации")
    
    for contest in contests:
        logger.info(f"[CONTEST] Активация конкурса ID: {contest['id']}")
        try:
            await activate_contest(contest, bot)
        except Exception as e:
            logger.error(f"[CONTEST] Ошибка при активации конкурса {contest['id']}: {e}")
            import traceback
            traceback.print_exc()

async def activate_contest(contest: dict, bot: Bot):
    """Активирует запланированный конкурс"""
    logger.info(f"[CONTEST] Активация конкурса {contest['id']}")
    
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
        # Используем сохранённый текст, если он есть
        contest_text = contest.get('contest_text')
        if not contest_text:
            contest_text = await generate_contest_text({
                'channel_url': contest['channel_url'],
                'winners_count': contest['winners_count'],
                'prizes': json.loads(contest['prizes']),
                'start_date': contest['start_date'],
                'end_date': contest['end_date']
            }, conditions)

        
        # Проверяем HTML-разметку
        from aiogram.utils.text_decorations import html_decoration as hd
        try:
            safe_text =(contest_text)
        except Exception as e:
            logger.error(f"[CONTEST] Ошибка при экранировании текста: {e}")
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
            
            logger.info(f"[CONTEST] Конкурс {contest['id']} успешно активирован и опубликован")
            
        except Exception as e:
            logger.error(f"[CONTEST] Ошибка при публикации конкурса {contest['id']}: {e}")
            # Возвращаем статус waiting для повторной попытки
            await Contest.update_contest_status(contest['id'], 'waiting')
            raise
            
    except json.JSONDecodeError as e:
        logger.error(f"[CONTEST] Ошибка декодирования JSON для конкурса {contest['id']}: {e}")
        await Contest.update_contest_status(contest['id'], 'error')
    except Exception as e:
        logger.error(f"[CONTEST] Неизвестная ошибка при активации конкурса {contest['id']}: {e}")
        await Contest.update_contest_status(contest['id'], 'error') 