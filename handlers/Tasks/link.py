from .tasks import *
from utils.Imports import *
import asyncio
from typing import Optional, List, Dict, Any

# Constants
LINK_TASK_PRICE = 1500  # Price for one link task
VERIFICATION_TYPES = {
    'auto': 0,
    'manual': 1
}

# States for link task creation
class LinkPromotionStates(StatesGroup):
    link_task_create = State()  # Entering task count
    link_task_create2 = State()  # Entering link
    link_task_create3 = State()  # Selecting verification type
    link_task_create4 = State()  # Entering manual verification description
    performing_task = State()  # Performing the task

# --- Task Creation Handlers ---

@tasks.callback_query(F.data == 'link_task_button')
async def link_task_handler(callback: types.CallbackQuery, state: FSMContext):
    """Initial handler for link task creation"""
    await callback.answer()
    user_id = callback.from_user.id
    
    try:
        user = await DB.select_user(user_id)
        balance = user.get('balance', 0)
        maxcount = balance // LINK_TASK_PRICE
        
        await callback.message.edit_text(
            f'''🔗 Переход по ссылке\n\n'''
            f'💵 {LINK_TASK_PRICE} MITcoin = 1 задание\n\n'
            f'Баланс: <b>{balance}</b>; Всего вы можете купить <b>{maxcount}</b> заданий\n\n'
            f'<b>Сколько нужно заданий?</b>❓\n\n'
            f'<em>Чтобы создать задание на вашем балансе должно быть не менее {LINK_TASK_PRICE} MITcoin</em>',
            reply_markup=pr_menu_canc()
        )
        await state.set_state(LinkPromotionStates.link_task_create)
    except Exception as e:
        logger.info(f"Error in link_task_handler: {e}")
        await callback.message.answer("❌ Произошла ошибка. Попробуйте позже.")

@tasks.message(LinkPromotionStates.link_task_create)
async def link_task_count_handler(message: types.Message, state: FSMContext):
    """Handler for processing task count input"""
    user_id = message.from_user.id
    
    try:
        user = await DB.select_user(user_id)
        balance = user.get('balance', 0)
        
        try:
            task_count = int(message.text.strip())
            if task_count < 1:
                raise ValueError("Count must be positive")
                
            total_price = LINK_TASK_PRICE * task_count
            
            if balance >= total_price:
                builder = InlineKeyboardBuilder()
                builder.add(InlineKeyboardButton(
                    text="✅ Продолжить", 
                    callback_data="link_task_confirm"))
                builder.add(InlineKeyboardButton(
                    text="🔙 Назад", 
                    callback_data="pr_menu_cancel"))
                
                await message.answer(
                    f'👍 <b>Количество: {task_count}</b>\n'
                    f'💰 <b>Стоимость: {total_price} MITcoin</b>\n\n'
                    f'<em>Нажмите кнопку <b>Продолжить</b> или введите другое число...</em>',
                    reply_markup=builder.as_markup()
                )
                await state.update_data(uscount=task_count, price=total_price)
            else:
                builder = InlineKeyboardBuilder()
                builder.add(InlineKeyboardButton(
                    text="Пополнить баланс", 
                    callback_data="cancel_all"))
                builder.add(InlineKeyboardButton(
                    text="🔙 Назад", 
                    callback_data="pr_menu_cancel"))
                
                await message.answer(
                    f'😢 <b>Недостаточно средств на балансе</b>\n'
                    f'Ваш баланс: {balance} MITcoin\n'
                    f'<em>Пополните баланс или измените желаемое количество заданий...</em>',
                    reply_markup=builder.as_markup()
                )
        except ValueError:
            await message.answer(
                '<b>❗Минимальная покупка от 1 задания!</b>\nВведи корректное число...',
                reply_markup=pr_menu_canc()
            )
    except Exception as e:
        logger.info(f"Error in link_task_count_handler: {e}")
        await message.answer("❌ Произошла ошибка. Попробуйте позже.")

@tasks.callback_query(F.data == 'link_task_confirm')
async def link_task_confirm_handler(callback: types.CallbackQuery, state: FSMContext):
    """Handler for confirming task count and proceeding to link input"""
    await callback.message.edit_text(
        '🔗 Теперь введите ссылку на бота, по которой нужно перейти. Я жду...',
        reply_markup=pr_menu_canc()
    )
    await state.set_state(LinkPromotionStates.link_task_create2)

