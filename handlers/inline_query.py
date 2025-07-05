from untils.Imports import *

iq = Router()

async def generate_check_image(amount: int):
    """Генерирует изображение чека с указанной суммой"""
    try:
        # Проверяем существование базового изображения
        if not os.path.exists("check.png"):
            return None
        
        # Открываем изображение
        image = Image.open("check.png")
        draw = ImageDraw.Draw(image)
        
        # Загружаем шрифт (если файл существует)
        font_path = "ocra_0.ttf"
        try:
            font_size = 48  # Размер шрифта
            font = ImageFont.truetype(font_path, font_size)
        except:
            # Если шрифт не найден, используем стандартный
            font = ImageFont.load_default()
        
        # Текст для отображения
        text = f"{amount} $MICO"
        
        # Рассчитываем положение текста (центр изображения)
        # Используем textbbox вместо устаревшего textsize
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        x = (image.width - text_width) // 2
        y = (image.height - text_height) // 2
        
        # Координаты можно настроить, добавляя/убавляя от центра
        x += 0  # Смещение по горизонтали
        y += 0  # Смещение по вертикали
        
        # Рисуем текст на изображении
        draw.text((x, y), text, font=font, fill="black")
        
        # Сохраняем временное изображение
        temp_path = f"temp_check_{amount}.png"
        image.save(temp_path)
        
        return temp_path
    except Exception as e:
        logger.error(f"Ошибка при генерации изображения чека: {e}")
        return None

@iq.inline_query()
async def inline_query_handler(inline_query: types.InlineQuery, bot: Bot):
    query = inline_query.query  # Текст после @username

    try:
        # Разбиваем запрос на части
        parts = query.split()
        if not parts:
            raise ValueError("Введите сумму чека. Формат: [сумма] [количество].")

        # Получаем сумму чека
        amount = int(parts[0])
        if amount < 1000:
            raise ValueError("Минимальная сумма чека - 1000 MitCoin.")

        # Получаем количество активаций (по умолчанию 1)
        quantity = int(parts[1]) if len(parts) > 1 else 1

        # Проверка баланса
        user_id = inline_query.from_user.id
        user_balance = await DB.get_user_balance(user_id)

        # Рассчитываем сумму для каждого активировавшего
        amount_per_activation = amount // quantity
        total_amount = amount_per_activation * quantity

        if user_balance < total_amount:
            result_text = f"❌ Недостаточно средств для создания чека. Необходимо: {total_amount} MitCoin."
            description = f"Недостаточно средств. Ваш баланс: {user_balance} MitCoin."
        else:
            # Создание чека
            uid = str(uuid.uuid4())
            await DB.update_balance(user_id, balance=user_balance - total_amount)
            
            check_type = 1 if quantity == 1 else 2  # 1 - сингл, 2 - мульти
            
            await DB.create_check(
                uid=uid,
                user_id=user_id,
                type=check_type,
                sum=amount_per_activation,
                amount=quantity,
                ref_bonus=None,
                ref_fund=None,
                locked_for_user=None
            )

            # Текст результата
            if quantity == 1:
                result_text = f"💸 Чек на сумму {amount_per_activation} $MICO"
                description = f"Одноразовый чек на {amount_per_activation} $MICO"
            else:
                result_text = f"💸 Мульти-чек: {quantity} активаций по {amount_per_activation} $MICO"
                description = f"Мульти-чек: {quantity} активаций по {amount_per_activation} $MICO"
            
            await DB.add_transaction(
                user_id=inline_query.from_user.id,
                amount=total_amount, 
                description=f"создание {'сингл' if quantity == 1 else 'мульти'} чека через inline",
                additional_info=None
            )

            # Генерируем изображение чека
            image_path = await generate_check_image(amount_per_activation)
            
            # Создаем Inline-результат с кнопкой
            bot_username = (await bot.get_me()).username
            check_link = f"https://t.me/{bot_username}?start=check_{uid}"
            
            # Если изображение сгенерировано, используем его, иначе без изображения
            if image_path:
                # Загружаем изображение
                with open(image_path, "rb") as image_file:
                    image_data = image_file.read()
                
                # Создаем временный URL для изображения
                # В реальном проекте нужно загрузить изображение на сервер и получить публичный URL
                # Здесь для примера используем фиктивный URL
                thumbnail_url = "https://example.com/check.png"  # Замените на реальный URL
                
                # Создаем результат с изображением
                inline_result = InlineQueryResultArticle(
                    id="1",
                    title="Создать чек",
                    input_message_content=InputTextMessageContent(
                        message_text=result_text,
                        parse_mode="HTML"
                    ),
                    description=description,
                    thumbnail_url=thumbnail_url,  # Используем URL вместо вложения
                    reply_markup=InlineKeyboardMarkup(
                        inline_keyboard=[
                            [
                                InlineKeyboardButton(
                                    text=f"Получить {amount_per_activation} $MICO",
                                    url=check_link
                                )
                            ]
                        ]
                    ),
                    thumbnail_width=100,
                    thumbnail_height=100
                )
                
                # Отправляем результат
                await bot.answer_inline_query(
                    inline_query.id,
                    results=[inline_result],
                    cache_time=1
                )
                
                # Удаляем временный файл
                os.remove(image_path)
            else:
                # Без изображения
                inline_result = InlineQueryResultArticle(
                    id="1",
                    title="Создать чек",
                    input_message_content=InputTextMessageContent(
                        message_text=result_text,
                        parse_mode="HTML"
                    ),
                    description=description,
                    reply_markup=InlineKeyboardMarkup(
                        inline_keyboard=[
                            [
                                InlineKeyboardButton(
                                    text=f"Получить {amount_per_activation} $MICO",
                                    url=check_link
                                )
                            ]
                        ]
                    )
                )
                await bot.answer_inline_query(inline_query.id, results=[inline_result], cache_time=1)

    except ValueError as e:
        # Обработка ошибок (некорректная сумма или ID)
        error_text = f"❌ Ошибка: {str(e)}"
        inline_result = InlineQueryResultArticle(
            id="1",
            title="Ошибка",
            input_message_content=InputTextMessageContent(message_text=error_text),
            description="Проверьте введенные данные"
        )
        await bot.answer_inline_query(inline_query.id, results=[inline_result], cache_time=1)