# import asyncio

# from aiogram import types, Router, F, Bot
# from aiogram.fsm.context import FSMContext
# from aiogram.fsm.state import State, StatesGroup
# from kb import admin_kb, cancel_all_kb, pr_menu_canc, back_menu_kb, get_stats_menu, admin_kb2
# from db import DB, Promo
# from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest
# from config import ADMINS_ID
# import os
# from aiogram.utils.keyboard import InlineKeyboardBuilder
# from aiogram.enums import ChatMemberStatus
# from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ChatMemberUpdated
# from aiogram.filters import Command

# class MailingStates(StatesGroup):
#     message = State()
#     progress = State()

# class AdminActions(StatesGroup):
#     update_rub_balance = State()
#     view_user_profile = State()
#     update_balance = State()

# class create_chating_tasks(StatesGroup):
#     create_task = State()
#     create_task2 = State()

# class create_op_tasks(StatesGroup):
#     create_op_task = State()
#     create_op_task2 = State()

# class create_opbonus_tasks(StatesGroup):
#     create_op = State()
#     create_op2 = State()


# admin = Router()











# def generate_opbonus_keyboard(op_bonus, bonuspage, total_pages):
#     builder = InlineKeyboardBuilder()

#     # Выводим задания на текущей странице (по 5 на страницу)
#     for task in op_bonus:
#         chat_id = task[1]

#         button_text = f"{chat_id}"
#         # Каждая кнопка в новой строке
#         builder.row(types.InlineKeyboardButton(text=button_text, callback_data=f"opbonus_{task[0]}"))

#     # Кнопка "Назад"
#     builder.row(types.InlineKeyboardButton(text="Создать 🔥", callback_data="create_opbonus_task"))
#     builder.row(types.InlineKeyboardButton(text="🔙 Назад", callback_data="back_admin"))
#     # Кнопки пагинации
#     pagination = []
#     if bonuspage > 1:
#         pagination.append(types.InlineKeyboardButton(text="⬅️", callback_data=f"bonuspage_{bonuspage - 1}"))
#     pagination.append(types.InlineKeyboardButton(text=str(bonuspage), callback_data="current_page"))
#     if bonuspage < total_pages:
#         pagination.append(types.InlineKeyboardButton(text="➡️", callback_data=f"bonuspage_{bonuspage + 1}"))

#     builder.row(*pagination)  # Кнопки пагинации в одну строку

#     return builder.as_markup()


# # Метод для получения страницы с заданиями (пагинация)
# def paginate_opbonus_tasks(tasks, bonuspage=1, per_page=5):
#     total_pages = (len(tasks) + per_page - 1) // per_page  # Вычисление общего количества страниц
#     start_idx = (bonuspage - 1) * per_page
#     end_idx = start_idx + per_page
#     tasks_on_page = tasks[start_idx:end_idx]
#     return tasks_on_page, total_pages


# @admin.callback_query(F.data == 'bonus_admin')
# async def bonus_tasks_handler(callback: types.CallbackQuery):
#     tasks = await DB.get_bonus_ops()
#     # Начинаем с первой страницы
#     bonuspage = 1
#     tasks_on_page, total_pages = paginate_opbonus_tasks(tasks, bonuspage)
#     # Генерируем инлайн кнопки
#     keyboard = generate_opbonus_keyboard(tasks_on_page, bonuspage, total_pages)
#     await callback.message.edit_text("Каналы/чаты в ОП бонусов", reply_markup=keyboard)




# @admin.callback_query(lambda c: c.data.startswith("bonuspage_"))
# async def change_page_handler(callback: types.CallbackQuery):
#     bonuspage = int(callback.data.split('_')[1])
#     user_id = callback.from_user.id
#     tasks = await DB.get_op_tasks()

#     # Получаем задания на нужной странице
#     tasks_on_page, total_pages = paginate_opbonus_tasks(tasks, bonuspage)

#     # Генерируем инлайн кнопки
#     keyboard = generate_opbonus_keyboard(tasks_on_page, bonuspage, total_pages)

#     await callback.message.edit_text("Каналы/чаты в ОП бонусов", reply_markup=keyboard)




# @admin.callback_query(lambda c: c.data.startswith("opbonus_"))
# async def task_detail_handler(callback: types.CallbackQuery, bot: Bot):
#     await callback.answer()
#     task_id = int(callback.data.split('_')[1])
#     task = await DB.get_bonus_op(task_id)


#     target = task[1]
#     link = task[2]
#     try:
#         chat = await bot.get_chat(target)
#         chat_title = chat.title
#     except:
#         chat_title = "Ошибка: невозможно получить название"

#     task_info = f"""
# Название - <b>{chat_title}</b>

# Ссылка - {link}

# {target}  
#     """
#     builder = InlineKeyboardBuilder()
#     builder.add(types.InlineKeyboardButton(text="🔙 Назад", callback_data="bonus_admin"))
#     builder.add(types.InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"bonusdelete_{task_id}"))
#     await callback.message.edit_text(task_info, reply_markup=builder.as_markup())






# @admin.callback_query(lambda c: c.data.startswith("bonusdelete_"))
# async def delete_task_handler(callback: types.CallbackQuery):
#     id = int(callback.data.split('_')[1])

#     # Удаляем задачу из базы данных
#     await DB.remove_bonus_op(id)
#     await callback.message.edit_text("Удалено!")

#     # После удаления возвращаем пользователя к его заданиям

#     tasks = await DB.get_bonus_ops()
#     bonuspage = 1
#     tasks_on_page, total_pages = paginate_opbonus_tasks(tasks, bonuspage)
#     keyboard = generate_opbonus_keyboard(tasks_on_page, bonuspage, total_pages)

#     await callback.message.edit_text("Каналы/чаты в ОП бонусов", reply_markup=keyboard)







# @admin.callback_query(F.data == 'create_opbonus_task')
# async def create_op_task_handler(callback: types.CallbackQuery, state: FSMContext):
#     await callback.answer()
#     builder = InlineKeyboardBuilder()
#     builder.add(types.InlineKeyboardButton(text="❌ Назад", callback_data="back_admin"))
#     await callback.message.edit_text("Пришлите канал или чат в формате юзернейма, пример - @telegram", reply_markup=builder.as_markup())
#     await state.set_state(create_opbonus_tasks.create_op)

# @admin.message(create_opbonus_tasks.create_op)
# async def create_opbonus_task_handler2(message: types.Message, state: FSMContext, bot: Bot):
#     target_id = message.text.strip()
#     builder = InlineKeyboardBuilder()
#     builder.add(types.InlineKeyboardButton(text="❌ Назад", callback_data="back_admin"))
#     await message.answer("Пришлите свою ссылку на канал/чат",
#                                      reply_markup=builder.as_markup())
#     await state.update_data(target_id=target_id)
#     await state.set_state(create_opbonus_tasks.create_op2)

# @admin.message(create_opbonus_tasks.create_op2)
# async def create_opbonus_task_handler2(message: types.Message, state: FSMContext, bot: Bot):
#     link = message.text.strip()
#     data = await state.get_data()
#     target_id = data.get('target_id')

#     await DB.add_bonus_op(target_id, link)
#     builder = InlineKeyboardBuilder()
#     builder.add(types.InlineKeyboardButton(text="🔙 Вернуться в меню", callback_data="back_menu"))
#     await message.answer("🥳 Задание создано! Оно будет размещено в разделе бонусов", reply_markup=builder.as_markup())
#     await state.clear()















# @admin.callback_query(F.data == 'adminoutputlist')
# async def adminoutputlist(callback: types.CallbackQuery, state: FSMContext):
#     builder = InlineKeyboardBuilder()
#     builder.add(types.InlineKeyboardButton(text="USDT", callback_data="adminusdtoutputlist"))
#     builder.add(types.InlineKeyboardButton(text="Рубли", callback_data="adminruboutputlist"))
#     builder.add(types.InlineKeyboardButton(text="🔙", callback_data="back_admin"))
#     await callback.message.edit_text(f'<b>Выберите тип вывода:</b>', reply_markup=builder.as_markup())



# def generate_usdt_keyboard(outputs, usdtpage, total_pages):
#     builder = InlineKeyboardBuilder()
#     # Выводим задания на текущей странице (по 5 на страницу)
#     for output in outputs:
#         amount = output[3]

#         button_text = f"{amount}"
#         # Каждая кнопка в новой строке
#         builder.row(types.InlineKeyboardButton(text=button_text, callback_data=f"usdttask_{output[0]}"))

#     # Кнопка "Назад"
#     builder.row(types.InlineKeyboardButton(text="🔙 Назад", callback_data="back_admin"))
#     # Кнопки пагинации
#     pagination = []
#     if usdtpage > 1:
#         pagination.append(types.InlineKeyboardButton(text="⬅️", callback_data=f"usdtpage_{usdtpage - 1}"))
#     pagination.append(types.InlineKeyboardButton(text=str(usdtpage), callback_data="current_page"))
#     if usdtpage < total_pages:
#         pagination.append(types.InlineKeyboardButton(text="➡️", callback_data=f"usdtpage_{usdtpage + 1}"))

#     builder.row(*pagination)  # Кнопки пагинации в одну строку

#     return builder.as_markup()

# # Метод для получения страницы с заданиями (пагинация)
# def paginate_usdt_tasks(outputs, usdtpage=1, per_page=5):
#     total_pages = (len(outputs) + per_page - 1) // per_page  # Вычисление общего количества страниц
#     start_idx = (usdtpage - 1) * per_page
#     end_idx = start_idx + per_page
#     tasks_on_page = outputs[start_idx:end_idx]
#     return tasks_on_page, total_pages

# @admin.callback_query(F.data == 'adminusdtoutputlist')
# async def adminusdtoutputlist(callback: types.CallbackQuery):
#     outputs = await DB.get_usdt_outputs()
#     # Начинаем с первой страницы
#     usdtpage = 1
#     tasks_on_page, total_pages = paginate_usdt_tasks(outputs, usdtpage)
#     # Генерируем инлайн кнопки
#     keyboard = generate_usdt_keyboard(tasks_on_page, usdtpage, total_pages)
#     await callback.message.edit_text("Список заявок на вывод в <b>USDT (BEP20)</b>", reply_markup=keyboard)


