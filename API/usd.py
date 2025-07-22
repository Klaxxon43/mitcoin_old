from utils.Imports import *
from datetime import datetime

async def create_invoice(amount: float, user_id: int, purpose='', asset: str = 'USDT') -> dict:
    """
    Создает счет для оплаты с записью в БД
    :param amount: Сумма платежа
    :param user_id: ID пользователя
    :param purpose: Назначение платежа
    :param asset: Криптовалюта (по умолчанию USDT)
    :return: Словарь с данными счета (invoice_id, bot_invoice_url, expires_in)
    """ 
    try:
        crypto = AioCryptoPay(token=CRYPTOBOT_TOKEN)

        invoice = await crypto.create_invoice(
            amount=amount,
            description=purpose or f"Deposit for user {user_id}",
            asset=asset,
            expires_in=180  # 3 минуты в секундах
        )
        
        # Generate unique order ID
        order_id = f"crypto_{int(time.time())}_{user_id}"
        
        # Save deposit record
        await DB.add_deposit(
            user_id=user_id,
            amount=amount,
            unique_id=order_id,
            status='pending',
            service='cryptobot',
            item=asset
        )
        
        return {
            'id': invoice.invoice_id,
            'url': invoice.bot_invoice_url,
            'status': invoice.status,
            'amount': invoice.amount,
            'asset': invoice.asset,
            'order_id': order_id  # Return order_id for reference
        }
    except Exception as e:
        print(f"Error creating invoice: {e}")
        return None

async def create_check(amount: float, user_id: int, asset: str = 'USDT') -> dict:
    """
    Создает чек для выплаты
    :param amount: Сумма выплаты
    :param user_id: ID пользователя (для описания)
    :param asset: Криптовалюта (по умолчанию USDT)
    :return: Словарь с данными чека (check_id, bot_check_url)
    """
    try:
        crypto = AioCryptoPay(token=CRYPTOBOT_TOKEN)

        check = await crypto.create_check(
            amount=amount,
            asset=asset,
            description=f'Вывод средств для пользователя {user_id}'
        )
        
        return {
            'check_id': check.check_id,
            'check_url': check.bot_check_url,
            'status': check.status,
            'amount': check.amount,
            'asset': check.asset
        }
    except Exception as e:
        print(f"Error creating check: {e}")
        return None

async def check_payment_status(invoice_id: int, order_id: str = None, timeout: int = 180) -> bool:
    """
    Проверяет статус оплаты счета и обновляет БД
    :param invoice_id: ID счета для проверки
    :param order_id: ID заказа в системе (для обновления БД)
    :param timeout: Время ожидания оплаты в секундах (по умолчанию 180)
    :return: True если оплачено, False если не оплачено или время истекло
    """
    try:
        crypto = AioCryptoPay(token=CRYPTOBOT_TOKEN)

        invoice = await crypto.get_invoices(invoice_ids=invoice_id)
        
        if invoice.status == 'paid':
            # Update deposit status if order_id is provided
            if order_id:
                deposit = await DB.get_deposit(order_id)
                if deposit:
                    await DB.update_deposit(
                        deposit['deposit_id'],
                        status='paid'#,
                        # updated_at=datetime.now().isoformat()
                    )
            return True
        return False
    except Exception as e:
        print(f"Error checking invoice status: {e}")
        return False


# Пример использования
async def main():
    user_id = 123456
    
    invoice = await create_invoice(10.50, user_id, "Test deposit")
    if invoice:
        print(f"Счет создан: {invoice['url']}")
        print(f"Order ID: {invoice['order_id']}")
        
        # Проверка оплаты с обновлением БД
        status = await check_payment_status(invoice['id'], invoice['order_id'])
        print(f"Статус: {status}")
    
    # Создание чека
    check = await create_check(5.25, user_id)
    if check:
        print(f"Чек создан: {check['check_url']}")

if __name__ == "__main__":
    asyncio.run(main()) 