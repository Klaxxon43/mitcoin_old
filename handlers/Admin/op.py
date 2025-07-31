from aiogram import F, types
from aiogram.fsm.context import FSMContext
from utils.Imports import *
from .states import *
from .admin import admin


# Функции для работы с ОП бонусами
def generate_opbonus_keyboard(op_bonus, bonuspage, total_pages):
    builder = InlineKeyboardBuilder()
    for task in op_bonus:
        chat_id = task[1]
        button_text = f"{chat_id}"
        builder.row(types.InlineKeyboardButton(text=button_text, callback_data=f"opbonus_{task[0]}"))

    builder.row(types.InlineKeyboardButton(text="Создать 🔥", callback_data="create_opbonus_task"))
    builder.row(types.InlineKeyboardButton(text="🔙 Назад", callback_data="back_admin"))
    
    pagination = []
    if bonuspage > 1:
        pagination.append(types.InlineKeyboardButton(text="⬅️", callback_data=f"bonuspage_{bonuspage - 1}"))
    pagination.append(types.InlineKeyboardButton(text=str(bonuspage), callback_data="current_page"))
    if bonuspage < total_pages:
        pagination.append(types.InlineKeyboardButton(text="➡️", callback_data=f"bonuspage_{bonuspage + 1}"))

    builder.row(*pagination)
    return builder.as_markup()

def paginate_opbonus_tasks(tasks, bonuspage=1, per_page=5):
    total_pages = (len(tasks) + per_page - 1) // per_page
    start_idx = (bonuspage - 1) * per_page
    end_idx = start_idx + per_page
    tasks_on_page = tasks[start_idx:end_idx]
    return tasks_on_page, total_pages

@admin.callback_query(F.data == 'bonus_admin')
async def bonus_tasks_handler(callback: types.CallbackQuery):
    tasks = await DB.get_bonus_ops()
    bonuspage = 1
    tasks_on_page, total_pages = paginate_opbonus_tasks(tasks, bonuspage)
    keyboard = generate_opbonus_keyboard(tasks_on_page, bonuspage, total_pages)
    await callback.message.edit_text("Каналы/чаты в ОП бонусов", reply_markup=keyboard)

@admin.callback_query(lambda c: c.data.startswith("bonuspage_"))
async def change_page_handler(callback: types.CallbackQuery):
    bonuspage = int(callback.data.split('_')[1])
    tasks = await DB.get_bonus_ops()
    tasks_on_page, total_pages = paginate_opbonus_tasks(tasks, bonuspage)
    keyboard = generate_opbonus_keyboard(tasks_on_page, bonuspage, total_pages)
    await callback.message.edit_text("Каналы/чаты в ОП бонусов", reply_markup=keyboard)

@admin.callback_query(lambda c: c.data.startswith("opbonus_"))
async def task_detail_handler(callback: types.CallbackQuery, bot: Bot):
    task_id = int(callback.data.split('_')[1])
    task = await DB.get_bonus_op(task_id)
    target = task[1]
    link = task[2]
    try:
        chat = await bot.get_chat(target)
        chat_title = chat.title
    except:
        chat_title = "Ошибка: невозможно получить название"

    task_info = f"""
Название - <b>{chat_title}</b>

Ссылка - {link}

{target}  
    """
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="🔙 Назад", callback_data="bonus_admin"))
    builder.add(types.InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"bonusdelete_{task_id}"))
    await callback.message.edit_text(task_info, reply_markup=builder.as_markup())

@admin.callback_query(lambda c: c.data.startswith("bonusdelete_"))
async def delete_task_handler(callback: types.CallbackQuery):
    id = int(callback.data.split('_')[1])
    await DB.remove_bonus_op(id)
    await callback.message.edit_text("Удалено!")
    tasks = await DB.get_bonus_ops()
    bonuspage = 1
    tasks_on_page, total_pages = paginate_opbonus_tasks(tasks, bonuspage)
    keyboard = generate_opbonus_keyboard(tasks_on_page, bonuspage, total_pages)
    await callback.message.edit_text("Каналы/чаты в ОП бонусов", reply_markup=keyboard)

