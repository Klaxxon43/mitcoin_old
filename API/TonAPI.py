from utils.Imports import *
from confIg import *

async def check_ton_payment(expected_amount_nano: str, comment: str) -> bool:
    """Проверка платежа в сети TON с подробным логированием"""
    logger.info(f"\n🔍 [Проверка платежа] Ожидаем: {expected_amount_nano} nanoTON, комментарий: '{comment}'")
    
    try:
        expected = int(expected_amount_nano)
        tolerance = max(int(expected * 0.1), 10000000)
        logger.info(f"🔢 Допустимый диапазон: {expected - tolerance} - {expected + tolerance} nanoTON")
        
        params = {
            'address': str(TON_WALLET),
            'limit': 20,
            'api_key': str(TON_API_TOKEN),
            'archival': 'true'
        }
        
        logger.info("🌐 Запрашиваем транзакции с параметрами:")
        logger.info(f" - Адрес: {TON_WALLET}")
        logger.info(f" - Лимит: 20")
        
        async with aiohttp.ClientSession() as session:
            try:
                response = await session.get(
                    f"{TON_API_BASE}getTransactions",
                    params=params,
                    timeout=20
                )
                
                logger.info(f"📡 Ответ API: статус {response.status}")
                
                if response.status != 200:
                    logger.info(f"❌ Ошибка API: HTTP {response.status}")
                    return False
                
                data = await response.json()
                logger.info(f"📊 Получено транзакций: {len(data.get('result', []))}")
                
                if not data.get('ok', False):
                    error_msg = data.get('error', 'Неизвестная ошибка API')
                    logger.info(f"❌ Ошибка API: {error_msg}")
                    return False
                
                for tx in data.get('result', []):
                    in_msg = tx.get('in_msg', {})
                    
                    # Обработка суммы
                    tx_value = 0
                    try:
                        value = in_msg.get('value')
                        if value is not None:
                            tx_value = int(float(value))
                    except (TypeError, ValueError):
                        continue
                    
                    # Обработка комментария
                    tx_comment = str(in_msg.get('message', '')).strip()
                    
                    logger.info(f"\n🔎 Проверяем транзакцию:")
                    logger.info(f" - Хэш: {tx.get('hash')}")
                    logger.info(f" - Сумма: {tx_value} nanoTON")
                    logger.info(f" - Комментарий: '{tx_comment}'")
                    logger.info(f" - Дата: {tx.get('utime')}")
                    
                    # Проверка совпадения
                    amount_match = abs(tx_value - expected) <= tolerance
                    comment_match = tx_comment == comment.strip()
                    
                    logger.info(f"🔹 Совпадение суммы: {'✅' if amount_match else '❌'}")
                    logger.info(f"🔹 Совпадение комментария: {'✅' if comment_match else '❌'}")
                    
                    if amount_match and comment_match:
                        logger.info(f"\n🎉 Найден подходящий платеж!")
                        logger.info(f" - Получено: {tx_value} nanoTON")
                        logger.info(f" - Ожидалось: {expected} nanoTON (±{tolerance})")
                        logger.info(f" - Комментарий: '{tx_comment}'")
                        logger.info(f" - Время: {tx.get('utime')}")
                        return True
                
                logger.info("\n🔍 Подходящих платежей не найдено")
                return False
                
            except asyncio.TimeoutError:
                logger.info("⏱️ Таймаут при запросе к TON API")
                return False
            except aiohttp.ClientError as e:
                logger.info(f"🌐 Ошибка сети: {str(e)}")
                return False
    
    except Exception as e:
        logger.info(f"💥 Критическая ошибка: {type(e).__name__}: {str(e)}")
        return False