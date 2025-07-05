from untils.Imports import *
from handlers.client.client import *
from .menu import check_router

@check_router.callback_query(F.data == 'multi_check')
async def create_multi_check(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    user_balance = await DB.get_user_balance(user_id)

    if user_balance < 1010:
        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(text="Пополнить баланс", callback_data='deposit_menu'))
        builder.add(InlineKeyboardButton(text="🔙 Назад", callback_data='back_menu'))
        await callback.message.edit_text(
            "❌ У вас недостаточно средств для создания мульти-чека.\nПополните баланс для продолжения.",
            reply_markup=builder.as_markup()
        )
        return

    await callback.message.edit_text(
        f"📋 <b>Введите необходимое количество активаций (целое число)</b>\n\nМаксимальное количество активаций при минимальной цене (1000 MitCoin) для вашего баланса - {int((user_balance/1000) - ((user_balance/1000)/100))}", reply_markup=cancel_all_kb()
    )
    await state.set_state(checks.multi_check_quantity)
    await state.update_data(balance=user_balance)

@check_router.message(checks.multi_check_quantity)
async def handle_multi_check_quantity(message: types.Message, state: FSMContext):
    data = await state.get_data()
    balance = data.get('balance')
    try:
        quantity = int(message.text)
        if quantity <= 0:
            await message.answer("❌ <b>Количество активаций не может быть меньше 0</b>, введите корректное число", reply_markup=cancel_all_kb())
            return
        if quantity > balance // 1000:
            await message.answer(f"❌ <b>У вас недостаточно MitCoin для создания {quantity} активаций чека.</b>\nПополните баланс для продолжения", reply_markup=cancel_all_kb())
            return

        await message.answer(f"💵 <b>Введите сумму MitCoin за одну активацию чека (целое число)</b>\n\n<i>Максимальная сумма для вашего баланса - {int(balance//quantity - ((balance//quantity)//100))} MitCoin</i>", reply_markup=cancel_all_kb())
        await state.set_state(checks.multi_check_amount)
        await state.update_data(quantity=quantity)
    except ValueError:
        await message.answer("❌ Пожалуйста, введите корректное количество активаций", reply_markup=cancel_all_kb())

@check_router.message(checks.multi_check_amount)
async def handle_multi_check_amount(message: types.Message, bot: Bot, state: FSMContext):
    user_id = message.from_user.id
    user_balance = await DB.get_user_balance(user_id)

    try:
        data = await state.get_data()
        quantity = data.get('quantity')

        amount_per_check = int(message.text)
        total_amount = quantity * amount_per_check

        if amount_per_check < 1000:
            await message.answer("❌ Сумма одного чека должна быть 1000 MitCoin или больше. Попробуйте ещё раз.", reply_markup=cancel_all_kb())
            return

        if total_amount > user_balance:
            builder = InlineKeyboardBuilder()
            builder.add(InlineKeyboardButton(text="Пополнить баланс", callback_data='deposit_menu'))
            builder.add(InlineKeyboardButton(text="🔙 Назад", callback_data='back_menu'))
            await message.answer(
                f"❌ <b>У вас недостаточно средств для создания чека на {quantity} активаций и суммы в {amount_per_check} MitCoin за одну активацию</b>\n\nВаш баланс: {user_balance}\nОбщая сумма чека - {total_amount} ",
                reply_markup=builder.as_markup()
            )
            return

        # Сохраняем данные о чеке в состоянии
        await state.update_data(amount_per_check=amount_per_check, total_amount=total_amount)

        # Спрашиваем, хочет ли пользователь включить реферальную систему
        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(text="Да", callback_data='enable_referral'))
        builder.add(InlineKeyboardButton(text="Нет", callback_data='disable_referral'))
        await message.answer("🔗 <b>Хотите включить реферальную систему для этого чека?</b>", reply_markup=builder.as_markup())

    except ValueError:
        await message.answer("❌ <b>Пожалуйста, введите корректную сумму за одну активацию чека</b>")