# @admin.callback_query(lambda c: c.data.startswith("usdtpage_"))
# async def change_page_handler(callback: types.CallbackQuery):
#     usdtpage = int(callback.data.split('_')[1])
#     outputs = await DB.get_usdt_outputs()

#     # Получаем задания на нужной странице
#     tasks_on_page, total_pages = paginate_usdt_tasks(outputs, usdtpage)

#     # Генерируем инлайн кнопки
#     keyboard = generate_usdt_keyboard(tasks_on_page, usdtpage, total_pages)
#     await callback.message.edit_text("Список заявок на вывод в <b>USDT (BEP20)</b>", reply_markup=keyboard)


# @admin.callback_query(lambda c: c.data.startswith("usdttask_"))
# async def task_detail_handler(callback: types.CallbackQuery, bot: Bot):
#     await callback.answer()
#     id = int(callback.data.split('_')[1])
#     output = await DB.get_output(id)
#     if output is not None:
#         try:
#             user_id = output[1]
#         except:
#             user_id = "ошибка"
#         try:
#             wallet = output[2]
#         except:
#             wallet = "ошибка"
#         try:
#             amount = output[3]
#         except:
#             amount = "ошибка"

#         task_info = f"""
# 📤 <b>Заявка на вывод в USDT:</b>
# <b>ID</b> - <code>{user_id}</code>
    
# 👛 <b>Кошелек USDT(BEP20)</b> - 
# <code>{wallet}</code>
    
# 💲 <b>Сумма</b> - <code>{amount}</code>
    
# <span class="tg-spoiler">⚠ При нажатии кнопки <b>Выполнено</b> заявка удаляется из списка и рубли на баланс юзера НЕ ВОЗВРАЩАЮТСЯ</span>
#         """
#         builder = InlineKeyboardBuilder()
#         builder.add(types.InlineKeyboardButton(text="✅ Выполнено", callback_data=f"usdtsuc_{id}"))
#         builder.add(types.InlineKeyboardButton(text="❌ Отклонить", callback_data=f"usdtdelete_{id}"))
#         builder.add(types.InlineKeyboardButton(text="🔙 Назад", callback_data="adminusdtoutputlist"))
#         await callback.message.edit_text(task_info, reply_markup=builder.as_markup())
#     else:
#         builder = InlineKeyboardBuilder()
#         builder.add(types.InlineKeyboardButton(text="🔙 Назад", callback_data="adminusdtoutputlist"))
#         await callback.message.edit_text("Заявка не найдена", reply_markup=builder.as_markup())

# @admin.callback_query(lambda c: c.data.startswith("usdtdelete_"))
# async def delete_task_handler(callback: types.CallbackQuery, bot: Bot):
#     id = int(callback.data.split('_')[1])
#     # Удаляем задачу из базы данных
#     output = await DB.get_output(id)
#     user_id = output[1]
#     await DB.delete_output(id)
#     await callback.message.edit_text("❌ Отклонено")
#     await bot.send_message(chat_id=user_id, text='☹ Ваша заявка на вывод отклонена', reply_markup=back_menu_kb(user_id))
#     outputs = await DB.get_usdt_outputs()
#     usdtpage = 1

#     tasks_on_page, total_pages = paginate_usdt_tasks(outputs, usdtpage)
#     keyboard = generate_usdt_keyboard(tasks_on_page, usdtpage, total_pages)
#     await callback.message.edit_text("Список заявок на вывод в <b>USDT</b>", reply_markup=keyboard)


# @admin.callback_query(lambda c: c.data.startswith("usdtsuc_"))
# async def delete_task_handler(callback: types.CallbackQuery, bot: Bot):
#     id = int(callback.data.split('_')[1])

#     output = await DB.get_output(id)
#     user_id = output[1]
#     await DB.delete_output(id)
#     await callback.message.edit_text("✅ Выполнено")
#     await bot.send_message(chat_id=user_id, text='🥳 Ваша заявка на вывод одобрена!', reply_markup=back_menu_kb(user_id))
#     outputs = await DB.get_usdt_outputs()
#     usdtpage = 1

#     tasks_on_page, total_pages = paginate_usdt_tasks(outputs, usdtpage)
#     keyboard = generate_usdt_keyboard(tasks_on_page, usdtpage, total_pages)
#     await callback.message.edit_text("Список заявок на вывод в <b>USDT</b>", reply_markup=keyboard)
















# def generate_rub_keyboard(outputs, rubpage, total_pages):
#     builder = InlineKeyboardBuilder()
#     # Выводим задания на текущей странице (по 5 на страницу)
#     for output in outputs:
#         amount = output[3]

#         button_text = f"{amount}"
#         # Каждая кнопка в новой строке
#         builder.row(types.InlineKeyboardButton(text=button_text, callback_data=f"rubtask_{output[0]}"))

#     # Кнопка "Назад"
#     builder.row(types.InlineKeyboardButton(text="🔙 Назад", callback_data="back_admin"))
#     # Кнопки пагинации
#     pagination = []
#     if rubpage > 1:
#         pagination.append(types.InlineKeyboardButton(text="⬅️", callback_data=f"rubpage_{rubpage - 1}"))
#     pagination.append(types.InlineKeyboardButton(text=str(rubpage), callback_data="current_page"))
#     if rubpage < total_pages:
#         pagination.append(types.InlineKeyboardButton(text="➡️", callback_data=f"rubpage_{rubpage + 1}"))

#     builder.row(*pagination)  # Кнопки пагинации в одну строку

#     return builder.as_markup()


# # Метод для получения страницы с заданиями (пагинация)
# def paginate_rub_tasks(outputs, rubpage=1, per_page=5):
#     total_pages = (len(outputs) + per_page - 1) // per_page  # Вычисление общего количества страниц
#     start_idx = (rubpage - 1) * per_page
#     end_idx = start_idx + per_page
#     tasks_on_page = outputs[start_idx:end_idx]
#     return tasks_on_page, total_pages


# @admin.callback_query(F.data == 'adminruboutputlist')
# async def adminruboutputlist(callback: types.CallbackQuery):
#     outputs = await DB.get_rub_outputs()
#     # Начинаем с первой страницы
#     rubpage = 1
#     tasks_on_page, total_pages = paginate_rub_tasks(outputs, rubpage)
#     # Генерируем инлайн кнопки
#     keyboard = generate_rub_keyboard(tasks_on_page, rubpage, total_pages)
#     await callback.message.edit_text("Список заявок на вывод в <b>рублях</b>", reply_markup=keyboard)


# @admin.callback_query(lambda c: c.data.startswith("rubpage_"))
# async def change_rubpage_handler(callback: types.CallbackQuery):
#     rubpage = int(callback.data.split('_')[1])
#     outputs = await DB.get_rub_outputs()

#     # Получаем задания на нужной странице
#     tasks_on_page, total_pages = paginate_rub_tasks(outputs, rubpage)

#     # Генерируем инлайн кнопки
#     keyboard = generate_rub_keyboard(tasks_on_page, rubpage, total_pages)
#     await callback.message.edit_text("Список заявок на вывод в <b>рублях</b>", reply_markup=keyboard)


# @admin.callback_query(lambda c: c.data.startswith("rubtask_"))
# async def task_detail_handler(callback: types.CallbackQuery, bot: Bot):
#     await callback.answer()
#     id = int(callback.data.split('_')[1])
#     output = await DB.get_output(id)
#     if output is not None:
#         try:
#             user_id = output[1]
#         except:
#             user_id = "ошибка"
#         try:
#             wallet = output[2]
#         except:
#             wallet = "ошибка"
#         try:
#             amount = output[3]
#         except:
#             amount = "ошибка"

#         task_info = f"""
# 📤 <b>Заявка на вывод в рублях:</b>
# <b>ID</b> - <code>{user_id}</code>

# 💳 <b>Карта/телефон(для СБП)</b> - 
# <code>{wallet}</code>

# 💲 <b>Сумма</b> - <code>{amount}</code>

# <span class="tg-spoiler">⚠ При нажатии кнопки <b>Отклонить</b> заявка удаляется из списка и рубли на баланс юзера НЕ ВОЗВРАЩАЮТСЯ</span>
#         """
#         builder = InlineKeyboardBuilder()
#         builder.add(types.InlineKeyboardButton(text="✅ Выполнено", callback_data=f"rubsuc_{id}"))
#         builder.add(types.InlineKeyboardButton(text="❌ Отклонить", callback_data=f"rubdelete_{id}"))
#         builder.add(types.InlineKeyboardButton(text="🔙", callback_data="adminruboutputlist"))
#         await callback.message.edit_text(task_info, reply_markup=builder.as_markup())
#     else:
#         builder = InlineKeyboardBuilder()
#         builder.add(types.InlineKeyboardButton(text="🔙 Назад", callback_data="adminruboutputlist"))
#         await callback.message.edit_text("Заявка не найдена", reply_markup=builder.as_markup())


# @admin.callback_query(lambda c: c.data.startswith("rubdelete_"))
# async def delete_task_handler(callback: types.CallbackQuery, bot: Bot):
#     id = int(callback.data.split('_')[1])
#     # Удаляем задачу из базы данных
#     output = await DB.get_output(id)
#     user_id = output[1]
#     await DB.delete_output(id)
#     await callback.message.edit_text("❌ Отклонено")
#     await bot.send_message(chat_id=user_id, text='☹ Ваша заявка на вывод отклонена', reply_markup=back_menu_kb(user_id))
#     outputs = await DB.get_rub_outputs()
#     rubpage = 1

#     tasks_on_page, total_pages = paginate_rub_tasks(outputs, rubpage)
#     keyboard = generate_rub_keyboard(tasks_on_page, rubpage, total_pages)
#     await callback.message.edit_text("Список заявок на вывод в <b>рублях</b>", reply_markup=keyboard)


# @admin.callback_query(lambda c: c.data.startswith("rubsuc_"))
# async def delete_task_handler(callback: types.CallbackQuery, bot: Bot):
#     id = int(callback.data.split('_')[1])

#     output = await DB.get_output(id)
#     user_id = output[1]
#     await DB.delete_output(id)
#     await callback.message.edit_text("✅ Выполнено")
#     await bot.send_message(chat_id=user_id, text='🥳 Ваша заявка на вывод одобрена!', reply_markup=back_menu_kb(user_id))
#     outputs = await DB.get_rub_outputs()
#     rubpage = 1

