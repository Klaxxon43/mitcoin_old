from aiogram.utils.keyboard import InlineKeyboardBuilder
from confIg import ADMINS_ID

def admin_kb():
    """Главное меню админ-панели"""
    ikb = InlineKeyboardBuilder()
    
    buttons = [
        # ('Всего пользователей📊', 'stats'),
        ('👀 Профиль пользователя ', 'view_user_profile'),
        ('📝Выгрузка', 'upload'),
        ('📩 Рассылка', 'mailing'),
        # ('Общее количество донатов', 'sum_deposit'),
        ('🔥 Привязка чата ', 'chat_privyazka'),
        ('Все ОП', 'adminAllOP'),
        ('🆘 Репорты на задания', 'reports_list_menu'),
        ('Заявки на вывод', 'adminoutputlist'),
        ('‼ 🗑Удалить все задания🗑 ‼', 'clean_task'),
        ('⛏️ Майнинг', 'adminMining'),
        ('📈 Подробная статистика', 'detailed_stats'),
        ('Далее ➡️', 'admin_kb2')  
    ]
    
    for text, callback_data in buttons:
        ikb.button(text=text, callback_data=callback_data)
    
    ikb.adjust(1)
    return ikb.as_markup()

def admin_kb2():
    """Главное меню админ-панели"""
    ikb = InlineKeyboardBuilder()
    

    buttons = [
        ('🎁 Создать промокод', 'promocreate'),
        ('✏️ Изменить цену продажи звёзд', 'editSellCurrency'), 
        ('Создать конкурс', 'admin_contest'), 
        (f"🛠 Тех. перерыв", 'toggle_break'),
        ('◀️ Назад', 'admin_kb')
    ]

    
    for text, callback_data in buttons:
        ikb.button(text=text, callback_data=callback_data)
    
    ikb.adjust(1)
    return ikb.as_markup()



def get_stats_menu():
    """Меню выбора типа статистики"""
    ikb = InlineKeyboardBuilder()
    
    stats_types = [
        ('👥 Новые пользователи', 'stats_users'),
        ('📢 Подписки на канал', 'stats_subschanel'),
        ('👥 Подписки на группы', 'stats_subsgroups'),
        ('✅ Выполненные задачи', 'stats_tasks'),
        ('👀 Просмотры', 'stats_views'),
        ('🎁 Подарки', 'stats_gifts'),
        ('🚀 Бусты', 'stats_boosts'),
        ('❤ Лайки', 'stats_likes'),
        ('🔗 Переходы по ссылкам', 'stats_links'),
        ('💬 Комментарии', 'stats_comments'),
        ('⛏ Добыча', 'stats_mined'),
        ('◀ Назад', 'admin_back')  # Кнопка назад
    ]
    
    for text, callback_data in stats_types:
        ikb.button(text=text, callback_data=callback_data)
    
    ikb.adjust(2, 2, 2, 2, 2, 1)  # Разбиваем кнопки по 2 в ряд
    return ikb.as_markup()

def cancel_all_kb():
    ikb = InlineKeyboardBuilder()
    ikb.button(text='🔙 Назад', callback_data='cancel_all')
    return ikb.as_markup()

def back_work_menu_kb(user_id):
    ikb = InlineKeyboardBuilder()
    ikb.button(text="Назад 🔙", callback_data='work_menu')
    return ikb.as_markup()

def back_dep_kb():
    ikb = InlineKeyboardBuilder()
    ikb.button(text="Назад 🔙", callback_data='select_deposit_menu')
    return ikb.as_markup()
def back_menu_kb(user_id):
    ikb = InlineKeyboardBuilder()
    ikb.button(text="Назад 🔙", callback_data='back_menu')
    return ikb.as_markup()

def back_profile_kb():
    ikb = InlineKeyboardBuilder()
    ikb.button(text="Назад 🔙", callback_data='profile')
    return ikb.as_markup()

def select_deposit_menu_kb(user_id):
    ikb = InlineKeyboardBuilder()
    ikb.button(text="🌟 Telegram Stars", callback_data="dep_stars_menu")
    ikb.button(text="🤖 CryptoBot", callback_data="deposit_menu")
    ikb.button(text="💰 Рубли", callback_data="rub_donate")
    ikb.button(text=f"💎 TON", callback_data=f'ton_deposit')

    ikb.button(text="🔙 Назад", callback_data="profile")
    ikb.adjust(2, 2, 1)
    return ikb.as_markup()