@admin.callback_query(F.data == 'create_opbonus_task')
async def create_op_task_handler(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="❌ Назад", callback_data="back_admin"))
    await callback.message.edit_text("Пришлите канал или чат в формате юзернейма, пример - @telegram", reply_markup=builder.as_markup())
    await state.set_state(create_opbonus_tasks.create_op)

@admin.message(create_opbonus_tasks.create_op)
async def create_opbonus_task_handler2(message: types.Message, state: FSMContext, bot: Bot):
    target_id = message.text.strip()
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="❌ Назад", callback_data="back_admin"))
    await message.answer("Пришлите свою ссылку на канал/чат", reply_markup=builder.as_markup())
    await state.update_data(target_id=target_id)
    await state.set_state(create_opbonus_tasks.create_op2)

@admin.message(create_opbonus_tasks.create_op2)
async def create_opbonus_task_handler2(message: types.Message, state: FSMContext, bot: Bot):
    link = message.text.strip()
    data = await state.get_data()
    target_id = data.get('target_id')
    await DB.add_bonus_op(target_id, link)
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="🔙 Вернуться в меню", callback_data="back_menu"))
    await message.answer("🥳 Задание создано! Оно будет размещено в разделе бонусов", reply_markup=builder.as_markup())
    await state.clear()

# Функции для работы с основными ОП
def generate_op_tasks_keyboard(op_tasks, oppage, total_pages):
    builder = InlineKeyboardBuilder()
    for task in op_tasks:
        chat_id = task[1]
        button_text = f"{chat_id}"
        builder.row(types.InlineKeyboardButton(text=button_text, callback_data=f"optask_{task[0]}"))

    builder.row(types.InlineKeyboardButton(text="Создать 🔥", callback_data="create_op_task"))
    builder.row(types.InlineKeyboardButton(text="🔙 Назад", callback_data="back_admin"))
    
    pagination = []
    if oppage > 1:
        pagination.append(types.InlineKeyboardButton(text="⬅️", callback_data=f"oppage_{oppage - 1}"))
    pagination.append(types.InlineKeyboardButton(text=str(oppage), callback_data="current_page"))
    if oppage < total_pages:
        pagination.append(types.InlineKeyboardButton(text="➡️", callback_data=f"oppage_{oppage + 1}"))

    builder.row(*pagination)
    return builder.as_markup()

def paginate_op_tasks(tasks, oppage=1, per_page=5):
    total_pages = (len(tasks) + per_page - 1) // per_page
    start_idx = (oppage - 1) * per_page
    end_idx = start_idx + per_page
    tasks_on_page = tasks[start_idx:end_idx]
    return tasks_on_page, total_pages

@admin.callback_query(F.data == 'op_pr_menu')
async def chating_tasks_handler(callback: types.CallbackQuery):
    tasks = await DB.get_op_tasks()
    oppage = 1
    tasks_on_page, total_pages = paginate_op_tasks(tasks, oppage)
    keyboard = generate_op_tasks_keyboard(tasks_on_page, oppage, total_pages)
    await callback.message.edit_text("Каналы/чаты в ОП", reply_markup=keyboard)

@admin.callback_query(lambda c: c.data.startswith("oppage_"))
async def change_page_handler(callback: types.CallbackQuery):
    oppage = int(callback.data.split('_')[1])
    tasks = await DB.get_op_tasks()
    tasks_on_page, total_pages = paginate_op_tasks(tasks, oppage)
    keyboard = generate_op_tasks_keyboard(tasks_on_page, oppage, total_pages)
    await callback.message.edit_text("Каналы/чаты в ОП", reply_markup=keyboard)

@admin.callback_query(lambda c: c.data.startswith("optask_"))
async def task_detail_handler(callback: types.CallbackQuery, bot: Bot):
    task_id = int(callback.data.split('_')[1])
    task = await DB.get_op_task_by_id(task_id)
    target = task[1]
    text = task[2]
    try:
        chat = await bot.get_chat(target)
        chat_title = chat.title
    except:
        chat_title = "Ошибка: невозможно получить название"
    
    task_info = f"""
Название - <b>{chat_title}</b>

Текст - {text}

{target}  
    """
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="🔙 Назад", callback_data="op_pr_menu"))
    builder.add(types.InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"opdelete_{task_id}"))
    await callback.message.edit_text(task_info, reply_markup=builder.as_markup())