#     tasks_on_page, total_pages = paginate_rub_tasks(outputs, rubpage)
#     keyboard = generate_rub_keyboard(tasks_on_page, rubpage, total_pages)
#     await callback.message.edit_text("Список заявок на вывод в <b>рублях</b>", reply_markup=keyboard)




























# # Назначим текстовые представления для типов заданий



# def generate_tasks_keyboard(chating_tasks, chatingpage, total_pages):
#     builder = InlineKeyboardBuilder()

#     # Выводим задания на текущей странице (по 5 на страницу)
#     for task in chating_tasks:

#         price = task[2]
#         button_text = f"ЧАТ | {price}"
#         # Каждая кнопка в новой строке
#         builder.row(types.InlineKeyboardButton(text=button_text, callback_data=f"chatingtask_{task[0]}"))

#     # Кнопка "Назад"
#     builder.row(types.InlineKeyboardButton(text="🔥 Создать", callback_data="create_chating_task"))
#     builder.row(types.InlineKeyboardButton(text="🔙 Назад", callback_data="back_admin"))
#     # Кнопки пагинации
#     pagination = []
#     if chatingpage > 1:
#         pagination.append(types.InlineKeyboardButton(text="⬅️", callback_data=f"chatingpage_{chatingpage - 1}"))
#     pagination.append(types.InlineKeyboardButton(text=str(chatingpage), callback_data="current_page"))
#     if chatingpage < total_pages:
#         pagination.append(types.InlineKeyboardButton(text="➡️", callback_data=f"chatingpage_{chatingpage + 1}"))

#     builder.row(*pagination)  # Кнопки пагинации в одну строку

#     return builder.as_markup()


# # Метод для получения страницы с заданиями (пагинация)
# def paginate_tasks(tasks, chatingpage=1, per_page=5):
#     total_pages = (len(tasks) + per_page - 1) // per_page  # Вычисление общего количества страниц
#     start_idx = (chatingpage - 1) * per_page
#     end_idx = start_idx + per_page
#     tasks_on_page = tasks[start_idx:end_idx]
#     return tasks_on_page, total_pages


# @admin.callback_query(F.data == 'chat_privyazka')
# async def chating_tasks_handler(callback: types.CallbackQuery, bot: Bot):
#     user_id = callback.from_user.id
#     tasks = await DB.get_chating_tasks()

#     # Начинаем с первой страницы
#     chatingpage = 1
#     tasks_on_page, total_pages = paginate_tasks(tasks, chatingpage)

#     # Генерируем инлайн кнопки
#     keyboard = generate_tasks_keyboard(tasks_on_page, chatingpage, total_pages)

#     await callback.message.edit_text("Привязанные чаты:", reply_markup=keyboard)




# @admin.callback_query(lambda c: c.data.startswith("chatingpage_"))
# async def change_page_handler(callback: types.CallbackQuery):
#     chatingpage = int(callback.data.split('_')[1])
#     user_id = callback.from_user.id
#     tasks = await DB.get_chating_tasks()

#     # Получаем задания на нужной странице
#     tasks_on_page, total_pages = paginate_tasks(tasks, chatingpage)

#     # Генерируем инлайн кнопки
#     keyboard = generate_tasks_keyboard(tasks_on_page, chatingpage, total_pages)

#     await callback.message.edit_text("Привязанные чаты:", reply_markup=keyboard)



# # Функция для проверки прав админа и генерации ссылки
# async def check_admin_and_get_invite_link(bot, chat_id):
#     try:
#         chat_administrators = await bot.get_chat_administrators(chat_id)
#         # Проверяем, является ли бот администратором
#         for admin in chat_administrators:
#             if admin.user.id == bot.id:
#                 # Если бот админ, генерируем ссылку-приглашение
#                 invite_link = await bot.export_chat_invite_link(chat_id)
#                 return invite_link
#         # Если бот не админ
#         return "😑 Предоставьте боту права администратора в чате!"
#     except:
#         return "😑 Предоставьте боту права администратора в чате!"

# @admin.callback_query(lambda c: c.data.startswith("chatingtask_"))
# async def task_detail_handler(callback: types.CallbackQuery, bot: Bot):
#     await callback.answer()
#     task_id = int(callback.data.split('_')[1])
#     task = await DB.get_chating_task_by_id(task_id)


#     try:
#         chat_id = task[1]
#         price = task[2]
#         chat = await bot.get_chat(chat_id)
#         invite_link = await check_admin_and_get_invite_link(bot, task[1])
#         chat_title = chat.title
#     except:
#         chat_title = '<i>Ошибка</i>'
#         invite_link = '<i>Ошибка</i>'
#         price = '<i>Ошибка</i>'

#     task_info = f"""
# Чат - {chat_title}

# 💰 Плата за 1 сообщение - {price} MITcoin 

# {invite_link}    
#     """
#     builder = InlineKeyboardBuilder()
#     builder.add(types.InlineKeyboardButton(text="🔙 Назад", callback_data="chat_privyazka"))
#     builder.add(types.InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"chatingdelete_{task_id}"))
#     await callback.message.edit_text(task_info, reply_markup=builder.as_markup())






# @admin.callback_query(lambda c: c.data.startswith("chatingdelete_"))
# async def delete_task_handler(callback: types.CallbackQuery):
#     task_id = int(callback.data.split('_')[1])

#     # Удаляем задачу из базы данных
#     await DB.delete_chating_task(task_id)
#     await callback.message.edit_text("Чат удален!")

#     # После удаления возвращаем пользователя к его заданиям

#     tasks = await DB.get_chating_tasks()
#     chatingpage = 1
#     tasks_on_page, total_pages = paginate_tasks(tasks, chatingpage)
#     keyboard = generate_tasks_keyboard(tasks_on_page, chatingpage, total_pages)

#     await callback.message.edit_text("Привязанные чаты:", reply_markup=keyboard)







# @admin.callback_query(F.data == 'create_chating_task')
# async def create_chating_task_handler(callback: types.CallbackQuery, state: FSMContext):
#     await callback.answer()
#     await callback.message.edit_text('Введите вознаграждение за 1 сообщение в чате:', reply_markup=cancel_all_kb())
#     await state.set_state(create_chating_tasks.create_task)

# @admin.message(create_chating_tasks.create_task)
# async def create_chating_task_handler2(message: types.Message, state: FSMContext):
#     price = int(message.text.strip())
#     try:
#         await state.update_data(price=price)
#         builder = InlineKeyboardBuilder()
#         builder.add(types.InlineKeyboardButton(text="✅ Продолжить", callback_data="pr_chating_confirm"))
#         builder.add(types.InlineKeyboardButton(text="❌ Назад", callback_data="back_admin"))
#         await message.answer(f'👥 Оплата за 1 сообщение - {price} MITcoin\n\nНажмите Продолжить или напишите другое число...', reply_markup=builder.as_markup())
#     except ValueError:
#         await message.answer('<b>Ошибка ввода</b>\nПопробуй ввести целое число...', reply_markup=pr_menu_canc())


# @admin.callback_query(F.data == 'pr_chating_confirm')
# async def pr_chat3(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
#     data = await state.get_data()
#     price = data.get('price')
#     await state.clear()
#     bot_username = (await bot.get_me()).username
#     invite_link = f"https://t.me/{bot_username}?startgroup&admin=invite_users+manage_chat"

#     add_button = InlineKeyboardButton(text="➕ Добавить бота в чат", url=invite_link)
#     add_button1 = InlineKeyboardButton(text="❌ Отмена", callback_data='pr_menu_cancel')
#     # Создаем клавиатуру и добавляем в нее кнопку
#     keyboard = InlineKeyboardMarkup(inline_keyboard=[[add_button], [add_button1]])
#     await callback.message.edit_text(f'''
# 👾 Теперь необходимо добавить бота в ваш чат и предоставить ему права администратора, для этого...

# <em>Добавьте бота в чат с помощью кнопки снизу -> предоставьте боту права админа -> перешлите в этот чат сообщение бота с кодом</em>
#         ''', reply_markup=keyboard)
#     await state.set_state(create_chating_tasks.create_task2)
#     await state.update_data(price=price)


# @admin.message(create_chating_tasks.create_task2)
# async def pr_chating4(message: types.Message, state: FSMContext, bot: Bot):
#     data = await state.get_data()
#     price = data.get('price')
#     user_id = message.from_user.id
#     bot_info = await bot.get_me()
#     code = message.text.strip()
#     code_chat_id, code_user_id = map(int, code.split(":"))
#     print(f'chat_id-{code_chat_id}; code_user_id - {code_user_id}, real user id - {user_id}')
#     if user_id == code_user_id:
#         try:
#             bot_member = await bot.get_chat_member(chat_id=code_chat_id, user_id=bot_info.id)
#         except Exception as e:
#             await message.answer(f"🫤 Не удалось получить информацию о чате. Убедитесь, что бот добавлен в группу.", reply_markup=pr_menu_canc())
#             return

#             # Проверяем, является ли бот администратором
#         if bot_member.status != ChatMemberStatus.ADMINISTRATOR:
#             await message.answer(
#                 "🫤 Бот не является администратором в этой группе. Пожалуйста, предоставьте боту права администратора и перешлите сообщение заново", reply_markup=pr_menu_canc())
#             return

#         builder = InlineKeyboardBuilder()
#         builder.add(types.InlineKeyboardButton(text="🔙 Вернуться в меню", callback_data="back_menu"))
#         await message.answer(
#             "🥳 Задание создано! Оно будет размещено в разделе <b>Заработать</b>\n",
#             reply_markup=builder.as_markup())
#         user_id = message.from_user.id

#         await DB.add_chating_task(chat_id=code_chat_id, price=price)
#         await bot.send_message(code_chat_id, '🥳 Настройка бота успешно завершена!')
#         await state.clear()
#         tasks = await DB.get_chating_tasks()
#         for task in tasks:
#             print('Задания - ', task)
#     else:
#         await message.answer("🫤 Проверьте, добавлен ли бот в группу и повторите попытку...", reply_markup=pr_menu_canc())




