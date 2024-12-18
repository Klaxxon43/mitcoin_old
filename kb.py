from aiogram.utils.keyboard import InlineKeyboardBuilder

def admin_kb():
    ikb = InlineKeyboardBuilder()

    ikb.button(text='Всего пользователей📊', callback_data='stats')
    ikb.button(text='Профиль пользователя 👀', callback_data='view_user_profile')
    ikb.button(text='Выгрузка📝', callback_data='upload')
    ikb.button(text='Рассылка📩', callback_data='mailing')
    ikb.button(text='Общее количество донатов', callback_data='sum_deposit')
    ikb.button(text='Привязка чата 🔥', callback_data='chat_privyazka')
    ikb.button(text='Реклама в ОП', callback_data='op_pr_menu')
    ikb.button(text='Репорты на задания', callback_data='reports_list_menu')
    ikb.button(text='‼ Удалить все задания ‼', callback_data='clean_task')
    ikb.adjust(1)
    return ikb.as_markup()


def cancel_all_kb():
    ikb = InlineKeyboardBuilder()
    ikb.button(text='🔙 Назад', callback_data='cancel_all')
    return ikb.as_markup()

def back_work_menu_kb():
    ikb = InlineKeyboardBuilder()
    ikb.button(text="Назад 🔙", callback_data='work_menu')
    return ikb.as_markup()

def back_dep_kb():
    ikb = InlineKeyboardBuilder()
    ikb.button(text="Назад 🔙", callback_data='select_deposit_menu')
    return ikb.as_markup()
def back_menu_kb():
    ikb = InlineKeyboardBuilder()
    ikb.button(text="Назад 🔙", callback_data='back_menu')
    return ikb.as_markup()

def back_profile_kb():
    ikb = InlineKeyboardBuilder()
    ikb.button(text="Назад 🔙", callback_data='profile')
    return ikb.as_markup()

def select_deposit_menu_kb():
    ikb = InlineKeyboardBuilder()
    ikb.button(text="🌟 Telegram Stars", callback_data="dep_stars_menu")
    ikb.button(text="🤖 CryptoBot", callback_data="deposit_menu")
    ikb.button(text="💰 Рубли", callback_data="rub_donate")
    ikb.button(text="🔙 Назад", callback_data="profile")
    ikb.adjust(1)
    return ikb.as_markup()

def profile_kb():
    ikb = InlineKeyboardBuilder()
    ikb.button(text="Пополнить 💲", callback_data='select_deposit_menu')
    ikb.button(text="Реферальная система 👥", callback_data='refka_menu')
    ikb.button(text="Мои задания 📋", callback_data='my_works')
    ikb.button(text="Назад 🔙", callback_data='back_menu')
    ikb.adjust(1)
    return ikb.as_markup()


def work_menu_kb():
    ikb = InlineKeyboardBuilder()
    ikb.button(text="🔥 Написать в чат", callback_data="work_chating")
    ikb.button(text="🔗 Шилл", url="https://telegra.ph/SHill-zadaniya-12-02")
    ikb.button(text="🌟 Продать звезды", callback_data="buy_stars")
    ikb.button(text="📢 Подписаться на канал | +1500", callback_data="work_chanel")
    ikb.button(text="👥 Вступить в чат | +1500", callback_data="work_chat")
    ikb.button(text="👀 Посмотреть пост | +250", callback_data="work_post")
    ikb.button(text="Назад 🔙", callback_data='back_menu')
    ikb.adjust(1)
    return ikb.as_markup()

def menu_kb():
    ikb = InlineKeyboardBuilder()
    ikb.button(text='💸 Заработать', callback_data='work_menu')
    ikb.button(text='👥 Рекламировать', callback_data='pr_menu')
    ikb.button(text='📄 ОП', callback_data='op_help_menu')
    ikb.button(text='💻 Профиль', callback_data='profile')
    ikb.button(text='🔄 Конвертация', callback_data='corvertation')
    ikb.button(text='💸 Чеки', callback_data='checks_menu')
    ikb.button(text='👀 Статистика', callback_data='menu_stats')
    ikb.button(text='💹 Пресейл', url='https://tonraffles.app/jetton/fairlaunch/MICO/EQAKAfkG7XDmKfAwVyziPryAPaArEOS1TWRs4YDagUlwygwl')
    ikb.button(text='О проекте 💎', callback_data='support')

    ikb.adjust(2)
    return ikb.as_markup()



def pr_menu_kb():
    ikb = InlineKeyboardBuilder()
    ikb.button(text="📢 Канал", callback_data='chanel_pr_button')
    ikb.button(text="👥 Чат", callback_data='chat_pr_button')
    ikb.button(text="📃 Пост", callback_data='post_pr_button')
    ikb.button(text="📣 Рассылка", callback_data='rasslka_menu')
    ikb.button(text="📖 Мои задания", callback_data='my_works')
    ikb.button(text="Назад 🔙", callback_data='back_menu')
    ikb.adjust(2)
    return ikb.as_markup()



def pr_menu_canc():
    ikb = InlineKeyboardBuilder()
    ikb.button(text="❌ Назад", callback_data='pr_menu_cancel')
    return ikb.as_markup()