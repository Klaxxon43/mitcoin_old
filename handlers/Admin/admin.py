from utils.Imports import *
from utils.kb import *

admin = Router()

@admin.callback_query(F.data == 'admin_back')
async def back_to_admin_menu(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "👨‍💻 <b>Админ-панель</b>",
        reply_markup=admin_kb()
    )
    await callback.answer()

@admin.callback_query(F.data == 'admin_kb2')
async def admin_kb2_handler(callback: types.CallbackQuery):
    if callback.from_user.id in ADMINS_ID:  
        await callback.message.edit_text('👨‍💻 <b>Админ-панель</b>', reply_markup=admin_kb2())
        await callback.answer() 

@admin.callback_query(F.data == 'admin_kb')
async def admin_kb_handler(callback: types.CallbackQuery):
    if callback.from_user.id in ADMINS_ID:  
        await callback.message.edit_text('👨‍💻 <b>Админ-панель</b>', reply_markup=admin_kb())
        await callback.answer()  

@admin.message(Command('admin'))
async def admin_cmd(message: types.Message):
    if message.from_user.id in ADMINS_ID:
        await message.answer('Админ панель', reply_markup=admin_kb())

@admin.callback_query(F.data == 'sum_deposit')
async def view_user_profile_handler(callback: types.CallbackQuery, state: FSMContext):
    all_deps = await DB.get_total_deposits()
    await callback.message.answer(f'сумма всех пополнений - {all_deps} usdt')


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