@tasks.message(LinkPromotionStates.link_task_create2)
async def link_task_link_handler(message: types.Message, state: FSMContext):
    """Handler for processing the link input"""
    link = message.text.strip()
    
    if not link.startswith("https://t.me/"):
        await message.answer("❌ Некорректная ссылка. Убедитесь, что ссылка начинается с https://t.me/.")
        return
    
    try:
        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(
            text="Автоматическая проверка 🤖", 
            callback_data="auto_check"))
        builder.add(InlineKeyboardButton(
            text="Ручная проверка 👨‍💻", 
            callback_data="manual_check"))
        
        await message.answer(
            "🔍 <b>Выберите тип проверки задания:</b>\n\n"
            "🤖 <b>Автоматическая проверка:</b> Пользователь пересылает сообщение от бота.\n"
            "👨‍💻 <b>Ручная проверка:</b> Пользователь отправляет скриншот, который проверяется администратором.",
            reply_markup=builder.as_markup()
        )
        
        data = await state.get_data()
        await state.update_data(
            link=link,
            amount=data['uscount'],
            price=data['price']
        )
        await state.set_state(LinkPromotionStates.link_task_create3)
    except Exception as e:
        logger.info(f"Error in link_task_link_handler: {e}")
        await message.answer("❌ Произошла ошибка при создании задания. Попробуйте позже.")

@tasks.callback_query(F.data == 'auto_check')
async def auto_check_handler(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    """Handler for auto verification type selection"""
    user_id = callback.from_user.id
    data = await state.get_data()
    
    try:
        link = data['link']
        amount = data['amount']
        price = data['price']
        
        # Deduct balance
        new_balance = await DB.update_balance(user_id, -price)
        
        # Create task with auto verification (other=0)
        await DB.add_task(
            user_id=user_id,
            target_id=link,
            amount=amount,
            task_type=5,  # Link task type
            other=VERIFICATION_TYPES['auto']  # 0 for auto verification
        )
        
        # Add transaction record
        await DB.add_transaction(
            user_id=user_id,
            amount=-price,
            description="Создание задания на переход по ссылке (авто)",
            additional_info=None
        )
        
        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(
            text="🔙 Вернуться в меню", 
            callback_data="back_menu"))
        
        await callback.message.answer(
            "🥳 Задание на переход по ссылке создано! Оно будет размещено в разделе <b>Заработать</b>\n\n"
            "Когда задание будет выполнено - Вы получите уведомление 😉",
            reply_markup=builder.as_markup()
        )
        
        # Notify admin channel
        await bot.send_message(
            TASKS_CHAT_ID,
            f'''🔔 СОЗДАНО НОВОЕ ЗАДАНИЕ 🔔
⭕️ Тип задания: 🔗 Переход по ссылке, автоматическая проверка
💸 Цена: {LINK_TASK_PRICE} 
👥 Количество выполнений: {amount}
💰 Стоимость: {price}'''
        )
        
        await state.clear()
        await RedisTasksManager.refresh_task_cache(bot, 'link')
    except Exception as e:
        logger.info(f"Error in auto_check_handler: {e}")
        await callback.message.answer("❌ Произошла ошибка при создании задания. Попробуйте позже.")

@tasks.callback_query(F.data == 'manual_check')
async def manual_check_handler(callback: types.CallbackQuery, state: FSMContext):
    """Handler for manual verification type selection"""
    await callback.message.answer(
        "📝 <b>Опишите, что должен сделать пользователь, перейдя по ссылке:</b>\n\n"
        "<em>Например: 'Напишите боту команду /start и отправьте скриншот ответа.'</em>",
        reply_markup=pr_menu_canc()
    )
    await state.set_state(LinkPromotionStates.link_task_create4)

