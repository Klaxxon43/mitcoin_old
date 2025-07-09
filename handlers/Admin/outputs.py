from utils.Imports import *
from utils.kb import back_menu_kb
from .admin import admin

@admin.callback_query(F.data == 'adminoutputlist')
async def adminoutputlist(callback: types.CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="USDT", callback_data="adminusdtoutputlist"))
    builder.add(types.InlineKeyboardButton(text="Рубли", callback_data="adminruboutputlist"))
    builder.add(types.InlineKeyboardButton(text="🔙", callback_data="back_admin"))
    await callback.message.edit_text(f'<b>Выберите тип вывода:</b>', reply_markup=builder.as_markup())

# USDT Outputs
def generate_usdt_keyboard(outputs, usdtpage, total_pages):
    builder = InlineKeyboardBuilder()
    for output in outputs:
        amount = output[3]
        button_text = f"{amount}"
        builder.row(types.InlineKeyboardButton(text=button_text, callback_data=f"usdttask_{output[0]}"))

    builder.row(types.InlineKeyboardButton(text="🔙 Назад", callback_data="back_admin"))
    
    pagination = []
    if usdtpage > 1:
        pagination.append(types.InlineKeyboardButton(text="⬅️", callback_data=f"usdtpage_{usdtpage - 1}"))
    pagination.append(types.InlineKeyboardButton(text=str(usdtpage), callback_data="current_page"))
    if usdtpage < total_pages:
        pagination.append(types.InlineKeyboardButton(text="➡️", callback_data=f"usdtpage_{usdtpage + 1}"))

    builder.row(*pagination)
    return builder.as_markup()

def paginate_usdt_tasks(outputs, usdtpage=1, per_page=5):
    total_pages = (len(outputs) + per_page - 1) // per_page
    start_idx = (usdtpage - 1) * per_page
    end_idx = start_idx + per_page
    tasks_on_page = outputs[start_idx:end_idx]
    return tasks_on_page, total_pages

@admin.callback_query(F.data == 'adminusdtoutputlist')
async def adminusdtoutputlist(callback: types.CallbackQuery):
    outputs = await DB.get_usdt_outputs()
    usdtpage = 1
    tasks_on_page, total_pages = paginate_usdt_tasks(outputs, usdtpage)
    keyboard = generate_usdt_keyboard(tasks_on_page, usdtpage, total_pages)
    await callback.message.edit_text("Список заявок на вывод в <b>USDT (BEP20)</b>", reply_markup=keyboard)

@admin.callback_query(lambda c: c.data.startswith("usdtpage_"))
async def change_page_handler(callback: types.CallbackQuery):
    usdtpage = int(callback.data.split('_')[1])
    outputs = await DB.get_usdt_outputs()
    tasks_on_page, total_pages = paginate_usdt_tasks(outputs, usdtpage)
    keyboard = generate_usdt_keyboard(tasks_on_page, usdtpage, total_pages)
    await callback.message.edit_text("Список заявок на вывод в <b>USDT (BEP20)</b>", reply_markup=keyboard)

@admin.callback_query(lambda c: c.data.startswith("usdttask_"))
async def task_detail_handler(callback: types.CallbackQuery, bot: Bot):
    id = int(callback.data.split('_')[1])
    output = await DB.get_output(id)
    if output is not None:
        try:
            user_id = output[1]
        except:
            user_id = "ошибка"
        try:
            wallet = output[2]
        except:
            wallet = "ошибка"
        try:
            amount = output[3]
        except:
            amount = "ошибка"

        task_info = f"""
📤 <b>Заявка на вывод в USDT:</b>
<b>ID</b> - <code>{user_id}</code>
    
👛 <b>Кошелек USDT(BEP20)</b> - 
<code>{wallet}</code>
    
💲 <b>Сумма</b> - <code>{amount}</code>
    
<span class="tg-spoiler">⚠ При нажатии кнопки <b>Выполнено</b> заявка удаляется из списка и рубли на баланс юзера НЕ ВОЗВРАЩАЮТСЯ</span>
        """
        builder = InlineKeyboardBuilder()
        builder.add(types.InlineKeyboardButton(text="✅ Выполнено", callback_data=f"usdtsuc_{id}"))
        builder.add(types.InlineKeyboardButton(text="❌ Отклонить", callback_data=f"usdtdelete_{id}"))
        builder.add(types.InlineKeyboardButton(text="🔙 Назад", callback_data="adminusdtoutputlist"))
        await callback.message.edit_text(task_info, reply_markup=builder.as_markup())
    else:
        builder = InlineKeyboardBuilder()
        builder.add(types.InlineKeyboardButton(text="🔙 Назад", callback_data="adminusdtoutputlist"))
        await callback.message.edit_text("Заявка не найдена", reply_markup=builder.as_markup())

@admin.callback_query(lambda c: c.data.startswith("usdtsuc_"))
async def delete_task_handler(callback: types.CallbackQuery, bot: Bot):
    id = int(callback.data.split('_')[1])
    output = await DB.get_output(id)
    user_id = output[1]
    await DB.delete_output(id)
    await callback.message.edit_text("✅ Выполнено")
    await bot.send_message(chat_id=user_id, text='🥳 Ваша заявка на вывод одобрена!', reply_markup=back_menu_kb(user_id))
    outputs = await DB.get_usdt_outputs()
    usdtpage = 1
    tasks_on_page, total_pages = paginate_usdt_tasks(outputs, usdtpage)
    keyboard = generate_usdt_keyboard(tasks_on_page, usdtpage, total_pages)
    await callback.message.edit_text("Список заявок на вывод в <b>USDT</b>", reply_markup=keyboard)