def profile_kb():
    ikb = InlineKeyboardBuilder()
    ikb.button(text="Пополнить 💲", callback_data='select_deposit_menu')
    ikb.button(text="Вывод 📤", callback_data='output_menu')
    ikb.button(text="Реферальная система 👥", callback_data='refka_menu')
    ikb.button(text="Мои задания 📋", callback_data='my_works')
    ikb.button(text="Активировать промокод 🎁", callback_data='activatePromo')
    ikb.button(text="Назад 🔙", callback_data='back_menu')
    ikb.adjust(1)
    return ikb.as_markup()


def work_menu_kb(user_id):
    from utils.Imports import all_price
    ikb = InlineKeyboardBuilder()
    ikb.button(text="🔥 Написать в чат", callback_data="work_chating")
    ikb.button(text="🔗 Шилл", url="https://telegra.ph/SHill-zadaniya-12-02")
    # ikb.button(text="🌟 Продать звезды", callback_data="buy_stars")
    ikb.button(text=f"📢 Канал | +{all_price['channel']}", callback_data="work_chanel")
    ikb.button(text=f"👥 Чат | +{all_price['chat']}", callback_data="work_chat")
    ikb.button(text=f"👀 Пост | +{all_price['post']}", callback_data="work_post")
    ikb.button(text=f"💬 Комментарий | +{all_price['comment']}", callback_data="work_comment")
    ikb.button(text=f'❤️ Реакции | +{all_price['reaction']}', callback_data='work_reaction')
    ikb.button(text=f"🤖 Перейти в бота | +{all_price['link']}", callback_data="work_link")
    ikb.button(text=f"⭐️ Буст канала | +{all_price['boost']}", callback_data="work_boost")  
    ikb.button(text="Назад 🔙", callback_data='back_menu')
    ikb.adjust(2, 2, 2, 2, 1, 1)
    return ikb.as_markup() 

def menu_kb(user_id):
    ikb = InlineKeyboardBuilder()
    ikb.button(text='💸 Заработать', callback_data='work_menu') 
    ikb.button(text='👥 Рекламировать', callback_data='pr_menu')
    ikb.button(text='📄 ОП', callback_data='op_help_menu')
    ikb.button(text='💻 Профиль', callback_data='profile')
    ikb.button(text='🔄 Конвертация', callback_data='convertation')
    ikb.button(text='💸 Чеки', callback_data='checks_menu')
    ikb.button(text='👀 Статистика', callback_data='menu_stats')
    ikb.button(text='🎁 Бонус', callback_data='bonus_menu')
    ikb.button(text='⛏️ Майнинг', callback_data='mining')
    ikb.button(text='О проекте 💎', callback_data='support')
    ikb.button(text='⭐️ Купить звёзды', callback_data='BuyStars')

    if user_id in ADMINS_ID:
        ikb.button(text='АДМИН МЕНЮ', callback_data='admin_back')



    ikb.adjust(2, 2, 2, 2, 2, 1)
    return ikb.as_markup()



def pr_menu_kb(user_id):
    ikb = InlineKeyboardBuilder()
    ikb.button(text="📢 Канал", callback_data='chanel_pr_button')
    ikb.button(text="👥 Чат", callback_data='chat_pr_button')
    ikb.button(text="📃 Пост", callback_data='post_pr_button')
    ikb.button(text="💬 Комментарии", callback_data='comment_pr_button')
    ikb.button(text="🔗 Переход в бота", callback_data='link_task_button') 
    ikb.button(text="⭐️ Бусты", callback_data='boost_pr_button') 
    ikb.button(text="❤️ Реакции", callback_data='reaction_pr_button') 
    ikb.button(text="📣 Рассылка", callback_data='rasslka_menu')
    ikb.button(text="📖 Мои задания", callback_data='my_works')
    ikb.button(text="❗️Инструкция", url='https://teletype.in/@klaxxon_off/hVNvmcEkKmb')
    ikb.button(text="Назад 🔙", callback_data='pr_menu')
    ikb.adjust(2, 2, 2, 2, 1, 1)
    return ikb.as_markup()



def pr_menu_canc():
    ikb = InlineKeyboardBuilder()
    ikb.button(text="❌ Назад", callback_data='pr_menu_cancel')
    return ikb.as_markup()