@tasks.message(LinkPromotionStates.link_task_create4)
async def manual_description_handler(message: types.Message, state: FSMContext, bot: Bot):
    """Handler for processing manual verification description"""
    user_id = message.from_user.id
    description = message.text.strip()
    data = await state.get_data()
    
    try:
        link = data['link']
        amount = data['amount']
        price = data['price']
        
        # Deduct balance
        new_balance = await DB.update_balance(user_id, -price)
        
        # Create task with manual verification (other="1|description")
        await DB.add_task(
            user_id=user_id,
            target_id=link,
            amount=amount,
            task_type=5,  # Link task type
            other=f"{VERIFICATION_TYPES['manual']}|{description}"  # 1 for manual verification
        )
        
        # Add transaction record
        await DB.add_transaction(
            user_id=user_id,
            amount=-price,
            description="Создание задания на переход по ссылке (ручная)",
            additional_info=None
        )
        
        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(
            text="🔙 Вернуться в меню", 
            callback_data="back_menu"))
        
        await message.answer(
            "🥳 Задание на переход по ссылке создано! Оно будет размещено в разделе <b>Заработать</b>\n\n"
            "Когда задание будет выполнено - Вы получите уведомление 😉",
            reply_markup=builder.as_markup()
        )
        
        # Notify admin channel
        await bot.send_message(
            TASKS_CHAT_ID,
            f'''🔔 СОЗДАНО НОВОЕ ЗАДАНИЕ 🔔
⭕️ Тип задания: 🔗 Переход по ссылке, ручная проверка
❗️ Условие выполнения: {description}
💸 Цена: {LINK_TASK_PRICE} 
👥 Количество выполнений: {amount}
💰 Стоимость: {price}'''
        )
        
        await state.clear()
        await RedisTasksManager.refresh_task_cache(bot, 'link')
    except Exception as e:
        logger.info(f"Error in manual_description_handler: {e}")
        await message.answer("❌ Произошла ошибка при создании задания. Попробуйте позже.")

# --- Task Execution Handlers ---

@tasks.callback_query(F.data == 'work_link')
async def works_link_handler(callback: types.CallbackQuery, bot: Bot):
    """Handler for showing available link tasks"""
    user_id = callback.from_user.id
    
    try:
        # Get cached tasks
        all_tasks = await RedisTasksManager.get_cached_tasks('link') or []
        
        # Filter tasks by verification type and completion status
        auto_tasks = []
        manual_tasks = []
        
        for task in all_tasks:
            try:
                # Skip if completed or failed
                if (await DB.is_task_completed(user_id, task['id']) or 
                    await DB.is_task_failed(user_id, task['id'])):
                    continue
                
                # Check verification type from 'other' field
                if str(task.get('other', '')).startswith(f"{VERIFICATION_TYPES['manual']}|"):
                    manual_tasks.append(task)
                else:
                    auto_tasks.append(task)
            except Exception as e:
                logger.info(f"Error processing task {task.get('id')}: {e}")
                continue
        
        # Prepare response
        status_text = (
            "🔍 <b>Доступные задания на переход по ссылке:</b>\n\n"
            f"🤖 <b>Автоматическая проверка:</b> {len(auto_tasks)} заданий\n"
            f"👨‍💻 <b>Ручная проверка:</b> {len(manual_tasks)} заданий\n\n"
            "<i>Выберите тип проверки:</i>"
        )
        
        # Create keyboard
        builder = InlineKeyboardBuilder()
        
        # Add buttons with counts
        builder.add(InlineKeyboardButton(
                text=f"Авто 🤖 ({len(auto_tasks)})", 
                callback_data="work_link_auto"))
        
        builder.add(InlineKeyboardButton(
                text=f"Ручная 👨‍💻 ({len(manual_tasks)})", 
                callback_data="work_link_manual"))

        
        builder.add(InlineKeyboardButton(
            text="🔙 Назад", 
            callback_data="work_menu"))
        
        builder.adjust(1)
        
        await callback.message.edit_text(
            status_text,
            reply_markup=builder.as_markup()
        )
    except Exception as e:
        logger.info(f"Error in works_link_handler: {e}")
        await callback.message.edit_text(
            "⚠️ Не удалось загрузить информацию о заданиях",
            reply_markup=back_work_menu_kb(user_id)
        )

