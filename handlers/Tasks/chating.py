from .tasks import *
from handlers.client import *
from handlers.client.my_works import check_admin_and_get_invite_link

@tasks.callback_query(F.data == 'work_chating')
async def chating_tasks_handler(callback: types.CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    tasks = await DB.get_chating_tasks()

    # Начинаем с первой страницы
    vchatingpage = 1
    tasks_on_page, total_pages = paginate_tasks(tasks, vchatingpage)

    # Генерируем инлайн кнопки
    keyboard = await generate_tasks_keyboard_chating(tasks_on_page, vchatingpage, total_pages, bot)

    await callback.message.edit_text(
        "🔥 <b>Зарабатывайте на сообщениях!</b>\nВыберите чат, вступите в него и получайте $MICO за каждое сообщение!",
        reply_markup=keyboard)
    

@tasks.callback_query(lambda c: c.data.startswith("vchatingpage_"))
async def vchange_page_handler(callback: types.CallbackQuery, bot: Bot):
    vchatingpage = int(callback.data.split('_')[1])
    user_id = callback.from_user.id
    tasks = await DB.get_chating_tasks()

    # Получаем задания на нужной странице
    tasks_on_page, total_pages = paginate_tasks(tasks, vchatingpage)

    # Генерируем инлайн кнопки
    keyboard = await generate_tasks_keyboard_chating(tasks_on_page, vchatingpage, total_pages, bot)

    await callback.message.edit_text(
        "🔥 <b>Зарабатывайте на сообщениях!</b>\nВыберите чат, вступите в него и получайте MITcoin за каждое сообщение!",
        reply_markup=keyboard)
    


@tasks.callback_query(lambda c: c.data.startswith("vchatingtask_"))
async def task_detail_handler(callback: types.CallbackQuery, bot: Bot):
    await callback.answer()
    task_id = int(callback.data.split('_')[1])
    task = await DB.get_chating_task_by_id(task_id)

    price = task[2]

    invite_link = await check_admin_and_get_invite_link(bot, task[1])
    chat_id = task[1]
    chat = await bot.get_chat(chat_id)
    task_info = f"""
<b>{chat.title}</b>

<em>Вступите в чат, пишите сообщения и зарабатывайте MITcoin</em>

💰 Плата за 1 сообщение - {price} MITcoin 

{invite_link}    
    """
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="🔙 Назад", callback_data="work_chating"))

    await callback.message.edit_text(task_info, reply_markup=builder.as_markup())

async def generate_tasks_keyboard_chating(chating_tasks, vchatingpage, total_pages, bot):
    builder = InlineKeyboardBuilder()

    # Выводим задания на текущей странице (по 5 на страницу)
    for task in chating_tasks:
        chat_id = task[1]
        chat = await bot.get_chat(chat_id)
        price = task[2]
        chat_title = chat.title
        button_text = f"{chat_title} | {price}"
        # Каждая кнопка в новой строке
        builder.row(InlineKeyboardButton(text=button_text, callback_data=f"vchatingtask_{task[0]}"))

    # Кнопка "Назад"
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="work_menu"))
    # Кнопки пагинации
    pagination = []
    if vchatingpage > 1:
        pagination.append(InlineKeyboardButton(text="⬅️", callback_data=f"vchatingpage_{vchatingpage - 1}"))
    pagination.append(InlineKeyboardButton(text=str(vchatingpage), callback_data="current_page"))
    if vchatingpage < total_pages:
        pagination.append(InlineKeyboardButton(text="➡️", callback_data=f"vchatingpage_{vchatingpage + 1}"))

    builder.row(*pagination)  # Кнопки пагинации в одну строку

    return builder.as_markup()