@admin.callback_query(lambda c: c.data.startswith("opdelete_"))
async def delete_task_handler(callback: types.CallbackQuery):
    task_id = int(callback.data.split('_')[1])
    await DB.delete_op_task(task_id)
    await callback.message.edit_text("Удалено!")
    tasks = await DB.get_op_tasks()
    oppage = 1
    tasks_on_page, total_pages = paginate_tasks(tasks, oppage)
    keyboard = generate_op_tasks_keyboard(tasks_on_page, oppage, total_pages)
    await callback.message.edit_text("Чаты/каналы в ОП", reply_markup=keyboard)

@admin.callback_query(F.data == 'create_op_task')
async def create_op_task_handler(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="❌ Назад", callback_data="back_admin"))
    await callback.message.edit_text("Пришлите канал или чат в формате юзернейма, пример - @telegram", reply_markup=builder.as_markup())
    await state.set_state(create_op_tasks.create_op_task)

@admin.message(create_op_tasks.create_op_task)
async def create_op_task_handler2(message: types.Message, state: FSMContext, bot: Bot):
    target_id = message.text.strip()
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="❌ Назад", callback_data="back_admin"))
    await message.answer("Пришлите текст, в который будет вставлена ссылка", reply_markup=builder.as_markup())
    await state.update_data(target_id=target_id)
    await state.set_state(create_op_tasks.create_op_task2)

@admin.message(create_op_tasks.create_op_task2)
async def create_op_task_handler2(message: types.Message, state: FSMContext, bot: Bot):
    text = message.text.strip()
    data = await state.get_data()
    target_id = data.get('target_id')
    await DB.add_op_task(target_id, text)
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="🔙 Вернуться в меню", callback_data="back_menu"))
    await message.answer("🥳 Задание создано! Оно будет размещено в сообщениях к ОП", reply_markup=builder.as_markup())
    await state.clear()