# @admin.callback_query(F.data == 'clean_task')
# async def delete_all_tasks(callback: types.CallbackQuery):
#     builder = InlineKeyboardBuilder()
#     builder.add(types.InlineKeyboardButton(text="✅ ДА", callback_data='clean_task_confirm'))
#     builder.add(types.InlineKeyboardButton(text="❌ НЕТ", callback_data='back_admin'))
#     await callback.message.edit_text('Вы уверены, что хотите удалить все задания?', reply_markup=builder.as_markup())

# @admin.callback_query(F.data == 'clean_task_confirm')
# async def delete_all_tasks_confirm(callback: types.CallbackQuery):
#     # Выполнение метода удаления заданий и возврата средств
#     await DB.clear_tasks_and_refund()
#     builder = InlineKeyboardBuilder()
#     builder.add(types.InlineKeyboardButton(text="В меню", callback_data='back_admin'))
#     await callback.message.edit_text('Все задания удалены, бабки возвращены', reply_markup=builder.as_markup())





# @admin.callback_query(F.data == 'sum_deposit')
# async def view_user_profile_handler(callback: types.CallbackQuery, state: FSMContext):
#     all_deps = await DB.get_total_deposits()
#     await callback.message.answer(f'сумма всех пополнений - {all_deps} usdt')


# @admin.callback_query(F.data == 'view_user_profile')
# async def view_user_profile_handler(callback: types.CallbackQuery, state: FSMContext):
#     await callback.message.answer('Введите ID пользователя для просмотра его профиля', reply_markup=cancel_all_kb())
#     await state.set_state(AdminActions.view_user_profile)
#     await callback.answer()





# @admin.message(AdminActions.view_user_profile)
# async def get_user_profile(message: types.Message, state: FSMContext):
#     user_id = message.text
#     try:
#         user = await DB.select_user(user_id)
#         if user:

#             balance = user['balance'] if user['balance'] is not None else 0
#             rub_balance = user['rub_balance'] if user['rub_balance'] is not None else 0
#             # Задания пользователя
#             tasks = await DB.get_tasks_by_user_admin(user_id)

#             chanel_tasks = [f"Канал | task_id - {task_id}" for task_id, type in tasks if type == 1]
#             chat_tasks = [f"Чат | task_id - {task_id}" for task_id, type in tasks if type == 2]
#             post_tasks = [f"Пост | task_id - {task_id}" for task_id, type in tasks if type == 3]

#             # Информация о донатах
#             donation_count = await DB.count_user_deposits(user_id)  # количество донатов
#             donation_sum = await DB.sum_user_deposits(user_id)  # сумма донатов

#             # Информация о рефералах
#             referral_count = await DB.get_referred_users(user_id)  # количество приглашенных пользователей
#             referral_earnings = await DB.get_earned_from_referrals(user_id)  # заработок с рефералов

#             # Примерный заработок с выполненных заданий
#             completed_tasks_count = await DB.count_user_completed_tasks(user_id)
#             approx_task_earnings = completed_tasks_count * 1700

#             # Форматирование текста с HTML-разметкой
#             profile_text = f"""
# 🆔 ID - <code>{user_id}</code> / <a href='tg://user?id={user_id}'>КЛИК</a>

# 💵 MitCoin - {balance} $MICO
# 💵 Рубли - {rub_balance}₽

# 💼 Задания:

# {chr(10).join(chanel_tasks)}
# {chr(10).join(chat_tasks)}
# {chr(10).join(post_tasks)}

# Примерно заработано с заданий - {approx_task_earnings}

# 💰 Количество донатов - {donation_count}
# 🎰 Сумма донатов - {donation_sum}

# 👥 Количество приглашенных пользователей - {len(referral_count)}
# 💸Заработано с рефералов - {referral_earnings}
# """

#             # Создание клавиатуры
#             builder = InlineKeyboardBuilder()
#             builder.add(types.InlineKeyboardButton(text="✏ Баланс", callback_data=f'update_balance:{user_id}'))
#             builder.add(types.InlineKeyboardButton(text="✏ Руб Баланс", callback_data=f'update_rub_balance:{user_id}'))
#             await message.answer(profile_text, reply_markup=builder.as_markup())
#         else:
#             await message.answer('Пользователь не найден 😓')
#     except Exception as e:
#         await message.answer(f"Произошла ошибка при получении профиля пользователя: {str(e)}")
#         print(e)
#     finally:
#         await state.clear()

















# @admin.callback_query(lambda c: c.data.startswith('update_balance:'))
# async def update_balance_handler(callback: types.CallbackQuery, state: FSMContext):
#     user_id = callback.data.split(':')[1]
#     await state.update_data(user_id=user_id)
#     await callback.message.answer('Введите новый баланс пользователя:')
#     await state.set_state(AdminActions.update_balance)
#     await callback.answer()



# @admin.message(AdminActions.update_balance)
# async def set_new_balance(message: types.Message, state: FSMContext):
#     data = await state.get_data()
#     user_id = data['user_id']
#     new_balance = int(message.text)
#     await DB.update_balance(user_id, balance=new_balance)
#     await message.answer(f"Баланс пользователя {user_id} обновлен до {new_balance}.")
#     await state.clear()







# @admin.callback_query(lambda c: c.data.startswith('update_rub_balance:'))
# async def update_rub_balance_handler(callback: types.CallbackQuery, state: FSMContext):
#     user_id = callback.data.split(':')[1]
#     await state.update_data(user_id=user_id)
#     await callback.message.answer('Введите новый баланс пользователя в рублях:')
#     await state.set_state(AdminActions.update_rub_balance)
#     await callback.answer()




# @admin.message(AdminActions.update_rub_balance)
# async def set_new_rub_balance(message: types.Message, state: FSMContext):
#     data = await state.get_data()
#     user_id = data['user_id']
#     new_balance = int(message.text)
#     await DB.update_rub_balance(user_id, rub_balance=new_balance)
#     await message.answer(f"Баланс (Рубли) пользователя {user_id} обновлен до {new_balance}.")
#     await state.clear()














# def generate_op_tasks_keyboard(op_tasks, oppage, total_pages):
#     builder = InlineKeyboardBuilder()

#     # Выводим задания на текущей странице (по 5 на страницу)
#     for task in op_tasks:
#         chat_id = task[1]

#         button_text = f"{chat_id}"
#         # Каждая кнопка в новой строке
#         builder.row(types.InlineKeyboardButton(text=button_text, callback_data=f"optask_{task[0]}"))

#     # Кнопка "Назад"
#     builder.row(types.InlineKeyboardButton(text="Создать 🔥", callback_data="create_op_task"))
#     builder.row(types.InlineKeyboardButton(text="🔙 Назад", callback_data="back_admin"))
#     # Кнопки пагинации
#     pagination = []
#     if oppage > 1:
#         pagination.append(types.InlineKeyboardButton(text="⬅️", callback_data=f"oppage_{oppage - 1}"))
#     pagination.append(types.InlineKeyboardButton(text=str(oppage), callback_data="current_page"))
#     if oppage < total_pages:
#         pagination.append(types.InlineKeyboardButton(text="➡️", callback_data=f"oppage_{oppage + 1}"))

#     builder.row(*pagination)  # Кнопки пагинации в одну строку

#     return builder.as_markup()


# # Метод для получения страницы с заданиями (пагинация)
# def paginate_op_tasks(tasks, oppage=1, per_page=5):
#     total_pages = (len(tasks) + per_page - 1) // per_page  # Вычисление общего количества страниц
#     start_idx = (oppage - 1) * per_page
#     end_idx = start_idx + per_page
#     tasks_on_page = tasks[start_idx:end_idx]
#     return tasks_on_page, total_pages


# @admin.callback_query(F.data == 'op_pr_menu')
# async def chating_tasks_handler(callback: types.CallbackQuery):
#     tasks = await DB.get_op_tasks()
#     # Начинаем с первой страницы
#     oppage = 1
#     tasks_on_page, total_pages = paginate_op_tasks(tasks, oppage)
#     # Генерируем инлайн кнопки
#     keyboard = generate_op_tasks_keyboard(tasks_on_page, oppage, total_pages)
#     await callback.message.edit_text("Каналы/чаты в ОП", reply_markup=keyboard)




# @admin.callback_query(lambda c: c.data.startswith("oppage_"))
# async def change_page_handler(callback: types.CallbackQuery):
#     oppage = int(callback.data.split('_')[1])
#     user_id = callback.from_user.id
#     tasks = await DB.get_op_tasks()

#     # Получаем задания на нужной странице
#     tasks_on_page, total_pages = paginate_op_tasks(tasks, oppage)

#     # Генерируем инлайн кнопки
#     keyboard = generate_op_tasks_keyboard(tasks_on_page, oppage, total_pages)

#     await callback.message.edit_text("Каналы/чаты в ОП", reply_markup=keyboard)




# @admin.callback_query(lambda c: c.data.startswith("optask_"))
# async def task_detail_handler(callback: types.CallbackQuery, bot: Bot):
#     await callback.answer()
#     task_id = int(callback.data.split('_')[1])
#     task = await DB.get_op_task_by_id(task_id)


#     target = task[1]
#     text = task[2]
#     try:
#         chat = await bot.get_chat(target)
#         chat_title = chat.title
#     except:
#         chat_title = "Ошибка: невозможно получить название"
#     task_info = f"""
# Название - <b>{chat_title}</b>

# Текст - {text}

# {target}  
#     """
#     builder = InlineKeyboardBuilder()
#     builder.add(types.InlineKeyboardButton(text="🔙 Назад", callback_data="op_pr_menu"))
#     builder.add(types.InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"opdelete_{task_id}"))
#     await callback.message.edit_text(task_info, reply_markup=builder.as_markup())






# @admin.callback_query(lambda c: c.data.startswith("opdelete_"))
# async def delete_task_handler(callback: types.CallbackQuery):
#     task_id = int(callback.data.split('_')[1])

#     # Удаляем задачу из базы данных
#     await DB.delete_op_task(task_id)
#     await callback.message.edit_text("Удалено!")

#     # После удаления возвращаем пользователя к его заданиям

#     tasks = await DB.get_op_tasks()
#     oppage = 1
#     tasks_on_page, total_pages = paginate_tasks(tasks, oppage)
#     keyboard = generate_op_tasks_keyboard(tasks_on_page, oppage, total_pages)

#     await callback.message.edit_text("Чаты/каналы в ОП", reply_markup=keyboard)







