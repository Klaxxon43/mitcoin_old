from untils.Imports import *
from .states import create_chating_tasks
from untils.kb import admin_kb, pr_menu_canc, cancel_all_kb, back_menu_kb
from .admin import admin

def generate_tasks_keyboard(chating_tasks, chatingpage, total_pages):
    builder = InlineKeyboardBuilder()
    for task in chating_tasks:
        price = task[2]
        button_text = f"ЧАТ | {price}"
        builder.row(types.InlineKeyboardButton(text=button_text, callback_data=f"chatingtask_{task[0]}"))

    builder.row(types.InlineKeyboardButton(text="🔥 Создать", callback_data="create_chating_task"))
    builder.row(types.InlineKeyboardButton(text="🔙 Назад", callback_data="back_admin"))
    
    pagination = []
    if chatingpage > 1:
        pagination.append(types.InlineKeyboardButton(text="⬅️", callback_data=f"chatingpage_{chatingpage - 1}"))
    pagination.append(types.InlineKeyboardButton(text=str(chatingpage), callback_data="current_page"))
    if chatingpage < total_pages:
        pagination.append(types.InlineKeyboardButton(text="➡️", callback_data=f"chatingpage_{chatingpage + 1}"))

    builder.row(*pagination)
    return builder.as_markup()

def paginate_tasks(tasks, chatingpage=1, per_page=5):
    total_pages = (len(tasks) + per_page - 1) // per_page
    start_idx = (chatingpage - 1) * per_page
    end_idx = start_idx + per_page
    tasks_on_page = tasks[start_idx:end_idx]
    return tasks_on_page, total_pages

@admin.callback_query(F.data == 'chat_privyazka')
async def chating_tasks_handler(callback: types.CallbackQuery, bot: Bot):
    tasks = await DB.get_chating_tasks()
    chatingpage = 1
    tasks_on_page, total_pages = paginate_tasks(tasks, chatingpage)
    keyboard = generate_tasks_keyboard(tasks_on_page, chatingpage, total_pages)
    await callback.message.edit_text("Привязанные чаты:", reply_markup=keyboard)

@admin.callback_query(lambda c: c.data.startswith("chatingpage_"))
async def change_page_handler(callback: types.CallbackQuery):
    chatingpage = int(callback.data.split('_')[1])
    tasks = await DB.get_chating_tasks()
    tasks_on_page, total_pages = paginate_tasks(tasks, chatingpage)
    keyboard = generate_tasks_keyboard(tasks_on_page, chatingpage, total_pages)
    await callback.message.edit_text("Привязанные чаты:", reply_markup=keyboard)

async def check_admin_and_get_invite_link(bot, chat_id):
    try:
        chat_administrators = await bot.get_chat_administrators(chat_id)
        for admin in chat_administrators:
            if admin.user.id == bot.id:
                invite_link = await bot.export_chat_invite_link(chat_id)
                return invite_link
        return "😑 Предоставьте боту права администратора в чате!"
    except:
        return "😑 Предоставьте боту права администратора в чате!"

@admin.callback_query(lambda c: c.data.startswith("chatingtask_"))
async def task_detail_handler(callback: types.CallbackQuery, bot: Bot):
    task_id = int(callback.data.split('_')[1])
    task = await DB.get_chating_task_by_id(task_id)
    try:
        chat_id = task[1]
        price = task[2]
        chat = await bot.get_chat(chat_id)
        invite_link = await check_admin_and_get_invite_link(bot, task[1])
        chat_title = chat.title
    except:
        chat_title = '<i>Ошибка</i>'
        invite_link = '<i>Ошибка</i>'
        price = '<i>Ошибка</i>'

    task_info = f"""
Чат - {chat_title}

💰 Плата за 1 сообщение - {price} MITcoin 

{invite_link}    
    """
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="🔙 Назад", callback_data="chat_privyazka"))
    builder.add(types.InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"chatingdelete_{task_id}"))
    await callback.message.edit_text(task_info, reply_markup=builder.as_markup())

@admin.callback_query(lambda c: c.data.startswith("chatingdelete_"))
async def delete_task_handler(callback: types.CallbackQuery):
    task_id = int(callback.data.split('_')[1])
    await DB.delete_chating_task(task_id)
    await callback.message.edit_text("Чат удален!")
    tasks = await DB.get_chating_tasks()
    chatingpage = 1
    tasks_on_page, total_pages = paginate_tasks(tasks, chatingpage)
    keyboard = generate_tasks_keyboard(tasks_on_page, chatingpage, total_pages)
    await callback.message.edit_text("Привязанные чаты:", reply_markup=keyboard)

