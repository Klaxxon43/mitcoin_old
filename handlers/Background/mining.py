from utils.Imports import *
from .locks import *

#напоминание о сборе майнинга
async def remind_mining_collection(bot):
    while True:
        try:
            print(f"\n[{datetime.now()}] Проверка майнинга...")
            
            async with DB.con.cursor() as cur:
                # 1. Проверка структуры таблицы
                await cur.execute("PRAGMA table_info(mining)")
                columns = {col[1]: col[2] for col in await cur.fetchall()}
                print("Структура таблицы:", columns)
                
                if 'reminder_sent' not in columns:
                    print("Добавляем колонку reminder_sent...")
                    await cur.execute("ALTER TABLE mining ADD COLUMN reminder_sent BOOLEAN DEFAULT FALSE")
                    await DB.con.commit()
                
                # 2. Получаем текущее время в том же формате, что хранится в БД
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                # 3. Находим пользователей для напоминания
                await cur.execute("""
                    SELECT user_id, time, earning, reminder_sent 
                    FROM mining 
                """)
                users = await cur.fetchall()
                print(f"Всего пользователей с earning > 0: {len(users)}")
                
                for user_id, mining_time_str, earning, reminder_sent in users:
                    try:
                        # Преобразуем строку времени из БД в datetime
                        mining_time = datetime.strptime(mining_time_str, '%Y-%m-%d %H:%M:%S')
                        current_time_dt = datetime.strptime(current_time, '%Y-%m-%d %H:%M:%S')
                        
                        # Вычисляем разницу в часах
                        hours_passed = (current_time_dt - mining_time).total_seconds() / 3600
                        print(f"Пользователь {user_id}: прошло {hours_passed:.2f} часов")
                        
                        if not reminder_sent and hours_passed >= 24:
                            print(f"Отправляем напоминание пользователю {user_id}")
                            await bot.send_message(
                                chat_id=user_id,
                                text=f"⏳ Ваш майнинг готов к сбору!"
                            )
                            await cur.execute("""
                                UPDATE mining 
                                SET reminder_sent = TRUE 
                                WHERE user_id = ?
                            """, (user_id,))
                            await DB.con.commit()
                            
                    except Exception as e:
                        print(f"Ошибка обработки пользователя {user_id}: {str(e)}")
                        continue
                        
        except Exception as e:
            print(f"Критическая ошибка: {str(e)}")
            import traceback
            traceback.print_exc()
        
        await asyncio.sleep(300)