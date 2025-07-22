from handlers.client.client import *

@router.callback_query(F.data == 'checks_menu')
async def checks_menu(callback: types.CallbackQuery, bot: Bot):
    user_id = callback.from_user.id

    # Проверяем, подписан ли пользователь на все каналы
    channels = await DB.all_channels_op()
    not_subscribed = []

    from handlers.client.client import check_subs_op
    if not await check_subs_op(user_id, bot):
        return
    
    if await DB.get_break_status() and user_id not in ADMINS_ID:
        await callback.message.answer('🛠Идёт технический перерыв🛠\nПопробуйте снова позже')
        return
    
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
        await callback.message.answer(
            "Для использования бота подпишитесь на следующие каналы:",
            reply_markup=keyboard.as_markup()
        )
    else:
        add_button = InlineKeyboardButton(text="👤 Сингл-чек (одноразовый)", callback_data="single_check")
        add_button1 = InlineKeyboardButton(text="💰 Мои чеки", callback_data="my_checks")
        add_button2 = InlineKeyboardButton(text="👥 Мульти-чек (многоразовый)", callback_data=f"multi_check")
        add_button3 = InlineKeyboardButton(text="🔙 Назад", callback_data="back_menu")
        # Создаем клавиатуру и добавляем в нее кнопку
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[add_button], [add_button1], [add_button2], [add_button3]])

        await callback.message.edit_text("💸 Чеки позволяют быстро и удобно передавать $MICO\n\n<b>Выберите необходимый тип чека:</b>", reply_markup=keyboard)

CHECKS_TYPES = {
    1: '👤 Сингл-Чек',
    2: '👥 Мульти-чек'
}

async def generate_tasks_keyboard_checks(checks, checkspage, total_pages):
    builder = InlineKeyboardBuilder()

    # Выводим задания на текущей странице (по 5 на страницу)
    for check in checks:
        print(check)
        check_type = CHECKS_TYPES.get(check[3], 'Неизвестно')
        amount = check[4]
        button_text = f"{check_type} | {amount} $MICO"
        # Каждая кнопка в новой строке
        builder.row(InlineKeyboardButton(text=button_text, callback_data=f"check_{check[0]}"))

    # Кнопка "Назад"
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="checks_menu"))

    # Кнопки пагинации
    pagination = []
    if checkspage > 1:
        pagination.append(InlineKeyboardButton(text="⬅️", callback_data=f"checkspage_{checkspage - 1}"))
    pagination.append(InlineKeyboardButton(text=str(checkspage), callback_data="checkscurrent_page"))
    if checkspage < total_pages:
        pagination.append(InlineKeyboardButton(text="➡️", callback_data=f"checkspage_{checkspage + 1}"))

    builder.row(*pagination)  # Кнопки пагинации в одну строку

    return builder.as_markup()

# Метод для получения страницы с заданиями (пагинация)
def checkspaginate_tasks(checks, checkspage=1, per_page=5):
    total_pages = (len(checks) + per_page - 1) // per_page  # Вычисление общего количества страниц
    start_idx = (checkspage - 1) * per_page
    end_idx = start_idx + per_page
    tasks_on_page = checks[start_idx:end_idx]
    return tasks_on_page, total_pages

