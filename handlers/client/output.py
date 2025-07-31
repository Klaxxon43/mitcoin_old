from .client import *

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

    logger.info(user_usdt)
    if user_usdt < 2.5:
        await callback.message.edit_text(f"😢 <b>Недостаточно средств на балансе</b>\n\nНа вашем балансе {round(user_usdt, 3)}$, минимальная сумма <b>должна быть более 2.5$</b>", reply_markup=back_profile_kb())
        return

    add_button2 = InlineKeyboardButton(text="🔙 Назад", callback_data='back_menu')
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
    
    # Добавление транзакции в базу данных
    await DB.add_transaction(
        user_id=user_id,
        amount=amount,
        description="вывод USDT",
        additional_info=None
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
    
    # Добавление транзакции в базу данных
    await DB.add_transaction(
        user_id=user_id,
        amount=amount,
        description="вывод RUB",
        additional_info=None
    )
    await DB.add_rub_balance(user_id=user_id, amount=-amount)
    await DB.add_output(user_id=user_id, amount=amount, wallet=wallet, type=2)
    await state.clear()