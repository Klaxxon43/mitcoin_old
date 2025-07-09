from utils.Imports import *
from handlers.client.client import *
from handlers.client.states import *
from .menu import check_router

@check_router.callback_query(F.data == 'single_check')
async def create_single_check(callback: types.CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    user_balance = await DB.get_user_balance(user_id)

    if user_balance < 1001:
        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(text="Пополнить баланс", callback_data='deposit_menu'))
        builder.add(InlineKeyboardButton(text="🔙 Назад", callback_data='back_menu'))
        await callback.message.edit_text(
            f"❌ У вас недостаточно средств для создания чека.\nПополните баланс для продолжения.\nБаланс: {user_balance:.0f} $MICO",
            reply_markup=builder.as_markup())
        return

    max_check = user_balance - (user_balance // 100)

    add_button = InlineKeyboardButton(text=f"📈 Максимально ({max_check} MitCoin)", callback_data=f'checkamount_{max_check}')
    add_button1 = InlineKeyboardButton(text=f"📉 Минимально (1000 MitCoin)", callback_data=f'checkamount_1000')
    add_button2 = InlineKeyboardButton(text="📊 Другая сумма", callback_data='customcheck_amount')
    add_button3 = InlineKeyboardButton(text="🔙 Назад", callback_data='checks_menu')
    # Создаем клавиатуру и добавляем в нее кнопку
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[add_button], [add_button1], [add_button2], [add_button3]])
    await callback.message.edit_text(
        "💰 <b>Сколько MitCoin вы хотите отправить пользователю?</b>",
        reply_markup=keyboard
    )

@check_router.callback_query(F.data == 'customcheck_amount')
async def custom_check_amount(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "💵 <b>Введите сумму MitCoin, которую получит пользователь за активацию чека (целое число)</b>"
    )
    await state.set_state(checks.single_check_create)

@check_router.message(checks.single_check_create)
async def handle_custom_check_amount(message: types.Message, bot: Bot, state: FSMContext):
    user_id = message.from_user.id
    user_balance = await DB.get_user_balance(user_id)

    bot_username = (await bot.get_me()).username
    try:
        sum = int(message.text)
        if sum + (sum // 100) > user_balance:
            builder = InlineKeyboardBuilder()
            builder.add(InlineKeyboardButton(text="Пополнить баланс", callback_data='deposit_menu'))
            builder.add(InlineKeyboardButton(text="🔙 Назад", callback_data='back_menu'))
            await message.answer(
                "❌ У вас недостаточно средств для создания чека на эту сумму, введите другое число",
                reply_markup=builder.as_markup()
            )
            return

        # Списание с баланса

        await state.clear()
        # Генерация уникального чека
        uid = str(uuid.uuid4())
        await DB.update_balance(user_id, balance=user_balance - (sum + sum//100))
        await DB.create_check(uid=uid, user_id=user_id, type=1, sum=sum, amount=1, ref_bonus=None, ref_fund=None)
        check = await DB.get_check_by_uid(uid)
        check_id = check[0]
        check_link = f"https://t.me/{bot_username}?start=check_{uid}"
        add_button1 = InlineKeyboardButton(text="✈ Отправить", switch_inline_query=check_link)
        add_button2 = InlineKeyboardButton(text="⚙ Настройка", callback_data=f'check_{check_id}')
        add_button3 = InlineKeyboardButton(text="🔙 Назад", callback_data='checks_menu')
        # Создаем клавиатуру и добавляем в нее кнопку
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[add_button1], [add_button2], [add_button3]])
        await message.answer(f'''
💸 <b>Одноразовый чек на сумму {sum} MitCoin</b>

❗ Помните, что отправляя кому-либо эту ссылку Вы передаете свои монеты без гарантий получить что-то в ответ
<i>Вы можете настроить чек с помощью кнопки ниже</i>

<span class="tg-spoiler">{check_link}</span>
        ''', reply_markup=keyboard)

        await DB.add_transaction(
            user_id=user_id,
            amount=sum + sum//100,
            description="создание сингл чека",
            additional_info= None
        )

    except ValueError:
        await message.answer("❌ Пожалуйста, введите корректную сумму.")

@check_router.callback_query(F.data.startswith('checkamount_'))
async def handle_check_amount(callback: types.CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    sum = int(callback.data.split('_')[1])
    bot_username = (await bot.get_me()).username
    # Проверка баланса
    user_balance = await DB.get_user_balance(user_id)

    if sum + (sum//100) > user_balance:
        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(text="Пополнить баланс", callback_data='deposit_menu'))
        builder.add(InlineKeyboardButton(text="🔙 Назад", callback_data='back_menu'))
        await callback.message.edit_text(
            "❌ У вас недостаточно средств для создания чека на эту сумму.",
            reply_markup=builder.as_markup()
        )
        return

    # Списание с баланса

    # Генерация уникального чека
    uid = str(uuid.uuid4())
    await DB.update_balance(user_id, balance=user_balance - (sum + (sum // 100)))
    await DB.create_check(uid=uid, user_id=user_id, type=1, sum=sum, amount=1, ref_bonus=0, ref_fund=0) 

    check = await DB.get_check_by_uid(uid)
    check_id = check[0]
    check_link = f"https://t.me/{bot_username}?start=check_{uid}"
    add_button1 = InlineKeyboardButton(text="✈ Отправить", switch_inline_query=check_link)
    add_button2 = InlineKeyboardButton(text="⚙ Настройка", callback_data=f'check_{check_id}')
    add_button3 = InlineKeyboardButton(text="🔙 Назад", callback_data='checks_menu')
    # Создаем клавиатуру и добавляем в нее кнопку
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[add_button1], [add_button2], [add_button3]])
    await callback.message.edit_text(f'''
💸 <b>Одноразовый чек на сумму {sum} MitCoin</b>

<i>Вы можете настроить чек с помощью кнопки ниже</i>
❗ Помните, что отправляя кому-либо эту ссылку Вы передаете свои монеты без каких-либо гарантий получить что-то в ответ

<span class="tg-spoiler">{check_link}</span>
    ''', reply_markup=keyboard)
    await DB.add_transaction(
        user_id=user_id,
        amount=sum+ (sum//100), 
        description="создание сингл чека",
        additional_info= None
    )