# RUB Outputs
def generate_rub_keyboard(outputs, rubpage, total_pages):
    builder = InlineKeyboardBuilder()
    for output in outputs:
        amount = output[3]
        button_text = f"{amount}"
        builder.row(types.InlineKeyboardButton(text=button_text, callback_data=f"rubtask_{output[0]}"))

    builder.row(types.InlineKeyboardButton(text="🔙 Назад", callback_data="back_admin"))
    
    pagination = []
    if rubpage > 1:
        pagination.append(types.InlineKeyboardButton(text="⬅️", callback_data=f"rubpage_{rubpage - 1}"))
    pagination.append(types.InlineKeyboardButton(text=str(rubpage), callback_data="current_page"))
    if rubpage < total_pages:
        pagination.append(types.InlineKeyboardButton(text="➡️", callback_data=f"rubpage_{rubpage + 1}"))

    builder.row(*pagination)
    return builder.as_markup()

def paginate_rub_tasks(outputs, rubpage=1, per_page=5):
    total_pages = (len(outputs) + per_page - 1) // per_page
    start_idx = (rubpage - 1) * per_page
    end_idx = start_idx + per_page
    tasks_on_page = outputs[start_idx:end_idx]
    return tasks_on_page, total_pages

@admin.callback_query(F.data == 'adminruboutputlist')
async def adminruboutputlist(callback: types.CallbackQuery):
    outputs = await DB.get_rub_outputs()
    rubpage = 1
    tasks_on_page, total_pages = paginate_rub_tasks(outputs, rubpage)
    keyboard = generate_rub_keyboard(tasks_on_page, rubpage, total_pages)
    await callback.message.edit_text("Список заявок на вывод в <b>рублях</b>", reply_markup=keyboard)

@admin.callback_query(lambda c: c.data.startswith("rubpage_"))
async def change_rubpage_handler(callback: types.CallbackQuery):
    rubpage = int(callback.data.split('_')[1])
    outputs = await DB.get_rub_outputs()
    tasks_on_page, total_pages = paginate_rub_tasks(outputs, rubpage)
    keyboard = generate_rub_keyboard(tasks_on_page, rubpage, total_pages)
    await callback.message.edit_text("Список заявок на вывод в <b>рублях</b>", reply_markup=keyboard)

@admin.callback_query(lambda c: c.data.startswith("rubtask_"))
async def task_detail_handler(callback: types.CallbackQuery, bot: Bot):
    id = int(callback.data.split('_')[1])
    output = await DB.get_output(id)
    if output is not None:
        try:
            user_id = output[1]
        except:
            user_id = "ошибка"
        try:
            wallet = output[2]
        except:
            wallet = "ошибка"
        try:
            amount = output[3]
        except:
            amount = "ошибка"

        task_info = f"""
📤 <b>Заявка на вывод в рублях:</b>
<b>ID</b> - <code>{user_id}</code>

💳 <b>Карта/телефон(для СБП)</b> - 
<code>{wallet}</code>

💲 <b>Сумма</b> - <code>{amount}</code>

<span class="tg-spoiler">⚠ При нажатии кнопки <b>Отклонить</b> заявка удаляется из списка и рубли на баланс юзера НЕ ВОЗВРАЩАЮТСЯ</span>
        """
        builder = InlineKeyboardBuilder()
        builder.add(types.InlineKeyboardButton(text="✅ Выполнено", callback_data=f"rubsuc_{id}"))
        builder.add(types.InlineKeyboardButton(text="❌ Отклонить", callback_data=f"rubdelete_{id}"))
        builder.add(types.InlineKeyboardButton(text="🔙", callback_data="adminruboutputlist"))
        await callback.message.edit_text(task_info, reply_markup=builder.as_markup())
    else:
        builder = InlineKeyboardBuilder()
        builder.add(types.InlineKeyboardButton(text="🔙 Назад", callback_data="adminruboutputlist"))
        await callback.message.edit_text("Заявка не найдена", reply_markup=builder.as_markup())

@admin.callback_query(lambda c: c.data.startswith("rubdelete_"))
async def delete_task_handler(callback: types.CallbackQuery, bot: Bot):
    id = int(callback.data.split('_')[1])
    output = await DB.get_output(id)
    user_id = output[1]
    await DB.delete_output(id)
    await callback.message.edit_text("❌ Отклонено")
    await bot.send_message(chat_id=user_id, text='☹ Ваша заявка на вывод отклонена', reply_markup=back_menu_kb(user_id))
    outputs = await DB.get_rub_outputs()
    rubpage = 1
    tasks_on_page, total_pages = paginate_rub_tasks(outputs, rubpage)
    keyboard = generate_rub_keyboard(tasks_on_page, rubpage, total_pages)
    await callback.message.edit_text("Список заявок на вывод в <b>рублях</b>", reply_markup=keyboard)

@admin.callback_query(lambda c: c.data.startswith("rubsuc_"))
async def delete_task_handler(callback: types.CallbackQuery, bot: Bot):
    id = int(callback.data.split('_')[1])
    output = await DB.get_output(id)
    user_id = output[1]
    await DB.delete_output(id)
    await callback.message.edit_text("✅ Выполнено")
    await bot.send_message(chat_id=user_id, text='🥳 Ваша заявка на вывод одобрена!', reply_markup=back_menu_kb(user_id))
    outputs = await DB.get_rub_outputs()
    rubpage = 1
    tasks_on_page, total_pages = paginate_rub_tasks(outputs, rubpage)
    keyboard = generate_rub_keyboard(tasks_on_page, rubpage, total_pages)
    await callback.message.edit_text("Список заявок на вывод в <b>рублях</b>", reply_markup=keyboard)