@check_router.callback_query(F.data == 'enable_referral')
async def enable_referral(callback: types.CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="25%", callback_data='referral_percent_25'))
    builder.add(InlineKeyboardButton(text="50%", callback_data='referral_percent_50'))
    builder.add(InlineKeyboardButton(text="75%", callback_data='referral_percent_75'))
    builder.add(InlineKeyboardButton(text="100%", callback_data='referral_percent_100'))
    await callback.message.edit_text("📊 <b>Выберите процент от суммы чека, который будут получать рефералы:</b>", reply_markup=builder.as_markup())

@check_router.callback_query(F.data.startswith('referral_percent_'))
async def set_referral_percent(callback: types.CallbackQuery, state: FSMContext):
    percent = int(callback.data.split('_')[-1])
    await state.update_data(referral_percent=percent)

    await callback.message.answer(
        "📊 <b>Введите количество доступных активаций по реферальным ссылкам:</b>",
        reply_markup=cancel_all_kb()
    )
    await state.set_state(checks.set_ref_fund)

@check_router.message(checks.set_ref_fund)
async def handle_set_ref_fund(message: types.Message, state: FSMContext, bot: Bot):
    try:
        ref_fund = int(message.text)
        if ref_fund < 0:
            await message.answer("❌ Количество активаций не может быть отрицательным. Попробуйте ещё раз.", reply_markup=cancel_all_kb())
            return

        # Получаем данные о чеке из состояния
        data = await state.get_data()
        quantity = data.get('quantity')
        amount_per_check = data.get('amount_per_check')
        total_amount = data.get('total_amount') 
        referral_percent = data.get('referral_percent')
        print(total_amount)
        total_amount = total_amount//quantity 
        print(total_amount)
        # Рассчитываем общую сумму списания
        total_deduction = total_amount * quantity + ( total_amount * (referral_percent / 100) * ref_fund ) 
        print(total_deduction) 
        print(f'{total_amount} * {quantity} + ( {total_amount} * ({referral_percent / 100}) * {ref_fund} ) = {total_deduction}')
        # Списание с баланса
        user_id = message.from_user.id
        user_balance = await DB.get_user_balance(user_id)
        if user_balance < total_deduction:
            await message.answer("❌ Недостаточно средств на балансе для создания чека с учётом реферального фонда.", reply_markup=cancel_all_kb())
            return

        await DB.update_balance(user_id, balance=user_balance - total_deduction)

        # Генерация уникального чека
        uid = str(uuid.uuid4()) 
        await DB.create_check(
            uid=uid,
            user_id=user_id,
            type=2,
            sum=amount_per_check,
            amount=quantity,
            ref_bonus=referral_percent,
            ref_fund=ref_fund
        )

        check = await DB.get_check_by_uid(uid)
        check_id = check[0]
        bot_username = (await bot.get_me()).username
        check_link = f"https://t.me/{bot_username}?start=check_{uid}"

        add_button1 = InlineKeyboardButton(text="✈ Отправить", switch_inline_query=check_link)
        add_button2 = InlineKeyboardButton(text="⚙ Настройка", callback_data=f'check_{check_id}')
        add_button3 = InlineKeyboardButton(text="🔙 Назад", callback_data='checks_menu')

        keyboard = InlineKeyboardMarkup(inline_keyboard=[[add_button1], [add_button2], [add_button3]])
        await message.answer(
            f'''
💸 <b>Ваш мульти-чек создан:</b>

Количество активаций: {quantity}
Сумма за одну активацию: {amount_per_check} MitCoin
Реферальный фонд: {ref_fund} активаций

💰 Общая сумма чека: {total_amount} MitCoin
💼 Реферальный процент: {referral_percent}%

❗ Помните, что отправляя кому-либо эту ссылку Вы передаете свои монеты без гарантий получить что-то в ответ
<i>Вы можете настроить чек с помощью кнопки ниже</i>

<span class="tg-spoiler">{check_link}</span>
''',
            reply_markup=keyboard
        )
        await DB.add_transaction(
            user_id=user_id,
            amount=total_deduction,
            description="создание сульти чека",
            additional_info= None
        )

        await state.clear()
    except ValueError:
        await message.answer("❌ Пожалуйста, введите корректное число.", reply_markup=cancel_all_kb())