# @admin.callback_query(F.data == 'create_op_task')
# async def create_op_task_handler(callback: types.CallbackQuery, state: FSMContext):
#     await callback.answer()
#     builder = InlineKeyboardBuilder()
#     builder.add(types.InlineKeyboardButton(text="❌ Назад", callback_data="back_admin"))
#     await callback.message.edit_text("Пришлите канал или чат в формате юзернейма, пример - @telegram", reply_markup=builder.as_markup())
#     await state.set_state(create_op_tasks.create_op_task)

# @admin.message(create_op_tasks.create_op_task)
# async def create_op_task_handler2(message: types.Message, state: FSMContext, bot: Bot):
#     target_id = message.text.strip()
#     builder = InlineKeyboardBuilder()
#     builder.add(types.InlineKeyboardButton(text="❌ Назад", callback_data="back_admin"))
#     await message.answer("Пришлите текст, в который будет вставлена ссылка",
#                                      reply_markup=builder.as_markup())
#     await state.update_data(target_id=target_id)
#     await state.set_state(create_op_tasks.create_op_task2)

# @admin.message(create_op_tasks.create_op_task2)
# async def create_op_task_handler2(message: types.Message, state: FSMContext, bot: Bot):
#     text = message.text.strip()
#     data = await state.get_data()
#     target_id = data.get('target_id')

#     await DB.add_op_task(target_id, text)
#     builder = InlineKeyboardBuilder()
#     builder.add(types.InlineKeyboardButton(text="🔙 Вернуться в меню", callback_data="back_menu"))
#     await message.answer("🥳 Задание создано! Оно будет размещено в сообщениях к ОП", reply_markup=builder.as_markup())
#     await state.clear()


















# # Назначим текстовые представления для типов заданий



# def generate_tasks_keyboard_report(reports, reportpage, total_pages):
#     builder = InlineKeyboardBuilder()

#     # Выводим задания на текущей странице (по 5 на страницу)
#     for report in reports:

#         id = report[0]
#         button_text = f"№{id}"
#         # Каждая кнопка в новой строке
#         builder.row(types.InlineKeyboardButton(text=button_text, callback_data=f"report_{report[0]}"))

#     # Кнопка "Назад"
#     builder.row(types.InlineKeyboardButton(text="🔙 Назад", callback_data="back_admin"))
#     # Кнопки пагинации
#     pagination = []
#     if reportpage > 1:
#         pagination.append(types.InlineKeyboardButton(text="⬅️", callback_data=f"reportpage_{reportpage - 1}"))
#     pagination.append(types.InlineKeyboardButton(text=str(reportpage), callback_data="current_page"))
#     if reportpage < total_pages:
#         pagination.append(types.InlineKeyboardButton(text="➡️", callback_data=f"reportpage_{reportpage + 1}"))

#     builder.row(*pagination)  # Кнопки пагинации в одну строку

#     return builder.as_markup()


# # Метод для получения страницы с заданиями (пагинация)
# def paginate_tasks_report(reports, reportpage=1, per_page=5):
#     total_pages = (len(reports) + per_page - 1) // per_page  # Вычисление общего количества страниц
#     start_idx = (reportpage - 1) * per_page
#     end_idx = start_idx + per_page
#     tasks_on_page = reports[start_idx:end_idx]
#     return tasks_on_page, total_pages


# @admin.callback_query(F.data == 'reports_list_menu')
# async def chating_tasks_handler(callback: types.CallbackQuery, bot: Bot):
#     user_id = callback.from_user.id
#     reports = await DB.get_reports()

#     # Начинаем с первой страницы
#     reportpage = 1
#     tasks_on_page, total_pages = paginate_tasks_report(reports, reportpage)

#     # Генерируем инлайн кнопки
#     keyboard = generate_tasks_keyboard_report(tasks_on_page, reportpage, total_pages)

#     await callback.message.edit_text("Все репорты:", reply_markup=keyboard)




# @admin.callback_query(lambda c: c.data.startswith("reportpage_"))
# async def change_page_handler(callback: types.CallbackQuery):
#     reportpage = int(callback.data.split('_')[1])
#     user_id = callback.from_user.id
#     reports = await DB.get_reports()

#     # Получаем задания на нужной странице
#     tasks_on_page, total_pages = paginate_tasks_report(reports, reportpage)

#     # Генерируем инлайн кнопки
#     keyboard = generate_tasks_keyboard_report(tasks_on_page, reportpage, total_pages)

#     await callback.message.edit_text("Все репорты:", reply_markup=keyboard)



# # Функция для проверки прав админа и генерации ссылки
# async def check_admin_and_get_invite_link_report(bot, chat_id):
#     try:
#         chat_administrators = await bot.get_chat_administrators(chat_id)
#         # Проверяем, является ли бот администратором
#         for admin in chat_administrators:
#             if admin.user.id == bot.id:
#                 try:
#                     ChatFullInfo = await bot.get_chat(chat_id)
#                     invite_link = ChatFullInfo.invite_link
#                     if invite_link is None:
#                         return "Бот был забанен в чате, либо не является админом"
#                     return invite_link

#                 except Exception as e:
#                     print(f'ошибка получения инвайта для {chat_id}, ошибка - {e}')
#                     return "Бот был забанен в чате, либо не является админом"
#         # Если бот не админ
#         return "Бот был забанен в чате, либо не является админом"
#     except:
#         return "Бот был забанен в чате, либо не является админом"

# @admin.callback_query(lambda c: c.data.startswith("report_"))
# async def task_detail_handler(callback: types.CallbackQuery, bot: Bot):
#     await callback.answer()
#     report_id = int(callback.data.split('_')[1])
#     try:
#         report = await DB.get_report(report_id)
#     except:
#         await callback.message.answer('Ошибка получения информации о репорте')
#         return
#     try:
#         reporter = report[3]
#     except:
#         reporter = "Неизвестный, рекомендую удалить репорт"

#     try:
#         task_id = report[1]
#         chat_id = report[2]
#         report_id = report[0]
#     except:
#         task_id = "Неизвестное задание, рекомендую удалить репорт"
#         chat_id = "Неизвестный чат айди, рекомендую удалить репорт"
#         report_id = "Неизвестный репорт, рекомендую удалить репорт"

#     try:
#         task = await DB.get_task_by_id(task_id)
#         if task is None:
#             keyboard_builder = InlineKeyboardBuilder()
#             # Добавляем кнопки
#             keyboard_builder.add(
#                 InlineKeyboardButton(text="❌ Удалить задание", callback_data=f"reporttaskdelete_{task_id}_{report_id}"),
#                 InlineKeyboardButton(text="❌💵 Удалить задание (+возврат MIT) ",
#                                      callback_data=f"taskcashbackdelete_{task_id}_{report_id}"),
#                 InlineKeyboardButton(text="❌⚠️ Удалить задание (+ БАН)",
#                                      callback_data=f"taskbandelete_{task_id}_{report_id}"),
#                 InlineKeyboardButton(text="🗑️ Удалить репорт", callback_data=f"reportdelete_{report_id}"),
#                 InlineKeyboardButton(text="🔙 Назад", callback_data="reports_list_menu")

#             )

#             # Устанавливаем количество кнопок в ряду (1 кнопка на ряд)
#             keyboard_builder.adjust(1)
#             # Получаем клавиатуру
#             keyboard = keyboard_builder.as_markup()
#             await callback.message.answer(f'Не удалось получить информацию о задании, ошибка',
#                                           reply_markup=keyboard)
#             return

#     except Exception as e:
#         task = None
#         keyboard_builder = InlineKeyboardBuilder()
#         # Добавляем кнопки
#         keyboard_builder.add(
#             InlineKeyboardButton(text="❌ Удалить задание", callback_data=f"reporttaskdelete_{task_id}_{report_id}"),
#             InlineKeyboardButton(text="❌💵 Удалить задание (+возврат MIT) ",
#                                  callback_data=f"taskcashbackdelete_{task_id}_{report_id}"),
#             InlineKeyboardButton(text="❌⚠️ Удалить задание (+ БАН)",
#                                  callback_data=f"taskbandelete_{task_id}_{report_id}"),
#             InlineKeyboardButton(text="🗑️ Удалить репорт", callback_data=f"reportdelete_{report_id}"),
#             InlineKeyboardButton(text="🔙 Назад", callback_data="reports_list_menu")

#         )

#         # Устанавливаем количество кнопок в ряду (1 кнопка на ряд)
#         keyboard_builder.adjust(1)
#         # Получаем клавиатуру
#         keyboard = keyboard_builder.as_markup()
#         await callback.message.answer(f'Не удалось получить информацию о задании, ошибка - {e}', reply_markup=keyboard)
#         return

#     if task[1]:
#         user_id_creator = task[1]
#     else:
#         user_id_creator = "Неизвестный, рекомендую удалить задание"

#     chat_title = "Неизвестный чат"
#     invite_link = "Невозможно создать ссылку"
#     if task[4] in [1, 2]:
#         invite_link = await check_admin_and_get_invite_link_report(bot, report[2])
#         try:
#             chat = await bot.get_chat(chat_id)
#             chat_title = chat.title
#         except:
#             chat_title = "Неизвестный чат"
#     elif task[4] in [3]:
#         chat_id_post, message_id = map(int, chat_id.split(":"))
#         chat_title = "Пост"
#         invite_link = "Невозможно создать ссылку на пост"
#         try:
#             await bot.forward_message(chat_id=callback.from_user.id, from_chat_id=chat_id_post, message_id=message_id)
#         except:
#             await callback.message.answer('Невозможно переслать пост (скорее всего он удален)')
#     task_info = f"""
# ID репорта - {report_id}
# Объект репорта - {chat_title}

# Кто пожаловался - <a href='tg://user?id={reporter}'>{reporter}</a>
# Кто создал задание - <code>{user_id_creator}</code>
# ID канала/чата или код поста (чат_айди:месседж_айди)- <code>{chat_id}</code> 
# ID задания - <code>{task_id}</code>

# Ссылка на канал/чат - {invite_link}

# Описание проблемы: <code>{report[4]}</code>

