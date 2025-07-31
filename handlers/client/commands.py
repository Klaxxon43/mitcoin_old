from .client import *

@router.message(Command('id'))
async def _(message: types.Message, bot: Bot):
    username = message.text.split()[1]
    logger.info(username)
    id = str(await DB.get_id_from_username(username)).replace("(", "").replace(")", "").replace(",","")
    await message.answer(f'ID Этого пользователя: <code>{id}</code>')


@router.message(Command('chatid'))
async def _(message: types.Message):
    await message.answer(message.chat.id) 

@router.message(Command("basketball"))
async def cmd_basketball_in_group(message: types.Message):
    await message.answer_dice(emoji=DiceEmoji.BASKETBALL)  


@router.message(Command("dice"))
async def cmd_dice_in_group(message: types.Message):
    await message.answer_dice(emoji=DiceEmoji.DICE) 


@router.message(Command('updatestatics'))
async def _(message: types.Message):
    await DB.reset_daily_statistics()
    await message.answer("Статистика обновлена!")


@router.message(Command('msg'))
async def send_message_to_user(message: types.Message, bot: Bot):
    from confIg import ADMINS_ID
    
    if message.from_user.id not in ADMINS_ID:
        await message.reply("⚠️ У вас нет прав для выполнения этой команды.")
        return
    
    if len(message.text.split()) > 2:
        user_id = message.text.split()[1]
        text = ' '.join(message.text.split()[2:])
        msg = (f"""
      🚨 <b>Новое сообщение от администратора!</b> 🚨
📝 <b>Текст сообщения:</b>
<blockquote>{text}</blockquote>"""
        )
        
        try:
            await bot.send_message(user_id, msg)
            await message.answer(f"✅ Сообщение успешно отправлено пользователю с ID {user_id}.")
        except Exception as e:
            logging.error(f"Не удалось отправить сообщение пользователю {user_id}: {e}")
            await message.answer(f"⚠️ Не удалось отправить сообщение пользователю с ID {user_id}.")
    else:
        await message.answer("⚠️ Пожалуйста, укажите ID пользователя и текст сообщения после команды /msg.")




@router.message(Command('dbinfo'))
async def handle_db_command(message: types.Message):
    structure = await DB.get_db_structure_sqlite()

    # Отправляем информацию о таблицах и колонках
    for table, columns in structure.items():
        column_info = []
        for column in columns:
            column_info.append(f"{column[1]} ({column[2]})")  # column[1] - имя колонки, column[2] - тип данных
        await message.answer(f"Таблица: {table}\nКолонки: {', '.join(column_info)}")


@router.message(Command('db'))
async def handle_db_command(message: types.Message):
    user_id = message.from_user.id

    # Проверяем, является ли пользователь администратором
    if user_id not in ADMINS_ID:
        await message.answer("❌ У вас нет прав для выполнения этой команды.")
        return

    # Получаем текст запроса
    if len(message.text.split()) > 1:
        query = ' '.join(message.text.split()[1:])
    logger.info(query)

    if not query:
        await message.answer("❌ Укажите SQL-запрос после команды /db.")
        return
    try: 
        # Выполняем запрос к базе данных
        result = await DB.execute_query(query)

        # Отправляем результат пользователю
        if isinstance(result, str):  # Если произошла ошибка
            await message.answer(result)
        else:
            # Форматируем результат для удобного отображения
            formatted_result = "\n".join([str(row) for row in result])
            await message.answer(f"✅ Результат запроса:\n<code>{formatted_result}</code>")
    except Exception as e:
        await message.answer(f"❌ Ошибка выполнения запроса: {e}")
        

# Обработчик команды /report
@router.message(Command('report'))
async def send_report(message: types.Message, bot: Bot):
    # Проверяем, что текст после команды /report не пустой
    if len(message.text.split()) > 1:
        report_text = ' '.join(message.text.split()[1:])  # Получаем текст после команды /report
        
        # Формируем сообщение для админов
        admin_message = (f"""
      🚨 <b>Новый репорт!</b> 🚨
👤 <b>Пользователь:</b> @{message.from_user.username}
🆔 <b>ID:</b> <code>{message.from_user.id}</code>\n
📝 <b>Текст репорта:</b>
<blockquote>{report_text}</blockquote>"""
        )
        from confIg import ADMINS_ID
        # Отправляем сообщение всем админам
        for admin_id in ADMINS_ID:
            try:
                await bot.send_message(admin_id, admin_message)
            except Exception as e:
                logging.error(f"Не удалось отправить сообщение админу {admin_id}: {e}")
        
        # Отправляем подтверждение пользователю
        await message.reply("✅ Ваш репорт успешно отправлен админам!")
    else:
        await message.reply("⚠️ Пожалуйста, укажите текст репорта после команды /report.")