@admin.callback_query(F.data == 'adminAllOP')
async def _(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    kb = InlineKeyboardBuilder()
    kb.add(InlineKeyboardButton(text="Реклама в ОП", callback_data="op_pr_menu"))
    kb.add(InlineKeyboardButton(text="ОП в бонусах", callback_data="bonus_admin"))
    kb.add(InlineKeyboardButton(text="ОП", callback_data="show_op"))
    kb.add(InlineKeyboardButton(text="🔙 Назад", callback_data="admin_kb"))
    kb.adjust(1)
    await callback.message.edit_text('Выберите: ', reply_markup=kb.as_markup())

# Метод для получения страницы с заданиями (пагинация)
def paginate_tasks(tasks, chatingpage=1, per_page=5):
    total_pages = (len(tasks) + per_page - 1) // per_page  # Вычисление общего количества страниц
    start_idx = (chatingpage - 1) * per_page
    end_idx = start_idx + per_page
    tasks_on_page = tasks[start_idx:end_idx]
    return tasks_on_page, total_pages



@admin.callback_query(F.data =='show_op')
async def show_op(callback: types.CallbackQuery):
    user_id = callback.from_user.id

    if user_id not in ADMINS_ID:
        await callback.message.answer("У вас нет прав для выполнения этой команды.")
        return

    channels = await DB.all_channels_op()
    if not channels:
        kb = InlineKeyboardBuilder()
        kb.add(InlineKeyboardButton(text='Добавить ОП',callback_data='add_op'))
        kb.add(InlineKeyboardButton(text='Выход',callback_data='admin_kb'))
        kb.adjust(1)
        await callback.message.answer("Список каналов ОП пуст.", reply_markup=kb.as_markup())

        return

    keyboard = InlineKeyboardBuilder()
    for channel in channels:
        channel_id, channel_name = channel
        keyboard.add(InlineKeyboardButton(text=channel_name, callback_data=f"channel:{channel_id}"))
    keyboard.add(InlineKeyboardButton(text='Добавить ОП',callback_data='add_op'))
    keyboard.add(InlineKeyboardButton(text='Выход',callback_data='admin_kb'))
    keyboard.adjust(1)
    await callback.message.answer("Список каналов ОП:", reply_markup=keyboard.as_markup())



# Команда /add_channel
@admin.callback_query(F.data == 'add_op')
async def add_channel(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id

    # Проверяем, является ли пользователь администратором
    if user_id not in ADMINS_ID:
        await callback.message.answer("У вас нет прав для выполнения этой команды.")
        return

    # Запрашиваем @username канала
    await callback.message.answer("Введите @username канала (например, @my_channel):")
    await state.set_state(AddChannelStates.waiting_for_username)

# Обработка @username канала
@admin.message(AddChannelStates.waiting_for_username)
async def process_username(message: types.Message, state: FSMContext):
    username = message.text.strip()

    # Проверяем, что username начинается с @
    if not username.startswith('@'):
        await message.answer("Username канала должен начинаться с @. Попробуйте снова.")
        return

    # Сохраняем username в состоянии
    await state.update_data(channel_username=username)

    # Запрашиваем имя канала
    await message.answer("Введите имя канала (например, My Channel):")
    await state.set_state(AddChannelStates.waiting_for_name)


# Обработка имени канала
@admin.message(AddChannelStates.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
    channel_name = message.text.strip()

    # Получаем сохранённый username из состояния
    data = await state.get_data()
    channel_username = data.get('channel_username')

    try:
        # Добавляем канал в базу данных (замените на ваш метод)
        await DB.add_chanell_op(channel_username, channel_name)

        await message.answer(f"Канал {channel_name} (@{channel_username}) успешно добавлен в ОП.")
    except Exception as e:
        await message.answer(f"Ошибка: {e}")
    finally:
        # Завершаем состояние
        await state.clear()

@admin.callback_query(F.data.startswith('channel:'))
async def process_channel_button(callback_query: types.CallbackQuery):
    channel_id = callback_query.data.split(':')[1]
    logger.info(channel_id)
    channel_info = await DB.get_channel_info(channel_id)

    if not channel_info:
        await callback_query.answer("Канал не найден.")
        return

    channel_id, channel_name, channel_username = channel_info

    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text="Изменить имя", callback_data=f"update_name:{channel_id}"))
    keyboard.add(InlineKeyboardButton(text="Изменить username", callback_data=f"update_username:{channel_id}"))
    keyboard.add(InlineKeyboardButton(text="Удалить", callback_data=f"opdelete:{channel_id}"))
    keyboard.adjust(1)
    await callback_query.message.answer(
        f"Информация о канале:\n\nID: {channel_id}\nИмя: {channel_name}\nUsername: {channel_username}",
        reply_markup=keyboard.as_markup()
    )
    await callback_query.answer()

@admin.callback_query(F.data.startswith('update_name:'))
async def edit_channel_name(callback_query: types.CallbackQuery, state: FSMContext):
    channel_id = callback_query.data.split(':')[1]
    await state.update_data(channel_id=channel_id)
    await callback_query.message.answer("Введите новое имя канала:")
    await state.set_state(EditChannelStates.waiting_for_name)

@admin.callback_query(F.data.startswith('update_username:'))
async def edit_channel_username(callback_query: types.CallbackQuery, state: FSMContext):
    channel_name = callback_query.data.split(':')[1]
    await state.update_data(channel_name=channel_name)
    await callback_query.message.answer("Введите новый @username канала:")
    await state.set_state(EditChannelStates.waiting_for_username)

@admin.message(EditChannelStates.waiting_for_name)
async def process_new_name(message: types.Message, state: FSMContext):
    new_name = message.text.strip()
    data = await state.get_data()
    channel_id = data['channel_id']

    await DB.update_channel_name(channel_id, new_name)
    await message.answer("Имя канала успешно обновлено.", reply_markup=admin_kb())
    await state.clear()

@admin.message(EditChannelStates.waiting_for_username)
async def process_new_username(message: types.Message, state: FSMContext):
    new_username = message.text.strip()
    data = await state.get_data()
    channel_name = data['channel_name']

    if not new_username.startswith('@'):
        await message.answer("Username канала должен начинаться с @. Попробуйте снова.")
        return

    await DB.update_channel_username(channel_name, new_username)
    await message.answer("Username канала успешно обновлен.")
    await state.clear()

@admin.callback_query(F.data.startswith('opdelete:'))
async def delete_channel(callback_query: types.CallbackQuery):
    channel_id = callback_query.data.split(':')[1]
    logger.info(channel_id)
    await DB.delete_channel(channel_id)
    await callback_query.message.answer("Канал успешно удален.")
    await callback_query.answer()