# <i>Выберите нужный вариант действия:</i>    
#     """
#     keyboard_builder = InlineKeyboardBuilder()
#     # Добавляем кнопки
#     keyboard_builder.add(
#         InlineKeyboardButton(text="❌ Удалить задание", callback_data=f"reporttaskdelete_{task_id}_{report_id}"),
#         InlineKeyboardButton(text="❌💵 Удалить задание (+возврат MIT) ", callback_data=f"taskcashbackdelete_{task_id}_{report_id}"),
#         InlineKeyboardButton(text="❌⚠️ Удалить задание (+ БАН)", callback_data=f"taskbandelete_{task_id}_{report_id}"),
#         InlineKeyboardButton(text="🗑️ Удалить репорт", callback_data=f"reportdelete_{report_id}"),
#         InlineKeyboardButton(text="🔙 Назад", callback_data="reports_list_menu")

#     )

#     # Устанавливаем количество кнопок в ряду (1 кнопка на ряд)
#     keyboard_builder.adjust(1)
#     # Получаем клавиатуру
#     keyboard = keyboard_builder.as_markup()

#     await callback.message.answer(task_info, reply_markup=keyboard)






# @admin.callback_query(lambda c: c.data.startswith("reporttaskdelete_"))
# async def delete_task_handler(callback: types.CallbackQuery):
#     task_id = int(callback.data.split('_')[1])
#     report_id = int(callback.data.split('_')[2])

#     # Удаляем задачу из базы данных
#     await DB.delete_task(task_id)
#     await DB.delete_report(report_id)
#     builder = InlineKeyboardBuilder()
#     builder.add(types.InlineKeyboardButton(text="🔙 Вернуться в репорты", callback_data="reports_list_menu"))
#     await callback.message.edit_text(f'❌ Задание {task_id} удалено! Монеты за задание на баланс пользователя возвращены НЕ были', reply_markup=builder.as_markup())

# @admin.callback_query(lambda c: c.data.startswith("taskcashbackdelete_"))
# async def delete_task_handler(callback: types.CallbackQuery):
#     task_id = int(callback.data.split('_')[1])
#     report_id = int(callback.data.split('_')[2])
#     price = 0
#     task = await DB.get_task_by_id(task_id)

#     if task[4] == 1:
#         price = 2000
#     elif task[4] == 2:
#         price = 3000
#     elif task[4] == 3:
#         price = 200

#     amounts = task[3]
#     user_id = task[1]
#     new_balance = amounts*price

#     # Удаляем задачу из базы данных
#     await DB.delete_task(task_id)
#     await DB.add_balance(user_id, amount=new_balance)
#     await DB.delete_report(report_id)
#     builder = InlineKeyboardBuilder()
#     builder.add(types.InlineKeyboardButton(text="🔙 Вернуться в репорты", callback_data="reports_list_menu"))
#     await callback.message.edit_text(f'❌ Задание {task_id} удалено! Создателю задания (<code>{user_id}</code>) было возвращено {new_balance} MitCoin', reply_markup=builder.as_markup())


# @admin.callback_query(lambda c: c.data.startswith("taskbandelete_"))
# async def delete_task_handler(callback: types.CallbackQuery):
#     task_id = int(callback.data.split('_')[1])
#     report_id = int(callback.data.split('_')[2])
#     task = await DB.get_task_by_id(task_id)
#     user_id = task[1]

#     new_balance = -10000000
#     # Удаляем задачу из базы данных
#     await DB.delete_task(task_id)
#     await DB.update_balance(user_id, new_balance)
#     await DB.delete_report(report_id)
#     builder = InlineKeyboardBuilder()
#     builder.add(types.InlineKeyboardButton(text="🔙 Вернуться в репорты", callback_data="reports_list_menu"))
#     await callback.message.edit_text(f'❌ Задание {task_id} удалено! Создателю задания (<code>{user_id}</code>) был установлен баланс {new_balance}', reply_markup=builder.as_markup())


# @admin.callback_query(lambda c: c.data.startswith("reportdelete_"))
# async def delete_task_handler(callback: types.CallbackQuery):
#     report_id = int(callback.data.split('_')[1])

#     # Удаляем задачу из базы данных
#     await DB.delete_report(report_id)
#     builder = InlineKeyboardBuilder()
#     builder.add(types.InlineKeyboardButton(text="🔙 Вернуться в репорты", callback_data="reports_list_menu"))
#     await callback.message.edit_text(f'❌ Репорт №{report_id} был удален без каких-либо действий', reply_markup=builder.as_markup())


















# @admin.callback_query(F.data == 'stats')
# async def stats_handler(callback: types.CallbackQuery):
#     user_count = len(await DB.select_all())

#     text = f"""
#     Статистика

# Всего юзеров: {user_count}"""

#     await callback.message.answer(text)
#     await callback.answer()


# @admin.callback_query(F.data == 'upload')
# async def upload_handler(callback: types.CallbackQuery, bot: Bot):
#     users = await DB.select_all()

#     with open('users.txt', 'w') as file:
#         for user in users:
#             file.write(f"{user['user_id']}, @{user['username']}, balance - {user['balance']}\n")

#     input_file = types.FSInputFile('users.txt')

#     await bot.send_document(chat_id=callback.from_user.id, document=input_file)
#     os.remove('./users.txt')
#     await callback.answer()






# @admin.callback_query(F.data == 'mailing')
# async def mailing_handler(callback: types.CallbackQuery, state: FSMContext):
#     builder = InlineKeyboardBuilder()
#     builder.add(
#         types.InlineKeyboardButton(text="Назад", callback_data='back_admin_not_clear'),
#         types.InlineKeyboardButton(text="Остановить", callback_data='stop_mailing')
#     )
#     await callback.message.answer('Отправьте сообщение для рассылки', reply_markup=builder.as_markup())
#     await state.set_state(MailingStates.message)
#     await callback.answer()

# @admin.message(MailingStates.message)
# async def mailing_get_msg(message: types.Message, state: FSMContext, bot: Bot):
#     text = message.text
#     users = await DB.select_all()
#     if not users:
#         await message.answer("❌ Нет пользователей для рассылки.")
#         await state.clear()
#         return

#     total_users = len(users)
#     completed_users = 0
#     dead_users = 0

#     builder = InlineKeyboardBuilder()
#     builder.add(
#         types.InlineKeyboardButton(text="Назад", callback_data='back_admin_not_clear'),
#         types.InlineKeyboardButton(text="Остановить", callback_data='stop_mailing')
#     )

#     progress_message = await message.answer(
#         f"📤 <b>Рассылка началась</b>\n\n"
#         f"Общее количество пользователей: {total_users}\n",
#         reply_markup=builder.as_markup()
#     )

#     await state.set_state(MailingStates.progress)
#     await state.update_data(stop_flag=False)

#     async def update_progress():
#         previous_text = None
#         while True:
#             data = await state.get_data()
#             if data.get('stop_flag', False):
#                 break
#             await asyncio.sleep(5)
#             current_text = (
#                 f"📤 <b>Рассылка в процессе...</b>\n\n"
#                 f"Общее количество пользователей: {total_users}\n"
#                 f"✅ Успешно отправлено: {completed_users}\n"
#                 f"💀 Мертвые пользователи: {dead_users}"
#             )
#             if current_text != previous_text:
#                 try:
#                     await progress_message.edit_text(
#                         current_text,
#                         reply_markup=builder.as_markup()
#                     )
#                     previous_text = current_text
#                 except TelegramBadRequest as e:
#                     if "message is not modified" in str(e):
#                         continue
#                     raise

#     asyncio.create_task(update_progress())

#     for user in users:
#         data = await state.get_data()
#         if data.get('stop_flag', False):
#             break
#         try:
#             user_id = message.from_user.id
#             await bot.copy_message(
#                 chat_id=int(user['user_id']),
#                 from_chat_id=message.from_user.id,
#                 message_id=message.message_id,
#                 reply_markup=back_menu_kb(user_id)
#             )
#             completed_users += 1
#             await asyncio.sleep(0.1)
#         except TelegramForbiddenError:
#             dead_users += 1

#         except Exception as e:
#             dead_users += 1
#             print(f"Ошибка при отправке пользователю {user['user_id']}: {e}")

#     await state.clear()
#     await progress_message.answer(
#         f"<b>Рассылка завершена</b>\n\n"
#         f"Общее количество пользователей: {total_users}\n"
#         f"✅ Успешно отправлено: {completed_users}\n"
#         f"💀 Мертвые пользователи: {dead_users}",
#         reply_markup=builder.as_markup()
#     )

# @admin.callback_query(F.data == 'stop_mailing')
# async def stop_mailing(callback: types.CallbackQuery, state: FSMContext):
#     await state.update_data(stop_flag=True)
#     await callback.message.edit_text("❌ Рассылка остановлена")
#     await callback.answer("Рассылка остановлена.")


# class EditChannelStates(StatesGroup):
#     waiting_for_name = State()
#     waiting_for_username = State()

# @admin.callback_query(F.data =='show_op')
# async def show_op(callback: types.CallbackQuery):
#     user_id = callback.from_user.id

#     if user_id not in ADMINS_ID:
#         await callback.message.answer("У вас нет прав для выполнения этой команды.")
#         return

#     channels = await DB.all_channels_op()
#     if not channels:
#         kb = InlineKeyboardBuilder()
#         kb.add(InlineKeyboardButton(text='Добавить ОП',callback_data='add_op'))
#         kb.add(InlineKeyboardButton(text='Выход',callback_data='admin_kb'))
#         kb.adjust(1)
#         await callback.message.answer("Список каналов ОП пуст.", reply_markup=kb.as_markup())

#         return 

#     keyboard = InlineKeyboardBuilder()
#     for channel in channels:
#         channel_id, channel_name = channel
#         keyboard.add(InlineKeyboardButton(text=channel_name, callback_data=f"channel:{channel_id}"))
#     keyboard.add(InlineKeyboardButton(text='Добавить ОП',callback_data='add_op'))
#     keyboard.add(InlineKeyboardButton(text='Выход',callback_data='admin_kb'))
#     keyboard.adjust(1) 
#     await callback.message.answer("Список каналов ОП:", reply_markup=keyboard.as_markup())



# # Состояния для FSM
# class AddChannelStates(StatesGroup):
#     waiting_for_username = State()
#     waiting_for_name = State()

# # Команда /add_channel
# @admin.callback_query(F.data == 'add_op')
# async def add_channel(callback: types.CallbackQuery, state: FSMContext):
#     user_id = callback.from_user.id