@tasks.callback_query(F.data == 'work_link_auto')
async def work_link_auto_handler(callback: types.CallbackQuery, bot: Bot, state: FSMContext):
    """Handler for auto verification link tasks"""
    user_id = callback.from_user.id
    
    try:
        # Get cached tasks
        all_tasks = await RedisTasksManager.get_cached_tasks('link') or []
        
        # Filter auto verification tasks
        available_tasks = []
        for task in all_tasks:
            try:
                # Skip if completed or failed
                if not await DB.is_task_available_for_user(user_id, task['id']):
                    continue
                
                # Check for auto verification (other doesn't start with "1|")
                logger.info(task)
                logger.info(VERIFICATION_TYPES['manual'])
                logger.info(str(task.get('other', '')).startswith(f"{VERIFICATION_TYPES['manual']}|"))
                if not str(task.get('other', '')).startswith(f"{VERIFICATION_TYPES['manual']}|"):
                    available_tasks.append(task)
            except Exception as e:
                logger.info(f"Error processing task {task.get('id')}: {e}")
                continue
        
        if not available_tasks:
            await callback.message.edit_text(
                "⏳ Нет доступных заданий с автоматической проверкой",
                reply_markup=back_work_menu_kb(user_id))
            return
        
        # Select random task
        task = random.choice(available_tasks)
        
        # Save task data in state
        await state.set_state(LinkPromotionStates.performing_task)
        await state.update_data(
            task_id=task['id'],
            target_link=task['target_id'],
            task_type=VERIFICATION_TYPES['auto']  # 0 for auto verification
        )

        await callback.message.edit_text(
            f"🔗 <b>Задание:</b> Перейдите по ссылке:\n{task['target_id']}\n\n"
            "➡️ Перешлите любое сообщение от этого бота для подтверждения",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⏭ Пропустить", callback_data=f"skip_link_{task['id']}")],
                [InlineKeyboardButton(text="⚠️ Репорт", callback_data=f"report_link_{task['id']}")],
                [InlineKeyboardButton(text="🔙 Назад", callback_data=f"work_link")]
            ]),
            disable_web_page_preview=True
        )
    except Exception as e:
        logger.info(f"Error in work_link_auto_handler: {e}")
        await callback.message.edit_text(
            "⚠️ Произошла ошибка. Попробуйте позже.",
            reply_markup=back_work_menu_kb(user_id)
        )

@tasks.callback_query(F.data == 'work_link_manual')
async def work_link_manual_handler(callback: types.CallbackQuery, bot: Bot, state: FSMContext):
    """Handler for manual verification link tasks"""
    user_id = callback.from_user.id
    
    try:
        # Get cached tasks
        all_tasks = await RedisTasksManager.get_cached_tasks('link') or []
        
        # Filter manual verification tasks
        available_tasks = []
        for task in all_tasks:
            try:
                # Skip if completed or failed
                if not await DB.is_task_available_for_user(user_id, task['id']):
                    continue
                
                # Check for manual verification (other starts with "1|")
                if str(task.get('other', '')).startswith(f"{VERIFICATION_TYPES['manual']}|"):
                    available_tasks.append(task)
            except Exception as e:
                logger.info(f"Error processing task {task.get('id')}: {e}")
                continue
        
        if not available_tasks:
            await callback.message.edit_text(
                "⏳ Нет доступных заданий с ручной проверкой",
                reply_markup=back_work_menu_kb(user_id))
            return
        
        # Select random task
        task = random.choice(available_tasks)
        
        # Extract description from other field
        description = str(task.get('other', '')).split('|', 1)[1] if '|' in str(task.get('other', '')) else "Сделайте скриншот выполнения задания"
        
        # Save task data in state
        await state.set_state(LinkPromotionStates.performing_task)
        await state.update_data(
            task_id=task['id'],
            target_link=task['target_id'],
            task_type=VERIFICATION_TYPES['manual'],  # 1 for manual verification
            description=description
        )

        await callback.message.edit_text(
            f"🔗 <b>Ссылка:</b> {task['target_id']}\n\n"
            f"📝 <b>Задание:</b> {description}\n\n"
            f"📷 <b>Отправьте скриншот выполнения</b>",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📷 Отправить скриншот", callback_data=f"send_link_screenshot_{task['id']}")],
                [InlineKeyboardButton(text="⏭ Пропустить", callback_data=f"skip_link_{task['id']}")],
                [InlineKeyboardButton(text="⚠️ Репорт", callback_data=f"report_link_{task['id']}")],
                [InlineKeyboardButton(text="🔙 Назад", callback_data=f"work_link")]
            ]),
            disable_web_page_preview=True
        )
    except Exception as e:
        logger.info(f"Error in work_link_manual_handler: {e}")
        await callback.message.edit_text(
            "⚠️ Произошла ошибка. Попробуйте позже.",
            reply_markup=back_work_menu_kb(user_id)
        )