@router.callback_query(F.data == 'my_checks')
async def my_checks(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    checks = await DB.get_check_by_user_id(user_id)
    print(checks)
    # Начинаем с первой страницы
    checkspage = 1
    tasks_on_page, total_pages = paginate_tasks(checks, checkspage)

    # Генерируем инлайн кнопки
    keyboard = await generate_tasks_keyboard_checks(tasks_on_page, checkspage, total_pages)

    await callback.message.edit_text("💸 <b>Ваши чеки:</b>", reply_markup=keyboard)

@router.callback_query(lambda c: c.data.startswith("checkspage_"))
async def change_page_handler(callback: types.CallbackQuery):
    checkspage = int(callback.data.split('_')[1])
    user_id = callback.from_user.id
    checks = await DB.get_check_by_user_id(user_id)

    # Получаем задания на нужной странице
    tasks_on_page, total_pages = paginate_tasks(checks, checkspage)

    # Генерируем инлайн кнопки
    keyboard = await generate_tasks_keyboard_checks(tasks_on_page, checkspage, total_pages)

    await callback.message.edit_text("💸 Ваши чеки:", reply_markup=keyboard)

@router.callback_query(lambda c: c.data.startswith("check_"))
async def check_detail_handler(callback: types.CallbackQuery, bot: Bot):
    await callback.answer()
    check_id = int(callback.data.split('_')[1]) 
    check = await DB.get_check_by_id(check_id)
    
    # Выносим значения из check в переменные с понятными именами
    check_id = check[0]  # check_id (INTEGER)
    uid = check[1]  # uid (TEXT)
    user_id = check[2]  # user_id (INTEGER)
    check_type = check[3]  # type (INTEGER)
    check_sum = check[4]  # sum (INTEGER)
    check_amount = check[5]  # amount (INTEGER)
    check_description = check[6]  # description (TEXT)
    locked_for_user = check[7]  # locked_for_user (INTEGER)
    password = check[8]  # password (TEXT)
    OP_id = check[9]  # OP_id (TEXT)
    max_amount = check[10]  # max_amount (INTEGER)
    ref_bonus = check[11]  # ref_bonus (INTEGER)
    ref_fund = check[12]  # ref_fund (INTEGER)
    OP_name = check[13]  # OP_name (TEXT)

    bot_username = (await bot.get_me()).username
    check_link = f'https://t.me/{bot_username}?start=check_{uid}'

    # Определяем тип задачи
    check_type_str = CHECKS_TYPES.get(check_type, 'Неизвестно')

    # Обработка значений по умолчанию
    if check_description is None:
        check_description = " "
    if locked_for_user is None:
        locked_for_user = "нет"
    if password is None:
        password = "нет"
    if OP_id is None:
        OP_id = "нет"

    # Получаем информацию о канале, если он указан
    if OP_id and OP_id != "нет":
        try:
            chat = await bot.get_chat(OP_id)
            OP_name = f'<a href="https://t.me/{chat.username}">{chat.title}</a>'
        except Exception as e:
            logger.error(f"Ошибка при получении информации о канале: {e}")
            OP_name = "Ошибка при получении информации"
    else:
        OP_name = OP_id

    # Формируем информацию о чеке в зависимости от его типа
    if check_type == 1:  # Одноразовый чек
        check_info = f'''
💸 <b>Одноразовый чек на сумму {check_sum} $MICO</b>

📝 <b>Описание:</b> {check_description}
📌 <b>Привязка к пользователю:</b> {locked_for_user}

❗ Помните, что отправляя кому-либо ссылку на чек - Вы передаете свои монеты без гарантий получить что-либо в ответ

<span class="tg-spoiler">{check_link}</span>
        '''
    elif check_type == 2:  # Многоразовый чек
        check_info = f"""
💸 <b>Многоразовый чек на сумму {check_sum * check_amount} $MICO</b>

<b>Общее количество активаций: {max_amount} </b>
<b>Количество оставшихся активаций: {check_amount} </b>
<b>Сумма одной активации: {check_sum} $MICO</b>
 
📝 <b>Описание:</b> {check_description}
🔐 <b>Пароль:</b> {password}
📣 <b>Обязательная подписка (ОП):</b> {OP_name}


❗ Помните, что отправляя кому-либо ссылку на чек - Вы передаете свои монеты без гарантий получить что-либо в ответ

<span class="tg-spoiler">{check_link}</span>
        """

    # Формируем клавиатуру в зависимости от типа чека
    if check_type == 1:  # Одноразовый чек
        add_button = InlineKeyboardButton(
            text="✈ Отправить",
            switch_inline_query=f'\nЧЕК НА СУММУ {check_sum} $MICO\n{check_description}\n\n{check_link}'
        )
        add_button1 = InlineKeyboardButton(
            text="📝 Добавить описание",
            callback_data=f'adddiscription_{check_id}'
        )
        add_button2 = InlineKeyboardButton(
            text="⛓ Привязать к пользователю",
            callback_data=f"pincheckuser_{check_id}"
        )
        add_button3 = InlineKeyboardButton(
            text="🗑 Удалить",
            callback_data=f"checkdelete_{check_id}"
        )
        add_button4 = InlineKeyboardButton(
            text="🔙 Назад",
            callback_data="my_checks"
        )
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[[add_button], [add_button1], [add_button2], [add_button3], [add_button4]]
        )
    elif check_type == 2:  # Многоразовый чек
        add_button = InlineKeyboardButton(
            text="✈ Отправить",
            switch_inline_query=f'💸 ЧЕК НА СУММУ {check_sum * check_amount} $MICO\n{check_description}\n\n{check_link}'
        )
        add_button1 = InlineKeyboardButton(
            text="📝 Добавить описание",
            callback_data=f'adddiscription_{check_id}'
        )
        add_button2 = InlineKeyboardButton(
            text="📣 Добавить ОП",
            callback_data=f"addopcheck_{check_id}"
        )
        add_button3 = InlineKeyboardButton(
            text="🔑 Задать пароль",
            callback_data=f"addpasswordcheck_{check_id}"
        )
        add_button4 = InlineKeyboardButton(
            text="👑 Разместить в $MICO DROPS",
            callback_data=f"sendmitdrops_{check_id}"
        )
        add_button5 = InlineKeyboardButton(
            text="💰 Пополнить баланс чека",
            callback_data=f"addbalancecheck_{check_id}"
        )
        add_button6 = InlineKeyboardButton(
            text="🗑 Удалить",
            callback_data=f"checkdelete_{check_id}"
        )
        add_button7 = InlineKeyboardButton(
            text="🔙 Назад",
            callback_data="my_checks"
        )
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [add_button], [add_button1], [add_button2], [add_button3],
                [add_button4], [add_button5], [add_button6], [add_button7]
            ]
        )

    # Редактируем сообщение с новой информацией и клавиатурой
    await callback.message.edit_text(check_info, reply_markup=keyboard)