#     # Проверяем, является ли пользователь администратором
#     if user_id not in ADMINS_ID:
#         await callback.message.answer("У вас нет прав для выполнения этой команды.")
#         return

#     # Запрашиваем @username канала
#     await callback.message.answer("Введите @username канала (например, @my_channel):")
#     await state.set_state(AddChannelStates.waiting_for_username)

# # Обработка @username канала
# @admin.message(AddChannelStates.waiting_for_username)
# async def process_username(message: types.Message, state: FSMContext):
#     username = message.text.strip()

#     # Проверяем, что username начинается с @
#     if not username.startswith('@'):
#         await message.answer("Username канала должен начинаться с @. Попробуйте снова.")
#         return

#     # Сохраняем username в состоянии
#     await state.update_data(channel_username=username)

#     # Запрашиваем имя канала
#     await message.answer("Введите имя канала (например, My Channel):")
#     await state.set_state(AddChannelStates.waiting_for_name)

# # Обработка имени канала
# @admin.message(AddChannelStates.waiting_for_name)
# async def process_name(message: types.Message, state: FSMContext):
#     channel_name = message.text.strip()

#     # Получаем сохранённый username из состояния
#     data = await state.get_data()
#     channel_username = data.get('channel_username')

#     try:
#         # Добавляем канал в базу данных (замените на ваш метод)
#         await DB.add_chanell_op(channel_username, channel_name)

#         await message.answer(f"Канал {channel_name} (@{channel_username}) успешно добавлен в ОП.")
#     except Exception as e:
#         await message.answer(f"Ошибка: {e}")
#     finally:
#         # Завершаем состояние
#         await state.clear()


# @admin.callback_query(F.data.startswith('channel:'))
# async def process_channel_button(callback_query: types.CallbackQuery):
#     channel_id = callback_query.data.split(':')[1]
#     print(channel_id)
#     channel_info = await DB.get_channel_info(channel_id)

#     if not channel_info:
#         await callback_query.answer("Канал не найден.")
#         return

#     channel_id, channel_name, channel_username = channel_info

#     keyboard = InlineKeyboardBuilder()
#     keyboard.add(InlineKeyboardButton(text="Изменить имя", callback_data=f"update_name:{channel_id}"))
#     keyboard.add(InlineKeyboardButton(text="Изменить username", callback_data=f"update_username:{channel_id}"))
#     keyboard.add(InlineKeyboardButton(text="Удалить", callback_data=f"opdelete:{channel_id}"))
#     keyboard.adjust(1)
#     await callback_query.message.answer( 
#         f"Информация о канале:\n\nID: {channel_id}\nИмя: {channel_name}\nUsername: {channel_username}",
#         reply_markup=keyboard.as_markup()
#     )
#     await callback_query.answer()

# @admin.callback_query(F.data.startswith('update_name:'))
# async def edit_channel_name(callback_query: types.CallbackQuery, state: FSMContext):
#     channel_id = callback_query.data.split(':')[1]
#     await state.update_data(channel_id=channel_id)
#     await callback_query.message.answer("Введите новое имя канала:")
#     await state.set_state(EditChannelStates.waiting_for_name)

# @admin.callback_query(F.data.startswith('update_username:'))
# async def edit_channel_username(callback_query: types.CallbackQuery, state: FSMContext):
#     channel_name = callback_query.data.split(':')[1]
#     await state.update_data(channel_name=channel_name)
#     await callback_query.message.answer("Введите новый @username канала:")
#     await state.set_state(EditChannelStates.waiting_for_username)

# @admin.message(EditChannelStates.waiting_for_name)
# async def process_new_name(message: types.Message, state: FSMContext):
#     new_name = message.text.strip()
#     data = await state.get_data()
#     channel_id = data['channel_id']

#     await DB.update_channel_name(channel_id, new_name)
#     await message.answer("Имя канала успешно обновлено.", reply_markup=admin_kb())
#     await state.clear()

# @admin.message(EditChannelStates.waiting_for_username)
# async def process_new_username(message: types.Message, state: FSMContext):
#     new_username = message.text.strip()
#     data = await state.get_data()
#     channel_name = data['channel_name']

#     if not new_username.startswith('@'):
#         await message.answer("Username канала должен начинаться с @. Попробуйте снова.")
#         return

#     await DB.update_channel_username(channel_name, new_username)
#     await message.answer("Username канала успешно обновлен.")
#     await state.clear()

# @admin.callback_query(F.data.startswith('opdelete:'))
# async def delete_channel(callback_query: types.CallbackQuery):
#     channel_id = callback_query.data.split(':')[1]
#     print(channel_id)
#     await DB.delete_channel(channel_id)
#     await callback_query.message.answer("Канал успешно удален.")
#     await callback_query.answer()



# @admin.message(Command('premiumusers'))
# async def premium_users_handler(message: types.Message):
#     # Отправляем начальное сообщение
#     sent_message = await message.answer('Обрабатываю запрос! Ожидайте...')
    
#     premium_users = 0
#     all_users = await DB.get_all_users()
#     total_users = len(all_users)
#     count = 0

#     # Перебор всех пользователей
#     for user in all_users:
#         count += 1
#         user_id = user[1]  # Предполагаем, что user_id находится на индексе 1

#         try:
#             # Проверяем, есть ли у пользователя Telegram Premium
#             from client import check_premium
#             prem = await check_premium(user_id)

#             if prem:
#                 premium_users += 1  # Увеличиваем счетчик, если у пользователя премиум

#             # Обновляем статус каждые 10 пользователей или на последнем шаге
#             if count % 10 == 0 or count == total_users:
#                 await sent_message.edit_text(
#                     f'Обрабатываю запрос! Ожидайте...\n'
#                     f'Обработано: {count} из {total_users}\n'
#                     f'Найдено Premium пользователей: {premium_users}'
#                 )
#         except Exception as e:
#             # Если возникает ошибка (например, неправильный user_id), пропускаем пользователя
#             print(f"Ошибка при проверке пользователя {user_id}: {e}")
#             continue  # Переходим к следующему пользователю

#     # Отправляем финальное сообщение
#     await sent_message.edit_text(
#         f'Запрос обработан!\n'
#         f'Всего пользователей: {total_users}\n'
#         f'Premium пользователей: {premium_users}'
#     ) 

# # from client import update_premium_users2

# # @admin.message(Command('update_premium_users'))
# # async def _(message: types.Message, bot: Bot):
# #     await message.answer('Обновляю') 
# #     await update_premium_users2(bot)
# #     await message.answer('Завершено')

# @admin.callback_query(F.data == 'back_admin_not_clear')
# async def mailing_handler(callback: types.CallbackQuery, state: FSMContext):

#     if callback.from_user.id in ADMINS_ID:
#         await callback.message.edit_text('Админ панель', reply_markup=admin_kb())


# @admin.callback_query(F.data == 'back_admin')
# async def mailing_handler(callback: types.CallbackQuery, state: FSMContext):
#     await state.clear()
#     if callback.from_user.id in ADMINS_ID:
#         await callback.message.edit_text('Админ панель', reply_markup=admin_kb())

# @admin.message(Command('admin'))
# async def admin_cmd(message: types.Message):
#     if message.from_user.id in ADMINS_ID:
#         await message.answer('Админ панель', reply_markup=admin_kb())

# @admin.callback_query(F.data == 'admin_kb2')
# async def admin_kb2_handler(callback: types.CallbackQuery):
#     if callback.from_user.id in ADMINS_ID:  
#         await callback.message.edit_text('Админ панель', reply_markup=admin_kb2())
#         await callback.answer() 

# @admin.callback_query(F.data == 'admin_kb')
# async def admin_kb_handler(callback: types.CallbackQuery):
#     if callback.from_user.id in ADMINS_ID:  
#         await callback.message.edit_text('Админ панель', reply_markup=admin_kb())
#         await callback.answer()  


# class add_mining(StatesGroup):
#     id = State()
#     id2 = State()


# @admin.callback_query(F.data == 'adminMining')
# async def _(callback: types.CallbackQuery, state: FSMContext):
#     kb = InlineKeyboardBuilder()
#     kb.add(InlineKeyboardButton(text='➕ Выдать майнинг', callback_data='add_mining'))
#     kb.add(InlineKeyboardButton(text='➖ Забрать майнинг', callback_data='minus_mining'))
#     kb.add(InlineKeyboardButton(text='🔙 Назад', callback_data='admin_kb'))
#     kb.adjust(1)
#     await callback.message.edit_text('Выберите: ', reply_markup=kb.as_markup())

# @admin.callback_query(F.data == 'add_mining')
# async def _(callback: types.CallbackQuery, state: FSMContext):
#     await state.set_state(add_mining.id)
#     await callback.message.answer('Введите id')

# @admin.callback_query(F.data == 'minus_mining')
# async def _(callback: types.CallbackQuery, state: FSMContext):
#     await state.set_state(add_mining.id2)
#     await callback.message.answer('Введите id')

# @admin.message(add_mining.id)
# async def _(message: types.Message, state: FSMContext, bot: Bot):
#     user_id = message.text  # Get the ID from the user's message
#     await state.update_data(id=user_id)  # Store it in state data
#     date = await state.get_data()
    
#     try:
#         a = await DB.add_mining(date['id'])
#         if a:
#             await bot.send_message(date['id'], 'Вам выдан майнинг!')
#             await message.answer(f'Вы выдали пользователю с Id {date["id"]} майнинг')
#         else:
#             await message.answer('У этого пользователя уже есть майнинг')
#     except Exception as e:
#         await message.answer(f'Ошибка: {e}')
#     finally:
#         await state.clear()

# @admin.message(add_mining.id2)
# async def _(message: types.Message, state: FSMContext, bot: Bot):
#     user_id = message.text  # Get the ID from the user's message
#     await state.update_data(id2=user_id)  # Store it in state data
#     date = await state.get_data()
    
#     try:
#         a = await DB.remove_mining(date['id2'])
#         if a:
#             await message.answer(f'Вы забрали майнинг у пользователя с Id {date["id2"]}')
#         else:
#             await message.answer('У этого пользователя уже нету майнинга!')
#     except Exception as e:
#         await message.answer(f'Ошибка: {e}')
#     finally:
#         await state.clear()