@admin.callback_query(F.data == 'create_chating_task')
async def create_chating_task_handler(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.edit_text('Введите вознаграждение за 1 сообщение в чате:', reply_markup=cancel_all_kb())
    await state.set_state(create_chating_tasks.create_task)

@admin.message(create_chating_tasks.create_task)
async def create_chating_task_handler2(message: types.Message, state: FSMContext):
    try:
        price = int(message.text.strip())
        await state.update_data(price=price)
        builder = InlineKeyboardBuilder()
        builder.add(types.InlineKeyboardButton(text="✅ Продолжить", callback_data="pr_chating_confirm"))
        builder.add(types.InlineKeyboardButton(text="❌ Назад", callback_data="back_admin"))
        await message.answer(f'👥 Оплата за 1 сообщение - {price} MITcoin\n\nНажмите Продолжить или напишите другое число...', reply_markup=builder.as_markup())
    except ValueError:
        await message.answer('<b>Ошибка ввода</b>\nПопробуй ввести целое число...', reply_markup=pr_menu_canc())

@admin.callback_query(F.data == 'pr_chating_confirm')
async def pr_chat3(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    price = data.get('price')
    await state.clear()
    bot_username = (await bot.get_me()).username
    invite_link = f"https://t.me/{bot_username}?startgroup&admin=invite_users+manage_chat"

    add_button = InlineKeyboardButton(text="➕ Добавить бота в чат", url=invite_link)
    add_button1 = InlineKeyboardButton(text="❌ Отмена", callback_data='pr_menu_cancel')
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[add_button], [add_button1]])
    await callback.message.edit_text(f'''
👾 Теперь необходимо добавить бота в ваш чат и предоставить ему права администратора, для этого...

<em>Добавьте бота в чат с помощью кнопки снизу -> предоставьте боту права админа -> перешлите в этот чат сообщение бота с кодом</em>
        ''', reply_markup=keyboard)
    await state.set_state(create_chating_tasks.create_task2)
    await state.update_data(price=price)

@admin.message(create_chating_tasks.create_task2)
async def pr_chating4(message: types.Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    price = data.get('price')
    user_id = message.from_user.id
    bot_info = await bot.get_me()
    code = message.text.strip()
    code_chat_id, code_user_id = map(int, code.split(":"))
    
    if user_id == code_user_id:
        try:
            bot_member = await bot.get_chat_member(chat_id=code_chat_id, user_id=bot_info.id)
            if bot_member.status != ChatMemberStatus.ADMINISTRATOR:
                await message.answer("🫤 Бот не является администратором в этой группе.", reply_markup=pr_menu_canc())
                return

            builder = InlineKeyboardBuilder()
            builder.add(types.InlineKeyboardButton(text="🔙 Вернуться в меню", callback_data="back_menu"))
            await message.answer("🥳 Задание создано! Оно будет размещено в разделе <b>Заработать</b>\n", reply_markup=builder.as_markup())
            await DB.add_chating_task(chat_id=code_chat_id, price=price)
            await bot.send_message(code_chat_id, '🥳 Настройка бота успешно завершена!')
            await state.clear()
        except Exception as e:
            await message.answer(f"🫤 Не удалось получить информацию о чате. Убедитесь, что бот добавлен в группу.", reply_markup=pr_menu_canc())
    else:
        await message.answer("🫤 Проверьте, добавлен ли бот в группу и повторите попытку...", reply_markup=pr_menu_canc())

@admin.callback_query(F.data == 'clean_task')
async def delete_all_tasks(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="✅ ДА", callback_data='clean_task_confirm'))
    builder.add(types.InlineKeyboardButton(text="❌ НЕТ", callback_data='back_admin'))
    await callback.message.edit_text('Вы уверены, что хотите удалить все задания?', reply_markup=builder.as_markup())

@admin.callback_query(F.data == 'clean_task_confirm')
async def delete_all_tasks_confirm(callback: types.CallbackQuery):
    await DB.clear_tasks_and_refund()
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="В меню", callback_data='back_admin'))
    await callback.message.edit_text('Все задания удалены, бабки возвращены', reply_markup=builder.as_markup())


from aiogram.types import ChatBoostUpdated

# @router.chat_boost()
async def on_chat_boost(chat_boost: ChatBoostUpdated, bot: Bot):
    if not chat_boost.boost.source.user:
        return

    user = chat_boost.boost.source.user
    chat_id = chat_boost.chat.id
    user_id = user.id

    print(f"Пользователь {user_id} забустил чат {chat_id}")