@router.callback_query(lambda c: c.data.startswith("sendmitdrops_"))
async def sendmitdrops(callback: types.CallbackQuery, state: FSMContext):
    check_id = int(callback.data.split('_')[1])
    user_id = callback.from_user.id
    add_button = InlineKeyboardButton(text="📤 Разместить", callback_data=f"mitcoindrop_{check_id}")
    add_button1 = InlineKeyboardButton(text="🔙 Назад", callback_data=f"check_{check_id}")
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[add_button], [add_button1]])
    await callback.message.edit_text('''
<b>Вы можете разместить свой чек в @mitcoin_drops</b> 

<b>Условия размещения:</b>
1) Чек без пароля
2) Общая сумма чека больше 50000 $MICO 
    ''', reply_markup=keyboard)

@router.callback_query(lambda c: c.data.startswith("mitcoindrop_"))
async def sendmitdrops1(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    check_id = int(callback.data.split('_')[1])
    user_id = callback.from_user.id
    check = await DB.get_check_by_id(check_id)
    type = check[3]
    sum = check[4]
    amount = check[5]
    bot_username = (await bot.get_me()).username
    general_sum = sum*amount
    check_link = f'https://t.me/{bot_username}?start=check_{check[1]}'
    if type == 2 and general_sum >= 50000 and check[8] is None:

        if check[6] is not None:
            description = check[6]
        else:
            description = ''
            
        text = f'''
💸 <b>Чек на сумму {general_sum} MitCoin</b>

{amount} активаций
{sum} MitCoin за одну активацию

{description}

{check_link}        
        '''
        try:
            add_button = InlineKeyboardButton(text="Получить", url=check_link)
            keyboard = InlineKeyboardMarkup(inline_keyboard=[[add_button]])
            await bot.send_message(chat_id='-1002446297366', text=text, reply_markup=keyboard)
            await callback.message.edit_text('🥳 Чек успешно размещен в @mitcoin_drops',reply_markup=back_menu_kb(user_id))
        except:
            await callback.message.edit_text('Ошибка размещения чека в @mitcoin_drops, попробуйте позже или обратитеть в тех поддержку', reply_markup=back_menu_kb(user_id))
    else:
        await callback.message.edit_text(
            '❌ Ваш чек не подходит по условиям',
            reply_markup=back_menu_kb(user_id))

@router.callback_query(lambda c: c.data.startswith("addopcheck_"))
async def delete_check_handler(callback: types.CallbackQuery, state: FSMContext):
    check_id = int(callback.data.split('_')[1])
    user_id = callback.from_user.id
    user = await DB.select_user(user_id)
    add_button = InlineKeyboardButton(text="🔙 Назад", callback_data=f"check_{check_id}")
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[add_button]])
    await callback.message.edit_text('📣 <b>Вы можете настроить обязательную подписку (ОП) для чека</b>\n\n<i>Пользователь не сможет активировать чек, пока не подпишется на канал</i>\n\n<b>Перешлите любое сообщение из канала, на который нужно подписаться</b>', reply_markup=keyboard)
    await state.set_state(checks.check_op)
    await state.update_data(check_id=check_id)

