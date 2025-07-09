from utils.Imports import *
from handlers.client.client import profile_handler  # Импортируем обработчик профиля

pr = Router()

class PromoStates(StatesGroup):
    waiting_for_promo = State()  # Состояние ожидания ввода промокода

@pr.callback_query(F.data == "activatePromo")
async def ask_promo_name(callback: types.CallbackQuery, state: FSMContext):
    """Запрос названия промокода"""
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_promo"))
    
    await callback.message.edit_text(
        "🔹 Введите название промокода для активации:",
        reply_markup=builder.as_markup()
    )
    await state.set_state(PromoStates.waiting_for_promo)
    await callback.answer()


@pr.callback_query(F.data == "cancel_promo")
async def cancel_promo(callback: types.CallbackQuery, state: FSMContext):
    """Отмена активации промокода с переходом в профиль"""
    await state.clear()  # Очищаем состояние
    await callback.answer()  # Подтверждаем обработку callback
    
    # Вызываем обработчик профиля напрямую
    await profile_handler(callback, bot=callback.bot)

@pr.message(PromoStates.waiting_for_promo)
async def process_promo_activation(message: types.Message, state: FSMContext, bot: Bot):
    """Обработка введенного промокода"""
    promo_name = message.text.strip()
    
    # Проверяем есть ли такой промокод
    promo = await Promo.get(promo_name)
    if not promo:
        await message.answer("❌ Промокод не найден или недействителен")
        await state.clear()
        return
    
    # Проверяем срок действия
    try:
        end_time = datetime.strptime(promo[8], "%Y-%m-%d %H:%M:%S.%f")
    except ValueError:
        try:
            end_time = datetime.strptime(promo[8], "%Y-%m-%d %H:%M:%S")
        except ValueError as e:
            print(f"Ошибка при разборе даты промокода {promo_name}: {e}")
            await Promo.delete(promo_name)
            await message.answer("❌ Промокод поврежден и был удален")
            await state.clear()
            return
    
    if end_time < datetime.now():
        await Promo.delete(promo_name)
        await message.answer("❌ Срок действия промокода истек")
        await state.clear()
        return
    
    # Проверяем был ли уже активирован этим пользователем
    user_id = message.from_user.id
    async with DB.con.cursor() as cur:
        await cur.execute('''
            SELECT 1 FROM activated_promocodes 
            WHERE user_id = ? AND promocode_id = ?
        ''', (user_id, promo[0]))
        if await cur.fetchone():
            await message.answer("❌ Вы уже активировали этот промокод!")
            await state.clear()
            return
    
    # Определяем тип начисления
    bonus_type = ""
    try:
        if promo[4] == "def_bal":
            await DB.add_balance(user_id, promo[3])
            bonus_type = "баланс $MICO"
        elif promo[4] == "def_bal_rub":
            await DB.add_rub_balance(user_id, promo[3])
            bonus_type = "рублевый баланс"
        elif promo[4] == "stars":  # Новый тип начисления
            await DB.add_star(user_id, int(promo[3]))
            bonus_type = "баланс звёзд"
        else:
            await message.answer("❌ Неизвестный тип начисления промокода")
            await state.clear()
            return
        
        # Записываем активацию
        async with DB.con.cursor() as cur:
            await cur.execute('''
                INSERT INTO activated_promocodes 
                (user_id, promocode_id, activation_time)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            ''', (user_id, promo[0]))
            await DB.con.commit()
        
        # Уменьшаем количество активаций
        is_finished = await Promo.decrease_count(promo_name)
        
        if is_finished:
            try:
                await bot.send_message(
                    promo[1],
                    f"⚠ Промокод {promo_name} закончился!\n"
                    f"Все {promo[6]} активаций были использованы."
                )
            except Exception as e:
                print(f"Ошибка при уведомлении создателя промокода: {e}")
        
        await message.answer(
            f"✅ Промокод активирован!\n"
            f"💎 Вам начислено {promo[3]:.0f} на {bonus_type}!"
        )
    except Exception as e:
        print(f"Ошибка при активации промокода: {e}")
        await message.answer("❌ Произошла ошибка при активации промокода")
    finally:
        await state.clear()