@tasks.message(F.forward_from, LinkPromotionStates.performing_task)
async def check_forwarded_message(message: types.Message, bot: Bot, state: FSMContext):
    """Handler for checking forwarded message (auto verification)"""
    user_id = message.from_user.id
    forwarded_from = message.forward_from
    
    if not forwarded_from:
        await message.answer("❌ Это сообщение не является пересланным от бота.")
        return
    
    data = await state.get_data()
    task_id = data.get("task_id")
    target_link = data.get("target_link")
    task_type = data.get("task_type")
    
    if not task_id or not target_link or task_type != VERIFICATION_TYPES['auto']:
        await message.answer("❌ Данные задания не найдены или тип задания не соответствует. Попробуйте начать заново.")
        await state.clear()
        return
    
    try:
        # Extract bot username from link
        bot_username = target_link.split("/")[-1].split("?")[0]
        
        if forwarded_from.username == bot_username:
            # Task completed successfully
            await DB.add_completed_task(
                user_id=user_id,
                task_id=task_id,
                target_id=target_link,
                task_sum=LINK_TASK_PRICE,
                owner_id=user_id,
                status=0
            )
            
            # Update user balance
            await DB.add_balance(user_id, LINK_TASK_PRICE)
            
            # Update statistics
            await update_dayly_and_weekly_tasks_statics(user_id)
            await DB.increment_statistics(1, 'links')
            await DB.increment_statistics(2, 'links')
            await DB.increment_statistics(1, 'all_taasks')
            await DB.increment_statistics(2, 'all_taasks')
            
            await message.answer(
                f"✅ Задание выполнено! Ваш баланс пополнен на {LINK_TASK_PRICE} MITcoin.\n\n"
                f"🔗 Ссылка: {target_link}\n"
                f"📝 Описание: Переход по ссылке",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="Дальше ⏭️", callback_data="work_link_auto")]]
                ))
            
            # Decrease task amount
            task = await DB.get_task_by_id(task_id)
            if task and task[3] > 0:
                await DB.update_task_amount2(task_id, task[3] - 1)
            
            await state.clear()
        else:
            await message.answer("❌ Пересланное сообщение не соответствует заданию.")
    except Exception as e:
        logger.info(f"Error in check_forwarded_message: {e}")
        await message.answer("❌ Произошла ошибка при обработке задания. Попробуйте позже.")

@tasks.message(F.photo, LinkPromotionStates.performing_task)
async def handle_screenshot(message: types.Message, state: FSMContext, bot: Bot):
    """Handler for processing screenshot (manual verification)"""
    user_id = message.from_user.id
    data = await state.get_data()
    task_id = data.get('task_id')
    target_link = data.get('target_link')
    task_type = data.get('task_type')
    description = data.get('description', '')
    
    if task_type != VERIFICATION_TYPES['manual']:
        await message.answer("❌ Это задание требует автоматической проверки.")
        return
    
    if not message.photo:
        await message.answer("❌ Пожалуйста, отправьте скриншот.")
        return
    
    try:
        screenshot_id = message.photo[-1].file_id
        
        # Add to pending tasks
        await DB.add_pending_reaction_task(
            user_id=user_id,
            task_id=task_id,
            target_id=target_link,
            post_id=0,
            reaction=0,
            screenshot=screenshot_id
        )
        
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='⏭ Далее', callback_data='work_link_manual')],
            [InlineKeyboardButton(text='🔙 Назад', callback_data='work_menu')]
        ])
        
        await message.answer(
            "✅ Скриншот отправлен на проверку. Ожидайте подтверждения.",
            reply_markup=kb
        )
        
        # Send to admin for verification
        builder = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="✅ Подтвердить", 
                callback_data=f"confirm_link_{task_id}_{user_id}")],
            [InlineKeyboardButton(
                text="❌ Отклонить", 
                callback_data=f"reject_link_{task_id}_{user_id}")]
        ])

        await bot.send_photo(
            CHECK_CHAT_ID,
            photo=screenshot_id,
            caption=(
                f"#ссылка\n"
                f"📝 <b>Задание на переход по ссылке</b>\n\n"
                f"👤 Пользователь: @{message.from_user.username} (ID: {user_id})\n"
                f"🔗 Ссылка: {target_link}\n"
                f"📝 Условие: {description}\n"
                f"💸 Награда: {LINK_TASK_PRICE} MITcoin\n"
                f"🆔 ID задания: {task_id}\n\n"
                f"Проверьте выполнение задания:"
            ),
            reply_markup=builder
        )
        
        await state.clear()
    except Exception as e:
        logger.info(f"Error in handle_screenshot: {e}")
        await message.answer("❌ Произошла ошибка при обработке скриншота. Попробуйте позже.")