@check_router.callback_query(F.data == 'disable_referral')
async def disable_referral(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    # Получаем данные о чеке из состояния
    data = await state.get_data()
    quantity = data.get('quantity')
    amount_per_check = data.get('amount_per_check')
    total_amount = quantity * amount_per_check
    print(f'{quantity} * {amount_per_check}')

    # Создаем чек без реферального фонда
    uid = str(uuid.uuid4())
    await DB.create_check(
        uid=uid,
        user_id=callback.from_user.id,
        type=2,
        sum=amount_per_check,
        amount=quantity,
        ref_bonus=None,
        ref_fund=None
    )
    await DB.update_balance(callback.from_user.id, balance=await DB.get_user_balance(callback.from_user.id) - total_amount)

    bot_username = (await bot.get_me()).username
    check_link = f"https://t.me/{bot_username}?start=check_{uid}"
    add_button1 = InlineKeyboardButton(text="✈ Отправить", switch_inline_query=check_link)
    add_button2 = InlineKeyboardButton(text="⚙ Настройка", callback_data=f'check_{uid}')
    add_button3 = InlineKeyboardButton(text="🔙 Назад", callback_data='checks_menu')

    keyboard = InlineKeyboardMarkup(inline_keyboard=[[add_button1], [add_button2], [add_button3]])
    await callback.message.answer(
            f'''
💸 <b>Ваш мульти-чек создан:</b>

Количество активаций: {quantity}
Сумма за одну активацию: {amount_per_check} MitCoin
Реферальный фонд: отсутствует

💰 Общая сумма чека: {total_amount} MitCoin
💼 Реферальный процент: отсутствует

❗ Помните, что отправляя кому-либо эту ссылку Вы передаете свои монеты без гарантий получить что-то в ответ
<i>Вы можете настроить чек с помощью кнопки ниже</i>

<span class="tg-spoiler">{check_link}</span>
''',        reply_markup=keyboard  # Pass the keyboard object directly, without calling it
    )
    await DB.add_transaction(
        user_id=callback.from_user.id,
        amount=total_amount,
        description="создание мульти чека",
        additional_info= None
    )
    await state.clear()

@check_router.callback_query(F.data.startswith('refill_ref_fund_'))
async def refill_ref_fund(callback: types.CallbackQuery, state: FSMContext):
    """
    Запрашивает у пользователя количество активаций для пополнения реферального фонда.
    """
    check_id = int(callback.data.split('_')[-1])  # Получаем ID чека из callback_data
    await state.update_data(check_id=check_id)  # Сохраняем ID чека в состоянии

    await callback.message.answer(
        "💵 <b>Введите количество активаций для пополнения реферального фонда:</b>",
        reply_markup=cancel_all_kb()
    )
    await state.set_state(checks.refill_ref_fund)

@check_router.message(checks.refill_ref_fund)
async def handle_refill_ref_fund(message: types.Message, state: FSMContext, bot: Bot):
    """
    Обрабатывает ввод пользователя и пополняет реферальный фонд.
    """
    try:
        ref_fund = int(message.text)  # Получаем количество активаций
        if ref_fund <= 0:
            await message.answer("❌ Количество активаций должно быть больше 0.", reply_markup=cancel_all_kb())
            return

        data = await state.get_data()
        check_id = data.get('check_id')  # Получаем ID чека из состояния

        # Получаем текущий реферальный фонд
        check = await DB.get_check_by_id(check_id)
        current_ref_fund = check[12]  # ref_fund находится в 12-й колонке

        # Обновляем реферальный фонд
        new_ref_fund = current_ref_fund + ref_fund
        check_summa = check[4]
        total_amount = ref_fund * check_summa  
        balance = await DB.get_user_balance(message.from_user.id)
        await DB.add_balance(message.from_user.id, balance - total_amount)
        await DB.update_check2(check_id, ref_fund=new_ref_fund) 
        user_id = message.from_user.id
        

        # Уведомляем пользователя об успешном пополнении
        await message.answer(
            f"✅ <b>Реферальный фонд успешно пополнен на {ref_fund} активаций.</b>\n\n"
            f"Теперь доступно {new_ref_fund} активаций.",
            reply_markup=back_menu_kb(user_id)
        )

        await DB.add_transaction(
            user_id=message.from_user.id,
            amount=total_amount, 
            description="пополнение реф фонда",
            additional_info= None
        )


        await state.clear()
    except ValueError:
        await message.answer("❌ Пожалуйста, введите корректное число.", reply_markup=cancel_all_kb())