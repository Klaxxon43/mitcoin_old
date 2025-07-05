from aiocryptopay import AioCryptoPay, Networks
import asyncio
import time
from config import CRYPTOBOT_TOKEN

# Глобальная переменная для клиента CryptoPay
crypto = None

async def init_crypto():
    """Инициализация AioCryptoPay"""
    global crypto
    if crypto is None:
        crypto = AioCryptoPay(token=CRYPTOBOT_TOKEN)
    return crypto

async def create_invoice(amount: float, purpose='', asset: str = 'USDT') -> dict:
    """
    Создает счет для оплаты
    :param amount: Сумма платежа
    :param user_id: ID пользователя (для описания)
    :param asset: Криптовалюта (по умолчанию USDT)
    :return: Словарь с данными счета (invoice_id, bot_invoice_url, expires_in)
    """
    try:
        invoice = await crypto.create_invoice(
            amount=amount,
            description=purpose,
            asset=asset,
            expires_in=180  # 3 минуты в секундах
        )
        
        return {
            'id': invoice.invoice_id,
            'url': invoice.bot_invoice_url,
            'status': invoice.status,
            'amount': invoice.amount,
            'asset': invoice.asset
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

async def check_payment_status(invoice_id: int, purpose = '', timeout: int = 180) -> bool:
    """
    Проверяет статус оплаты счета
    :param invoice_id: ID счета для проверки
    :param timeout: Время ожидания оплаты в секундах (по умолчанию 180)
    :return: True если оплачено, False если не оплачено или время истекло
    """
    try:
        invoice = await crypto.get_invoices(invoice_ids=invoice_id)
        
        if invoice.status == 'paid':
            return True
        return False
    except Exception as e:
        print(f"Error checking invoice status: {e}")


# Пример использования
async def main():
    # Создание счета
    invoice = await create_invoice(10.50, 123456)
    if invoice:
        print(f"Счет создан: {invoice['payment_url']}")
        
        # Проверка оплаты
        is_paid = await check_payment_status(invoice['invoice_id'])
        print(f"Оплачен: {is_paid}")
    
    # Создание чека
    check = await create_check(5.25, 123456)
    if check:
        print(f"Чек создан: {check['check_url']}")

