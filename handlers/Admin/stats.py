from utils.Imports import *
from .admin import admin

@admin.callback_query(F.data == 'stats')
async def stats_handler(callback: types.CallbackQuery):
    user_count = len(await DB.select_all())
    text = f"""
    Статистика

Всего юзеров: {user_count}"""
    await callback.message.answer(text)
    await callback.answer()

@admin.callback_query(F.data == 'upload')
async def upload_handler(callback: types.CallbackQuery, bot: Bot):
    users = await DB.select_all()

    with open('users.txt', 'w') as file:
        for user in users:
            file.write(f"{user['user_id']}, @{user['username']}, balance - {user['balance']}\n")

    input_file = types.FSInputFile('users.txt')
    await bot.send_document(chat_id=callback.from_user.id, document=input_file)
    os.remove('./users.txt')
    await callback.answer()

@admin.callback_query(F.data == 'detailed_stats')
async def show_stats_menu(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "📊 <b>Выберите тип статистики:</b>",
        reply_markup=get_stats_menu()
    )
    await callback.answer()

@admin.callback_query(F.data.startswith('stats_'))
async def handle_stats_request(callback: types.CallbackQuery):
    stat_type = callback.data.split('_')[1]
    
    stat_mapping = {
        'users': ('add_users', 'Новые пользователи', 'Количество'),
        'subschanel': ('all_subs_chanel', 'Подписки на канал', 'Подписчики'),
        'subsgroups': ('all_subs_groups', 'Подписки на группы', 'Подписчики'),
        'tasks': ('all_tasks', 'Выполненные задачи', 'Количество'),
        'views': ('all_see', 'Просмотры', 'Количество'),
        'gifts': ('gift', 'Подарки', 'Количество'),
        'boosts': ('boosts', 'Бусты', 'Количество'),
        'likes': ('likes', 'Лайки', 'Количество'),
        'links': ('links', 'Переходы по ссылкам', 'Количество'),
        'comments': ('comments', 'Комментарии', 'Количество'),
        'mined': ('mined', 'Добыча', 'Количество')
    }
    
    if stat_type not in stat_mapping:
        await callback.answer("❌ Неизвестный тип статистики")
        return
    
    db_field, title, ylabel = stat_mapping[stat_type]

    try:
        graph = await DB.create_statistics_graph(
            stat_type=db_field,
            title=title,
            ylabel=ylabel
        )
        
        if graph is not None:
            await callback.message.answer_photo(
                photo=graph,
                caption=f"📊 {title} за 30 дней"
            )
        else:
            await callback.answer(f"⚠️ Нет данных по {title.lower()}")
    except Exception as e:
        await callback.message.answer(f"❌ Ошибка при генерации графика: {str(e)}")
    
    await callback.answer()