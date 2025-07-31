import httpx, asyncio, aiohttp, json, hashlib, base64, hmac
from typing import Optional

BASE_URL = "https://nicepay.io/public/api"

MERCHANT_ID = "686fb2a8e987437077e6a878"
SECRET_KEY = "ij8JG-NLVUK-Icsme-EflwC-i7kRY"

async def create_payment2():
    pass
    # # Данные платежа
    # payment_data = {
    #     "merchant_id": MERCHANT_ID,
    #     "secret": SECRET_KEY,
    #     "order_id": "2",
    #     "customer": "user@gmail.com",
    #     "amount": 55500,  # 35.40 USD (в центах)
    #     "currency": "RUB",
    #     "description": "Top up balance on website"
    # }

    # # URL API
    # api_url = f"{BASE_URL}/payment"

    # async with aiohttp.ClientSession() as session:
    #     try:
    #         async with session.post(api_url, json=payment_data) as response:
    #             response_data = await response.json()
                
    #             if response_data.get("status") == "success":
    #                 logger.info("Платеж успешно создан!")
    #                 logger.info(f"ID платежа: {response_data['data']['payment_id']}")
    #                 logger.info(f"Сумма: {response_data['data']['amount'] / 100} {response_data['data']['currency']}")
    #                 logger.info(f"Ссылка на оплату: {response_data['data']['link']}")
    #             else:
    #                 logger.info("Ошибка при создании платежа:")
    #                 logger.info(response_data.get("data", {}).get("message", "Неизвестная ошибка"))
                    
        # except Exception as e:
        #     logger.info(f"Произошла ошибка: {e}")

# Запуск асинхронной функции
# asyncio.run(create_payment2())
