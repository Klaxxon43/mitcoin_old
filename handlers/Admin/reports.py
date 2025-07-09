from utils.Imports import *
from .states import AdminActions
from utils.kb import admin_kb, cancel_all_kb
from utils.Imports import *
from .admin import admin

def generate_tasks_keyboard_report(reports, reportpage, total_pages):
    builder = InlineKeyboardBuilder()
    for report in reports:
        id = report[0]
        button_text = f"№{id}"
        builder.row(types.InlineKeyboardButton(text=button_text, callback_data=f"report_{report[0]}"))

    builder.row(types.InlineKeyboardButton(text="🔙 Назад", callback_data="back_admin"))
    
    pagination = []
    if reportpage > 1:
        pagination.append(types.InlineKeyboardButton(text="⬅️", callback_data=f"reportpage_{reportpage - 1}"))
    pagination.append(types.InlineKeyboardButton(text=str(reportpage), callback_data="current_page"))
    if reportpage < total_pages:
        pagination.append(types.InlineKeyboardButton(text="➡️", callback_data=f"reportpage_{reportpage + 1}"))

    builder.row(*pagination)
    return builder.as_markup()

def paginate_tasks_report(reports, reportpage=1, per_page=5):
    total_pages = (len(reports) + per_page - 1) // per_page
    start_idx = (reportpage - 1) * per_page
    end_idx = start_idx + per_page
    tasks_on_page = reports[start_idx:end_idx]
    return tasks_on_page, total_pages

@admin.callback_query(F.data == 'reports_list_menu')
async def chating_tasks_handler(callback: types.CallbackQuery, bot: Bot):
    reports = await DB.get_reports()
    reportpage = 1
    tasks_on_page, total_pages = paginate_tasks_report(reports, reportpage)
    keyboard = generate_tasks_keyboard_report(tasks_on_page, reportpage, total_pages)
    await callback.message.edit_text("Все репорты:", reply_markup=keyboard)

@admin.callback_query(lambda c: c.data.startswith("reportpage_"))
async def change_page_handler(callback: types.CallbackQuery):
    reportpage = int(callback.data.split('_')[1])
    reports = await DB.get_reports()
    tasks_on_page, total_pages = paginate_tasks_report(reports, reportpage)
    keyboard = generate_tasks_keyboard_report(tasks_on_page, reportpage, total_pages)
    await callback.message.edit_text("Все репорты:", reply_markup=keyboard)

async def check_admin_and_get_invite_link_report(bot, chat_id):
    try:
        chat_administrators = await bot.get_chat_administrators(chat_id)
        for admin in chat_administrators:
            if admin.user.id == bot.id:
                try:
                    ChatFullInfo = await bot.get_chat(chat_id)
                    invite_link = ChatFullInfo.invite_link
                    if invite_link is None:
                        return "Бот был забанен в чате, либо не является админом"
                    return invite_link
                except Exception as e:
                    print(f'Ошибка получения инвайта для {chat_id}, ошибка - {e}')
                    return "Бот был забанен в чате, либо не является админом"
        return "Бот был забанен в чате, либо не является админом"
    except:
        return "Бот был забанен в чате, либо не является админом"

