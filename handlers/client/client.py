from utils.Imports import *
from utils.redis_utils import *
from handlers.client.states import *
# from handlers.Checks.menu import *

from handlers.Tasks.channel import generate_tasks_keyboard_chanel
from handlers.Tasks.tasks import *
from handlers.Tasks.post import *
from handlers.Tasks.comment import *
from handlers.Tasks.reaction import *
from handlers.Tasks.link import *
from handlers.Tasks.boost import *

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = Router()

task_cache = {}
task_cache_chat = {}
task_count_cache = {}

# Назначим текстовые представления для типов заданий
TASK_TYPES = {
    1: '📢 Канал',
    2: '👥 Чат',
    3: '👀 Пост',
    4: '💬 Комментарии',
    5: '🔗 Бот',
    6: '⭐️ Буст',
    7: '❤️ Реакция'
}

@router.callback_query(F.data == 'profile')
async def profile_handler(callback: types.CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    if not await check_subs_op(user_id, bot):
        return
    
    if not await DB.get_break_status():
        await callback.message.answer('🛠Идёт технический перерыв🛠\nПопробуйте снова позже')
        return
    else:

        user_id = callback.from_user.id
        user = await DB.select_user(user_id)
        print(user)
        balance = user['balance']
        rub_balance = user['rub_balance']
        if balance is None:
            balance = 0
        await callback.answer()
        # if user['prem'] == True: 
        #     prem = 'Есть'
        # else:
        #     prem = 'Нету' 

        stars = await DB.get_stars(user_id)
        await callback.message.edit_text(f'''
👀 <b>Профиль:</b>
                                         
⭐️ <b>TG Premium:</b> {'Есть' if callback.from_user.is_premium == True else 'Нету'}
📅 <b>Дата регистрации </b> <em>{user['reg_time']}</em>                                         
🪪 <b>ID</b> - <code>{user_id}</code>

💰 Баланс $MICO - {balance:.2f} MitCoin
💳 Баланс руб - {rub_balance:.2f} ₽
⭐️ Баланс Stars - {stars}

🚀 Выполнено заданий за сегодня: {(await DB.get_task_counts(user_id))[0]}
        ''', reply_markup=profile_kb()) 


@router.callback_query(F.data == 'back_menu')
async def back_menu_handler(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()
    user_id = callback.from_user.id
    await callback.message.edit_text(
        "<b>💎 PR MIT</b> - <em>мощный и уникальный инструмент для рекламы ваших проектов</em>\n\n<b>Главное меню</b>",
        reply_markup=menu_kb(user_id))


@router.callback_query(F.data == 'rasslka_menu')
async def back_menu_handler(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    await callback.answer()
    await callback.message.edit_text(
        "Рассылка в боте - 1000 рублей, обращаться - @Coin_var",
        reply_markup=back_menu_kb(user_id))


@router.callback_query(F.data == 'op_piar_menu')
async def back_menu_handler(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    await callback.answer()
    await callback.message.edit_text(
        "Реклама в ОП - 500 рублей за 1 день, обращаться - @Coin_var",
        reply_markup=back_menu_kb(user_id))


@router.callback_query(F.data == 'cancel_all')
async def cancel_all(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    await state.clear()
    await profile_handler(callback, bot)



@router.callback_query(F.data == 'menu_stats')
async def stats_menu_handler(callback: types.CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    if not await check_subs_op(user_id, bot):
        return
    
    if not await DB.get_break_status():
        await callback.message.answer('🛠Идёт технический перерыв🛠\nПопробуйте снова позже')
        return
    else:

        user_count = len(await DB.select_all())
        # all_tasks = len(await DB.get_tasks())
        calculate_total_cost = await DB.calculate_total_cost()
        statics = await DB.get_statics() 
        id, chanels, groups, all, see, users, _, gift2, boosts, reactions, links, comments, mined, _, _, _, _, _, _, _, _ = statics[0]
        id2, chanels2, groups2, all2, see2, users, _, gift, boosts2, reactions2, links2, comments2, mined2, _, _, _, _, _, _, _, _ = statics[1] 
        balance = await DB.all_balance() 
        gifts = await DB.count_bonus_time_rows()
        today_gifts = await DB.count_today_gifts()  # Количество подарков за сегодня
        comment_stats = len(await DB.select_like_comment())
        

        cha1 = len(task_cache.get('all_tasks', [])) #chanel
        cha2 = len(task_cache_chat.get('all_tasks', []))  #chats       
        pos = len(processed_tasks)
        com= comment_stats
        rea = len(available_reaction_tasks)
        lin = len(available_tasks)
        boo = len(available_boost_tasks)

        all_tasks = cha1+cha2+pos+com+rea+lin+boo

        # prem_users = await DB.scount_premium_user() 

        all_minings = await  DB.get_mining_line()
 

        text = f""" 
        
    <b>🌐 Статистика 🌐 </b>

👥 Всего пользователей: {user_count}
⛏️ пользователей с майнингом: {all_minings} 

💼 Всего заданий: {all_tasks}
💸 Возможно заработать: {f"{calculate_total_cost:,}".replace(",", " ")} 

🗓<b>Ежедненая статистика</b>: 
💼 <b>Выполнено заданий всех типов:</b> {all2}
📣 <b>Подписались на каналы:</b> {chanels2}
👥 <b>Подписались на группы:</b> {groups2}
👁️ <b>Просмотров:</b> {see2}
💬 <b>Комментариев:</b> {comments2}
🔗 <b>Переходов:</b> {links2}
🚀 <b>Бустов:</b> {boosts2}
❤️ <b>Реакций:</b> {reactions2}
👤 <b>Новых пользователей:</b> {users}
🎁 <b>Подарков собрано:</b> {gift} раз(а)
⛏️ <b>Намайнено сегодня:</b> {mined2:.2f}

🗓<b>Статистика за всё время работы:</b>
💼 <b>Выполнено заданий всех типов:</b> {all}
📣 <b>Подписались на каналы:</b> {chanels}
👥 <b>Подписались на группы:</b> {groups}
👁️ <b>Общее количество просмотров:</b> {see} 
💬 <b>Общее количество комментариев:</b> {comments}
🔗 <b>Общее количество переходов:</b> {links} 
🚀 <b>Бустов за всё время:</b> {boosts}
❤️ <b>Реакции за всё время:</b> {reactions}
💸 <b>Баланс всех пользователей:</b> {f"{balance:,.0f}".replace(",", " ")} $MICO
🎁 <b>Собрано подарков:</b> {gift2} раз(а)
⛏️ <b>Намайнено:</b> {f"{mined:.0f}".replace(',', ' ')} $MICO

    """
        build = InlineKeyboardBuilder()
        build.add(InlineKeyboardButton(text='🏆Рейтинг по балансу', callback_data='rating'))
        build.add(InlineKeyboardButton(text='🏆Рейтинг по рефералам', callback_data='top_referrers')) 
        # build.add(InlineKeyboardButton(text='🏆Рейтинг по рефералам за 24 часа', callback_data='referrers24hour')) 
        build.add(InlineKeyboardButton(text="🔙 Назад", callback_data='back_menu'))
        build.adjust(1)
        await callback.message.edit_text(text, reply_markup=build.as_markup())
        await callback.answer()


@router.callback_query(F.data == 'support')
async def refki_handler(callback: types.CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    if not await check_subs_op(user_id, bot):
        return
    
    if not await DB.get_break_status():
        await callback.message.answer('🛠Идёт технический перерыв🛠\nПопробуйте снова позже')
        return
    
    else:
        await callback.answer()
        roadmap = "https://telegra.ph/Dorozhnaya-karta-proekta-Mit-Coin--Mit-Coin-Project-Roadmap-11-25"
        token = "https://telegra.ph/Tokenomika-monety-MitCoin-MICO-11-25"
        channel = "https://t.me/mitcoinnews"
        add_button01 = InlineKeyboardButton(text="📋 О нас", url='https://telegra.ph/O-proekte-Mit-Coin-11-26')
        add_button0 = InlineKeyboardButton(text="💎 Канал бота", url=channel)
        add_button = InlineKeyboardButton(text="🚙 Дорожная карта", url=roadmap)
        add_button2 = InlineKeyboardButton(text="💱 Токеномика", url=token)
        add_button3 = InlineKeyboardButton(text="🛠️ Служба поддержки", callback_data='support_menu')
        add_button1 = InlineKeyboardButton(text="🔙 Назад", callback_data='back_menu')
        # Создаем клавиатуру и добавляем в нее кнопку
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[add_button01], [add_button], [add_button2], [add_button0], [add_button3], [add_button1]])
        await callback.message.edit_text('''
    Тут вы найдите всю нужную информацию касательно нашего проекта
        ''', reply_markup=keyboard)

@router.callback_query(F.data == 'support_menu')
async def refki_handler(callback: types.CallbackQuery):
    support_link = "https://t.me/mitcoinmen"
    add_button3 = InlineKeyboardButton(text="🛠️ Служба поддержки", url=support_link)
    add_button1 = InlineKeyboardButton(text="🔙 Назад", callback_data='back_menu')
    # Создаем клавиатуру и добавляем в нее кнопку
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[add_button3], [add_button1]])
    await callback.message.edit_text('''
🛠️ Если у вас возникли технические трудности или вы нашли баг, пишите /report. Или <a href='https://t.me/mitcoin_chat'>в наш ЧАТ</a>. 
<b> ❓ Как использовать /report ? </b>
Всё просто! просто напишите /report и описание своей проблемы, например: 
<blockquote> /report я нашёл баг </blockquote>
или любая другая проблема
                                     
За находку багов вознаграждение.
Связь с владельцем - @Coin_var
        ''', reply_markup=keyboard)

@router.callback_query(F.data == 'op_help_menu')
async def refki_handler(callback: types.CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    if not await check_subs_op(user_id, bot):
        return
    
    if not await DB.get_break_status():
        await callback.message.answer('🛠Идёт технический перерыв🛠\nПопробуйте снова позже')
        return
    
    else:

        await callback.answer()
        await callback.message.edit_text("""
    👤 ОП (Обязательная Подписка) - функция для чатов, пользователи не смогут писать в чат, пока не подпишутся на необходимые каналы  

    <b>Для настройки обязательной подписки (ОП)</b>:

    1) Бот должен быть админом в данном чате и в рекламируемых (необходимых к подписке) каналах/чатах 📛
    2) Напишите команду /setup @канал 
    (⌛ для настройки ОП с таймером используйте /setup @канал **h, где ** количество часов)
    <i>пример - /setup @mitcoinnews 12h</i>
    3) для удаления всех ОП используйте /unsetup 
    или /unsetup @канал для удаления конкретного канала 
    4) список всех активных ОП в чате - /status
            """,reply_markup=back_menu_kb(user_id))

@router.callback_query(F.data == 'bonus_menu')
async def bonus_menu(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    user_id = callback.from_user.id
    if not await check_subs_op(user_id, bot):
        return

    if not await DB.get_break_status():
        await callback.message.answer('🛠Идёт технический перерыв🛠\nПопробуйте снова позже')
        return
    
    else:
        await callback.answer()
        user_id = callback.from_user.id
        ops = await DB.get_bonus_ops()


        unsubscribed_channels = []
        if ops:
            for op in ops:
                channel_id = op[1]
                link = op[2]
                if not await is_user_subscribed(user_id, channel_id, bot):
                    unsubscribed_channels.append(link)

            # Если есть каналы, на которые нужно подписаться
        if unsubscribed_channels:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Подписаться", url=channel) for channel in unsubscribed_channels],
                [InlineKeyboardButton(text="✅ Проверить", callback_data='bonus_proverka')],
                [InlineKeyboardButton(text="🔙 Назад", callback_data='back_menu')]
            ])

            # Формируем список каналов для текстового сообщения
            channels_list = "\n".join(
                [f"{channel}" for channel in unsubscribed_channels])

            await callback.message.edit_text(f"🎁 <b>Подпишитесь на следующие каналы для получения бонуса</b>\n<i>После подписки перезайдите в этот раздел для получения бонуса</i>\n\n{channels_list}", reply_markup=keyboard, disable_web_page_preview=True)
            return

        last_bonus_date = await DB.get_last_bonus_date(user_id)
        today = datetime.now(MOSCOW_TZ).strftime("%Y-%m-%d")
        if last_bonus_date == today:
            await callback.message.edit_text("❌ <b>Внимание!</b>\nБонус можно получить только один раз в день.\nПопробуйте снова завтра! \n\n<em>⏰ Возможность получения бонуса обновляется в 00:00 по МСК.</em>", reply_markup=back_menu_kb(user_id))
            return

        await DB.update_last_bonus_date(user_id)
        await DB.add_balance(user_id, 5000)
        await DB.increment_statistics(1, 'gifts')
        await DB.increment_statistics(2, 'gifts')
        await callback.answer('+5000 $MICO')
        await callback.message.edit_text(f"🎉 <b>Поздравляем!</b> 🎉\n🎁Вы получили свой ежедневный бонус — <b>5000 $MICO!</b> ✨\n💰 Мы ценим ваше участие.\n\n>Не забудьте заглянуть завтра за новым бонусом! ", reply_markup=back_menu_kb(user_id))
        



@router.callback_query(F.data == 'bonus_proverka')
async def bonus_menu(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    await callback.answer()
    user_id = callback.from_user.id
    ops = await DB.get_bonus_ops()


    unsubscribed_channels = []
    if ops:
        for op in ops:
            channel_id = op[1]
            link = op[2]
            if not await is_user_subscribed(user_id, channel_id, bot):
                unsubscribed_channels.append(link)

        # Если есть каналы, на которые нужно подписаться
    if unsubscribed_channels:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Подписаться", url=channel) for channel in unsubscribed_channels],
            [InlineKeyboardButton(text="✅ Проверить", callback_data='bonus_proverka')],
            [InlineKeyboardButton(text="🔙 Назад", callback_data='back_menu')]
        ])

        # Формируем список каналов для текстового сообщения
        channels_list = "\n".join(
            [f"{channel}" for channel in unsubscribed_channels])

        await callback.message.edit_text(f"🎁 <b>Подпишитесь на следующие каналы для получения бонуса</b>\n<i>(после подписки перезайдите в этот раздел для получения бонуса):</i>\n\n{channels_list}", reply_markup=keyboard, disable_web_page_preview=True)
        return

    last_bonus_date = await DB.get_last_bonus_date(user_id)
    today = datetime.now(MOSCOW_TZ).strftime("%Y-%m-%d")
    if last_bonus_date == today:
        await callback.message.edit_text("❌ <b>Бонус можно получить только один раз в день.</b>\n\nПопробуйте завтра <i>(возможность получения бонуса обновляется в 00:00 по МСК)</i>", reply_markup=back_menu_kb(user_id))
        return

    await DB.update_last_bonus_date(user_id)
    await DB.add_balance(user_id, 5000)
    await callback.answer('+5000 $MICO')
    await callback.message.edit_text(f"🎁 <b>Вы получили ежедневный бонус в размере 5000 $MICO</b>\n\nВозвращайтесь завтра 😉", reply_markup=back_menu_kb(user_id))




@router.callback_query(F.data == 'output_menu')
async def outputmenu(callback: types.CallbackQuery, state: FSMContext):
    """Меню выбора способа вывода"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="💰 RUB(ВРЕМЕННО НЕДОСТУПНО)", callback_data="withdraw_rub"),
        InlineKeyboardButton(text="⭐️ Stars", callback_data="withdraw_stars"),
    ) 
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="profile"))
    builder.adjust(1)
    
    await callback.message.edit_text(
        "💸 <b>Вывод средств</b>\n\n"
        "Выберите способ вывода:",
        reply_markup=builder.as_markup()
    )



@router.callback_query(F.data == 'output_menuF')
async def outputmenu(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    user_id = callback.from_user.id
    user = await DB.select_user(user_id)
    rub_balance = user['rub_balance']

    add_button1 = InlineKeyboardButton(text=f"💲 USDT", callback_data=f'usdt_output_menu')
    add_button2 = InlineKeyboardButton(text=f"RUB", callback_data=f'rub_output_menu') 
    add_button3 = InlineKeyboardButton(text="🔙 Назад", callback_data='profile')
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[add_button1], [add_button2], [add_button3]])
    await callback.message.edit_text(f'''
⚡ В данном разделе Вы можете произвести вывод ваших средств с баланса в рублях <i>(рубли можно получить при помощи конвертации)</i>

<span class="tg-spoiler"><b>Лимиты:</b>
Вывод в USDT - от 2.5$ 
Вывод в рублях - от 250₽</span>

⚠ Вывод производится в течении 3 рабочих дней

<b>Выберите способ вывода:</b>
    ''', reply_markup=keyboard)


@router.callback_query(F.data == 'usdt_output_menuF')
async def outputusdtmenu(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    user = await DB.select_user(user_id)
    rub_balance = user['rub_balance']

    data_cbr = requests.get('https://www.cbr-xml-daily.ru/daily_json.js').json()
    usd_data = data_cbr['Valute']['USD']
    usd = usd_data['Value']
    usd = int(usd)
    user_usdt = rub_balance/usd

    print(user_usdt)
    if user_usdt < 2.5:
        await callback.message.edit_text(f"😢 <b>Недостаточно средств на балансе</b>\n\nНа вашем балансе {round(user_usdt, 3)}$, минимальная сумма <b>должна быть более 2.5$</b>", reply_markup=back_profile_kb())
        return


    add_button2 = InlineKeyboardButton(text="🔙 Назад", callback_data='back_menu')
    # Создаем клавиатуру и добавляем в нее кнопку
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[add_button2]])
    await callback.message.edit_text(f'💳 Укажите сумму <b>от 2.5 до {round(user_usdt, 3)} USDT</b>, которую вы хотите вывести', reply_markup=keyboard)
    await state.set_state(output.usdt)
    await state.update_data(usd=usd, user_usdt=user_usdt)



@router.message(output.usdt)
async def outputusdtmenu1(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    try:
        text = float(message.text)
    except ValueError:
        await message.answer("<b>Введите целое число</b>",reply_markup=back_menu_kb(user_id))
        return

    statedata = await state.get_data()
    usd = statedata['usd']
    user_usdt = statedata['user_usdt']

    if text < 2.5 or text > user_usdt:
        await message.answer(f'❗ Укажите сумму <b>от 2.5 до {user_usdt} USDT</b>', reply_markup=back_menu_kb(user_id))
        return
    await state.clear()
    await state.set_state(output.usdt1)
    await state.update_data(usd=usd, user_usdt=user_usdt, amount=text)

    await message.answer(f'👛 Теперь укажите Ваш кошелёк <b>USDT (BEP20)</b>, на который будет произведен вывод\n\n‼ <b>Внимание! При некорректном адресе кошелька/неверной сети - сумма вывода возвращена НЕ будет</b>', reply_markup=back_menu_kb(user_id))





@router.message(output.usdt1)
async def outputusdtmenu11(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    statedata = await state.get_data()
    usd = statedata['usd']
    amount = statedata['amount']

    try:
        wallet = str(message.text)

        if len(wallet) < 5 or len(wallet) > 50:
            await message.answer("‼ <b>Введите корректный адрес кошелька</b>", reply_markup=back_menu_kb(user_id))
            return

    except:
        await message.answer("‼ <b>Введите корректный адрес кошелька</b>",reply_markup=back_menu_kb(user_id))
        return


    usd = int(usd)
    sum = amount * usd
    sum = int(sum)

    await message.answer(f'🥳 <b>Заявка на вывод на {amount} USDT создана!</b>\nС вашего баланса списано {sum}₽', reply_markup=back_menu_kb(user_id))
# Пример добавления транзакции
    await DB.add_transaction(
        user_id=user_id,
        amount=amount,
        description="вывод USDT",
        additional_info= None
    )
    await DB.add_rub_balance(user_id=user_id, amount=-sum)
    await DB.add_output(user_id=user_id, amount=amount, wallet=wallet, type=1)
    await state.clear()










@router.callback_query(F.data == 'rub_output_menu')
async def outputrubmenu(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    user = await DB.select_user(user_id)
    rub_balance = user['rub_balance']


    if rub_balance < 250:
        await callback.message.edit_text(f"😢 <b>Недостаточно средств на балансе</b>\n\nНа вашем балансе {rub_balance}₽, минимальная сумма <b>должна быть 250₽ или более</b>", reply_markup=back_profile_kb())
        return


    add_button = InlineKeyboardButton(text="🔙 Назад", callback_data='back_menu')
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[add_button]])
    await callback.message.edit_text(f'💳 Укажите сумму <b>от 250₽ до {rub_balance}₽</b>, которую вы хотите вывести (целое число)', reply_markup=keyboard)
    await state.set_state(output.rub)


@router.message(output.rub)
async def outputrubmenu1(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    user = await DB.select_user(user_id)
    rub_balance = user['rub_balance']
    try:
        text = int(message.text)
    except ValueError:
        await message.answer("<b>Введите число</b>", reply_markup=back_menu_kb(user_id))
        return

    if text < 250 or text > rub_balance:
        await message.answer(f'❗ Укажите сумму <b>от 250₽ до {rub_balance}₽</b>', reply_markup=back_menu_kb(user_id))
        return

    await state.clear()
    await state.set_state(output.rub1)
    await state.update_data(amount=text)

    await message.answer(f'👛 Теперь укажите номер <b>банковской карты/телефона</b> (для перевода по СБП), а так же <b>имя и фамилию получателя</b>\n\n‼ <b>Внимание! При некорректном номере карты/телефона - сумма вывода возвращена НЕ будет</b>', reply_markup=back_menu_kb(user_id))


@router.message(output.rub1)
async def outputrubmenu11(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    statedata = await state.get_data()
    amount = statedata['amount']
    try:
        wallet = str(message.text)
        if len(wallet) > 100 or len(wallet) < 5:
            await message.answer("‼ <b>Введите корректный номер карты/телефона</b>", reply_markup=back_menu_kb(user_id))
            return

    except:
        await message.answer("‼ <b>Введите корректный номер карты/телефона</b>", reply_markup=back_menu_kb(user_id))
        return

    await message.answer(f'🥳 <b>Заявка на вывод на {amount}₽ создана!</b>\nС вашего баланса списано {amount} рублей', reply_markup=back_menu_kb(user_id))
    await DB.add_transaction(
        user_id=user_id,
        amount=amount,
        description="вывод RUB",
        additional_info= None
    )
    await DB.add_rub_balance(user_id=user_id, amount=-amount)
    await DB.add_output(user_id=user_id, amount=amount, wallet=wallet, type=2)
    await state.clear()










@router.callback_query(F.data == 'corvertation')  # <-- исправлено название
async def convertation_handler(callback: types.CallbackQuery, bot: Bot):
    user_id = callback.from_user.id

    if not await check_subs_op(user_id, bot):
        return

    if not await DB.get_break_status():
        await callback.message.answer('🛠Идёт технический перерыв🛠\nПопробуйте снова позже')
        return

    # Проверка конвертации
    last_conversion_date = await DB.get_last_conversion_date(user_id)
    print(last_conversion_date)
    today = datetime.now(MOSCOW_TZ).strftime("%Y-%m-%d")

    if last_conversion_date == today:
        await callback.message.edit_text(
            "❌ <b>Конвертацию можно проводить только один раз в день.</b>\n\n"
            "Попробуйте завтра <i>(возможность конвертации обновляется в 00:00 по МСК)</i>",
            reply_markup=back_profile_kb()
        )
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Продолжить!", callback_data='mittorub')],
        [InlineKeyboardButton(text="🔙 Назад", callback_data='back_menu')],
    ])
    await callback.message.edit_text(
        "🌀 <b>Вы можете конвертировать ваши $MICO в рубли!</b>\n\n"
        "<i>Конвертацию можно проводить не более 1 раза в день и не более чем на 1% от баланса</i>",
        reply_markup=keyboard
    )


@router.callback_query(F.data == 'mittorub')
async def corvertation_rubtomit_handler(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    user_id = callback.from_user.id
    user = await DB.select_user(user_id)
    mit_balance = user['balance']

    print(mit_balance)

    last_conversion_date = await DB.get_last_conversion_date(user_id) 
    today = datetime.now(MOSCOW_TZ).strftime("%Y-%m-%d")
    if last_conversion_date == today:
        await callback.message.answer("❌ <b>Конвертацию можно проводить только один раз в день.</b>\n\nПопробуйте завтра <i>(возможность конвертации обновляется в 00:00 по МСК)</i>", reply_markup=back_profile_kb())
        return 

    if mit_balance is None or mit_balance == 0:
        await callback.message.edit_text('😢 <b>У вас недостаточно $MICO для осуществления конвертации</b>', reply_markup=back_profile_kb())

    maxprocent = mit_balance // 100

    if maxprocent < 1000:
        await callback.message.edit_text('😢 <b>У вас недостаточно $MICO для осуществления конвертации</b>', reply_markup=back_profile_kb())


    add_button1 = InlineKeyboardButton(text=f"Максимально ({maxprocent} $MICO)", callback_data=f'convert_{maxprocent}')
    add_button2 = InlineKeyboardButton(text="🔙 Назад", callback_data='back_menu')
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[add_button1], [add_button2]])

    await callback.message.edit_text(f'''
❓ <b>Сколько $MICO (MitCoin) вы хотите конвертировать в рубли?</b>

<i>Максимальная сумма: 1% от MitCoin баланса</i> - {maxprocent}
    ''', reply_markup=keyboard)

    await state.set_state(convertation.mittorub)
    await state.update_data(maxprocent=maxprocent)


@router.message(convertation.mittorub)
async def corvertation_rubtomit_input(message: types.Message, state: FSMContext):
    maxprocent = await state.get_data()
    maxprocent = maxprocent['maxprocent']
    print(f'макс процент {maxprocent}')

    try:
        convert_amount = int(message.text)
        await state.clear()
    except ValueError:
        await message.reply("❌ Введено некорректное значение, пожалуйста, введите число.", reply_markup=back_menu_kb(user_id))
        return

    user_id = message.from_user.id
    user = await DB.select_user(user_id)
    mit_balance = user['balance']
    rub_balance = user['rub_balance']


    last_conversion_date = await DB.get_last_conversion_date(user_id)
    today = datetime.now(MOSCOW_TZ).strftime("%Y-%m-%d")

    if last_conversion_date == today:
        await message.answer("❌ <b>Конвертацию можно проводить только один раз в день.</b>\n\nПопробуйте завтра <i>(возможность конвертации обновляется в 00:00 по МСК)</i>", reply_markup=back_menu_kb(user_id))
        return

    if convert_amount > maxprocent:
        await message.answer('❌ Вы не можете конвертировать больше 1% от своего $MICO баланса', reply_markup=back_menu_kb(user_id))
        return

    if convert_amount < 1000:
        await message.answer('❌ Невозможно конвертировать сумму меньше 1000 $MICO', reply_markup=back_menu_kb(user_id))
        return


    add_rub_balance = convert_amount//1000  # 1000 $MICO = 1 рубль
    await DB.add_rub_balance(user_id, add_rub_balance)
    await DB.add_balance(user_id, -convert_amount)
    await DB.update_last_conversion_date(user_id)

    user = await DB.select_user(user_id)
    mit_balance = user['balance']
    rub_balance = user['rub_balance']
    await DB.add_transaction(
        user_id=user_id,
        amount=convert_amount,
        description="конвертация",
        additional_info= None
    )
    await message.answer(f"✅ <b>Вы успешно конвертировали {convert_amount} $MICO в {add_rub_balance}₽</b>\n\n"
                                     f"💰 <b>Текущий баланс:</b>\nMitCoin - {mit_balance} $MICO;\nРубли - {rub_balance}₽", reply_markup=back_menu_kb(user_id))




@router.callback_query(lambda c: c.data.startswith("convert_"))
async def corvertation_rubtomit_input1(callback: types.CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    convert_amount = int(callback.data.split('_')[1])  # Начальная страница
    user = await DB.select_user(user_id)
    mit_balance = user['balance']
    rub_balance = user['rub_balance']
    maxprocent = mit_balance // 100

    last_conversion_date = await DB.get_last_conversion_date(user_id)
    today = datetime.now(MOSCOW_TZ).strftime("%Y-%m-%d")

    if last_conversion_date == today:
        await callback.message.answer("❌ <b>Конвертацию можно проводить только один раз в день.</b>\n\nПопробуйте завтра <i>(возможность конвертации обновляется в 00:00 по МСК)</i>", reply_markup=back_menu_kb(user_id))
        return

    if convert_amount > maxprocent:
        await callback.message.edit_text('❌ Вы не можете конвертировать больше 1% от своего $MICO баланса', reply_markup=back_menu_kb(user_id))
        return

    if convert_amount < 1000:
        await callback.message.edit_text('❌ Невозможно конвертировать сумму меньше 1000 $MICO', reply_markup=back_menu_kb(user_id))
        return


    add_rub_balance = convert_amount//1000  # 1000 $MICO = 1 рубль
    await DB.add_rub_balance(user_id, add_rub_balance)
    await DB.add_balance(user_id, -convert_amount)
    await DB.update_last_conversion_date(user_id)

    user = await DB.select_user(user_id)
    mit_balance = user['balance']
    rub_balance = user['rub_balance']

    await callback.message.edit_text(f"✅ <b>Вы успешно конвертировали {convert_amount} $MICO в {add_rub_balance}₽</b>\n\n"
                                     f"💰 <b>Текущий баланс:</b>\nMitCoin - {mit_balance} $MICO;\nРубли - {rub_balance}₽", reply_markup=back_menu_kb(user_id))


    await DB.add_transaction(
        user_id=user_id,
        amount=convert_amount,
        description="конвертация",
        additional_info= None
    )







CRYPTOBOT_TESTNET = False  # Указываем, что это тестовая среда

# Глобальная переменная для cryptopay
cryptopay = None

async def init_cryptopay():
    """Инициализация AioCryptoPay"""
    global cryptopay
    if cryptopay is None:
        cryptopay = AioCryptoPay(token=CRYPTOBOT_TOKEN, network=Networks.MAIN_NET)
    return cryptopay


@router.callback_query(F.data == 'select_deposit_menu')
async def select_deposit_handler(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    await callback.answer()
    await callback.message.edit_text("<b>Выберите удобный Вам способ депозита:</b>\n\n🔥 Акция, при депозите за рубли +25% к пополнению!", reply_markup=select_deposit_menu_kb(user_id))

@router.callback_query(F.data == 'deposit_menu')
async def deposit_handler(callback: types.CallbackQuery):
    # Создание кнопок для депозитов
    buttons = [
        ("100к MITcoin | 1💲", 100000, 1),
        ("250к MITcoin | 2.5💲", 250000, 2.5),
        ("500к MITcoin | 5💲", 500000, 5),
        ("1кк MITcoin | 10💲", 1000000, 10),
        ("2.5кк MITcoin | 25💲", 2500000, 25),
        ("5кк MITcoin | 50💲", 5000000, 50),
        ("🔙 Назад", None, None)  # Кнопка "Назад"
    ]

    # Создание списка кнопок для InlineKeyboardMarkup
    inline_buttons = []
    for text, amount, price in buttons:
        if amount is not None and price is not None and isinstance(amount, int):
            inline_buttons.append([InlineKeyboardButton(text=text, callback_data=f'deposit_{amount}_{price}')])
        else:
            inline_buttons.append([InlineKeyboardButton(text=text, callback_data='select_deposit_menu')])  # Кнопка "Назад"

    builder = InlineKeyboardMarkup(inline_keyboard=inline_buttons)  # Передача inline_keyboard

    await callback.message.edit_text(
        "💵 <b>Пополните баланс с помощью CryptoBot</b>\n\nВыберите сумму для пополнения:",
        reply_markup=builder)


@router.callback_query(F.data.startswith('deposit_'))
async def handle_deposit(callback: types.CallbackQuery, bot: Bot):
    data = callback.data.split('_')
    amount = int(data[1])  # Сумма MITcoin
    price = float(data[2])  # Цена в USDT

    try:
        invoice = await cryptopay.create_invoice(
            amount=price,
            asset='USDT',  # Указываем, что это счет для USDT
            description=f'Пополнение на {amount} MITcoin'
        )

        # Выводим все доступные атрибуты объекта invoice для отладки
        logger.error(f"Объект инвойса: {invoice}")

        # Получаем URL для оплаты
        payment_url = invoice.bot_invoice_url

        if not payment_url:
            logger.error("URL для оплаты не найден.")
            await callback.message.edit_text("🤔 Ошибка при создании счета. Попробуйте еще раз...",
                                             reply_markup=back_profile_kb())
            return

        # Создаем разметку для клавиатуры
        builder = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🔗 Оплатить", url=payment_url)
            ],
            [
                InlineKeyboardButton(text="🔙 Назад", callback_data="deposit_menu")
            ]
        ])

        await callback.message.edit_text(
            f"🧾 <b>Ваш счет на {amount} MITcoin:</b> \n\nСумма к оплате: {price} USDT. \n\n‼️ <b>После оплаты счета НЕ ВЫХОДИТЕ из данного меню до получения уведомления, иначе Ваш баланс пополнен НЕ БУДЕТ</b>\n\n⏳ <em>Счет действителен 5 минут</em>",
            reply_markup=builder
        )

        user_id = callback.from_user.id
        invoice_id = invoice.invoice_id
        for _ in range(30):  # 30 * 10 секунд = 300 секунд (5 минут)
            invoice = await cryptopay.get_invoices(invoice_ids=invoice_id)  # Получаем текущий статус инвойса
            logger.info(f"Статус инвойса {invoice_id}: {invoice.status}")

            if invoice.status == 'paid':
                # Если счет оплачен, начисляем MITCoin пользователю
                await DB.add_balance_dep(user_id, amount)
                await DB.add_deposit(user_id, amount=price)
                await callback.message.edit_text(f"🥳 Поздравляем! Вам начислено {amount} MITcoin",
                                                 reply_markup=back_menu_kb(user_id))
                await DB.add_transaction(
                    user_id=user_id,
                    amount=amount,
                    description="пополнение кб",
                    additional_info= None 
                )
                return

            await asyncio.sleep(10)  # Ждем 10 секунд перед следующей проверкой

    except Exception as e:
        logger.error(f"Ошибка при создании счета: {e}")
        await callback.message.edit_text("Ошибка при создании счета. Попробуйте еще раз.")




@router.callback_query(F.data == 'dep_stars_menu')
async def dep_stars_handler(callback: types.CallbackQuery):
    # Создание кнопок для пополнений через Telegram Stars
    buttons = [
        ("100к MITcoin | 49 ⭐", 100000, 49),
        ("250к MITcoin | 124 ⭐", 250000, 124),
        ("500к MITcoin | 249 ⭐", 500000, 249),
        ("1кк MITcoin | 499 ⭐", 1000000, 499),
        ("2.5кк MITcoin | 1249 ⭐", 2500000, 1249),
        ("5кк MITcoin | 2499 ⭐", 5000000, 2499),
        ("🔙 Назад", None, None)  # Кнопка "Назад"
    ]

    # Создание списка кнопок для InlineKeyboardMarkup
    inline_buttons = []
    for text, amount, price in buttons:
        if amount is not None and price is not None and isinstance(amount, int):
            inline_buttons.append([InlineKeyboardButton(text=text, callback_data=f'stars_{amount}_{price}')])
        else:
            inline_buttons.append([InlineKeyboardButton(text=text, callback_data='select_deposit_menu')])  # Кнопка "Назад"

    builder = InlineKeyboardMarkup(inline_keyboard=inline_buttons)

    await callback.message.edit_text(
        "⭐ <b>Пополните баланс через Telegram Stars:</b>\n\nВыберите сумму:",
        reply_markup=builder
    )


# Обработка кнопок пополнения через Telegram Stars
# Функция обработки кнопок для оплаты Stars
@router.callback_query(F.data.startswith('stars_'))
async def process_stars_payment(callback: types.CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    data = callback.data.split('_')  # Разделяем данные

    try:
        amount = int(data[1])  # Сумма MITcoin
        stars = int(data[2])   # Стоимость в Stars
    except (IndexError, ValueError):
        await callback.message.edit_text("❌ Ошибка обработки данных для платежа. Попробуйте снова.")
        await callback.answer()
        return

    # Создаем цены для оплаты
    prices = [LabeledPrice(label=f"{stars} Stars", amount=stars)]  # Цена в копейках

    try:
        # Отправляем счет
        await bot.send_invoice(
            chat_id=user_id,
            title=f"⭐ {amount} $MICO",
            description=f"Купить {amount} $MICO ($MICO) за {stars} Stars",
            payload=f"user_{user_id}_stars_{amount}",
            provider_token="",
            currency="XTR",
            prices=prices,
            start_parameter="stars_payment"
        )
    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка при создании счета: {e}")
        print(e)
        await callback.answer()

# Функция для обработки платежей
@router.pre_checkout_query()
async def pre_checkout_handler(pre_checkout_query: PreCheckoutQuery, bot: Bot):
    # Подтверждаем платеж
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

# Функция завершения оплаты

@router.message(F.successful_payment)
async def successful_payment_handler(message: types.Message, bot: Bot):
    user_id = message.from_user.id 
    payload = message.successful_payment.invoice_payload  # Определяем payload до использования


    # Проверяем, является ли оплата за майнинг
    if payload.startswith(f"user_{user_id}_stars_199"):
        # Обработка оплаты за майнинг
        # await DB.activate_mining(user_id)  # Активируем майнинг в базе данных
        await DB.add_mining(user_id, 1)
        kb = InlineKeyboardBuilder()
        kb.button(text='🚀 Майнинг', callback_data='mining')
        await message.answer("🚀 Майнинг активирован! Теперь вы можете зарабатывать $MICO автоматически. Заходите в меню майнинга, чтобы следить за доходом!", reply_markup=kb.as_markup())
        return 
    
    try:
        # Разделяем payload
        parts = payload.split('_')  # ['user', '<user_id>', 'stars', '<amount>']
        user_id = int(parts[1])  # Преобразуем user_id
        amount = int(parts[3])  # Преобразуем amount
    except (ValueError, IndexError) as e:
        await message.answer("☹  Произошла ошибка при обработке оплаты, обратитесь в тех. поддержку с чеком, который доступен выше")
        print(f"Error parsing payload: {payload} - {e}") 
        return

    # Определяем количество звезд в зависимости от суммы
    if amount == 100000:
        stars = 49
    elif amount == 250000:
        stars = 124 
    elif amount == 500000:
        stars = 249
    elif amount == 1000000:
        stars = 499
    elif amount == 2500000:
        stars = 1249
    elif amount == 5000000:
        stars = 2499
    else:
        stars = amount / 3000

    dep_stats = stars * 0.013
    # Зачисляем MITcoin на баланс пользователя
    await DB.add_balance_dep(user_id, amount)
    await DB.add_deposit(user_id, amount=dep_stats)

    # Отправляем сообщение об успешном пополнении
    await message.answer(
        f"✅ Пополнение успешно завершено!\n\n💳 Сумма: <b>{amount} MITcoin</b>\n"
        f"💸 Стоимость: <b>{stars} Stars</b>\n\nСпасибо за то, что Вы с нами! 😊",
        reply_markup=back_profile_kb()
    )

    # Записываем транзакцию в базу данных
    await DB.add_transaction(
        user_id=user_id,
        amount=amount,
        description="пополнение звёзды",
        additional_info=None
    )






@router.callback_query(F.data == 'buy_stars')
async def buystars_handler(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    await callback.answer()
    await callback.message.edit_text("<b>Вы можете обменять свои Telegram Stars на $MICO по курсу:</b>\n\n1⭐ = 3000 $MICO\n\n<b>Введите количество звезд, которое вы хотите продать</b>", reply_markup=back_menu_kb(user_id))
    await state.set_state(buystars.buystars)


@router.message(buystars.buystars)
async def buystars_hand(message: types.Message, state: FSMContext, bot: Bot):
    stars_amount = message.text
    try:
        stars_amount = int(stars_amount)
    except ValueError:
        await message.answer("Ошибка, повторите попытку", reply_markup=back_menu_kb(user_id))
        return

    user_id = message.from_user.id
    stars = stars_amount
    amount = stars * 3000

    await state.clear()
    # Создаем цены для оплаты

    prices = [LabeledPrice(label=f"{stars} Stars", amount=stars)]  # Цена в копейках
    try:
        # Отправляем счет
        await bot.send_invoice(
            chat_id=user_id,
            title=f"Продажа ⭐",
            description=f"Продать {stars} ⭐ за {amount} MitCoin",
            payload=f"user_{user_id}_stars_{amount}",
            provider_token="",
            currency="XTR",
            prices=prices,
            start_parameter="stars_payment"
        )
    except Exception as e:
        await message.answer(f"❌ Ошибка при создании счета: {e}", reply_markup=back_menu_kb(user_id))
        print(e)





@router.callback_query(F.data == 'rub_donate')
async def rub_donate_h(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.edit_text("🔥 Акция, при депозите за рубли +25% к пополнению!\n\n💰 Для депозита в рублях обращаться - @Coin_var", reply_markup=back_dep_kb())


@router.callback_query(F.data == 'refka_menu')
async def refki_handler(callback: types.CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    bot_username = (await bot.get_me()).username
    ref_link = f'https://t.me/{bot_username}?start={user_id}'
    user = await DB.select_user(user_id)

    if user and user.get('referrer_id'):
        referrer_id = user['referrer_id']
    else:
        referrer_id = 'нету'

    referred_users = await DB.get_referred_users(user_id)
    earned_from_referrals = await DB.get_earned_from_referrals(user_id)
    if earned_from_referrals is not None:
        earned_from_referrals = round(earned_from_referrals, 3)
    else:
        earned_from_referrals = 0
    stars = await DB.get_max_stars(user_id)

    text = (f'''

<b>Ваша реферальная ссылка:</b> \n<code>{ref_link}</code>\n
ID того, кто пригласил: <code>{referrer_id}</code>\n

<em>500 MITcoin и 1 ⭐ за каждого приглашенного пользователя</em>
<em>15% за пополнения и выполнение заданий рефералом</em>

Кол-во приглашенных пользователей: {len(referred_users)}  
Заработано с рефералов: {earned_from_referrals} MIT 💎
Звёзды: {stars} ⭐
''')


    await callback.message.edit_text(text, reply_markup=back_profile_kb())
    await callback.answer()


async def get_cached_data(key):
    """Получить данные из кэша"""
    data = redis_client.get(key)
    return json.loads(data) if data else None

async def set_cached_data(key, data, ttl=None):
    """Сохранить данные в кэш"""
    if ttl:
        redis_client.setex(key, timedelta(seconds=ttl), json.dumps(data))
    else:
        redis_client.set(key, json.dumps(data))


from utils.redis_utils import *

async def update_message_with_data(message, data, user_id):
    """Обновить сообщение с данными о заданиях"""
    await message.edit_text(
        f'''
💰 Вы можете заработать - <b>{data['total']} $MICO</b>

<b>Заданий на:</b>
📣 Каналы - {data['channel']} 
👥 Чаты - {data['chat']}         
👀 Посты - {data['post']}
💬 Комментарии - {data['comment']}
❤️ Реакции - {data['reaction']} 
🔗 Переходы в бота - {data['link']}
🚀 Бусты - {data['boost']}

🚨 <em>Запрещено покидать канал/чат ранее чем через 7 дней. За нарушение вы можете получить блокировку заработка или штраф!</em>

<b>Выберите способ заработка</b> 👇    
        ''',
        reply_markup=work_menu_kb(user_id)
    )

@router.callback_query(F.data == 'work_menu')
async def works_handler(callback: types.CallbackQuery, bot: Bot):
    user_id = callback.from_user.id

    if not await check_subs_op(user_id, bot):
        return

    if not await DB.get_break_status():
        await callback.message.answer('🛠Идёт технический перерыв🛠\nПопробуйте снова позже')
        return
    
    await callback.answer()

    temp_message = await callback.message.edit_text(
        '''
💰 Вы можете заработать - <b>загрузка...</b>

<b>Заданий на:</b>
📣 Каналы - загрузка... 
👥 Чаты - загрузка...         
👀 Посты - загрузка...
💬 Комментарии - загрузка...
❤️ Реакции - загрузка... 
🔗 Переходы в бота - загрузка...
🚀 Бусты - загрузка...

🚨 <em>Запрещено покидать канал/чат ранее чем через 7 дней. За нарушение вы можете получить блокировку заработка или штраф!</em>

<b>Выберите способ заработка</b> 👇    
        ''',
        reply_markup=work_menu_kb(user_id)
    )

    task_types = ['channel', 'chat', 'post', 'comment', 'reaction', 'link', 'boost']
    counts = {key: 0 for key in task_types}

    for task_type in task_types:
        # Обновляем кэш перед подсчётом
        await RedisTasksManager.refresh_task_cache(bot, task_type)
        cached = await RedisTasksManager.get_cached_tasks(task_type)

        valid_count = 0
        for task in cached or []:
            task_id = task['id'] if isinstance(task, dict) else task[0]
            if not (await DB.is_task_completed(user_id, task_id) or
                    await DB.is_task_failed(user_id, task_id) or
                    await DB.is_task_pending(user_id, task_id)):
                valid_count += 1

        counts[task_type] = valid_count

    counts['total'] = sum(counts.values())

    await update_message_with_data(temp_message, counts, user_id)



async def get_filtered_tasks_with_info(task_type, bot, user_id):
    tasks = await DB.select_tasks_by_type(task_type)
    filtered_tasks = []
    
    for task in tasks:
        if (await DB.is_task_completed(user_id, task[0]) or
            await DB.is_task_failed(user_id, task[0]) or
            await DB.is_task_pending(user_id, task[0])):
            continue
            
        task_info = {
            'id': task[0],
            'user_id': task[1],
            'target_id': task[2],
            'amount': task[3],
            'type': task[4],
            'other': task[6],
            'valid': True
        }
        
        try:
            if task_type in [1, 2]:
                try:
                    chat = await bot.get_chat(task[2])
                    task_info['title'] = chat.title
                    task_info['username'] = getattr(chat, 'username', None)
                    task_info['invite_link'] = getattr(chat, 'invite_link', None)
                except Exception as e:
                    task_info['valid'] = False
        except Exception as e:
            task_info['valid'] = False
        
        if task_info['valid']:
            filtered_tasks.append(task_info)
    
    return filtered_tasks








# Запуск фоновой задачи в основном цикле
# async def start_background_tasks(bot, DB):
    # Запускаем задачу обновления кэша раз в 5 минут
    # asyncio.create_task(remind_mining_collection(bot))
    # asyncio.create_task(scheduled_cache_update(bot, DB)) #channel
    # asyncio.create_task(scheduled_cache_update_chat(bot, DB)) #chat
    # asyncio.create_task(check_subscriptions_periodically(bot))
    # asyncio.create_task(check_subscriptions_periodically_boost(bot))
    # asyncio.create_task(process_tasks_periodically(bot)) #post
    # asyncio.create_task(update_reaction_tasks_periodically()) #reactions
    # asyncio.create_task(scheduled_db_backup(bot)) #отправка бд в чат





#ЗАДАНИЯ НА ПРОСМОТОР. ОТБОР

# Глобальная переменная для хранения обработанных заданий
processed_tasks = [] # POST
available_tasks = [] # LINKS
available_boost_tasks = [] # BOOSTS 



async def get_available_tasks(user_id, all_tasks):
    tasks = []
    for task in all_tasks:
        task_id = task[0]
        # Check if task has remaining amount and is valid
        if (task[3] > 0 and 
            not await DB.is_task_completed(user_id, task_id) and
            not await DB.is_task_skipped(user_id, task_id)):
            tasks.append(task)
    return tasks




# Метод для получения страницы с заданиями (пагинация)
def paginate_tasks(tasks, page=1, per_page=5):
    total_pages = (len(tasks) + per_page - 1) // per_page  # Вычисление общего количества страниц
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    tasks_on_page = tasks[start_idx:end_idx]
    return tasks_on_page, total_pages

@router.my_chat_member()
async def on_bot_added(event: ChatMemberUpdated, bot: Bot):
    # Проверяем, что бот был добавлен
    if event.new_chat_member.user.id == (await bot.get_me()).id:
        # Проверяем, что бот был добавлен в группу или супергруппу
        if event.chat.type in ['group', 'supergroup']:
            # Бота добавили в группу
            if event.new_chat_member.status in ['member', 'administrator']:
                chat_id = event.chat.id
                chat_title = event.chat.title
                inv_user_id = event.from_user.id

                # Отправляем сообщение в чат
                await bot.send_message(chat_id, "👋")
                await bot.send_message(chat_id, f"{chat_id}:{inv_user_id}")
                await bot.send_message(chat_id,
                                       "👆 Для завершения настройки перешлите <b>сообщение с кодом</b> в личные сообщения бота")
        # Игнорируем событие, если бот добавлен в канал
        elif event.chat.type == 'channel':
            return


# Метод для получения страницы с заданиями (пагинация)
async def paginate_tasks_chating(tasks, vchatingpage=1, per_page=5):
    total_pages = (len(tasks) + per_page - 1) // per_page  # Вычисление общего количества страниц
    start_idx = (vchatingpage - 1) * per_page
    end_idx = start_idx + per_page
    tasks_on_page = tasks[start_idx:end_idx]
    return tasks_on_page, total_pages








@router.message(Command('help'))
async def help_handler(message: types.Message, state: FSMContext):
    if message.chat.type in ['group', 'supergroup']:
        await message.answer('''
<b>Для настройки обязательной подписки (ОП)</b>:

1) Бот должен быть админом в данном чате и в рекламируемых каналах 📛
2) Напишите команду /setup @канал 
(для настройки ОП с таймером используйте /setup @канал **h, где ** количество часов)
<i>пример - /setup @mitcoinnews 12h</i>
3) для удаления всех ОП используйте /unsetup 
или /unsetup @канал для удаления конкретного канала 
4) список всех активных ОП в чате - /status

При включенной обязательной подписке пользователи не смогут писать в чат, пока не подпишутся на необходимые каналы 
        ''')


# Команда /setup для настройки ОП
@router.message(Command('setup'))
async def setup_op(message: types.Message, bot: Bot):
    # ID чата, где было отправлено сообщение
    chat_id = message.chat.id  

    # ID пользователя, который отправил команду
    user_id = message.from_user.id  

    # Проверяем, является ли пользователь админом в этом чате
    if not await is_user_admin(user_id, chat_id, bot):
        await message.answer(f'Вы не администратор в этом чате ({chat_id})')
        return  

    # Разбираем команду и проверяем указанный канал
    command_parts = message.text.split()
    if len(command_parts) < 2:
        await message.reply("🧾 Укажите канал/чат для настройки ОП. Пример: /setup @mitcoinnews")
        return

    channel_id = command_parts[1]  # ID канала из команды
    try:
        # Проверяем, является ли бот администратором в канале
        bot_member = await bot.get_chat_member(channel_id, bot.id)
        if bot_member.status != 'administrator':
            await message.reply("Бот должен быть администратором в указанном канале ⚠️")
            return
    except TelegramBadRequest:
        await message.reply("Канал не найден или бот не является его администратором 📛")
        return

    # Проверка наличия таймера
    timer_hours = None
    if len(command_parts) > 2 and command_parts[2].endswith("h"):
        timer_hours = int(command_parts[2][:-1])
        expiration_time = datetime.now() + timedelta(hours=timer_hours)
    else:
        expiration_time = None

    # Сохраняем ОП в базе данных
    await DB.add_op(chat_id, channel_id, expiration_time)

    if timer_hours:
        await message.reply(f"ОП на {channel_id} добавлена на {timer_hours} часов.")
    else:
        await message.reply(f"ОП на {channel_id} добавлена.")

    # Если есть таймер, запускаем задачу удаления
    if expiration_time:
        asyncio.create_task(remove_op_after_delay(chat_id, channel_id, expiration_time, bot))



# Команда /unsetup для удаления ОП
@router.message(Command('unsetup'))
async def unsetup_op(message: types.Message, bot: Bot):
    user_id = message.from_user.id
    chat_id = message.chat.id

    if not await is_user_admin(user_id, chat_id, bot):
        return  # Игнорируем команды от неадминистраторов

    command_parts = message.text.split()
    if len(command_parts) == 1:
        await DB.remove_op(chat_id)
        await message.reply("Все ОП были удалены 🗑️")
    else:
        channel_id = command_parts[1]
        await DB.remove_op(chat_id, channel_id)
        await message.reply(f"ОП на {channel_id} удалена 🗑️")


# Команда /status для отображения всех ОП
@router.message(Command('status'))
async def status_op(message: types.Message):
    chat_id = message.chat.id

    # Получаем все активные ОП из базы данных
    ops = await DB.get_ops(chat_id)
    if not ops:
        await message.reply("📄 В чате нет активных ОП")
        return

    status_message = "🗒️ Активные ОП:\n\n"
    for op in ops:
        channel = op[0]
        expiration = op[1]

        if expiration:
            expiration = datetime.strptime(expiration, "%Y-%m-%d %H:%M:%S.%f")

            remaining_time = expiration - datetime.now()
            # Расчет оставшихся часов и минут
            total_seconds = remaining_time.total_seconds()
            hours_left = int(total_seconds // 3600)
            minutes_left = int((total_seconds % 3600) // 60)

            status_message += f"{channel} - {hours_left} час(ов) {minutes_left} минут(ы)\n"
        else:
            status_message += f"{channel}\n"

    await message.reply(status_message)


async def is_user_admin(user_id, chat_id, bot):
    member = await bot.get_chat_member(chat_id, user_id)
    # Проверка статуса на наличие прав администратора или владельца
    return member.status in ["administrator", "creator"]


async def is_user_subscribed(user_id: int, channel_id: int, bot: Bot) -> bool:
    # Проверка, подписан ли пользователь на канал.
    try:
        member = await bot.get_chat_member(channel_id, user_id)
        return member.status != 'left'
    except TelegramBadRequest:
        return False


async def remove_op_after_delay(chat_id: int, channel_id: str, expiration_time: datetime, bot: Bot):
    # Функция для автоматического удаления ОП по истечении времени.
    delay = (expiration_time - datetime.now()).total_seconds()
    await asyncio.sleep(delay)
    await DB.remove_op(chat_id, channel_id)
    await bot.send_message(chat_id, f"ОП на {channel_id} была удалена в связи с окончанием таймера 🗑️")


@router.message(lambda message: message.chat.type in ['group', 'supergroup'])
async def handler_chat_message(message: types.Message, bot: Bot):
    user_id = message.from_user.id
    chat_id = message.chat.id
    name = message.from_user.full_name
    commands_list = ['/help', '/status', '/setup', '/unsetup']
    # Проверяем, является ли чат группой или супер-группой
    if (message.chat.type in ['group', 'supergroup']) and (message.text not in commands_list):

        # Получаем список всех задач из базы данных
        chating_tasks = await DB.get_chating_tasks()

        # Проверяем, есть ли чат в списке задач
        for task in chating_tasks:
            task_chat_id = task[1]
            price = task[2]
            if chat_id == task_chat_id:
                # Проверяем, есть ли пользователь в базе данных
                user_in_db = await DB.select_user(user_id)
                if user_in_db:
                    # Начисляем пользователю сумму на баланс
                    await DB.add_balance(user_id, price)
                break

        member = await bot.get_chat_member(chat_id, user_id)
        if name is None:
            name = "👤"
        if member.status in ["member"]:
            # Получаем все ОП для чата
            ops = await DB.get_ops(chat_id)
            if not ops:
                return  # Если нет активных ОП, не проверяем

            # Проверяем, подписан ли пользователь на все каналы ОП
            unsubscribed_channels = []
            op_tasks = await DB.get_op_tasks()
            if op_tasks:
                pr_op_task = random.choice(op_tasks)
                pr_op = pr_op_task[1]
                text = pr_op_task[2]

                pr_text = f"<a href='https://t.me/{pr_op[1:]}'>{text}</a>"
            else:
                pr_text = "ㅤ"

            # Цикл для проверки подписки и отправки сообщения с кнопками
            for op in ops:
                channel_id = op[0]
                if not await is_user_subscribed(user_id, channel_id, bot):
                    unsubscribed_channels.append(channel_id)

            # Если есть каналы, на которые нужно подписаться
            if unsubscribed_channels:
                try:
                    await message.delete()
                except:
                    print(f"ошибка удаления сообщения в {chat_id}")

                # Создаем клавиатуру вручную, экранируя текст в URL-канале
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="Подписаться", url=f"https://t.me/{channel[1:]}")]
                    for channel in unsubscribed_channels
                ])

                # Формируем список каналов для текстового сообщения
                channels_list = "\n".join(
                    [f"@{channel[1:]}" for channel in unsubscribed_channels])

                # Отправляем сообщение с кнопками
                msg = await message.answer(f"""
<a href='tg://user?id={user_id}'>{name}</a>, <b>для того чтобы отправлять сообщения в этот чат, подпишитесь на указанные каналы:</b>

{channels_list}
                """, reply_markup=keyboard, disable_web_page_preview=True)
                await asyncio.sleep(30)
                await msg.delete()









# Команда /top
@router.callback_query(F.data.startswith('rating'))
async def show_top(callback: types.CallbackQuery):
    top_users = await DB.get_top_users(ADMINS_ID)
    print(top_users)
    
    # Создаем клавиатуру с рейтингом
    keyboard = InlineKeyboardBuilder()

    for i in range(len(top_users)):
        user_id, username, balance = top_users[i]
        if i+1 == 1:
            emoji = "🥇"
        elif i+1 == 2:
            emoji = "🥈"
        elif i+1 == 3:
            emoji = "🥉"
        else:
            emoji = "🔹"
        keyboard.add(InlineKeyboardButton(text=f"{emoji}{i+1}. {username} - {balance} 💰", url='https://t.me/'+ username))
    keyboard.add(InlineKeyboardButton(text="🔙 Назад", callback_data='menu_stats'))
    keyboard.adjust(1) 

    
    # Отправляем сообщение с рейтингом
    await callback.message.edit_text("🏆 Топ-10 пользователей по балансу 🏆", reply_markup=keyboard.as_markup())


@router.callback_query(F.data.startswith('top_referrers'))
async def show_top_referrers(callback: types.CallbackQuery):
    # Получаем топ-10 пользователей по количеству рефералов
    top_referrers = await DB.get_top_referrers()
    
    # Создаем клавиатуру с рейтингом
    keyboard = InlineKeyboardBuilder()

    for i in range(len(top_referrers)):
        user_id, username, referral_count = top_referrers[i]
        if i + 1 == 1:
            emoji = "🥇"
        elif i + 1 == 2:
            emoji = "🥈"
        elif i + 1 == 3:
            emoji = "🥉"
        else:
            emoji = "🔹"
        keyboard.add(InlineKeyboardButton(
            text=f"{emoji}{i + 1}. {username} - {referral_count} 👥", 
            url=f'https://t.me/{username}'  # Ссылка на профиль пользователя
        ))
    
    # Добавляем кнопку "Назад"
    keyboard.add(InlineKeyboardButton(text="🔙 Назад", callback_data='menu_stats'))
    keyboard.adjust(1) 

    # Отправляем сообщение с рейтингом
    await callback.message.edit_text(
        "🏆 Топ-10 пользователей по количеству приглашённых рефералов 🏆", 
        reply_markup=keyboard.as_markup()
    )


@router.callback_query(F.data.startswith('referrers24hour'))
async def show_top_referrers(callback: types.CallbackQuery):
    # Получаем топ-10 пользователей по количеству рефералов за последние 24 часа
    top_referrers = await DB.get_top_referrers24hour(ADMINS_ID)
    
    # Создаем клавиатуру с рейтингом
    keyboard = InlineKeyboardBuilder()

    for i in range(len(top_referrers)):
        user_id, username, referral_count = top_referrers[i]
        if i + 1 == 1:
            emoji = "🥇"
        elif i + 1 == 2:
            emoji = "🥈"
        elif i + 1 == 3:
            emoji = "🥉"
        else:
            emoji = "🔹"

        # Если username отсутствует, не добавляем ссылку
        if username:
            button_text = f"{emoji}{i + 1}. {username} - {referral_count} 👥"
            keyboard.add(InlineKeyboardButton(
                text=button_text, 
                url=f'https://t.me/{username}'  # Ссылка на профиль пользователя
            ))
        else:
            button_text = f"{emoji}{i + 1}. Пользователь #{user_id} - {referral_count} 👥"
            keyboard.add(InlineKeyboardButton(
                text=button_text, 
                callback_data="no_link"  # Кнопка без ссылки
            ))
    
    # Добавляем кнопку "Назад"
    keyboard.add(InlineKeyboardButton(text="🔙 Назад", callback_data='menu_stats'))
    keyboard.adjust(1) 

    # Отправляем сообщение с рейтингом
    await callback.message.edit_text(
        "🏆 Топ-10 пользователей по количеству приглашённых рефералов за последние 24 часа 🏆", 
        reply_markup=keyboard.as_markup()
    )
# Пример использования



async def increment_daily_statistics(column):
    """Увеличивает значение в колонке ежедневной статистики."""
    await DB.increment_statistics(user_id=2, column=column)




# @router.callback_query(F.data.startswith('info_'))
# async def info_handler(callback: types.CallbackQuery, bot: Bot):
#     user_id = callback.from_user.id
#     task_id = int(callback.data.split('_')[-1])  # Извлекаем ID задания из callback_data

#     # Получаем данные задания
#     task = await DB.get_task_by_id(task_id)
#     if not task:
#         await callback.answer(" не найдено.")
#         return

#     target_id = task[2]
#     chat_id, message_id = map(int, target_id.split(":"))

#     # Получаем информацию о посте
#     success = await info(user_id, chat_id, message_id, bot)

#     if success:
#         await callback.answer("✅ Информация о посте отправлена.")
#     else:
#         await callback.answer("❌ Не удалось получить информацию о посте.")




# # Обработчик команды /info
# @router.message(Command('info'))
# async def handle_info_command(message: types.Message, state: FSMContext):
#     # Запрашиваем у пользователя переслать пост
#     await state.set_state(Info.forward)
#     await message.answer("📨 Пожалуйста, перешлите пост из канала, о котором хотите получить информацию.")


@router.message(Command('opp'))
async def start(message: types.Message, bot: Bot):
    user_id = message.from_user.id
    if not await check_subs_op(user_id, bot):
        return
    
    if not await DB.get_break_status():
        await message.answer('🛠Идёт технический перерыв🛠\nПопробуйте снова позже')
        return
    
    else:
        # Если пользователь подписан на все каналы
        await message.answer("Добро пожаловать! Вы подписаны на все каналы.")

# Обработка нажатия на кнопку "Я подписался"
@router.callback_query(F.data == 'op_proverka')
async def check_subscription(callback_query: types.CallbackQuery, bot: Bot):
    user_id = callback_query.from_user.id

    # Повторная проверка подписки
    channels = await DB.all_channels_op()
    not_subscribed = []

    for channel in channels:
        channel_id = channel[0]
        try:
            chat_member = await bot.get_chat_member(chat_id=channel_id, user_id=user_id)
            if chat_member.status not in ['member', 'administrator', 'creator']: 
                not_subscribed.append(channel)
        except Exception as e:
            print(f"Ошибка при проверке подписки: {e}")

    if not_subscribed:
        # Если пользователь всё ещё не подписан
        await callback_query.answer("Вы не подписались на все каналы!", show_alert=True)
    else:
        # Если пользователь подписался
        await callback_query.answer("Спасибо за подписку!", show_alert=True)
        await bot.send_message(user_id, "Теперь вы можете пользоваться ботом.")





async def check_subs_op(user_id, bot: Bot):

    # Проверяем, подписан ли пользователь на все каналы
    channels = await DB.all_channels_op()
    not_subscribed = []

    for channel in channels:
        channel_id = channel[0]
        try:
            chat_member = await bot.get_chat_member(chat_id=channel_id, user_id=user_id)
            if chat_member.status not in ['member', 'administrator', 'creator']:
                not_subscribed.append(channel)
        except Exception as e:
            print(f"Ошибка при проверке подписки: {e}")

    if not_subscribed:
        print(f'https://t.me/{channel[0].replace("@", "")}')
        # Если пользователь не подписан на некоторые каналы
        keyboard = InlineKeyboardBuilder()
        for channel in not_subscribed:
            keyboard.add(InlineKeyboardButton(
                text=f"📢 {channel[1]}",
                url=f"https://t.me/{channel[0].replace('@', '')}"
            ))
        keyboard.add(InlineKeyboardButton(
            text="✅ Я подписался",
            callback_data="op_proverka"
        ))
        keyboard.adjust(1)
        await bot.send_message(
            user_id,
            "Для использования бота подпишитесь на следующие каналы:",
            reply_markup=keyboard.as_markup()
        )
        return False
    return True



# from telethon import TelegramClient
# from config import api_id, api_hash, phone_number
# from telethon.tl.functions.messages import GetMessagesRequest, GetRecentReactionsRequest, ReadReactionsRequest, GetRecentReactionsRequest, GetRepliesRequest, GetHistoryRequest
# from telethon.tl.types import ReactionEmoji  
# from telethon import functions, types 
# from telethon.tl.types import InputMessageID 
# from telethon.errors import ChatWriteForbiddenError
# from telethon.tl.types import InputPeerChat, InputPeerChannel, InputPeerUser
# from telethon.tl.functions.premium import GetBoostsStatusRequest, GetUserBoostsRequest
# from telethon.tl.types import InputPeerChannel, InputUser
# from telethon.tl.functions.channels import GetFullChannelRequest

# # Инициализация клиента Telethon
# from telethon.errors import FloodWaitError

# # Инициализация клиентов
# clients = [
#     TelegramClient('session_name1', 26226969, 'ad23f103ca534197dca27c8b3b5c98a1'),
#     TelegramClient('session_name2', 27766851, '9caf54b36748a7043312fdb202a92ae4'),
#     TelegramClient('session_name3', 25159668, '3c0bf4ca735fec3f3cb59302239a0cca')
# ]

# # sessions = [
# #     {"session_name": "session_name", "api_id": 25159668, "api_hash": "3c0bf4ca735fec3f3cb59302239a0cca", "phone_number": "+79097217693"},
# #     {"session_name": "session_name2", "api_id": 26226969, "api_hash": "ad23f103ca534197dca27c8b3b5c98a1", "phone_number": "+79914512687"},
# #     {"session_name": "session_name3", "api_id": 27766851, "api_hash": "9caf54b36748a7043312fdb202a92ae4", "phone_number": "+79223348628"},
# # ]

# # Индекс последней использованной сессии
# last_used_client_index = 0

# # Функция для отправки уведомления в Telegram
# async def send_notification(message):
#     try:
#         # Используем первый клиент для отправки уведомления
#         await clients[0].start()
#         await clients[0].connect()
#         await clients[0].send_message(5129878568, message)  # Отправляем сообщение
#         await clients[0].disconnect()
#     except Exception as e:
#         print(f"Ошибка при отправке уведомления: {e}")

# # Функция для получения следующей сессии
# def get_next_client():
#     global last_used_client_index
#     router = clients[last_used_client_index]
#     last_used_client_index = (last_used_client_index + 1) % len(clients)  # Переход к следующей сессии
#     return router

# async def comment(user_id, chat_id, message_id):
#     """
#     Проверяет, оставил ли пользователь комментарий под постом.
#     :param user_id: ID пользователя, который должен оставить комментарий.
#     :param chat_id: ID чата, где находится пост.
#     :param message_id: ID сообщения (поста).
#     :return: True, если комментарий есть, иначе False.
#     """
#     # for _ in range(len(clients)):  # Перебираем все сессии
#     #     router = get_next_client()
#     #     try:
#     #         print(f"Используется сессия: {router.session.filename}")
#     #         await router.start()
#     #         await router.connect()

#     #         # Получаем информацию о чате
#     #         try:
#     #             peer = await router.get_entity(chat_id)
#     #         except Exception as e:
#     #             print(f"Ошибка при получении информации о чате: {e}")
#     #             await router.disconnect()
#     #             continue

#     #         # Получаем список комментариев к сообщению
#     #         replies = await router(GetRepliesRequest(
#     #             peer=peer,
#     #             msg_id=message_id,
#     #             offset_id=0,
#     #             offset_date=None,
#     #             add_offset=0,
#     #             limit=100,  # Максимальное количество комментариев для проверки
#     #             max_id=0,
#     #             min_id=0,
#     #             hash=0
#     #         ))
#     #         print(replies)

#     #         # Проверяем, есть ли среди комментариев комментарий от нужного пользователя
#     #         for message in replies.messages:
#     #             if message.from_id and message.from_id.user_id == user_id:
#     #                 print(f"Пользователь {user_id} оставил комментарий!")
#     #                 await router.disconnect()
#     #                 return True
#     #         await router.disconnect()
#     #     except FloodWaitError as e:
#     #         # Отправляем уведомление о блокировке
#     #         await send_notification(f"Сессия {router.session.filename} заблокирована на {e.seconds} секунд.")
#     #         print(f"FloodWait: нужно подождать {e.seconds} секунд")
#     #         continue  # Переходим к следующей сессии
#     #     except Exception as e:
#     #         print(f"Ошибка при проверке комментария: {e}")
#     #         continue  # Переходим к следующей сессии
#     return False

# async def boost(channel_username, user_id):
#     # for _ in range(len(clients)):  # Перебираем все сессии
#     #     router = get_next_client()
#     #     try:
#     #         print(f"Используется сессия: {router.session.filename}")
#     #         await router.start()
#     #         await router.connect()

#     #         # Получаем информацию о канале
#     #         channel = await router.get_entity(channel_username)

#     #         # Получаем полную информацию о канале
#     #         full_channel = await router(GetFullChannelRequest(channel=channel))

#     #         # Создаем объект InputPeerChannel для использования в GetBoostsStatusRequest
#     #         input_peer = InputPeerChannel(channel_id=channel.id, access_hash=channel.access_hash)

#     #         # Получаем статус бустов
#     #         boosts_status = await router(GetBoostsStatusRequest(peer=input_peer))

#     #         # Получаем информацию о пользователе
#     #         user = await router.get_entity(user_id)
#     #         input_user = InputUser(user_id=user.id, access_hash=user.access_hash)

#     #         # Получаем информацию о бустах пользователя
#     #         user_boosts = await router(GetUserBoostsRequest(peer=input_peer, user_id=input_user))

#     #         # Проверяем, есть ли у пользователя бусты на канале
#     #         if hasattr(user_boosts, 'boosts') and len(user_boosts.boosts) > 0:
#     #             print(f"Пользователь {user_id} сделал буст на канал {channel_username}.")
#     #             await router.disconnect()
#     #             return True

#     #         await router.disconnect()
#     #     except FloodWaitError as e:
#     #         # Отправляем уведомление о блокировке
#     #         await send_notification(f"Сессия {router.session.filename} заблокирована на {e.seconds} секунд.")
#     #         print(f"FloodWait: нужно подождать {e.seconds} секунд")
#     #         continue  # Переходим к следующей сессии
#     #     except Exception as e:
#     #         print(f"Ошибка при проверке буста: {e}")
#     #         continue  # Переходим к следующей сессии
#     return False

# async def check_premium(user_id):
#     # for _ in range(len(clients)):  # Перебираем все сессии
#     #     router = get_next_client()
#     #     try:
#     #         print(f"Используется сессия: {router.session.filename}")
#     #         await router.connect()

#     #         # Получаем информацию о пользователе
#     #         user = await router.get_entity(user_id)
#     #         if user.premium:
#     #             print(f"У пользователя {user.first_name} есть Telegram Premium!")
#     #             await router.disconnect()
#     #             return True
#     #         else:
#     #             print(f"У пользователя {user.first_name} нет Telegram Premium.")
#     #             await router.disconnect()
#     #     except FloodWaitError as e:
#     #         # Отправляем уведомление о блокировке
#     #         await send_notification(f"Сессия {router.session.filename} заблокирована на {e.seconds} секунд.")
#     #         print(f"FloodWait: нужно подождать {e.seconds} секунд")
#     #         continue  # Переходим к следующей сессии
#     #     except Exception as e:
#     #         print(f"Ошибка при проверке премиума: {e}")
#     #         continue  # Переходим к следующей сессии
#     return False














# # import asyncio
# # from telethon import TelegramClient
# # from telethon.errors import FloodWaitError
# # from aiogram import Bot

# # # Импортируем конфигурацию
# # from config import sessions  # Убедитесь, что sessions определен в config.py

# # # Создаем клиенты для каждой сессии
# # clients = []
# # for session in sessions:
# #     tg_client = TelegramClient(session["session_name"], session["api_id"], session["api_hash"])
# #     clients.append(tg_client)


# # async def update_premium_users2(bot: Bot):
# #     try:
# #         # Получаем всех пользователей из базы данных
# #         all_users = await DB.get_all_users()  # Убедитесь, что DB определен
# #         total_users = len(all_users)
# #         premium_users_count = 0
# #         count = 0

# #         # Отправляем начальное сообщение
# #         message = await bot.send_message(
# #             5129878568,
# #             f'#prem \nПроверка начата. Всего пользователей: {total_users}. '
# #             f'Обработано: 0. Премиум: 0. Обычные: 0.'
# #         )

# #         # Переворачиваем список пользователей для обработки с конца
# #         all_users_reversed = all_users[::-1]

# #         # Перебор всех пользователей с конца
# #         for i, user in enumerate(all_users_reversed):
# #             user_id = user[1]  # Убедитесь, что user_id находится на индексе 1

# #             # Выбираем клиента по очереди
# #             tg_client = clients[i % len(clients)]
# #             session = sessions[i % len(sessions)]

# #             try:
# #                 # Проверяем, есть ли у пользователя Telegram Premium
# #                 prem = await check_premium(user_id, tg_client)
# #                 if prem:
# #                     prem = 1
# #                     premium_users_count += 1  # Увеличиваем счетчик премиум-пользователей
# #                 else:
# #                     prem = 0
# #                 print(user_id, prem)
# #                 count += 1  # Увеличиваем общий счетчик обработанных пользователей

# #                 # Обновляем данные пользователя в базе данных
# #                 await DB.update_user_premium(user_id, prem)  # Убедитесь, что DB определен

# #                 # Обновляем сообщение
# #                 await message.edit_text(
# #                     f'#prem \nПроверка начата. Всего пользователей: {total_users}. '
# #                     f'Обработано: {count}. Премиум: {premium_users_count}. Обычные: {count - premium_users_count}.'
# #                 )

# #                 # Задержка после каждого запроса
# #                 await asyncio.sleep(3)

# #                 # Пауза после каждых 7 запросов
# #                 if count % 7 == 0:  # Пауза после каждых 7 запросов
# #                     await asyncio.sleep(30)

# #             except Exception as e:
# #                 # Логируем ошибку, если что-то пошло не так
# #                 print(f"Ошибка при проверке пользователя {user_id}: {e}")
# #                 continue  # Переходим к следующему пользователю

# #         # Отправляем итоговое сообщение
# #         await bot.send_message(
# #             5129878568,
# #             f'#prem \nПроверка завершена. Premium статус обновлен для {total_users} пользователей. '
# #             f'Из них {premium_users_count} имеют Telegram Premium.'
# #         )
# #     except Exception as e:
# #         # Логируем любые неожиданные ошибки
# #         print(f"Неожиданная ошибка в update_premium_users: {e}")





# url = "http://45.143.203.232/get_balance"
# data = {"user_id": 5129878568}

# response = requests.post(url, json=data)
# print(response.json())  



