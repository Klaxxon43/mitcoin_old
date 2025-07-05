from aiogram import F, types
from aiogram.fsm.context import FSMContext
from untils.Imports import *
from .states import create_op_tasks, create_opbonus_tasks
from untils.kb import admin_kb, back_menu_kb
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