@admin.callback_query(lambda c: c.data.startswith("report_"))
async def task_detail_handler(callback: types.CallbackQuery, bot: Bot):
    report_id = int(callback.data.split('_')[1])
    try:
        report = await DB.get_report(report_id)
    except:
        await callback.message.answer('Ошибка получения информации о репорте')
        return
    
    try:
        reporter = report[3]
    except:
        reporter = "Неизвестный, рекомендую удалить репорт"

    try:
        task_id = report[1]
        chat_id = report[2]
        report_id = report[0]
    except:
        task_id = "Неизвестное задание, рекомендую удалить репорт"
        chat_id = "Неизвестный чат айди, рекомендую удалить репорт"
        report_id = "Неизвестный репорт, рекомендую удалить репорт"

    try:
        task = await DB.get_task_by_id(task_id)
        if task is None:
            keyboard_builder = InlineKeyboardBuilder()
            keyboard_builder.add(
                InlineKeyboardButton(text="❌ Удалить задание", callback_data=f"reporttaskdelete_{task_id}_{report_id}"),
                InlineKeyboardButton(text="❌💵 Удалить задание (+возврат MIT)", callback_data=f"taskcashbackdelete_{task_id}_{report_id}"),
                InlineKeyboardButton(text="❌⚠️ Удалить задание (+ БАН)", callback_data=f"taskbandelete_{task_id}_{report_id}"),
                InlineKeyboardButton(text="🗑️ Удалить репорт", callback_data=f"reportdelete_{report_id}"),
                InlineKeyboardButton(text="🔙 Назад", callback_data="reports_list_menu")
            )
            keyboard_builder.adjust(1)
            keyboard = keyboard_builder.as_markup()
            await callback.message.answer(f'Не удалось получить информацию о задании, ошибка', reply_markup=keyboard)
            return
    except Exception as e:
        task = None
        keyboard_builder = InlineKeyboardBuilder()
        keyboard_builder.add(
            InlineKeyboardButton(text="❌ Удалить задание", callback_data=f"reporttaskdelete_{task_id}_{report_id}"),
            InlineKeyboardButton(text="❌💵 Удалить задание (+возврат MIT)", callback_data=f"taskcashbackdelete_{task_id}_{report_id}"),
            InlineKeyboardButton(text="❌⚠️ Удалить задание (+ БАН)", callback_data=f"taskbandelete_{task_id}_{report_id}"),
            InlineKeyboardButton(text="🗑️ Удалить репорт", callback_data=f"reportdelete_{report_id}"),
            InlineKeyboardButton(text="🔙 Назад", callback_data="reports_list_menu")
        )
        keyboard_builder.adjust(1)
        keyboard = keyboard_builder.as_markup()
        await callback.message.answer(f'Не удалось получить информацию о задании, ошибка - {e}', reply_markup=keyboard)
        return

    if task[1]:
        user_id_creator = task[1]
    else:
        user_id_creator = "Неизвестный, рекомендую удалить задание"

    chat_title = "Неизвестный чат"
    invite_link = "Невозможно создать ссылку"
    if task[4] in [1, 2]:
        invite_link = await check_admin_and_get_invite_link_report(bot, report[2])
        try:
            chat = await bot.get_chat(chat_id)
            chat_title = chat.title
        except:
            chat_title = "Неизвестный чат"
    elif task[4] in [3]:
        chat_id_post, message_id = map(int, chat_id.split(":"))
        chat_title = "Пост"
        invite_link = "Невозможно создать ссылку на пост"
        try:
            await bot.forward_message(chat_id=callback.from_user.id, from_chat_id=chat_id_post, message_id=message_id)
        except:
            await callback.message.answer('Невозможно переслать пост (скорее всего он удален)')

    task_info = f"""
ID репорта - {report_id}
Объект репорта - {chat_title}

Кто пожаловался - <a href='tg://user?id={reporter}'>{reporter}</a>
Кто создал задание - <code>{user_id_creator}</code>
ID канала/чата или код поста (чат_айди:месседж_айди)- <code>{chat_id}</code> 
ID задания - <code>{task_id}</code>

Ссылка на канал/чат - {invite_link}

Описание проблемы: <code>{report[4]}</code>

<i>Выберите нужный вариант действия:</i>    
    """
    keyboard_builder = InlineKeyboardBuilder()
    keyboard_builder.add(
        InlineKeyboardButton(text="❌ Удалить задание", callback_data=f"reporttaskdelete_{task_id}_{report_id}"),
        InlineKeyboardButton(text="❌💵 Удалить задание (+возврат MIT)", callback_data=f"taskcashbackdelete_{task_id}_{report_id}"),
        InlineKeyboardButton(text="❌⚠️ Удалить задание (+ БАН)", callback_data=f"taskbandelete_{task_id}_{report_id}"),
        InlineKeyboardButton(text="🗑️ Удалить репорт", callback_data=f"reportdelete_{report_id}"),
        InlineKeyboardButton(text="🔙 Назад", callback_data="reports_list_menu")
    )
    keyboard_builder.adjust(1)
    keyboard = keyboard_builder.as_markup()
    await callback.message.answer(task_info, reply_markup=keyboard)

@admin.callback_query(lambda c: c.data.startswith("reporttaskdelete_"))
async def delete_task_handler(callback: types.CallbackQuery):
    task_id = int(callback.data.split('_')[1])
    report_id = int(callback.data.split('_')[2])
    await DB.delete_task(task_id)
    await DB.delete_report(report_id)
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="🔙 Вернуться в репорты", callback_data="reports_list_menu"))
    await callback.message.edit_text(f'❌ Задание {task_id} удалено! Монеты за задание на баланс пользователя возвращены НЕ были', reply_markup=builder.as_markup())

@admin.callback_query(lambda c: c.data.startswith("taskcashbackdelete_"))
async def delete_task_handler(callback: types.CallbackQuery):
    task_id = int(callback.data.split('_')[1])
    report_id = int(callback.data.split('_')[2])
    price = 0
    task = await DB.get_task_by_id(task_id)

    if task[4] == 1:
        price = 2000
    elif task[4] == 2:
        price = 3000
    elif task[4] == 3:
        price = 200

    amounts = task[3]
    user_id = task[1]
    new_balance = amounts*price

    await DB.delete_task(task_id)
    await DB.add_balance(user_id, amount=new_balance)
    await DB.delete_report(report_id)
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="🔙 Вернуться в репорты", callback_data="reports_list_menu"))
    await callback.message.edit_text(f'❌ Задание {task_id} удалено! Создателю задания (<code>{user_id}</code>) было возвращено {new_balance} MitCoin', reply_markup=builder.as_markup())

@admin.callback_query(lambda c: c.data.startswith("taskbandelete_"))
async def delete_task_handler(callback: types.CallbackQuery):
    task_id = int(callback.data.split('_')[1])
    report_id = int(callback.data.split('_')[2])
    task = await DB.get_task_by_id(task_id)
    user_id = task[1]
    new_balance = -10000000
    
    await DB.delete_task(task_id)
    await DB.update_balance(user_id, new_balance)
    await DB.delete_report(report_id)
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="🔙 Вернуться в репорты", callback_data="reports_list_menu"))
    await callback.message.edit_text(f'❌ Задание {task_id} удалено! Создателю задания (<code>{user_id}</code>) был установлен баланс {new_balance}', reply_markup=builder.as_markup())

@admin.callback_query(lambda c: c.data.startswith("reportdelete_"))
async def delete_task_handler(callback: types.CallbackQuery):
    report_id = int(callback.data.split('_')[1])
    await DB.delete_report(report_id)
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="🔙 Вернуться в репорты", callback_data="reports_list_menu"))
    await callback.message.edit_text(f'❌ Репорт №{report_id} был удален без каких-либо действий', reply_markup=builder.as_markup())