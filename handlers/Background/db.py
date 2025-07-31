from utils.Imports import *
from .locks import *

async def scheduled_db_backup(bot: Bot):
    """Периодическая отправка базы данных каждые 10 минут"""
    while True:
        await send_db_to_chat(bot)
        await asyncio.sleep(600)  # 10 минут = 600 секунд



async def send_db_to_chat(bot: Bot):
    """Функция для отправки актуальной версии базы данных в чат"""
    db_path = Path("data/users.db")

    if not db_path.exists():
        logger.info(f"Файл базы данных {db_path} не найден!")
        return

    try:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        
        # Вариант 1: Использование BufferedInputFile (если нужно прочитать файл в память)
        with open(db_path, 'rb') as file:
            input_file = BufferedInputFile(
                file=file.read(),
                filename=f"users_db_{timestamp}.db"
            )
        
        """
        # Вариант 2: Использование FSInputFile (более эффективен для больших файлов)
        input_file = FSInputFile(
            path=db_path,
            filename=f"users_db_{timestamp}.db"
        )
        """

        await bot.send_document(
            chat_id=DB_CHAT_ID,
            document=input_file,
            caption=f"Резервная копия базы данных ({timestamp})",
        )
        logger.info(f"База данных успешно отправлена в {timestamp}")
    except Exception as e:
        logger.info(f"Ошибка при отправке базы данных: {e}")