@router.message(checks.check_op)
async def handle_custom_check_amount(message: types.Message, bot: Bot, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    check_id = data.get('check_id')

    # Проверяем, переслано ли сообщение из канала
    if not message.forward_from_chat or message.forward_from:
        await message.answer('❗ Пожалуйста, перешлите сообщение из канала, на который нужно подписаться.')
        return

    channel_id = message.forward_from_chat.id
    channel_name = message.forward_from_chat.title

    try:
        # Получаем информацию о канале
        chat = await bot.get_chat(channel_id)

        # Проверяем, является ли бот администратором канала
        bot_member = await bot.get_chat_member(channel_id, bot.id)
        if bot_member.status != 'administrator':
            # Если бот не администратор, предлагаем кнопку для добавления
            add_bot_button = InlineKeyboardButton(
                text="➕ Добавить бота в канал",
                url=f"https://t.me/mitcoin2bot?startchannel"
            )
            back_button = InlineKeyboardButton(text="🔙 Назад", callback_data=f"check_{check_id}")
            keyboard = InlineKeyboardMarkup(inline_keyboard=[[add_bot_button], [back_button]])
            print(channel_id)
            await message.answer(
                '❗ Бот не является администратором этого канала.\n\n'
                '1. Добавьте бота в канал как администратора.\n'
                '2. Дайте боту права на публикацию сообщений.\n'
                '3. Повторите попытку.',
                reply_markup=keyboard
            )
            return
        # Если бот администратор, сохраняем данные в базу
        await DB.update_check(check_id=check_id, OP_id=channel_id, OP_name=channel_name)
        add_button1 = InlineKeyboardButton(text="✅ Готово", callback_data=f"check_{check_id}")
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[add_button1]])
        await message.answer(f'📣 Канал <b>{channel_name}</b> успешно добавлен к ОП', reply_markup=keyboard)
        await state.clear()

    except Exception as e:
        print(e)
        print(channel_id)
        await message.answer('☹ Не удалось найти канал, либо произошла ошибка. Повторите попытку.')
        return

@router.callback_query(lambda c: c.data.startswith("addbalancecheck_"))
async def activation_check_handler(callback: types.CallbackQuery, state: FSMContext):
    check_id = int(callback.data.split('_')[1])
    user_id = callback.from_user.id
    user = await DB.select_user(user_id)
    balance = user["balance"]
    check = await DB.get_check_by_id(check_id)
    sum = check[4]
    available_act = balance // sum
    add_button = InlineKeyboardButton(text="🔙 Назад", callback_data=f"check_{check_id}")
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[add_button]])
    await callback.message.edit_text(f'➕ Вы можете добавить количество активаций к вашему чеку, не создавая новый\n\n<b>Введите количество активаций, которое вы хотите добавить ({available_act} максимально):</b>', reply_markup=keyboard)
    await state.set_state(checks.add_activation)
    await state.update_data(check_id=check_id)

@router.message(checks.add_activation)
async def handle_custom_check_activation(message: types.Message, bot: Bot, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    user = await DB.select_user(user_id)
    check_id = data.get('check_id')
    balance = user["balance"]
    check = await DB.get_check_by_id(check_id)
    sum = check[4]
    available_act = balance // sum
    try:
        text = int(message.text)
        if text > available_act:
            await message.answer(f'❗ Максимально вы можете добавить {available_act} активаций')
            return
        if text == "None":
            await message.answer('❗ Введите целое число')
            return
        new_amount = check[5] + text
        await DB.update_check(check_id=check_id, amount=new_amount)
        new_price = sum*text
        await DB.add_balance(user_id, amount=-new_price)
        add_button = InlineKeyboardButton(text="🔙 Назад", callback_data=f"check_{check_id}")
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[add_button]])
        await message.answer(f'🥳 <b>К чеку добавлено {text} активаций</b>', reply_markup=keyboard)
        await DB.add_transaction(
            user_id=user_id,
            amount=new_price,
            description="добавление выполнений к чеку",
            additional_info= None
        ) 
        await state.clear()
    except ValueError:
        await message.answer('❗ Введите желаемое количество активаций в виде целого числа')

@router.callback_query(lambda c: c.data.startswith("addpasswordcheck_"))
async def delete_check_handler(callback: types.CallbackQuery, state: FSMContext):
    check_id = int(callback.data.split('_')[1])
    user_id = callback.from_user.id
    user = await DB.select_user(user_id)
    add_button = InlineKeyboardButton(text="🔙 Назад", callback_data=f"check_{check_id}")
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[add_button]])
    await callback.message.edit_text('📝 <b>Отправьте пароль для чека:</b>', reply_markup=keyboard)
    await state.set_state(checks.check_password)
    await state.update_data(check_id=check_id)

