from untils.Imports import *

xpay = Router()

@xpay.message(Command('rub'))
async def handle_rub_command(message: types.Message):
    try:
        # Конфигурационные параметры
        SHOP_ID = "458"
        SHOP_TOKEN = "x-bb3735531298eb51ba8f2308f7a4eec6"
        API_URL = f"https://xpay.bot-wizard.org:5000/{SHOP_ID}/{SHOP_TOKEN}/createInvoice"
        TIMEOUT = 15  # секунд

        # Подготовка данных запроса
        payload = {
            "amount": 100.00,
            "description": f"Пополнение баланса пользователя {message.from_user.id}",
            "payload": str(message.from_user.id)
        }

        # Отключаем SSL-предупреждения для чистоты логов
        requests.packages.urllib3.disable_warnings()

        try:
            # Выполняем запрос с обработкой возможных ошибок
            response = requests.post(
                API_URL,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=TIMEOUT,
                verify=False
            )
            
            # Анализ ответа сервера
            if response.status_code == 404:
                error_msg = (
                    "🔴 Платежный шлюз временно недоступен.\n"
                    "Попробуйте позже или используйте другой способ оплаты."
                )
                await message.answer(error_msg)
                logging.error(f"Endpoint not found: {API_URL}")
                return

            if 'html' in response.headers.get('Content-Type', '').lower():
                error_msg = (
                    "⚠️ Технические работы в платежной системе.\n"
                    "Попробуйте выполнить операцию через 10-15 минут."
                )
                await message.answer(error_msg)
                logging.error(f"HTML response received: {response.text[:500]}")
                return

            try:
                data = response.json()
            except ValueError:
                error_msg = (
                    "🔄 Платежная система вернула некорректный ответ.\n"
                    "Мы уже работаем над решением проблемы."
                )
                await message.answer(error_msg)
                logging.error(f"Invalid JSON response: {response.text[:500]}")
                return

            if response.status_code == 200:
                if not (payment_url := data.get('url')):
                    await message.answer("❌ Не удалось получить платежную ссылку")
                    return

                # Формируем клавиатуру с кнопкой оплаты
                kb = InlineKeyboardBuilder()
                kb.button(text="💳 Оплатить 100 RUB", url=payment_url)
                kb.button(text="❌ Отмена", callback_data="cancel_payment")

                await message.answer(
                    "💸 Для пополнения баланса:\n\n"
                    "1. Нажмите кнопку 'Оплатить'\n"
                    "2. Следуйте инструкциям в боте XPay\n"
                    "3. После оплаты баланс обновится автоматически",
                    reply_markup=kb.as_markup()
                )

            else:
                error_text = data.get('error', 'Неизвестная ошибка')
                await message.answer(
                    f"⚠️ Ошибка платежной системы:\n{error_text[:200]}"
                )

        except requests.exceptions.Timeout:
            await message.answer("⌛ Платежный шлюз не отвечает. Попробуйте позже.")
        except requests.exceptions.RequestException as e:
            await message.answer("🔴 Ошибка соединения с платежной системой.")
            logging.error(f"Request failed: {str(e)}")

    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}", exc_info=True)
        await message.answer(
            "⛔ Критическая ошибка. Администратор уже уведомлен.\n"
            "Попробуйте позже или обратитесь в поддержку."
        )