@tasks.callback_query(F.data.startswith('confirm_link_'))
async def confirm_link_handler(callback: types.CallbackQuery, bot: Bot):
    """Handler for admin confirming a link task"""
    try:
        parts = callback.data.split('_')
        task_id = int(parts[2])
        user_id = int(parts[3])
        
        # Get pending task
        pending_task = await DB.get_pending_reaction_task(task_id, user_id)
        if not pending_task:
            await callback.answer("Задание не найдено.")
            return
        
        # Mark as completed
        await DB.add_completed_task(
            user_id=user_id,
            task_id=task_id,
            target_id=pending_task[3],  # target_id
            task_sum=LINK_TASK_PRICE,
            owner_id=user_id,
            status=0
        )
        
        # Delete pending task
        await DB.delete_pending_reaction_task(task_id, user_id)
        
        # Update user balance
        await DB.add_balance(user_id, LINK_TASK_PRICE)
        
        # Decrease task amount
        task = await DB.get_task_by_id(task_id)
        if task and task[3] > 0:
            await DB.update_task_amount2(task_id, task[3] - 1)
        
        # Notify user
        await bot.send_message(
            user_id,
            f"🎉 <b>Ваше задание на переход по ссылке подтверждено!</b>\n\n"
            f"💸 Вам начислено: {LINK_TASK_PRICE} MITcoin\n"
            f"🔗 Ссылка: {pending_task[3]}\n"
            f"🆔 ID задания: {task_id}"
        )
        
        # Update statistics
        await update_dayly_and_weekly_tasks_statics(user_id)
        await DB.increment_statistics(1, 'links')
        await DB.increment_statistics(2, 'links')
        await DB.increment_statistics(1, 'all_taasks')
        await DB.increment_statistics(2, 'all_taasks')
        
        await callback.answer("✅ Задание подтверждено.")
    except Exception as e:
        logger.info(f"Error in confirm_link_handler: {e}")
        await callback.answer("❌ Произошла ошибка при подтверждении задания.")

@tasks.callback_query(F.data.startswith('reject_link_'))
async def reject_link_handler(callback: types.CallbackQuery, bot: Bot):
    """Handler for admin rejecting a link task"""
    try:
        parts = callback.data.split('_')
        task_id = int(parts[2])
        user_id = int(parts[3])
        
        # Get pending task
        pending_task = await DB.get_pending_reaction_task(task_id, user_id)
        if not pending_task:
            await callback.answer("Задание не найдено.")
            return
        
        # Mark as failed
        await DB.add_failed_task(user_id, task_id)
        
        # Delete pending task
        await DB.delete_pending_reaction_task(task_id, user_id)
        
        # Notify user
        await bot.send_message(
            user_id,
            f"❌ <b>Ваше задание на переход по ссылке отклонено.</b>\n\n"
            f"🔗 Ссылка: {pending_task[3]}\n"
            f"🆔 ID задания: {task_id}\n\n"
            f"Пожалуйста, убедитесь, что вы выполнили задание правильно."
        )
        
        # Notify admin
        await bot.send_message(
            CHECK_CHAT_ID,
            f"❌ <b>Задание на переход по ссылке отклонено.</b>\n\n"
            f"👤 Пользователь: @{callback.from_user.username} (ID: {user_id})\n"
            f"🔗 Ссылка: {pending_task[3]}\n"
            f"🆔 ID задания: {task_id}"
        )
        
        await callback.answer("❌ Задание отклонено.")
    except Exception as e:
        logger.info(f"Error in reject_link_handler: {e}")
        await callback.answer("❌ Произошла ошибка при отклонении задания.")