@router.message(checks.check_password)
async def handle_custom_check_amount(message: types.Message, bot: Bot, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    check_id = data.get('check_id')
    try:
        text = str(message.text)
        if len(text) > 20:
            await message.answer('❗ Пароль не должен превышать 20 символов...')
            return
        if text == "None":
            await message.answer('❗ Пароль может быть исключительно в текстовом формате! Повторите попытку')
            return
        await DB.update_check(check_id=check_id, password=text)
        add_button = InlineKeyboardButton(text="🔙 К чеку", callback_data=f"check_{check_id}")
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[add_button]])
        await message.answer(f'<i>{text}</i>\n\nПароль установлен к чеку', reply_markup=keyboard)
        await state.clear()
    except ValueError:
        await message.answer('❗ Напишите пароль в текстовом формате...')

@router.callback_query(lambda c: c.data.startswith("adddiscription_"))
async def delete_check_handler(callback: types.CallbackQuery, state: FSMContext):
    check_id = int(callback.data.split('_')[1])
    user_id = callback.from_user.id
    user = await DB.select_user(user_id)
    await callback.message.edit_text('📝 <b>Отправьте необходимое описание для чека:</b>')
    await state.set_state(checks.check_discription)
    await state.update_data(check_id=check_id)

@router.message(checks.check_discription)
async def handle_custom_check_amount(message: types.Message, bot: Bot, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    check_id = data.get('check_id')
    try:
        text = str(message.text)
        if len(text) > 50:
            await message.answer('❗ Описание не должно превышать 50 символов...')
            return
        if text == "None":
            await message.answer('❗ В описании не может быть стикеров, картинок и другого медиа-контента, допустим только текст...')
            return
        await DB.update_check(check_id=check_id, description=text)
        add_button = InlineKeyboardButton(text="🔙 К чеку", callback_data=f"check_{check_id}")
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[add_button]])
        await message.answer(f'<i>{text}</i>\n\nОписание установлено к чеку', reply_markup=keyboard)
        await state.clear()
    except ValueError:
        await message.answer('❗ Напишите текстовое описание к чеку...')

@router.callback_query(lambda c: c.data.startswith("pincheckuser_"))
async def delete_check_handler(callback: types.CallbackQuery, state: FSMContext):
    check_id = int(callback.data.split('_')[1])
    user_id = callback.from_user.id
    user = await DB.select_user(user_id)
    await callback.message.edit_text('📝 <b>Отправьте @username либо ID пользователя, к которому нужно привязать чек</b>')
    await state.set_state(checks.check_lock_user)
    await state.update_data(check_id=check_id)

@router.message(checks.check_lock_user)
async def handle_custom_check_amount(message: types.Message, bot: Bot, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    check_id = data.get('check_id')
    try:
        user = str(message.text)

        if user == "None" or len(user) > 20:
            await message.answer('❗ Укажите верный юзернейм либо ID пользователя')
            return
        await DB.update_check(check_id=check_id, locked_for_user=user)
        add_button = InlineKeyboardButton(text="🔙 К чеку", callback_data=f"check_{check_id}")
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[add_button]])
        await message.answer(f'🔐 <b>Теперь этот чек доступен только для</b> {user}', reply_markup=keyboard)
        await state.clear()
    except ValueError:
        await message.answer('❗ Попробуйте заново...')

@router.callback_query(lambda c: c.data.startswith("checkdelete_"))
async def delete_check_handler(callback: types.CallbackQuery):
    check_id = int(callback.data.split('_')[1])
    user_id = callback.from_user.id
    user = await DB.select_user(user_id)
    balance = user['balance']
    check = await DB.get_check_by_id(check_id)
    amount = check[5]
    sum = check[4]

    cost = sum*amount

    new_balance = balance + cost

    # Удаляем задачу из базы данных
    await DB.delete_check(check_id=check_id, user_id=user_id)
    await DB.update_balance(user_id, balance=new_balance)
    await callback.message.edit_text("🗑")
    await asyncio.sleep(1)
    # После удаления возвращаем пользователя к его заданиям
    user_id = callback.from_user.id
    checks = await DB.get_check_by_user_id(user_id)
    checkspage = 1
    tasks_on_page, total_pages = paginate_tasks(checks, checkspage)
    keyboard = await generate_tasks_keyboard_checks(tasks_on_page, checkspage, total_pages)

    await callback.message.edit_text("💸 <b>Ваши чеки:</b>", reply_markup=keyboard)