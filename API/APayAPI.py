from utils.Imports import *
from confIg import APAY_CLIENT_ID as CLIENT_ID, APAY_SECRET_KEY as SECRET_KEY

class APayAPI:
    @staticmethod
    async def create_invoice(amount: int, order_id: str) -> dict:
        """Создание платежа в APays"""
        sign = hashlib.md5(f"{order_id}:{amount}:{SECRET_KEY}".encode()).hexdigest()
        
        params = {
            "client_id": CLIENT_ID,
            "order_id": order_id,
            "amount": amount,
            "sign": sign
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://apays.io/backend/create_order",
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    response.raise_for_status()
                    result = await response.json()
                    
                    # Save deposit record if invoice was created successfully
                    if result.get('status'):
                        rub_amount = amount / 100  # Convert back to rubles from kopecks
                        await DB.add_deposit(
                            user_id=int(order_id.split('_')[-1]),  # Extract user_id from order_id
                            amount=rub_amount,
                            unique_id=order_id,
                            status='pending',
                            service='apays',
                            item='deposit'
                        )
                    
                    return result
        except Exception as e:
            return {"status": False, "error": str(e)}

    @staticmethod
    async def check_status(order_id: str, max_retries: int = 5, delay: int = 3) -> dict:
        """Проверка статуса платежа"""
        sign = hashlib.md5(f"{order_id}:{SECRET_KEY}".encode()).hexdigest()
        
        params = {
            "client_id": CLIENT_ID,
            "order_id": order_id,
            "sign": sign
        }

        for attempt in range(max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        "https://apays.io/backend/get_order",
                        params=params,
                        timeout=aiohttp.ClientTimeout(total=10)
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            if data.get('status'):
                                # Update deposit status if payment was approved
                                if data.get('order_status') == 'approve':
                                    deposit = await DB.get_deposit(order_id)
                                    if deposit:
                                        await DB.update_deposit(
                                            deposit['deposit_id'],
                                            status='paid'#,
                                            # updated_at=datetime.now().isoformat()
                                        )
                                return data
                        
                        await asyncio.sleep(delay)
            except Exception as e:
                await asyncio.sleep(delay)
        
        return {"status": False, "error": "max_retries_exceeded"}
    

# 🧪 Тестовый запуск
async def main():
    user_id = 123456
    amount_rub = 100  # рубли
    amount_kopecks = int(amount_rub * 100)
    order_id = f"apays_{int(time.time())}_{user_id}"

    # Создание счёта
    invoice = await APayAPI.create_invoice(amount=amount_kopecks, order_id=order_id)
    if invoice.get('status'):
        logger.info(f"✅ Счёт создан: {invoice.get('link')}")
    else:
        logger.info(f"❌ Ошибка создания счёта: {invoice.get('error')}")

    # Ожидание и проверка оплаты
    logger.info("⏳ Ожидание оплаты...")
    status = await APayAPI.check_status(order_id)
    if status.get('status') and status.get('order_status') == 'approve':
        logger.info("💰 Оплата подтверждена.")
    else:
        logger.info(f"❌ Оплата не подтверждена: {status.get('error') or status.get('order_status')}")


# if __name__ == '__main__':
#     asyncio.run(main())