# @admin.callback_query(F.data=='adminAllOP')
# async def _(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
#     kb = InlineKeyboardBuilder()
#     kb.add(InlineKeyboardButton(text='Реклама в ОП', callback_data='op_pr_menu'))
#     kb.add(InlineKeyboardButton(text='ОП в бонусах', callback_data='bonus_admin'))
#     kb.add(InlineKeyboardButton(text='ОП', callback_data='show_op'))
#     kb.add(InlineKeyboardButton(text='🔙 Назад', callback_data='admin_kb'))
#     kb.adjust(1)
#     await callback.message.edit_text('Выберите: ', reply_markup=kb.as_markup())


# @admin.callback_query(F.data == 'detailed_stats')
# async def show_stats_menu(callback: types.CallbackQuery):
#     await callback.message.edit_text(
#         "📊 <b>Выберите тип статистики:</b>",
#         reply_markup=get_stats_menu()
#     )
#     await callback.answer()

# @admin.callback_query(F.data == 'admin_back')
# async def back_to_admin_menu(callback: types.CallbackQuery):
#     await callback.message.edit_text(
#         "👨‍💻 <b>Админ-панель</b>",
#         reply_markup=admin_kb()
#     )
#     await callback.answer()

# @admin.callback_query(F.data.startswith('stats_'))
# async def handle_stats_request(callback: types.CallbackQuery):
#     stat_type = callback.data.split('_')[1]
    
#     # Соответствие между callback_data и полями в БД
#     stat_mapping = {
#         'users': ('add_users', 'Новые пользователи', 'Количество'),
#         'subschanel': ('all_subs_chanel', 'Подписки на канал', 'Подписчики'),
#         'subsgroups': ('all_subs_groups', 'Подписки на группы', 'Подписчики'),
#         'tasks': ('all_tasks', 'Выполненные задачи', 'Количество'),
#         'views': ('all_see', 'Просмотры', 'Количество'),
#         'gifts': ('gift', 'Подарки', 'Количество'),
#         'boosts': ('boosts', 'Бусты', 'Количество'),
#         'likes': ('likes', 'Лайки', 'Количество'),
#         'links': ('links', 'Переходы по ссылкам', 'Количество'),
#         'comments': ('comments', 'Комментарии', 'Количество'),
#         'mined': ('mined', 'Добыча', 'Количество')
#     }
#     print(stat_type) 
#     if stat_type not in stat_mapping:
#         await callback.answer("❌ Неизвестный тип статистики")
#         return
    
#     db_field, title, ylabel = stat_mapping[stat_type]

#     try:
#         graph = await DB.create_statistics_graph(
#             stat_type=db_field,
#             title=title,
#             ylabel=ylabel
#         )
        
#         if graph is not None:
#             await callback.message.answer_photo(
#                 photo=graph,
#                 caption=f"📊 {title} за 30 дней"
#             )
#         else:
#             await callback.answer(f"⚠️ Нет данных по {title.lower()}")
            
#     except Exception as e:
#         await callback.message.answer(f"❌ Ошибка при генерации графика: {str(e)}")
    
#     await callback.answer() 























# # ПРОМО ПРОМО ПРОМО

# from datetime import datetime, timedelta
# import random
# import string
# from typing import Union


# # Состояния для FSM
# class PromoStates(StatesGroup):
#     waiting_amount = State()
#     waiting_name = State()
#     waiting_name_manual = State()
#     waiting_where = State()
#     waiting_count = State()
#     waiting_days = State()

# # 3. Генератор случайных промокодов
# def generate_promo_code(length=8):
#     chars = string.ascii_uppercase + string.digits
#     return ''.join(random.choice(chars) for _ in range(length))


# # 4. Обработчики для админ-панели
# @admin.callback_query(F.data == "promocreate")
# async def create_promo_start(callback: types.CallbackQuery, state: FSMContext):
#     """Начало создания промокода"""
#     print('p')
#     await callback.message.edit_text(
#         "Создание нового промокода:\n\nВведите сумму бонуса:",
#         reply_markup=InlineKeyboardMarkup(inline_keyboard=[
#             [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_menu")]
#         ])
#     )
#     await state.set_state(PromoStates.waiting_amount)
#     await state.update_data(creator_id=callback.from_user.id)

# @admin.message(PromoStates.waiting_amount)
# async def promo_get_amount(message: types.Message, state: FSMContext):
#     """Получение суммы промокода"""
#     try:
#         amount = float(message.text)
#         if amount <= 0:
#             raise ValueError
#         await state.update_data(amount=amount)
        
#         # Предлагаем сгенерировать промокод автоматически
#         auto_promo = generate_promo_code()
#         markup = InlineKeyboardMarkup(inline_keyboard=[
#             [InlineKeyboardButton(text=f"🔢 {auto_promo}", callback_data=f"use_auto_promo:{auto_promo}")],
#             [InlineKeyboardButton(text="✏ Ввести вручную", callback_data="enter_manually")],
#             [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_menu")]
#         ])
        
#         await message.answer(
#             "Выберите или введите название промокода:",
#             reply_markup=markup
#         )
#         await state.set_state(PromoStates.waiting_name)
#     except ValueError:
#         await message.answer("❌ Неверная сумма! Введите число больше 0:")

# @admin.callback_query(F.data.startswith("use_auto_promo:"), PromoStates.waiting_name)
# async def use_auto_promo(callback: types.CallbackQuery, state: FSMContext):
#     """Использование автоматически сгенерированного промокода"""
#     promo_name = callback.data.split(":")[1]
#     await state.update_data(name=promo_name)
#     await promo_select_where(callback.message, state)

# @admin.callback_query(F.data == "enter_manually", PromoStates.waiting_name)
# async def enter_promo_manually(callback: types.CallbackQuery, state: FSMContext):
#     """Запрос на ввод промокода вручную"""
#     await callback.message.edit_text(
#         "Введите название промокода:",
#         reply_markup=InlineKeyboardMarkup(inline_keyboard=[
#             [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_menu")]
#         ])
#     )
#     await state.set_state(PromoStates.waiting_name_manual)

# @admin.message(PromoStates.waiting_name_manual)
# async def promo_get_name_manual(message: types.Message, state: FSMContext):
#     """Получение названия промокода вручную"""
#     if len(message.text) < 3:
#         await message.answer("❌ Слишком короткое название! Минимум 3 символа:")
#         return
    
#     await state.update_data(name=message.text.strip())
#     await promo_select_where(message, state)

# async def promo_select_where(message: Union[types.Message, types.CallbackQuery], state: FSMContext):
#     """Выбор типа начисления"""
#     markup = InlineKeyboardMarkup(inline_keyboard=[
#         [InlineKeyboardButton(text="MICO", callback_data="where:def_bal")],
#         [InlineKeyboardButton(text="RUB", callback_data="where:def_bal_rub")],
#         [InlineKeyboardButton(text="Stars", callback_data="where:stars")],
#         [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_menu")]
#     ])
    
#     if isinstance(message, types.CallbackQuery):
#         await message.message.edit_text(
#             "Выберите куда начислять бонус:",
#             reply_markup=markup
#         )
#     else:
#         await message.answer(
#             "Выберите куда начислять бонус:",
#             reply_markup=markup
#         )
#     await state.set_state(PromoStates.waiting_where)

# @admin.callback_query(F.data.startswith("where:"), PromoStates.waiting_where)
# async def promo_get_where(callback: types.CallbackQuery, state: FSMContext):
#     """Получение типа начисления"""
#     where_to = callback.data.split(":")[1]
#     await state.update_data(where_to=where_to)
    
#     await callback.message.edit_text(
#         "Введите количество активаций:",
#         reply_markup=InlineKeyboardMarkup(inline_keyboard=[
#             [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_menu")]
#         ])
#     )
#     await state.set_state(PromoStates.waiting_count)

# @admin.message(PromoStates.waiting_count)
# async def promo_get_count(message: types.Message, state: FSMContext):
#     """Получение количества активаций"""
#     try:
#         count = int(message.text)
#         if count <= 0:
#             raise ValueError
            
#         await state.update_data(count=count)
        
#         await message.answer(
#             "Введите срок действия в днях:",
#             reply_markup=InlineKeyboardMarkup(inline_keyboard=[
#                 [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_menu")]
#             ])
#         )
#         await state.set_state(PromoStates.waiting_days)
#     except ValueError:
#         await message.answer("❌ Неверное количество! Введите целое число больше 0:")

# @admin.message(PromoStates.waiting_days)
# async def promo_get_days(message: types.Message, state: FSMContext):
#     """Получение срока действия"""
#     try:
#         days = int(message.text)
#         if days <= 0:
#             raise ValueError
            
#         data = await state.get_data()
        
#         # Создаем промокод
#         await Promo.create(
#             creator_id=data['creator_id'],
#             name=data['name'],
#             amount=data['amount'],
#             where_to=data['where_to'],
#             count=data['count'],
#             days=days
#         )
        
#         await message.answer(
#             f"✅ Промокод успешно создан!\n\n"
#             f"🔢 Название: <code>{data['name']}</code>\n"
#             f"💰 Сумма: {data['amount']}\n"
#             f"📌 Тип: {data['where_to']}\n"
#             f"🔢 Активаций: {data['count']}\n"
#             f"📅 Срок действия: {days} дней",
#             reply_markup=admin_kb()
#         )
#         await state.clear()
#     except ValueError:
#         await message.answer("❌ Неверное количество дней! Введите целое число больше 0:")


# class edit_sell_currency(StatesGroup):
#     amount = State()


# @admin.callback_query(F.data.startswith("editSellCurrency"))
# async def _(callback: types.CallbackQuery, state: FSMContext):
#     await state.set_state(edit_sell_currency.amount)
#     currency = await DB.get_stars_sell_currency()
#     await callback.message.edit_text(f'Введи новый курс продажи звёзд\nТекущий курс: {currency[0]}')

# @admin.message(edit_sell_currency.amount)
# async def edit_currency_handler(message: types.Message, state: FSMContext):
#     try:
#         # Преобразуем введенное значение в float
#         new_currency_value = float(message.text)
        
#         # Вызываем метод обновления курса
#         await DB.update_buy_sell_currency(new_currency_value)
        
#         await message.answer('✅ Курс успешно изменён')
#     except ValueError:
#         await message.answer('❌ Пожалуйста, введите число!')
#     except Exception as e:
#         await message.answer(f'❌ Ошибка: {e}')
#     finally:
#         await state.clear()