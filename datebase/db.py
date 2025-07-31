import aiosqlite, json
from datetime import datetime
import pytz
from aiocron import crontab
import asyncio
from aiogram import Bot 
from aiogram.types import InputFile, BufferedInputFile
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from io import BytesIO
from aiogram.types import BufferedInputFile
from datetime import datetime
from utils.Imports import *
import io
from datetime import datetime, timedelta


MOSCOW_TZ = pytz.timezone("Europe/Moscow")

class DataBase:
    def __init__(self):
        self.con = None
        # self.pool = pool 


    async def create(self):
        self.con = await aiosqlite.connect('data/users.db')
        
        if self.con is None:  # Избегайте повторной инициализации
            self.con = await aiosqlite.connect('data/users.db')
        print('бд подключена')


    # история транзакций

    async def add_transaction(self, user_id: int, amount: float, description: str, additional_info: str = None):
        """Добавляет транзакцию в историю."""
        async with self.con.cursor() as cur:
            await cur.execute('''
                INSERT INTO transaction_history (user_id, amount, description, additional_info)
                VALUES (?, ?, ?, ?)
            ''', (user_id, amount, description, additional_info))
            await self.con.commit()

    async def get_transaction_history(self, user_id: int):
        """Возвращает историю транзакций для конкретного пользователя."""
        async with self.con.cursor() as cur:
            await cur.execute('''
                SELECT id, user_id, timestamp, amount, description, additional_info
                FROM transaction_history
                WHERE user_id = ?
                ORDER BY timestamp DESC
            ''', (user_id,))
            return await cur.fetchall() 
        


    async def get_top_users(self, admins_id):
        async with self.con.cursor() as cur:
            # Преобразуем список admins_id в кортеж
            admins_tuple = tuple(admins_id)
            
            # Выбираем топ-10 пользователей по балансу, исключая админов
            await cur.execute('''
                SELECT user_id, username, balance 
                FROM users 
                WHERE user_id NOT IN ({}) 
                ORDER BY balance DESC 
                LIMIT 10
            '''.format(','.join('?' * len(admins_tuple))), admins_tuple)
            
            top_users = await cur.fetchall()  # Получаем результат запроса
            return top_users 
        

    async def get_active_completed_tasks(self):
        """Получить активные задания для проверки"""
        async with self.con.cursor() as cur:
            await cur.execute('''
                SELECT * FROM completed_tasks 
                WHERE status = 1 AND rem_days > 0
            ''')
            return await cur.fetchall()

    async def update_completed_task(self, task_id, status=None, rem_days=None):
        """Обновить данные выполненного задания"""
        updates = []
        params = []
        async with self.con.cursor() as cur:
            if status is not None:
                updates.append("status = ?")
                params.append(status)
            if rem_days is not None:
                updates.append("rem_days = ?")
                params.append(rem_days)

            if updates:
                params.append(task_id)
                await cur.execute(f'''
                    UPDATE completed_tasks 
                    SET {', '.join(updates)} 
                    WHERE user_id = ?
                ''', params)
                await self.con.commit()



    async def execute_query(self, query):
        """Выполняет SQL-запрос и возвращает результат."""
        try:
            async with self.con.cursor() as cur:
                await cur.execute(query)
                result = await cur.fetchall()
                return result
        except Exception as e:
            return f"Ошибка при выполнении запроса: {e}"


    async def is_task_completed_check(self, user_id, task_id):
        """Проверка, выполнено ли задание пользователем"""
        async with self.con.cursor() as cur:
            await cur.execute(
                'SELECT * FROM completed_tasks WHERE user_id = ? AND task_id = ?',
                (user_id, task_id)
            )
            return await cur.fetchone() is not None
        
    async def add_completed_task(self, user_id, task_id, target_id, task_sum, owner_id, status, other=7):
        """Добавление выполненного задания в базу"""
        async with self.con.cursor() as cur:
            await cur.execute(
                'INSERT INTO completed_tasks (user_id, task_id, target_id, task_sum, owner_id, status, rem_days) VALUES (?, ?, ?, ?, ?, ?, ?)',
                (user_id, task_id, target_id, task_sum, owner_id, status, other)  
            ) 
            await self.con.commit()

            referrer_id = await self.get_referrer_id(user_id)
            task = await self.get_task_by_id(task_id)
            task_type = task[4]
            if referrer_id:
                bonus = await self.get_tasks_bonus(task_type)
                await self.add_balance(user_id=referrer_id, amount=bonus)
                await self.record_referral_earnings(referrer_id, user_id, bonus)


    async def add_completed_task_boost(self, user_id, task_id, target_id, task_sum, owner_id, status, rem_days):
        """Добавление выполненного задания в базу"""
        async with self.con.cursor() as cur:
            await cur.execute(
                'INSERT INTO completed_tasks (user_id, task_id, target_id, task_sum, owner_id, status, rem_days) VALUES (?, ?, ?, ?, ?, ?, ?)',
                (user_id, task_id, target_id, task_sum, owner_id, status, rem_days)
            )
            await self.con.commit()

            referrer_id = await self.get_referrer_id(user_id)
            task = await self.get_task_by_id(task_id)
            task_type = 6
            if referrer_id: 
                bonus = await self.get_tasks_bonus(task_type)
                await self.add_balance(user_id=referrer_id, amount=bonus)
                await self.record_referral_earnings(referrer_id, user_id, bonus)


    async def get_bonus_ops(self):
        async with self.con.cursor() as cur:
            await cur.execute(
                'SELECT * FROM bonus',
            )
            return await cur.fetchall()


    async def get_bonus_op(self, id):
        async with self.con.cursor() as cur:
            await cur.execute('SELECT * FROM bonus WHERE id = ?', (id,))
            return await cur.fetchone()


    # Метод для добавления ОП
    async def add_bonus_op(self, target_id, link):
        async with self.con.cursor() as cur:
            await cur.execute('''INSERT INTO bonus (target_id, link)
                          VALUES (?, ?)''', (target_id, link))
            await self.con.commit()

    # Метод для удаления ОП (удаляет все ОП или только для указанного канала)
    async def remove_bonus_op(self, id):
        async with self.con.cursor() as cur:
            await cur.execute('DELETE FROM bonus WHERE id = ?', (id,))
            await self.con.commit()


    async def get_last_bonus_date(self, user_id: int) -> str:
        async with self.con.execute(
                "SELECT last_bonus_date FROM bonus_time WHERE user_id = ?",
                (user_id,),
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None

    async def update_last_bonus_date(self, user_id: int):
        """Обновить дату последней конвертации."""
        async with self.con.cursor() as cur:
            today = datetime.now(MOSCOW_TZ).strftime("%Y-%m-%d")
            await cur.execute('''
                INSERT INTO bonus_time (user_id, last_bonus_date)
                VALUES (?, ?)
                ON CONFLICT(user_id) DO UPDATE SET last_bonus_date = excluded.last_bonus_date
            ''', (user_id, today))
            await self.con.commit()



#ОБЩАЯ СТАТИСТИКА
    # Функция для увеличения значения в колонке all_subs_chanel на 1
    async def increment_all_subs_chanel(self):
        async with self.con.cursor() as cur:
            await cur.execute('''
            UPDATE all_statics
            SET all_subs_chanel = all_subs_chanel + 1
            WHERE user_id = 1
            ''')
            await self.con.commit()

    # Функция для увеличения значения в колонке all_subs_group на 1
    async def increment_all_subs_group(self):
        async with self.con.cursor() as cur:
            await cur.execute('''
            UPDATE all_statics
            SET all_subs_groups = all_subs_groups + 1
            WHERE user_id = 1
            ''')
            await self.con.commit()

    # Функция для увеличения значения в колонке all_taasks на 1
    async def increment_all_taasks(self):
        async with self.con.cursor() as cur:
            await cur.execute('''
            UPDATE all_statics
            SET all_taasks = all_taasks + 1
            WHERE user_id = 1
            ''')
            await self.con.commit()

    # Функция для увеличения значения в колонке all_see на 1
    async def increment_all_see(self):
        async with self.con.cursor() as cur:
            await cur.execute('''
            UPDATE all_statics
            SET all_see = all_see + 1
            WHERE user_id = 1
            ''')
            await self.con.commit()

    async def count_bonus_time_rows(self) -> int:
        """Асинхронно подсчитывает количество строк в таблице bonus_time."""
        async with self.con.cursor() as cur:
            await cur.execute("SELECT COUNT(*) FROM bonus_time")
            row = await cur.fetchone()
            return row[0] 


    async def get_statics(self):
            # Подключение к базе данных
            async with self.con.cursor() as cur:
                # Выполнение запроса для получения всех данных из таблицы
                await cur.execute('SELECT * FROM all_statics')
                
                # Получение всех строк
                rows = await cur.fetchall()
                
                # Возврат результата
                return rows 

    async def get_game_statics(self):
        """Получает только игровую статистику из таблицы all_statics"""
        async with self.con.cursor() as cur:
            # Запрос только игровых колонок (начиная с game_wins)
            await cur.execute('''
                SELECT 
                    user_id,
                    game_wins,
                    game_losses,
                    dice_played,
                    basketball_played,
                    football_played,
                    darts_played,
                    casino_played,
                    withdraw_from_game
                FROM all_statics
            ''')
            
            # Получаем данные и преобразуем в список словарей
            columns = [
                'user_id',
                'game_wins',
                'game_losses',
                'dice_played',
                'basketball_played',
                'football_played',
                'darts_played',
                'casino_played',
                'withdraw_from_game'
            ]
            
            rows = await cur.fetchall()
            result = []
            
            for row in rows:
                result.append(dict(zip(columns, row)))
            
            return result

    #ЕЖЕДНЕВНАЯ ОБЩАЯ СТАТИСТИКА
    async def reset_daily_statistics(self):
        statics = await self.get_statics()
        _, chanels, groups, all, see, users, _, gift, boosts, reactions, links, comments, mined, _, _, _, _, _, _, _, _ = statics[1] 
        print('обновляю')
        await self.update_daily_stats(users, chanels, groups, all, see, gift, boosts, reactions, links, comments, mined)

        async with self.con.cursor() as cur:
            # Обнуление статистики для user_id = 2 
            await cur.execute('''
            UPDATE all_statics
            SET all_subs_chanel = 0, all_subs_groups = 0, all_taasks = 0, all_see = 0, gifts = 0, comments=0, links=0, users=0, boosts=0, likes=0, mined=0, game_wins=0, game_losses=0, dice_played=0, basketball_played=0, football_played=0, darts_played=0, casino_played=0, withdraw_from_game=0
            WHERE user_id = 2 
            ''')
            await self.con.commit()
            print(f"Статистика для user_id = 2 очищена в {datetime.now()}")


    async def increment_statistics(self, user_id, column):
        async with self.con.cursor() as cur:
            # Увеличение значения в указанной колонке
            await cur.execute(f'''
            UPDATE all_statics
            SET {column} = {column} + 1
            WHERE user_id = ?
            ''', (user_id,))
            await self.con.commit() 

    async def increment_statistics_withdraw_from_game(self, user_id, bonus):
        async with self.con.cursor() as cur:
            # Увеличение значения в указанной колонке
            await cur.execute(f'''
            UPDATE all_statics
            SET withdraw_from_game = withdraw_from_game + ?
            WHERE user_id = ?
            ''', (bonus, user_id,))
            await self.con.commit() 

    async def all_balance(self):
        try:
            from confIg import ADMINS_ID
            print(f"ADMINS_ID: {ADMINS_ID}")
            async with self.con.cursor() as cur:
                query = """
                SELECT SUM(balance)
                FROM users
                WHERE user_id NOT IN (:id1, :id2, :id3, :id4)
                AND balance >= 0;
                """
                params = {'id1': ADMINS_ID[0], 'id2': ADMINS_ID[1], 'id3': ADMINS_ID[2], 'id4': ADMINS_ID[3]}
                result = await cur.execute(query, params)
                row = await result.fetchone()
                total_balance = row[0] if row else 0
                return total_balance 
        except Exception as e:
            print(f"Ошибка: {e}")
            return 0

    # Функция для увеличения значения в колонке users на 1
    async def increment_all_users(self):
        async with self.con.cursor() as cur:
            await cur.execute('''
            UPDATE all_statics
            SET users = users + 1
            WHERE user_id = 2
            ''')
            await self.con.commit()

    async def check_fund_minus(self, id):
        async with self.con.cursor() as cur:
            await cur.execute('''
            UPDATE checks
            SET ref_fund = ref_fund - 1
            WHERE check_id = ?
            ''', (id, ))
            await self.con.commit()



    async def count_today_gifts(self) -> int:
        """Подсчитывает количество подарков, собранных за сегодня."""
        async with self.con.cursor() as cur:
            await cur.execute('''
            SELECT COUNT(*) 
            FROM bonus_time 
            WHERE DATE(last_bonus_date) = DATE('now')
            ''')
            row = await cur.fetchone()
            return row[0] if row else 0




    async def get_db_structure_sqlite(self):
        """Получение структуры базы данных."""
        try:
            async with self.con.cursor() as cur:
                # Получаем список всех таблиц
                await cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = await cur.fetchall()

                db_structure = {}

                # Для каждой таблицы получаем информацию о колонках
                for table in tables:
                    table_name = table[0]
                    await cur.execute(f"PRAGMA table_info({table_name});")
                    columns = await cur.fetchall()
                    db_structure[table_name] = columns

                return db_structure
        except Exception as e:
            print(f"Ошибка: {e}")
            return {}





    async def update_last_conversion_date(self, user_id: int):
        """Обновить дату последней конвертации."""
        async with self.con.cursor() as cur:
            today = datetime.now(MOSCOW_TZ).strftime("%Y-%m-%d")
            await cur.execute('''
                INSERT INTO conversions (user_id, last_conversion_date)
                VALUES (?, ?)
                ON CONFLICT(user_id) DO UPDATE SET last_conversion_date = excluded.last_conversion_date
            ''', (user_id, today))
            await self.con.commit()

    async def get_last_conversion_date(self, user_id: int):
        """Получает дату последней конвертации пользователя"""
        async with self.con.execute(
            "SELECT last_conversion_date FROM conversions WHERE user_id = ?", 
            (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            print(row)
            return row[0] if row else None  # Обращаемся по индексу, а не по ключу


    # ВЫВОД

    async def add_output(self, user_id, wallet, amount, type):
        async with self.con.cursor() as cur:
            await cur.execute('SELECT 1 FROM output WHERE user_id = ?', (user_id,))
            if await cur.fetchone() is None:
                await cur.execute('INSERT INTO output (user_id, wallet, amount, type) VALUES (?, ?, ?, ?)',
                                  (user_id, wallet, amount, type))
                await self.con.commit()
                return True


    async def get_outputs(self):
        async with self.con.cursor() as cur:
            await cur.execute('SELECT * FROM output')
            return await cur.fetchall()

    async def get_usdt_outputs(self):
        async with self.con.cursor() as cur:
            await cur.execute('SELECT * FROM output WHERE type = 1')
            return await cur.fetchall()

    async def get_rub_outputs(self):
        async with self.con.cursor() as cur:
            await cur.execute('SELECT * FROM output WHERE type = 2')
            return await cur.fetchall()

    async def get_output_userid(self, user_id):
        async with self.con.cursor() as cur:
            await cur.execute('SELECT * FROM output WHERE user_id = ?', (user_id,))
            return await cur.fetchone()

    async def get_output(self, id):
        async with self.con.cursor() as cur:
            await cur.execute('SELECT * FROM output WHERE id = ?', (id,))
            return await cur.fetchone()

    async def delete_output(self, id):
        async with self.con.cursor() as cur:
            await cur.execute('DELETE FROM output WHERE id = ?', (id,))
            await self.con.commit()
            return cur.rowcount > 0



    # КОНВЕРТАЦИЯ

    async def connect(self):
        connection = await aiosqlite.connect("users.db")
        connection.row_factory = aiosqlite.Row  # Добавляем row_factory для доступа по ключам
        return connection




  





    async def is_check_activated(self, user_id, uid):
        """Проверка, выполнено ли задание пользователем"""
        async with self.con.cursor() as cur:
            await cur.execute(
                'SELECT * FROM activated_checks WHERE user_id = ? AND uid = ?',
                (user_id, uid)
            )
            return await cur.fetchone() is not None

    async def add_activated_check(self, user_id, uid):
        """Добавление выполненного задания в базу"""
        async with self.con.cursor() as cur:
            await cur.execute(
                'INSERT INTO activated_checks (user_id, uid) VALUES (?, ?)',
                (user_id, uid)
            )
            await self.con.commit()

    async def create_check(self, uid, user_id, type, sum, amount, ref_bonus, ref_fund, locked_for_user=None, password=None):
        """
        Создает новый чек с обязательными параметрами.

        :param uid: уникальный идентификатор чека.
        :param user_id: ID пользователя, который создает чек.
        :param type: тип чека (1 - сингл, 2 - мульти).
        :param sum: сумма чека.
        :param amount: количество активаций (для сингл-чека = 1).
        :param ref_bonus: реферальный бонус.
        :param ref_fund: реферальный фонд.
        :param locked_for_user: ID пользователя, к которому привязан чек (опционально).
        """
        async with self.con.cursor() as cur:
            await cur.execute('''
                INSERT INTO checks (uid, user_id, type, sum, amount, max_amount, ref_bonus, ref_fund, locked_for_user, password)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (uid, user_id, type, sum, amount, amount, ref_bonus, ref_fund, locked_for_user, password, ))
            await self.con.commit()






    async def update_check(self, check_id, amount=None, description=None, locked_for_user=None, password=None,
                           OP_id=None, OP_name = None):
        """
        Изменяет необязательные параметры чека.

        :param cur: курсор базы данных.
        :param check_id: ID чека, который нужно изменить.
        :param description: новое описание для чека (опционально).
        :param locked_for_user: ID пользователя для привязки сингл-чека (опционально).
        :param password: новый пароль для мульти-чека (опционально).
        :param OP_id: новая обязательная подписка (опционально).
        """
        updates = []
        insert = []
        params = []
        async with self.con.cursor() as cur:
            if amount is not None:
                updates.append("amount = ?")
                params.append(amount)
            if description is not None:
                updates.append("description = ?")
                params.append(description)
            if locked_for_user is not None:
                updates.append("locked_for_user = ?")
                params.append(locked_for_user)
            if password is not None:
                updates.append("password = ?")
                params.append(password)
            if OP_id is not None:
                updates.append("OP_id = ?")
                params.append(OP_id)           
            if OP_name is not None:
                updates.append("OP_name = ?")
                params.append(OP_name)

            if updates:
                query = f"UPDATE checks SET {', '.join(updates)} WHERE check_id = ?"
                params.append(check_id)
                await cur.execute(query, params)
            if insert:
                query = f"INSERT checks SET {', '.join(insert)} WHERE check_id = ?"
                params.append(check_id)
                await cur.execute(query, params)

            await self.con.commit()

    async def update_check2(self, check_id, ref_fund=None, **kwargs):
        """
        Обновляет параметры чека, включая реферальный фонд.
        """
        updates = []
        params = []
        if ref_fund is not None:
            updates.append("ref_fund = ?")
            params.append(ref_fund)
        if kwargs:
            for key, value in kwargs.items():
                updates.append(f"{key} = ?")
                params.append(value)
        if updates:
            query = f"UPDATE checks SET {', '.join(updates)} WHERE check_id = ?"
            params.append(check_id)
            async with self.con.cursor() as cur:
                await cur.execute(query, params)
                await self.con.commit()

    async def process_check_activation(self, uid):
        """
        Уменьшает количество активаций для чека при активации или удаляет чек, если это сингл-чек.

        :param cur: курсор базы данных.
        :param uid: уникальный идентификатор чека.
        """
        async with self.con.cursor() as cur:
            # Проверяем, сингл это чек или мульти
            check = await cur.execute('SELECT check_id, type, sum, amount FROM checks WHERE uid = ?', (uid,))
            result = await check.fetchone()

            if not result:
                raise ValueError("Чек не найден")

            check_id, check_type, sum, amount = result

            if check_type == 1:  # Сингл-чек
                await cur.execute('DELETE FROM checks WHERE check_id = ?', (check_id,))
            elif check_type == 2:  # Мульти-чек
                if amount > 1:
                    await cur.execute('UPDATE checks SET amount = amount - 1 WHERE check_id = ?', (check_id,))
                    print('минус 1 чек')
                else:
                    await cur.execute('DELETE FROM checks WHERE check_id = ?', (check_id,))

            await self.con.commit()

    async def delete_check(self, user_id, check_id):

        async with self.con.cursor() as cur:
            await cur.execute('DELETE FROM checks WHERE check_id = ? AND user_id = ?', (check_id, user_id))
            await self.con.commit()

    async def get_check_by_uid(self, uid):
        """
        Получает чек из базы данных по его уникальному идентификатору (UID).

        :param uid: Уникальный идентификатор чека (строка).
        :return: Словарь с данными чека или None, если чек не найден.
        """
        async with self.con.cursor() as cur:
            try:
                await cur.execute('SELECT * FROM checks WHERE uid = ?', (uid,))
                return await cur.fetchone()
            except Exception as e:
                return None 

    async def get_referral_percent(self, check_uid):
        """
        Получает процент реферала для чека.

        :param check_uid: Уникальный идентификатор чека.
        :return: Процент реферала.
        """
        async with self.con.cursor() as cur:
            await cur.execute("SELECT referral_percent FROM checks WHERE uid = ?", (check_uid,))
            result = await cur.fetchone()
            return result[0] if result else 0

    
    async def get_check_by_user_id(self, user_id):
        async with self.con.cursor() as cur:
            await cur.execute('SELECT * FROM checks WHERE user_id = ?', (user_id,))
            return await cur.fetchall()

    async def get_check_by_id(self, check_id):
        async with self.con.cursor() as cur:
            await cur.execute('SELECT * FROM checks WHERE check_id = ?', (check_id,))
            return await cur.fetchone()

    async def clear_tasks_and_refund(self):
        from handlers.client.client import all_price 
        task_prices = {1: all_price['channel'], 2: all_price['chat'], 3: all_price['post'], 4: all_price['comment'], 5: all_price['link'], 6: all_price['boost'], 7: all_price['reaction']}

        async with self.con.cursor() as cur:
            await cur.execute('SELECT user_id, amount, type FROM tasks')
            tasks = await cur.fetchall()

            refunds = {}
            for user_id, amount, task_type in tasks:
                if task_type in task_prices:
                    refund_amount = task_prices[task_type] * amount
                    refunds[user_id] = refunds.get(user_id, 0) + refund_amount

            for user_id, refund in refunds.items():
                await cur.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?', (refund, user_id))

            await cur.execute('DELETE FROM tasks')
            await cur.execute('DELETE FROM completed_tasks')
            await self.con.commit() 

    async def add_report(self, task_id, chat_id, user_id, description):
        async with self.con.cursor() as cur:
            await cur.execute('SELECT 1 FROM task_reports WHERE chat_id = ?', (chat_id,))
            if await cur.fetchone() is None:
                await cur.execute('''
                    INSERT INTO task_reports (task_id, chat_id, user_id, description)
                    VALUES (?, ?, ?, ?)
                ''', (task_id, chat_id, user_id, description))
                await self.con.commit()
                return True
        return False

    async def get_reports(self):
        async with self.con.cursor() as cur:
            await cur.execute('SELECT * FROM task_reports')
            return await cur.fetchall()

    async def get_report(self, report_id):
        async with self.con.cursor() as cur:
            await cur.execute('SELECT * FROM task_reports WHERE report_id = ?', (report_id,))
            return await cur.fetchone()

    async def delete_report(self, report_id):
        async with self.con.cursor() as cur:
            await cur.execute('DELETE FROM task_reports WHERE report_id = ?', (report_id,))
            await self.con.commit()
            return cur.rowcount > 0

    # Метод для добавления ОП
    async def add_op(self, chat_id: int, channel_id: str, expiration_time: datetime = None):
        async with self.con.cursor() as cur:
            await cur.execute('''INSERT INTO mandatory_subscriptions (chat_id, channel_id, expiration_time)
                          VALUES (?, ?, ?)''', (chat_id, channel_id, expiration_time))
            await self.con.commit()

    # Метод для удаления ОП (удаляет все ОП или только для указанного канала)
    async def remove_op(self, chat_id: int, channel_id: str = None):
        async with self.con.cursor() as cur:
            if channel_id:
                await cur.execute('DELETE FROM mandatory_subscriptions WHERE chat_id = ? AND channel_id = ?',
                                  (chat_id, channel_id))
            else:
                await cur.execute('DELETE FROM mandatory_subscriptions WHERE chat_id = ?', (chat_id,))
            await self.con.commit()

    # Метод для получения всех активных ОП в чате
    async def get_ops(self, chat_id: int):
        async with self.con.cursor() as cur:
            await cur.execute(
                'SELECT channel_id, expiration_time FROM mandatory_subscriptions WHERE chat_id = ?',
                (chat_id,)
            )
            ops = await cur.fetchall()
            return ops

    # Метод для удаления просроченных ОП
    async def remove_expired_ops(self):
        now = datetime.now()
        async with self.con.cursor() as cur:
            await cur.execute(
                'DELETE FROM mandatory_subscriptions WHERE expiration_time IS NOT NULL AND expiration_time < ?',
                (now,)
            )
            await self.con.commit()

    # ЗАДАЧИ

    async def add_task(self, user_id, target_id, amount, task_type, other=None):
        """
        Добавляет новую задачу в таблицу tasks с инкрементом task_id вручную.
        Возвращает: task_id новой задачи.
        """
        async with self.con.cursor() as cur:
            # Получаем максимальный task_id
            await cur.execute('SELECT MAX(task_id) FROM tasks')
            result = await cur.fetchone()

            max_task_id = result[0] if result and result[0] is not None else 0
            new_task_id = max_task_id + 1

            # Вставляем новую задачу
            await cur.execute('''
                INSERT INTO tasks (task_id, user_id, target_id, amount, type, max_amount, other, time)
                VALUES (?, ?, ?, ?, ?, ?, ?, datetime(CURRENT_TIMESTAMP, '+3 hours'))
            ''', (new_task_id, user_id, target_id, amount, task_type, amount, other))

            await self.con.commit()
            return new_task_id



    # async def add_user(self, user_id, username):
    #     async with self.con.cursor() as cur:
    #         await cur.execute('''
    #             INSERT OR IGNORE INTO users (user_id, username, registration_time)
    #             VALUES (?, ?, datetime(CURRENT_TIMESTAMP, '+3 hours'))
    #         ''', (user_id, username))
    #         await self.con.commit()


    async def get_tasks(self):
        """Метод для получения всех задач из базы данных"""
        async with self.con.cursor() as cur:
            await cur.execute('SELECT * FROM tasks')
            return await cur.fetchall()

    async def get_tasks_by_user(self, user_id):
        """Метод для получения всех задач пользователя, отсортированных по времени создания"""
        async with self.con.cursor() as cur:
            await cur.execute('''
                SELECT * FROM tasks
                WHERE user_id = ?
                ORDER BY STRFTIME('%Y-%m-%d %H:%M:%S', time) DESC
            ''', (user_id,))
            tasks = await cur.fetchall()
        return tasks

    async def get_completed_tasks_by_user(self, user_id):
        """Метод для получения всех задач из базы данных для конкретного user_id"""
        async with self.con.cursor() as cur:
            await cur.execute('SELECT * FROM completed_tasks WHERE user_id = ?', (user_id,))
            return await cur.fetchall()
        
    async def get_tasks_by_user_admin(self, user_id):
        """Метод для получения всех задач из базы данных для конкретного user_id"""
        async with self.con.cursor() as cur:
            await cur.execute('SELECT task_id, type FROM tasks WHERE user_id = ?', (user_id,))
            return await cur.fetchall()

    async def get_target_id_by_user_admin(self, user_id):
        """Метод для получения всех задач из базы данных для конкретного user_id"""
        async with self.con.cursor() as cur:
            await cur.execute('SELECT target_id, type FROM tasks WHERE user_id = ?', (user_id,))
            return await cur.fetchall() 

    async def get_task_by_id(self, task_id):
        """Метод для получения задания по его порядковому номеру (task_id)"""
        async with self.con.cursor() as cur:
            await cur.execute('SELECT * FROM tasks WHERE task_id = ?', (task_id,))
            return await cur.fetchone()

    async def delete_task(self, task_id):
        """Удаление задания из базы данных по его task_id"""
        async with self.con.cursor() as cur:
            await cur.execute('DELETE FROM tasks WHERE task_id = ?', (task_id,))
            await self.con.commit()

    # выбирает задачи для КАНАЛОВ
    async def select_chanel_tasks(self):
        async with self.con.cursor() as cur:
            await cur.execute('SELECT * FROM tasks WHERE type = 1')
            return await cur.fetchall() 

    # выбирает задачи для ЧАТОВ
    async def select_chat_tasks(self):
        async with self.con.cursor() as cur:
            await cur.execute('SELECT * FROM tasks WHERE type = 2')
            return await cur.fetchall()

    # выбирает задачи для ПОСТОВ
    async def select_post_tasks(self):
        async with self.con.cursor() as cur:
            await cur.execute('SELECT * FROM tasks WHERE type = 3')
            return await cur.fetchall()
        

    async def is_task_completed(self, user_id, task_id):
        """Проверка, выполнено ли задание пользователем"""
        async with self.con.cursor() as cur:
            await cur.execute(
                'SELECT * FROM completed_tasks WHERE user_id = ? AND task_id = ?',
                (user_id, task_id)
            )
            return await cur.fetchone() is not None



    async def get_tasks_bonus(self, task_type):
        # Здесь определите бонусы для каждого уровня грузовиков
        bonuses = {1: 150, 2: 225, 3: 15}
        return bonuses.get(task_type, 0)

    async def update_task_amount(self, task_id):
        """Обновление количества (amount) в задании"""
        async with self.con.cursor() as cur:
            await cur.execute('UPDATE tasks SET amount = amount - 1 WHERE task_id = ?', (task_id,))
            await self.con.commit()

    async def update_task_amount2(self, task_id, amount):
        """Обновление количества (amount) в задании"""
        async with self.con.cursor() as cur:
            await cur.execute('UPDATE tasks SET amount = ? WHERE task_id = ?', (amount, task_id,))
            await self.con.commit()

    async def calculate_total_cost(self):
        """Метод для расчета общей стоимости всех заданий."""
        async with self.con.cursor() as cur:
            # Получаем все типы заданий из базы данных
            await cur.execute('SELECT type FROM tasks')
            tasks = await cur.fetchall()

            # Словарь с ценами для каждого типа задания
            from handlers.client.client import all_price
            prices = {1: all_price['channel'], 2: all_price['chat'], 3: all_price['post'], 4: all_price['comment'], 5: all_price['link'], 6: all_price['boost'], 7: all_price['reaction']}


            # Считаем количество заданий для каждого типа
            task_count = {}
            for task_type in tasks:
                task_type = task_type[0]  # Извлекаем тип задания из кортежа
                task_count[task_type] = task_count.get(task_type, 0) + 1

            # Рассчитываем общую стоимость
            total_cost = 0
            for task_type, count in task_count.items():
                price_per_item = prices.get(task_type, 0)  # Получаем цену для типа задания
                total_cost += count * price_per_item  # Умножаем количество заданий на цену

            return total_cost

    async def add_balance_dep(self, user_id, amount):
        async with self.con.cursor() as cur:
            await cur.execute(
                'UPDATE users SET balance = balance + ? WHERE user_id = ?',
                (amount, user_id)
            )
            await self.con.commit()

            referrer_id = await self.get_referrer_id(user_id)
            if referrer_id:
                bonus = amount * 0.15
                await self.add_balance(user_id=referrer_id, amount=bonus)
                await self.record_referral_earnings(referrer_id, user_id, bonus)

    async def count_user_deposits(self, user_id):
        async with self.con.cursor() as cur:
            await cur.execute('SELECT COUNT(*) FROM deposit WHERE user_id = ?', (user_id,))
            result = await cur.fetchone()
            return result[0] if result else 0

    async def sum_user_deposits(self, user_id):
        async with self.con.cursor() as cur:
            await cur.execute('SELECT SUM(amount) FROM deposit WHERE user_id = ?', (user_id,))
            result = await cur.fetchone()
            return result[0] if result[0] is not None else 0

    async def add_deposit(self, user_id, amount, unique_id=None, status=None, service=None, item=None):
        async with self.con.cursor() as cur:
            await cur.execute('''
                INSERT INTO deposit (unique_id, user_id, amount, status, service, item)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (unique_id, user_id, amount, status, service, item))
            await self.con.commit()


    async def update_deposit(self, deposit_id: int, **fields):
        if not fields:
            return
        async with self.con.cursor() as cur:
            set_clause = ", ".join(f"{k}=?" for k in fields)
            values = list(fields.values()) + [deposit_id]
            query = f"UPDATE deposit SET {set_clause} WHERE deposit_id=?"
            await cur.execute(query, values)
            await self.con.commit()

    async def get_deposit(self, unique_id: str) -> Optional[Dict]:
        async with self.con.cursor() as cur:
            await cur.execute("SELECT * FROM deposit WHERE unique_id=?", (unique_id,))
            row = await cur.fetchone()
            if row:
                columns = [desc[0] for desc in cur.description]
                return dict(zip(columns, row))
            return None
        
    async def get_total_deposits(self):
        """Метод для подсчета общей суммы всех депозитов"""
        async with self.con.cursor() as cur:
            await cur.execute('SELECT SUM(amount) FROM deposit')
            result = await cur.fetchone()
            return result[0] if result[0] is not None else 0

    async def count_user_completed_tasks(self, user_id):
        async with self.con.cursor() as cur:
            await cur.execute('SELECT COUNT(*) FROM completed_tasks WHERE user_id = ?', (user_id,))
            result = await cur.fetchone()
            return result[0] if result else 0

    async def add_chating_task(self, chat_id, price):
        """Метод для добавления новой задачи с инкрементом task_id"""
        async with self.con.cursor() as cur:
            await cur.execute('SELECT MAX(task_id) FROM chating_tasks')
            max_task_id = await cur.fetchone()
            new_task_id = 1 if max_task_id[0] is None else max_task_id + 1

            await cur.execute('''
                INSERT INTO chating_tasks (task_id, chat_id, price)
                VALUES (?, ?, ?)
            ''', (new_task_id, chat_id, price))
            await self.con.commit()

    async def get_chating_tasks(self):
        """Метод для получения всех задач из базы данных"""
        async with self.con.cursor() as cur:
            await cur.execute('SELECT * FROM chating_tasks')
            return await cur.fetchall()

    async def delete_chating_task(self, task_id):
        """Удаление задания из базы данных по его task_id"""
        async with self.con.cursor() as cur:
            await cur.execute('DELETE FROM chating_tasks WHERE task_id = ?', (task_id,))
            await self.con.commit()

    async def get_chating_task_by_id(self, task_id):
        """Метод для получения задания по его порядковому номеру (task_id)"""
        async with self.con.cursor() as cur:
            await cur.execute('SELECT * FROM chating_tasks WHERE task_id = ?', (task_id,))
            return await cur.fetchone()

    async def add_op_task(self, target_id, text):
        """Метод для добавления новой задачи с инкрементом task_id"""
        async with self.con.cursor() as cur:
            # Получаем максимальный task_id
            await cur.execute('SELECT MAX(task_id) FROM op_pr')
            result = await cur.fetchone()
            max_task_id = result[0] if result else None  # Извлекаем значение из кортежа или устанавливаем None

            # Если записей нет, начинаем с task_id = 1
            new_task_id = 1 if max_task_id is None else max_task_id + 1

            # Добавляем новую задачу с инкрементированным task_id
            await cur.execute('''
                INSERT INTO op_pr (task_id, target_id, text)
                VALUES (?, ?, ?)
            ''', (new_task_id, target_id, text))
            await self.con.commit()

    async def get_op_tasks(self):
        """Метод для получения всех задач из базы данных"""
        async with self.con.cursor() as cur:
            await cur.execute('SELECT * FROM op_pr')
            return await cur.fetchall()

    async def delete_op_task(self, task_id):
        """Удаление задания из базы данных по его task_id"""
        async with self.con.cursor() as cur:
            await cur.execute('DELETE FROM op_pr WHERE task_id = ?', (task_id,))
            await self.con.commit()

    async def get_op_task_by_id(self, task_id):
        """Метод для получения задания по его порядковому номеру (task_id)"""
        async with self.con.cursor() as cur:
            await cur.execute('SELECT * FROM op_pr WHERE task_id = ?', (task_id,))
            return await cur.fetchone()

    async def get_id_from_username(self, username):
        async with self.con.cursor() as cur: 
            await cur.execute("""SELECT user_id FROM users 
                                 WHERE username =?""",
                                (username, )) 
            id = await cur.fetchone() 
            return id  

    async def get_break_status(self):
        async with self.con.execute('SELECT status FROM break LIMIT 1') as cursor:
            res = await cursor.fetchone()
            return res[0] if res else 0

    async def update_break_status(self, current_status: int):
        new_status = 0 if current_status else 1
        async with self.con.cursor() as cur:
            await cur.execute('UPDATE break SET status = ?', (new_status,))
            await self.con.commit()

    # БАЛАНС

    async def get_user_balance(self, user_id):
        async with self.con.execute(
            'SELECT balance FROM users WHERE user_id = ?', (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            print(row)
            return row[0] if row else 0
                

    async def add_balance(self, user_id, amount):
        async with self.con.cursor() as cur:
            await cur.execute(
                'UPDATE users SET balance = balance + ? WHERE user_id = ?',
                (amount, user_id)
            )
            await self.con.commit()
            # Пример добавления транзакции
            await DB.add_transaction(
                user_id=user_id,
                amount=amount,
                description="Другое"
            )

    async def update_balance(self, user_id, balance):
        async with self.con.cursor() as cur:
            await cur.execute(
                'UPDATE users SET balance = ? WHERE user_id = ?',
                (balance, user_id)
            )
            await self.con.commit()



    # РУБ БАЛАНС

    async def get_user_rub_balance(self, user_id):
        async with self.con.execute('SELECT rub_balance FROM users WHERE user_id = ?', (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0  # Возвращаем баланс или 0, если записи нет

    async def add_rub_balance(self, user_id, amount):
        async with self.con.cursor() as cur:
            await cur.execute(
                'UPDATE users SET rub_balance = rub_balance + ? WHERE user_id = ?',
                (amount, user_id)
            )
            await self.con.commit()

    async def update_rub_balance(self, user_id, rub_balance):
        async with self.con.cursor() as cur:
            await cur.execute(
                'UPDATE users SET rub_balance = ? WHERE user_id = ?',
                (rub_balance, user_id)
            )
            await self.con.commit()


    # Получить количество звезд пользователя
    async def get_stars(self, user_id: int) -> int:
        async with self.con.cursor() as cur:
            await cur.execute("SELECT stars FROM users WHERE user_id = ?", (user_id,)) 
            row = await cur.fetchone()
            return row[0] if row else 0

    # Увеличить количество звезд
    async def add_star(self, user_id: int, amount: int = 1):
        async with self.con.cursor() as cur:
            await cur.execute("UPDATE users SET stars = stars + ? WHERE user_id = ?", (amount, user_id))
            await cur.execute("UPDATE users SET max_stars = max_stars + ? WHERE user_id = ?", (amount, user_id))
            await self.con.commit()

    async def get_max_stars(self, user_id: int) -> int:
        async with self.con.cursor() as cur:
            await cur.execute("SELECT max_stars FROM users WHERE user_id = ?", (user_id,)) 
            row = await cur.fetchone()
            return row[0] if row else 0

    # РЕФЕРАЛКА
    async def count_user_referrals(self, user_id):
        async with self.con.cursor() as cur:
            await cur.execute('SELECT COUNT(*) FROM referral_stats WHERE user_id = ?', (user_id,))
            result = await cur.fetchone()
            return result[0] if result else 0

    async def get_referrer_id(self, user_id):
        async with self.con.cursor() as cur:
            await cur.execute('SELECT referrer_id FROM users WHERE user_id = ?', (user_id,))
            row = await cur.fetchone()
            return row[0] if row else None

    async def get_referred_users(self, user_id):
        async with self.con.cursor() as cur:
            await cur.execute('SELECT user_id FROM users WHERE referrer_id = ?', (user_id,))
            return await cur.fetchall()

    async def get_earned_from_referrals(self, user_id):
        async with self.con.cursor() as cur:
            await cur.execute('SELECT SUM(earned_from_referrals) FROM referral_stats WHERE user_id = ?', (user_id,))
            row = await cur.fetchone()
            return row[0] if row else 0

    async def record_referral_earnings(self, referrer_id, referred_user_id, amount):
        async with self.con.cursor() as cur:
            await cur.execute('''
                INSERT INTO referral_stats (user_id, referred_user_id, earned_from_referrals)
                VALUES (?, ?, ?)
            ''', (referrer_id, referred_user_id, amount))
            await self.con.commit()

    # ЮЗЕРЫ

    async def update_user(self, user_id, balance=None, referrer_id=None):
        async with self.con.cursor() as cur:
            if balance is not None:
                await cur.execute('''
                    UPDATE users SET balance = ? WHERE user_id = ?
                ''', (balance, user_id))

            if referrer_id is not None:
                await cur.execute('''
                    UPDATE users SET referrer_id = ? WHERE user_id = ?
                ''', (referrer_id, user_id))

            await self.con.commit()

    async def select_user(self, user_id):
        if self.con is None:  # Избегайте повторной инициализации
            self.con = await aiosqlite.connect('users.db')
        async with self.con.cursor() as cur:
            await cur.execute('''
                SELECT * FROM users WHERE user_id = ?
            ''', (user_id,))
            row = await cur.fetchone()
            if row:
                return {
                    'user_id': row[0],
                    'username': row[1],
                    'balance': row[2],
                    'referrer_id': row[3],
                    'rub_balance': row[4],
                    'prem': row[5],
                    'reg_time': row[6]
                }
            else:
                return None

    async def add_user(self, user_id: int, username: str):
        """Создает нового пользователя во всех необходимых таблицах"""
        async with self.con.cursor() as cur:
            # Создаем в основной таблице users
            await cur.execute('''
                INSERT OR IGNORE INTO users 
                (user_id, username, registration_time)
                VALUES (?, ?, datetime(CURRENT_TIMESTAMP, '+3 hours'))
            ''', (user_id, username))
            
            # Создаем запись в таблице game
            await cur.execute('''
                INSERT OR IGNORE INTO game 
                (user_id, username, bal, bal_rub)
                VALUES (?, ?, 0, 0)
            ''', (user_id, username))
            
            await self.con.commit()

    async def add_user_on_game(self, user_id: int, username: str):
        """Создает нового пользователя во всех необходимых таблицах"""
        async with self.con.cursor() as cur:
            # Создаем запись в таблице game
            await cur.execute('''
                INSERT OR IGNORE INTO game 
                (user_id, username, bal, bal_rub)
                VALUES (?, ?, 0, 0)
            ''', (user_id, username))
            
            await self.con.commit()

    async def update_user(self, user_id, username):
        async with self.con.cursor() as cur:
            await cur.execute('''
                UPDATE users SET username = ? WHERE user_id = ?
            ''', (username, user_id)) 
            await self.con.commit() 

    async def update_user_referrer_id(self, user_id, username):
        async with self.con.cursor() as cur:
            await cur.execute('''
                UPDATE users SET referrer_id = ? WHERE user_id = ?
            ''', (username, user_id)) 
            await self.con.commit() 

    async def update_user_premium(self, user_id, prem):
        async with self.con.cursor() as cur:
            await cur.execute('''
                UPDATE users SET premium = ? WHERE username = ?
            ''', (prem, user_id)) 
            await self.con.commit()  

    async def scount_premium_user(self):
        async with self.con.cursor() as cur:
            await cur.execute('''
                SELECT * FROM users WHERE premium = 1
            ''')
            row = await cur.fetchone()
            if row:
                return len(row) 
            else:
                return 0

    async def reset_all_premium(self):
        """
        Устанавливает значение premium = False для всех пользователей в таблице users.
        """
        try:
            async with self.con.cursor() as cur:
                # Выполняем массовый запрос
                await cur.execute('''
                    UPDATE users SET premium = ?
                ''', (False,))  # Устанавливаем premium = False для всех пользователей
                await self.con.commit()
                print("Все пользователи обновлены: premium = False.")
        except Exception as e:
            print(f"Ошибка при массовом обновлении premium: {e}")

    async def get_all_users(self):
        """Метод для получения списка всех user_id из таблицы пользователей."""
        async with self.con.cursor() as cur:
            await cur.execute("SELECT user_id FROM users")
            rows = await cur.fetchall()
            return [row[0] for row in rows]  # Возвращаем только user_id

    async def select_all(self):
        async with self.con.cursor() as cur:
            await cur.execute('''
                SELECT user_id, username, balance FROM users
            ''')
            rows = await cur.fetchall()
            users = [
                {'user_id': row[0], 'username': row[1], 'balance': row[2]}
                for row in rows
            ]
            return users
        
    async def get_all_users(self):
        async with self.con.cursor() as cur:
            await cur.execute("SELECT * FROM users")
            users = await cur.fetchall()
            return users 

    async def delete_user(self, user_id):
        async with self.con.cursor() as cur:
            await cur.execute('DELETE FROM users WHERE user_id = ?', (user_id,))
            await self.con.commit()

    async def create_referral_link(self, check_id: int, referrer_id: int, referral_link: str):
        """
        Создает запись о реферальной ссылке в базе данных.

        :param check_id: ID чека
        :param referrer_id: ID пользователя, который создал чек
        :param referral_link: Уникальная реферальная ссылка
        """
        async with self.con.cursor() as cur:
            query = await cur.execute("""
            INSERT INTO check_referrals (check_id, referrer_id, referral_link)
            VALUES (?, ?, ?)
            """, (check_id, referrer_id, referral_link))
            await self.con.commit()


    async def select_like_comment(self):
        try:
            async with self.con.cursor() as cur:
                # Убедитесь, что столбец называется `type` или измените на правильное имя
                await cur.execute("SELECT * FROM tasks WHERE type = 4")
                result = await cur.fetchall()
                return result
        except Exception as e:
            print(f"Ошибка при выполнении запроса select_like_tasks: {e}")
            return None  # Возвращаем None в случае ошибки
        
        
    async def select_link_tasks(self):
            try:
                async with self.con.cursor() as cur:
                    # Убедитесь, что столбец называется `type` или измените на правильное имя
                    await cur.execute("SELECT * FROM tasks WHERE type = 5")
                    result = await cur.fetchall()
                    return result
            except Exception as e:
                print(f"Ошибка при выполнении запроса select_like_tasks: {e}")
                return None  # Возвращаем None в случае ошибки 
            
    async def select_boost_tasks(self):
            try:
                async with self.con.cursor() as cur:
                    # Убедитесь, что столбец называется `type` или измените на правильное имя
                    await cur.execute("SELECT * FROM tasks WHERE type = 6")
                    result = await cur.fetchall()
                    return result
            except Exception as e:
                print(f"Ошибка при выполнении запроса select_like_tasks: {e}")
                return None  # Возвращаем None в случае ошибки 
            
    async def select_reaction_tasks(self):
            try:
                async with self.con.cursor() as cur:
                    # Убедитесь, что столбец называется `type` или измените на правильное имя
                    await cur.execute("SELECT * FROM tasks WHERE type = 7")
                    result = await cur.fetchall()
                    return result
            except Exception as e:
                print(f"Ошибка при выполнении запроса select_like_tasks: {e}")
                return None  # Возвращаем None в случае ошибки 
            

    async def update_task_max_amount(self, task_id: int, new_max_amount: int):
        async with self.con.cursor() as cur:
            await cur.execute(
                "UPDATE tasks SET max_amount = ? WHERE task_id = ?",
                (new_max_amount, task_id)
            )
            await self.con.commit()

    async def update_task_amount(self, task_id: int, new_amount: int):
        async with self.con.cursor() as cur:
            await cur.execute(
                "UPDATE tasks SET amount = ? WHERE task_id = ?",
                (new_amount, task_id)
            )
            await self.con.commit()

            
    async def get_user_tasks(self, user_id: int, task_type: int):
        """
        Получает список заданий пользователя определённого типа.
        :param user_id: ID пользователя.
        :param task_type: Тип задания (например, 5 — переход по ссылке).
        :return: Список заданий.
        """
        async with self.con.cursor() as cur:
            await cur.execute("""
                SELECT * FROM tasks 
                WHERE user_id = ? AND type = ?
            """, (user_id, task_type))
            return await cur.fetchall() 
            


    async def get_top_referrers(self):
        """
        Получает топ-10 пользователей по количеству приглашённых рефералов.
        :return: Список кортежей (user_id, username, referral_count).
        """
        async with self.con.cursor() as cur:
            await cur.execute("""
                SELECT referrer_id, COUNT(*) AS referral_count 
                FROM users 
                WHERE referrer_id IS NOT NULL 
                GROUP BY referrer_id 
                ORDER BY referral_count DESC 
                LIMIT 10
            """)
            top_referrers = await cur.fetchall()

            # Получаем username для каждого user_id
            result = []
            for user_id, referral_count in top_referrers:
                await cur.execute("SELECT username FROM users WHERE user_id = ?", (user_id,))
                username = await cur.fetchone()
                if username:
                    result.append((user_id, username[0], referral_count))
            return result
        

    async def get_top_referrers24hour(self, ADMINS_ID):
        """Получает топ-10 рефереров за последние 24 часа, исключая админов."""
        async with self.con.cursor() as cur:
            # Формируем SQL-запрос
            query = '''
                SELECT 
                    referrer_id, 
                    COUNT(*) AS referral_count 
                FROM 
                    users 
                WHERE 
                    referrer_id IS NOT NULL 
                    AND registration_time >= datetime('now', '-24 hours') 
                    AND registration_time != None
                    AND referrer_id NOT IN ({})  
                GROUP BY 
                    referrer_id 
                ORDER BY 
                    referral_count DESC 
                LIMIT 10;
            '''.format(",".join(map(str, ADMINS_ID)))  # Подставляем ID админов

            await cur.execute(query)
            top_referrers = await cur.fetchall()

            # Получаем username для каждого реферера
            result = []
            for referrer_id, referral_count in top_referrers:
                await cur.execute('SELECT user_id, username FROM users WHERE user_id = ?', (referrer_id,))
                user_data = await cur.fetchone()
                if user_data:
                    user_id, username = user_data
                    result.append((user_id, username, referral_count))

            return result
        

    async def add_chanell_op(self, channel_id, channel_name):
        async with self.con.cursor() as cur:
            await cur.execute( "INSERT INTO OP_start (channel_id, channel_name) VALUES (?, ?)", 
                              (channel_id, channel_name))
            await self.con.commit()



# channels = cursor.execute("SELECT channel_id, channel_name FROM channels").fetchall()

    async def all_channels_op(self):
        async with self.con.cursor() as cur:
            await cur.execute("SELECT channel_id, channel_name FROM OP_start")
            return await cur.fetchall()

    async def get_channel_info(self, channel_id):
        async with self.con.cursor() as cur:
            await cur.execute("SELECT * FROM OP_start WHERE channel_id = ?", (channel_id,))
            return await cur.fetchone()

    async def update_channel_name(self, channel_id, channel_name):
        async with self.con.cursor() as cur:
            await cur.execute("UPDATE OP_start SET channel_name = ? WHERE id = ?",
                            (channel_name, channel_id))
            await self.con.commit()

    async def update_channel_username(self, channel_name, channel_id):
        async with self.con.cursor() as cur:
            await cur.execute("UPDATE OP_start SET channel_id = ? WHERE id = ?",
                            (channel_id, channel_name))
            await self.con.commit()

    async def delete_channel(self, channel_id):
        async with self.con.cursor() as cur:
            await cur.execute("DELETE FROM OP_start WHERE id = ?", (channel_id,))
            await self.con.commit()


    async def get_boost_tasks(self):
        """Получить задания на буст канала (status = 0)"""
        async with self.con.cursor() as cur:
            await cur.execute('''
                SELECT * FROM completed_tasks 
                WHERE status = 1 AND rem_days > 0 AND task_sum = 5000
            ''') 
            return await cur.fetchall()
        
    async def add_pending_reaction_task(self, user_id: int, task_id: int, target_id: str, post_id: int, reaction: str, screenshot: str):
        async with self.con.cursor() as cur:
            await cur.execute('''
                INSERT INTO pending_reaction_tasks (user_id, task_id, target_id, post_id, reaction, screenshot)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, task_id, target_id, post_id, reaction, screenshot))
            await self.con.commit()

    async def get_pending_reaction_task(self, task_id: int, user_id: int):
        async with self.con.cursor() as cur:
            await cur.execute('''
                SELECT * FROM pending_reaction_tasks
                WHERE task_id = ? AND user_id = ?
            ''', (task_id, user_id))
            return await cur.fetchone()
        
    async def get_pending_reaction_task_all(self, task_id: int, user_id: int):
        async with self.con.cursor() as cur:
            await cur.execute('''
                SELECT * FROM pending_reaction_tasks
                WHERE task_id = ? AND user_id = ?
            ''', (task_id, user_id))
            return await cur.fetchone()  

    async def delete_pending_reaction_task(self, task_id: int, user_id: int):
        async with self.con.cursor() as cur:
            await cur.execute('''
                DELETE FROM pending_reaction_tasks
                WHERE task_id = ? AND user_id = ?
            ''', (task_id, user_id))
            await self.con.commit()

    async def is_task_pending(self, user_id: int, task_id: int) -> bool:
        async with self.con.cursor() as cur:
            await cur.execute('''
                SELECT * FROM pending_reaction_tasks
                WHERE task_id = ? AND user_id = ?
            ''', (task_id, user_id))
            return await cur.fetchone() is not None

    async def add_failed_task(self, user_id: int, task_id: int):
        """Добавляет задание в список проваленных для пользователя."""
        async with self.con.cursor() as cur:
            await cur.execute('''
                INSERT INTO failed_tasks (user_id, task_id)
                VALUES (?, ?)
            ''', (user_id, task_id))
            await self.con.commit()

    async def is_task_failed(self, user_id: int, task_id: int) -> bool:
        """Проверяет, провалил ли пользователь задание."""
        async with self.con.cursor() as cur:
            await cur.execute('''
                SELECT 1 FROM failed_tasks
                WHERE user_id = ? AND task_id = ?
            ''', (user_id, task_id))
            return await cur.fetchone() is not None
        

    async def is_task_available_for_user(self, user_id: int, task_id: int) -> bool:
        """
        Проверяет, доступно ли задание для пользователя
        Возвращает True если задание НЕ выполнено, НЕ провалено, 
        НЕ находится на проверке и НЕ было пропущено пользователем
        """
        async with self.con.cursor() as cur:
            # Проверяем completed_tasks
            await cur.execute('SELECT 1 FROM completed_tasks WHERE user_id = ? AND task_id = ?', 
                            (user_id, task_id))
            if await cur.fetchone():
                return False
                
            # Проверяем failed_tasks
            await cur.execute('SELECT 1 FROM failed_tasks WHERE user_id = ? AND task_id = ?', 
                            (user_id, task_id))
            if await cur.fetchone():
                return False
                
            # Проверяем pending_reaction_tasks
            await cur.execute('SELECT 1 FROM pending_reaction_tasks WHERE user_id = ? AND task_id = ?', 
                            (user_id, task_id))
            if await cur.fetchone():
                return False
                
            # Проверяем skeep_tasks
            await cur.execute('SELECT 1 FROM skeep_tasks WHERE user_id = ? AND task_id = ?', 
                            (user_id, task_id))
            if await cur.fetchone():
                return False
                
        return True

    async def get_user_task_statuses(self, user_id: int) -> set[int]:
        """Возвращает множество task_id, уже завершённых, проваленных или ожидающих"""
        task_ids = set()

        async with self.con.cursor() as cur:
            # Все выполненные задания
            await cur.execute('''
                SELECT task_id FROM completed_tasks WHERE user_id = ?
            ''', (user_id,))
            task_ids.update(row[0] for row in await cur.fetchall())

            # Все проваленные задания
            await cur.execute('''
                SELECT task_id FROM failed_tasks WHERE user_id = ?
            ''', (user_id,))
            task_ids.update(row[0] for row in await cur.fetchall())

            # Все задания, в ожидании реакции
            await cur.execute('''
                SELECT task_id FROM pending_reaction_tasks WHERE user_id = ?
            ''', (user_id,))
            task_ids.update(row[0] for row in await cur.fetchall())

        return task_ids

    async def update_task_amount_and_max(self, task_id: int, new_amount: int):
        """
        Обновляет количество выполнений (amount) и максимальное количество (max_amount) задания.
        Если new_amount > max_amount, то max_amount также обновляется.
        """
        async with self.con.cursor() as cur:
            await cur.execute('''
                UPDATE tasks
                SET amount = ?,
                    max_amount = CASE WHEN ? > max_amount THEN ? ELSE max_amount END
                WHERE task_id = ?
            ''', (new_amount, new_amount, new_amount, task_id))
            await self.con.commit()


    async def search_mining(self, user_id):
        async with self.con.cursor() as cur:
            await cur.execute('''
                SELECT * FROM mining WHERE user_id = ?
            ''', (user_id, ))
            
            res = await cur.fetchall()
            if res:
                return True
            return False

    async def get_deposit_mining(self, user_id):
        async with self.con.cursor() as cur:
            await cur.execute('''
                SELECT deposit FROM mining WHERE user_id = ?
            ''', (user_id, ))
            
            res = await cur.fetchall()
            if res:
                return res
            return False  
        
    async def get_earning_mining(self, user_id):
        async with self.con.cursor() as cur:
            await cur.execute('''
                SELECT earning FROM mining WHERE user_id = ?
            ''', (user_id, ))
            
            res = await cur.fetchall()
            if res:
                return res[0][0]
            return False  

    async def add_mining(self, user_id, deposit=1):
        async with self.con.cursor() as cur:
            # Сначала проверяем, есть ли уже запись с таким user_id
            await cur.execute('SELECT 1 FROM mining WHERE user_id = ?', (user_id,))
            existing_record = await cur.fetchone()
            
            if existing_record:
                return False  # Запись уже существует, ничего не добавляем
            
            # Если записи нет, добавляем новую
            await cur.execute('''
                INSERT INTO mining (user_id, deposit, time)
                VALUES (?, ?, strftime('%Y-%m-%d %H:%M:%S', datetime('now', '+3 hours')))
            ''', (user_id, deposit))
            await self.con.commit()
            return True  # Успешно добавили новую запись
        
    async def remove_mining(self, user_id):
        async with self.con.cursor() as cur:
            # Проверяем, есть ли запись с таким user_id
            await cur.execute('SELECT 1 FROM mining WHERE user_id = ?', (user_id,))
            existing_record = await cur.fetchone()
            
            if not existing_record: 
                return False  # Записи нет, нечего удалять
            
            # Если запись есть, удаляем её
            await cur.execute('DELETE FROM mining WHERE user_id = ?', (user_id,))
            await self.con.commit()
            return True  # Успешно удалили запись

    async def check_mining(self, user_id):
        async with self.con.cursor() as cur:
            await cur.execute('''
                SELECT time FROM mining WHERE user_id = ?
            ''', (user_id,))
            res = await cur.fetchone()

            if res:
                db_time = res[0]
                try:
                    db_datetime = datetime.strptime(str(db_time), '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    print(f"Неверный формат времени в базе данных: {db_time}")
                    # return False, "Ошибка в данных майнинга."

                now = datetime.now()
                time_diff = now - db_datetime

                if time_diff.total_seconds() <  10800:
                    remaining_time = 10800 - time_diff.total_seconds()
                    return False, f"Майнинг завершится через {int(remaining_time // 3600)} часов {int((remaining_time % 3600) // 60)} минут."
                else:
                    await self.update_time_mining(user_id)    
                    return True, f'Майнинг закончился'
            # return False, "Майнинг не активирован."
        
    async def update_time_mining(self, user_id):
        async with self.con.cursor() as cur:
                    await cur.execute(
                        "UPDATE mining SET time = strftime('%Y-%m-%d %H:%M:%S', datetime('now', '+3 hours')) WHERE user_id = ?",
                        (user_id,),
                    )              
                    await self.con.commit()   

    async def status_mining(self, user_id):
        async with self.con.cursor() as cur:
            await cur.execute('''
                SELECT time FROM mining WHERE user_id = ?
            ''', (user_id,))
            res = await cur.fetchone()

            if res:
                db_time = res[0]
                try:
                    db_datetime = datetime.strptime(str(db_time), '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    print(f"Неверный формат времени в базе данных: {db_time}")
                    return False, "Ошибка в данных майнинга."

                now = datetime.now()
                time_diff = now - db_datetime

                if time_diff.total_seconds() <  10800:
                    remaining_time = 10800 - time_diff.total_seconds()
                    return False, f"Завершится через {int(remaining_time // 3600)} часов {int((remaining_time % 3600) // 60)} минут."
                else:                 
                    return True, f'Можно собрать'
            return False, "Майнинг не активирован."
        
        
    async def add_earning(self, user_id, earning):
        async with self.con.cursor() as cur:
            await cur.execute('''
                UPDATE mining
                SET earning = ? WHERE user_id = ?
            ''', (earning, user_id,))
            await self.con.commit()
            return True
        
    async def get_earning(self, user_id):
        async with self.con.cursor() as cur:
            await cur.execute('''
                SELECT earning FROM mining WHERE user_id = ?
            ''', (user_id,))
            res = await cur.fetchone()
            return res


    async def get_last_collection_time(self, user_id):
        async with self.con.cursor() as cur:
            await cur.execute('''
                SELECT time FROM mining WHERE user_id = ?
            ''', (user_id,))
            res = await cur.fetchone()
            return datetime.strptime(res[0], '%Y-%m-%d %H:%M:%S') if res else datetime.now()

    async def update_last_collection_time(self, user_id, time):
        async with self.con.cursor() as cur:
            await cur.execute('''
                UPDATE mining SET time = ? WHERE user_id = ?
            ''', (time.strftime('%Y-%m-%d %H:%M:%S'), user_id))
            await self.con.commit()

    async def get_last_collection_time(self, user_id):
        async with self.con.cursor() as cur:
            await cur.execute("""
                              SELECT time FROM mining WHERE user_id = ?
                              """, (user_id, ))
            return (await cur.fetchall())[0][0]
        


    # async def get_constant(self, name):
    #     async with self.con.cursor() as cur:
    #         await cur.execute("""
    #                             cursor.execute("SELECT value FROM constants WHERE name = ?", (name,))
    #                           """, (name, ))
    #     result = await cur.fetchone()
    #     return result[0] if result else None

    async def get_mining_line(self):
        async with self.con.cursor() as cur:
            await cur.execute("SELECT COUNT(*) FROM mining")
            result = await cur.fetchone()
            return result[0] if result else 0
        
    async def add_mined_from_all_stats(self, user_id, mined):
        print(f"DEBUG: Starting update for user {user_id} with amount {mined}")  # Отладочный вывод
        async with self.con.cursor() as cur:
            await cur.execute('''
            UPDATE all_statics
            SET mined = mined + ?
            ''', (mined, ))
            print(f"DEBUG: Rows affected: {cur.rowcount}")  # Сколько строк было изменено
            await self.con.commit()
            print("DEBUG: Commit successful")  # Подтверждение commit


    async def update_daily_stats(self,
        add_users: int = 0,
        all_subs_chanel: int = 0,
        all_subs_groups: int = 0,
        all_tasks: int = 0,
        all_see: int = 0,
        gift: int = 0,
        boosts: int = 0,
        likes: int = 0,
        links: int = 0,
        comments: int = 0,
        mined: int = 0
    ):
        """
        Создает новую запись ежедневной статистики.
        day - автоинкрементный ID, дата берется из created_at.
        """
        async with self.con.cursor() as cur:
            # Вставляем новую запись
            await cur.execute("""
                INSERT INTO statics_history (
                    add_users, all_subs_chanel, all_subs_groups,
                    all_tasks, all_see, gift, boosts, likes,
                    links, comments, mined
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                add_users, all_subs_chanel, all_subs_groups,
                all_tasks, all_see, gift, boosts, likes,
                links, comments, mined
            ))
            
            print(f"Создана новая запись статистики (ID: {cur.lastrowid})")
            await self.con.commit()



    async def create_statistics_graph(self, stat_type: str, title: str, ylabel: str) -> BufferedInputFile:
        """
        Универсальная функция для создания графиков статистики
        :param stat_type: Поле из таблицы для анализа (add_users, all_subs_chanel и т.д.)
        :param title: Заголовок графика
        :param ylabel: Подпись оси Y
        :return: BufferedInputFile с изображением графика
        """
        column_mapping = {
            'add_users': 'Новые пользователи',
            'all_subs_chanel': 'Подписки на канал',
            'all_subs_groups': 'Подписки на группы',
            'all_tasks': 'Выполненные задачи',
            'all_see': 'Просмотры',
            'gift': 'Подарки',
            'boosts': 'Бусты',
            'likes': 'Лайки',
            'links': 'Переходы по ссылкам',
            'comments': 'Комментарии',
            'mined': 'Добыча'
        }
        
        async with self.con.cursor() as cur:
            try:
                # Получаем данные из БД за последние 30 дней
                await cur.execute(f"""
                    SELECT 
                        strftime('%d.%m.%Y', created_at) as formatted_date,
                        SUM({stat_type}) as total_value
                    FROM statics_history
                    WHERE created_at >= DATE('now', '-30 days')
                    GROUP BY DATE(created_at)
                    ORDER BY created_at ASC
                """)
                
                data = await cur.fetchall()
                
                if not data or all(row[1] == 0 for row in data):
                    return None
                
                # Подготовка данных
                dates = [row[0] for row in data]
                values = [row[1] for row in data]
                
                # Создаем график
                plt.figure(figsize=(14, 7))
                
                # Основной график с настройками
                bars = plt.bar(dates, values, 
                            color=self.get_color_for_stat(stat_type),
                            width=0.7, 
                            edgecolor=self.get_edge_color(stat_type),
                            linewidth=1,
                            alpha=0.8)
                
                # Добавляем значения на столбцы
                for bar in bars:
                    height = bar.get_height()
                    if height > 0:
                        plt.text(bar.get_x() + bar.get_width()/2., height,
                                f'{int(height)}',
                                ha='center', va='bottom',
                                fontsize=9, fontweight='bold')
                
                # Настройки графика
                plt.title(f'{title} за последние 30 дней', 
                        pad=20, fontsize=14, fontweight='bold')
                plt.xlabel('Дата', fontsize=12, labelpad=10)
                plt.ylabel(ylabel, fontsize=12, labelpad=10)
                
                # Настройка осей
                plt.xticks(rotation=45, ha='right', fontsize=10)
                plt.yticks(fontsize=10)
                
                # Автоматическое масштабирование
                y_max = max(values) * 1.25 if max(values) > 0 else 10
                plt.ylim(0, y_max)
                
                # Сетка и оформление
                plt.grid(axis='y', linestyle='--', alpha=0.5)
                plt.gca().set_axisbelow(True)
                plt.tight_layout(pad=2.0)
                
                # Сохраняем в буфер
                buf = BytesIO()
                plt.savefig(buf, format='png', dpi=150, 
                        bbox_inches='tight', 
                        facecolor='white')
                buf.seek(0)
                plt.close()
                
                return BufferedInputFile(buf.getvalue(), 
                                    filename=f'{stat_type}_stats.png')
                
            except Exception as e:
                print(f"Error creating graph for {stat_type}: {str(e)}")
                plt.close()
                return None

    def get_color_for_stat(self, stat_type: str) -> str:
        """Возвращает цвет для каждого типа статистики"""
        colors = {
            'add_users': '#4285F4',
            'all_subs_chanel': '#34A853',
            'all_subs_groups': '#EA4335',
            'all_tasks': '#FBBC05',
            'all_see': '#673AB7',
            'gift': '#FF5722',
            'boosts': '#9C27B0',
            'likes': '#00BCD4',
            'links': '#8BC34A',
            'comments': '#607D8B',
            'mined': '#795548'
        }
        return colors.get(stat_type, '#4285F4')

    def get_edge_color(self, stat_type: str) -> str:
        """Возвращает цвет границы для столбцов"""
        return self.get_color_for_stat(stat_type)













# CASINO



    async def get_user_balance_game(self, user_id: int) -> float:
        """Получает баланс пользователя из таблицы game"""
        async with self.con.cursor() as cur:
            await cur.execute('''SELECT bal FROM game WHERE user_id = ?''', (user_id,))
            result = await cur.fetchone()
            return result[0]

    async def get_user_balance_stars_game(self, user_id: int) -> float:
        """Получает баланс пользователя из таблицы game"""
        async with self.con.cursor() as cur:
            await cur.execute('''SELECT bal_rub FROM game WHERE user_id = ?''', (user_id,))
            result = await cur.fetchone()
            return result[0]
        
    async def update_user_balance_game(self, user_id: int, amount: float):
        """Обновляет баланс пользователя в таблице game"""
        async with self.con.cursor() as cur:
            
            await cur.execute('''
                UPDATE game SET bal = bal + ? 
                WHERE user_id = ?
            ''', (amount, user_id))
            await self.con.commit()

    async def update_user_balance_stars_game(self, user_id: int, amount: float):
        """Обновляет баланс пользователя в таблице game"""
        async with self.con.cursor() as cur:
            
            await cur.execute('''
                UPDATE game SET bal_rub = bal_rub + ? 
                WHERE user_id = ?
            ''', (amount, user_id))
            await self.con.commit()

    
    async def update_game_stats(self, user_id: int, stat_type: str):
        """
        Обновляет статистику пользователя.
        stat_type: 'bet', 'win' или 'loss'
        """
        if stat_type not in ('bet', 'win', 'loss'):
            return
            
        column = {
            'bet': 'bets_count',
            'win': 'bets_won',
            'loss': 'bets_lost'
        }[stat_type]
        
        async with self.con.cursor() as cur:
            await cur.execute(f'''
                UPDATE game 
                SET {column} = {column} + 1
                WHERE user_id = ?
            ''', (user_id,))
            await self.con.commit()
    
    async def add_game_history(self, user_id: int, amount: float, result: str, game_mode: str, currency: str = 'mico'):
        """Добавляет запись в историю игр."""
        async with self.con.cursor() as cur:
            await cur.execute('''
                INSERT INTO game_history (user_id, date, amount, res, game_mode, currency)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, datetime.now(), amount, result, game_mode, currency))
            await self.con.commit()

    async def get_game_financial_stats(self, currency: str = None):
        """
        Получает финансовую статистику по играм с корректным расчетом
        :param currency: Если None - все валюты, иначе только указанную
        :return: dict с статистикой
        """
        from other.casino import GAME_COEFFICIENTS
        async with self.con.cursor() as cur:
            # Основной запрос для получения всех нужных данных
            query = '''
                SELECT 
                    SUM(amount) as total_bet,
                    SUM(CASE WHEN res = 'win' THEN amount ELSE 0 END) as win_bets,
                    SUM(CASE WHEN res = 'big_win' THEN amount ELSE 0 END) as big_win_bets,
                    SUM(CASE WHEN res = 'loss' THEN amount ELSE 0 END) as loss_bets,
                    game_mode,
                    currency
                FROM game_history
            '''
            
            params = []
            if currency:
                query += ' WHERE currency = ?'
                params.append(currency)
            
            query += ' GROUP BY game_mode, currency'
            
            await cur.execute(query, params)
            rows = await cur.fetchall()
            
            stats = {
                'total': {
                    'bet': 0,          # Все ставки (win + loss)
                    'win': 0,          # Сумма выигрышей (с коэффициентами)
                    'loss': 0,         # Сумма проигрышных ставок
                    'profit': 0        # Чистая прибыль (win - loss)
                },
                'by_game': {}
            }
            
            for row in rows:
                total_bet, win_bets, big_win_bets, loss_bets, game_mode, curr = row
                
                # Получаем коэффициенты для игры
                coeffs = GAME_COEFFICIENTS.get(game_mode, 1)
                if isinstance(coeffs, dict):
                    normal_coeff = coeffs.get('three_any', coeffs.get('even', 1))
                    big_win_coeff = coeffs.get('three_7', coeffs.get('bullseye', 1))
                else:
                    normal_coeff = big_win_coeff = coeffs
                
                # Рассчитываем выплаты с учетом коэффициентов
                normal_payout = (win_bets or 0) * normal_coeff
                big_win_payout = (big_win_bets or 0) * big_win_coeff
                total_payout = normal_payout + big_win_payout
                
                stats['by_game'][game_mode] = {
                    'bet': total_bet or 0,
                    'win': total_payout,
                    'loss': loss_bets or 0,
                    'profit': total_payout - (loss_bets or 0)
                }
                
                # Обновляем общую статистику
                stats['total']['bet'] += total_bet or 0
                stats['total']['win'] += total_payout
                stats['total']['loss'] += loss_bets or 0
                stats['total']['profit'] += total_payout - (loss_bets or 0)
            
            return stats
                    
    async def update_game_mode_stats(self, user_id: int, game_mode: str, result: str):
        """
        Обновляет статистику по режимам игры.
        game_mode: 'dice', 'basketball', 'football', 'darts', 'casino'
        result: 'win' или 'loss'
        """
        if game_mode not in ('dice', 'basketball', 'football', 'darts', 'casino') or result not in ('win', 'loss'):
            return
            
        async with self.con.cursor() as cur:
            # Обновляем общую статистику побед/поражений
            column = 'game_wins' if result == 'win' else 'game_losses'
            await cur.execute(f'''
                UPDATE all_statics 
                SET {column} = {column} + 1
                WHERE user_id = ?
            ''', (user_id,))
            
            # Обновляем статистику по конкретному режиму игры
            mode_column = f"{game_mode}_played"
            await cur.execute(f'''
                UPDATE all_statics 
                SET {mode_column} = {mode_column} + 1
                WHERE user_id = ?
            ''', (user_id,))
            
            await self.con.commit()


    async def get_user_bet(self, user_id: int) -> int:
        """Получает текущую ставку пользователя"""
        async with self.con.cursor() as cur:
            await cur.execute('''SELECT bet FROM game WHERE user_id = ?''', (user_id,))
            result = await cur.fetchone()
            return result[0] if result else 1  # Возвращаем 1 как ставку по умолчанию

    async def update_user_bet(self, user_id: int, new_bet: int) -> None:
        """Обновляет ставку пользователя"""
        async with self.con.cursor() as cur:
            await cur.execute('''UPDATE game SET bet = ? WHERE user_id = ?''', (new_bet, user_id))
            await self.con.commit()




    async def add_currency_column_if_not_exists(self):
        """Добавляет колонку currency в таблицу game, если её нет"""
        async with self.con.cursor() as cur:
            await cur.execute('''PRAGMA table_info(game)''')
            columns = [column[1] for column in await cur.fetchall()]
            if 'currency' not in columns:
                await cur.execute('''ALTER TABLE game ADD COLUMN currency TEXT DEFAULT 'mico' ''')
                await self.con.commit()

    async def get_user_currency(self, user_id: int) -> str:
        """Возвращает выбранную валюту пользователя (mico/stars)"""
        async with self.con.cursor() as cur:
            await cur.execute('''SELECT currency FROM game WHERE user_id = ?''', (user_id,))
            result = await cur.fetchone()
            return result[0] if result else 'mico'

    async def update_user_currency(self, user_id: int, currency: str) -> None:
        """Обновляет выбранную валюту пользователя"""
        async with self.con.cursor() as cur:
            await cur.execute('''UPDATE game SET currency = ? WHERE user_id = ?''', (currency, user_id))
            await self.con.commit()

    async def get_user_balance_for_game(self, user_id: int) -> float:
        """Возвращает баланс пользователя в выбранной валюте для игры"""
        async with self.con.cursor() as cur:
            currency = await self.get_user_currency(user_id)
            column = 'bal' if currency == 'mico' else 'bal_rub'
            await cur.execute(f'''SELECT {column} FROM game WHERE user_id = ?''', (user_id,))
            result = await cur.fetchone()
            return result[0] if result else 0

    async def update_user_balance_for_game(self, user_id: int, amount: float) -> None:
        """Обновляет баланс пользователя в выбранной для игры валюте"""
        async with self.con.cursor() as cur:
            currency = await self.get_user_currency(user_id)
            column = 'bal' if currency == 'mico' else 'bal_rub'
            await cur.execute(f'''UPDATE game SET {column} = {column} + ? WHERE user_id = ?''', (amount, user_id))
            await self.con.commit()

    async def update_buy_sell_currency(self, buy_sell_currency):
        """Уменьшение количества доступных активаций"""
        async with self.con.cursor() as cur:
            await cur.execute('''
                UPDATE settings SET buy_sell_currency = ?
                WHERE id = 1
            ''', (buy_sell_currency,))
            await self.con.commit()

    async def get_stars_sell_currency(name: str):
        """Получение информации о промокоде"""
        async with DB.con.cursor() as cur:
            await cur.execute('''
                SELECT buy_sell_currency FROM settings WHERE id = 1
            ''')
            return await cur.fetchone()

    async def skip_task(self, user_id: int, task_id: int):
        """Добавляет задание в список пропущенных для пользователя"""
        async with self.con.cursor() as cur:
            await cur.execute('''
                INSERT INTO skeeped_tasks (user_id, task_id)
                VALUES (?, ?)
            ''', (user_id, task_id))
            await self.con.commit()

    async def is_task_skipped(self, user_id: int, task_id: int) -> bool:
        """Проверяет, пропустил ли пользователь это задание"""
        async with self.con.cursor() as cur:
            await cur.execute('''
                SELECT 1 FROM skeeped_tasks 
                WHERE user_id = ? AND task_id = ?
            ''', (user_id, task_id))
            return bool(await cur.fetchone())

    async def add_order(
        self,
        user_id: int,
        order_id: int,
        service_id: int,
        link: str,
        quantity: int,
        cost: float,
        status: str
    ) -> bool:
        """Добавить новый заказ в БД"""
        query = """
        INSERT INTO orders (
            user_id, order_id, service_id, 
            link, quantity, cost, status, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
        """
        try:
            async with self.con.cursor() as cur:
                await cur.execute(
                    query,
                    (user_id, order_id, service_id,
                    link, quantity, cost, status)
                )
                return True
        except Exception as e:
            print(f"Error adding order: {e}")
            return False

    async def get_user_orders(self, user_id: int):
        """Получить заказы пользователя"""
        query = """
        SELECT * FROM orders 
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT 10
        """
        async with self.con.cursor() as cur:
            await cur.execute(query, (user_id,))
            rows = await cur.fetchall()
            if rows:
                # Для SQLite используем такой вариант
                columns = [desc[0] for desc in cur.description]
                return [dict(zip(columns, row)) for row in rows]
            return []

    async def get_order(self, order_id: int):
        """Получить заказ по ID"""
        query = "SELECT * FROM orders WHERE order_id = ?"
        async with self.con.cursor() as cur:
            await cur.execute(query, (order_id,))
            row = await cur.fetchone()
            if row:
                columns = [desc[0] for desc in cur.description]
                return dict(zip(columns, row))
            return None

    async def update_order_status(self, order_id: int, status: str) -> bool:
        """Обновить статус заказа"""
        query = "UPDATE orders SET status = ? WHERE order_id = ?"
        try:
            async with self.con.cursor() as cur:
                await cur.execute(query, (status, order_id))
                return True
        except Exception as e:
            print(f"Error updating order status: {e}")
            return False


    async def increment_daily_completed_task_count(self, user_id: int):
        """Увеличивает счетчик дневных задач на 1 с проверкой сброса"""
        async with self.con.cursor() as cur:
            # Проверяем, нужно ли сбросить счетчик (прошел ли день)
            await cur.execute('''
                UPDATE users 
                SET 
                    dayly_completed_task = CASE 
                        WHEN date(last_daily_reset) < date('now') THEN 1 
                        ELSE dayly_completed_task + 1 
                    END,
                    last_daily_reset = CASE 
                        WHEN date(last_daily_reset) < date('now') THEN datetime('now') 
                        ELSE last_daily_reset 
                    END
                WHERE user_id = ?
            ''', (user_id,))
        await self.con.commit()

    async def increment_weekly_completed_task_count(self, user_id: int):
        """Увеличивает счетчик недельных задач на 1 с проверкой сброса"""
        async with self.con.cursor() as cur:
            # Проверяем, нужно ли сбросить счетчик (прошла ли неделя)
            await cur.execute('''
                UPDATE users 
                SET 
                    weekly_completed_task = CASE 
                        WHEN date(last_weekly_reset) <= date('now', '-7 days') THEN 1 
                        ELSE weekly_completed_task + 1 
                    END,
                    last_weekly_reset = CASE 
                        WHEN date(last_weekly_reset) <= date('now', '-7 days') THEN datetime('now') 
                        ELSE last_weekly_reset 
                    END
                WHERE user_id = ?
            ''', (user_id,))
        await self.con.commit()

    async def reset_daily_tasks_if_needed(self):
        """Сбрасывает дневные задачи, если прошел день"""
        async with self.con.cursor() as cur:
            await cur.execute('''
                UPDATE users 
                SET 
                    dayly_completed_task = 0,
                    last_daily_reset = datetime('now')
                WHERE date(last_daily_reset) < date('now')
            ''')
        await self.con.commit()

    async def reset_weekly_tasks_if_needed(self):
        """Сбрасывает недельные задачи, если прошла неделя"""
        async with self.con.cursor() as cur:
            await cur.execute('''
                UPDATE users 
                SET 
                    weekly_completed_task = 0,
                    last_weekly_reset = datetime('now')
                WHERE date(last_weekly_reset) <= date('now', '-7 days')
            ''')
        await self.con.commit()

    async def reset_daily_completed_task(self):
        async with self.con.cursor() as cur:
            await cur.execute('''
                UPDATE users
                SET dayly_completed_task = 0,
                    last_daily_reset = datetime('now')
            ''')
        await self.con.commit() 

    async def reset_weekly_statistics(self):
        async with self.con.cursor() as cur:
            await cur.execute('''
                UPDATE users
                SET weekly_completed_task = 0,
                    last_weekly_reset = datetime('now')
            ''')
        await self.con.commit()

    async def get_task_counts(self, user_id: int) -> tuple[int, int, str, str]:
        """Возвращает текущие значения счетчиков и даты последнего сброса"""
        async with self.con.cursor() as cur:
            await cur.execute('''
                SELECT 
                    dayly_completed_task, 
                    weekly_completed_task,
                    last_daily_reset,
                    last_weekly_reset
                FROM users 
                WHERE user_id = ?
            ''', (user_id,))
            result = await cur.fetchone()
            return result if result else (0, 0, None, None)

    async def force_reset_daily_tasks(self):
        """Принудительно сбрасывает все дневные задачи"""
        async with self.con.cursor() as cur:
            await cur.execute('''
                UPDATE users 
                SET 
                    dayly_completed_task = 0,
                    last_daily_reset = datetime('now')
            ''')
        await self.con.commit()

    async def force_reset_weekly_tasks(self):
        """Принудительно сбрасывает все недельные задачи"""
        async with self.con.cursor() as cur:
            await cur.execute('''
                UPDATE users 
                SET 
                    weekly_completed_task = 0,
                    last_weekly_reset = datetime('now')
            ''')
        await self.con.commit()



    async def add_bg_task(self, task_type: str, task_data: dict, delay_seconds: int = 0, original_id=None):
        next_run_at = datetime.now() + timedelta(seconds=delay_seconds)
        async with self.con.cursor() as cur:
            import json
            if original_id:
                # Вставляем с конкретным ID
                await cur.execute('''
                    INSERT OR REPLACE INTO background_tasks 
                    (task_id, task_type, task_data, status, next_run_at)
                    VALUES (?, ?, ?, ?, ?)
                ''', (original_id, task_type, json.dumps(task_data), 'pending', next_run_at))
            else:
                await cur.execute('''
                    INSERT INTO background_tasks (task_type, task_data, status, created_at, next_run_at, attempts)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    task_type,
                    json.dumps(task_data),
                    'pending',
                    datetime.now(),
                    next_run_at,
                    0
                ))


    async def get_pending_bg_tasks(self):
        """Получает все задачи, готовые к выполнению"""
        async with self.con.cursor() as cur:
            # Вариант с явным приведением времени
            await cur.execute('''
                SELECT * FROM background_tasks 
                WHERE status IN ('pending', 'failed', 'running')
                AND (
                    datetime(substr(next_run_at, 1, 19)) <= datetime('now', 'localtime')
                    OR 
                    next_run_at <= datetime('now', 'localtime')
                )
                ORDER BY next_run_at ASC
            ''')
            return await cur.fetchall()

    async def restore_background_tasks():
        async with DB.con.cursor() as cur:
            import json
            await cur.execute('SELECT * FROM background_tasks')
            for task in await cur.fetchall():
                task_id, task_data = task[0], json.loads(task[2])
                # Просто обновляем next_run_at и статус
                await cur.execute('''
                    UPDATE background_tasks 
                    SET status='pending', 
                        next_run_at=datetime('now', '+1 hour')
                    WHERE task_id=?
                ''', (task_id,))

                
    async def mark_bg_task_running(self, task_id: int):
        """Помечает задачу как выполняющуюся"""
        async with self.con.cursor() as cur:
            await cur.execute('''
                UPDATE background_tasks 
                SET status = 'running', attempts = attempts + 1
                WHERE task_id = ?
            ''', (task_id,))
            await self.con.commit()

    async def mark_bg_task_completed(self, task_id: int):
        """Помечает задачу как выполненную"""
        async with self.con.cursor() as cur:
            await cur.execute('''
                DELETE FROM background_tasks 
                WHERE task_id = ?
            ''', (task_id,))
            await self.con.commit()

    async def mark_bg_task_failed(self, task_id: int, retry_after: int = 3600):
        """Помечает задачу как невыполненную и планирует повтор"""
        next_run_at = datetime.now() + timedelta(seconds=retry_after)
        async with self.con.cursor() as cur:
            await cur.execute('''
                UPDATE background_tasks 
                SET status = 'failed', next_run_at = ?
                WHERE task_id = ?
            ''', (next_run_at, task_id))
            await self.con.commit()



    async def select_tasks_by_type(self, task_type: int):
        """Получает все задания определенного типа"""
        async with self.con.cursor() as cur:
            await cur.execute('''
                SELECT * FROM tasks 
                WHERE type = ? AND amount > 0
                ORDER BY task_id DESC
            ''', (task_type,))
            return await cur.fetchall()

    async def is_task_completed(self, user_id: int, task_id: int) -> bool:
        """Проверяет, выполнено ли задание пользователем"""
        async with self.con.cursor() as cur:
            await cur.execute('''
                SELECT 1 FROM completed_tasks 
                WHERE user_id = ? AND task_id = ?
            ''', (user_id, task_id))
            return bool(await cur.fetchone())


    async def is_task_skipped(self, user_id: int, task_id: int) -> bool:
        """Проверяет, пропущено ли задание пользователем"""
        async with self.con.cursor() as cur:
            await cur.execute('''
                SELECT 1 FROM skeep_tasks 
                WHERE user_id = ? AND task_id = ?
            ''', (user_id, task_id))
            return bool(await cur.fetchone())

    async def calculate_total_cost(self) -> int:
        """Рассчитывает общую сумму всех доступных заданий"""
        async with self.con.cursor() as cur:
            await cur.execute('''
                SELECT SUM(amount * 
                    CASE 
                        WHEN type = 1 THEN 1500  -- Каналы
                        WHEN type = 2 THEN 1500  -- Чаты
                        WHEN type = 3 THEN 300   -- Посты
                        WHEN type = 4 THEN 1000  -- Комментарии
                        WHEN type = 5 THEN 1000  -- Переходы
                        WHEN type = 6 THEN 500   -- Бусты
                        WHEN type = 7 THEN 500   -- Реакции
                        ELSE 0
                    END)
                FROM tasks
                WHERE amount > 0
            ''')
            result = await cur.fetchone()
            return result[0] or 0

    async def get_filtered_tasks(self, task_type: int, user_id: int):
        """Возвращает задания определенного типа, исключая уже выполненные пользователем"""
        query = '''
            SELECT * FROM tasks 
            WHERE type = ? AND id NOT IN (
                SELECT task_id FROM completed_tasks 
                WHERE user_id = ? AND status = 1
            )
        '''
        return await self.con.execute(query, (task_type, user_id))

    async def select_all_active_tasks(self):
        """Получить все активные задания"""
        async with self.con.cursor() as cur:
            return await cur.fetchall(
                "SELECT * FROM tasks WHERE status = 1 AND amount > 0"
            )

    async def calculate_rewards_for_type(self, task_type: int):
        """Рассчитать общую сумму вознаграждений для типа заданий"""
        async with self.con.cursor() as cur:
            return await cur.fetchall(
                "SELECT COALESCE(SUM(amount * price_per_action), 0) FROM tasks "
                "WHERE type = $1 AND status = 1 AND amount > 0",
                task_type
            )






class Promo:
    async def create(creator_id: int, name: str, amount: float, where_to: str, count: int, days: int):
        """Создание нового промокода"""
        end_time = datetime.now() + timedelta(days=days)
        async with DB.con.cursor() as cur:
            await cur.execute('''
                INSERT INTO promocodes 
                (creator_id, name, amount, where_to, count, all_count, end_time)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (creator_id, name, amount, where_to, count, count, end_time))
            await DB.con.commit()

    async def get(name: str):
        """Получение информации о промокоде"""
        async with DB.con.cursor() as cur:
            await cur.execute('''
                SELECT * FROM promocodes WHERE name = ?
            ''', (name,))
            return await cur.fetchone()

    async def decrease_count(name: str):
        """Уменьшение количества доступных активаций"""
        async with DB.con.cursor() as cur:
            await cur.execute('''
                UPDATE promocodes SET count = count - 1 
                WHERE name = ? AND count > 0
            ''', (name,))
            await DB.con.commit()
            
            # Проверяем остались ли активации
            await cur.execute('''
                SELECT count FROM promocodes WHERE name = ?
            ''', (name,))
            result = await cur.fetchone()
            if result and result[0] <= 0:
                await Promo.delete(name)
                return True  # Промокод закончился
            return False

    async def delete(name: str):
        """Удаление промокода"""
        async with DB.con.cursor() as cur:
            await cur.execute('''
                DELETE FROM promocodes WHERE name = ?
            ''', (name,))
            await DB.con.commit()

    async def check_expired():
        """Удаление просроченных промокодов"""
        async with DB.con.cursor() as cur:
            await cur.execute('''
                DELETE FROM promocodes WHERE end_time < CURRENT_TIMESTAMP
            ''')
            await DB.con.commit()


class Contest:
    @staticmethod
    async def create_contest(channel_url: str, winners_count: int, prizes: str, 
                           start_date: str, end_date: str, conditions: str, 
                           contest_text: str, image_path: str, status: str) -> int:
        async with DB.con.cursor() as cur:
            await cur.execute('''
                INSERT INTO contests 
                (channel_url, winners_count, prizes, start_date, end_date, 
                 conditions, contest_text, image_path, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                channel_url, winners_count, prizes, start_date, end_date,
                conditions, contest_text, image_path, status
            ))
            contest_id = cur.lastrowid
            await DB.con.commit()
            return contest_id

    @staticmethod
    async def get_contest(contest_id: int) -> dict:
        async with DB.con.cursor() as cur:
            await cur.execute('''
                SELECT * FROM contests WHERE id = ?
            ''', (contest_id,))
            return await cur.fetchone()
        
    @classmethod
    async def get_contest2(cls, contest_id: int) -> dict:
        """Получает конкурс по ID"""
        async with DB.con.cursor() as cur:
            await cur.execute('SELECT * FROM contests WHERE id = ?', (contest_id,))
            row = await cur.fetchone()
            if not row:
                return None
            
            # Получаем названия столбцов
            columns = [desc[0] for desc in cur.description]
            
            return dict(zip(columns, row))
        
    @staticmethod
    async def update_contest_message_id(contest_id: int, message_id: int):
        async with DB.con.cursor() as cur:
            await cur.execute('''
                UPDATE contests SET message_id = ? WHERE id = ?
            ''', (message_id, contest_id))
            await DB.con.commit()

    @staticmethod
    async def add_participant(contest_id: int, user_id: int, username: str) -> bool:
        async with DB.con.cursor() as cur:
            try:
                await cur.execute('''
                    INSERT INTO contest_participants (contest_id, user_id, username)
                    VALUES (?, ?, ?)
                ''', (contest_id, user_id, username))
                await DB.con.commit()
                return True
            except:
                return False

    @staticmethod
    async def get_participants_count(contest_id: int) -> int:
        async with DB.con.cursor() as cur:
            await cur.execute('''
                SELECT COUNT(*) FROM contest_participants WHERE contest_id = ?
            ''', (contest_id,))
            return (await cur.fetchone())[0]

    @staticmethod
    async def select_winners(contest_id: int, winners_count: int) -> list:
        async with DB.con.cursor() as cur:
            await cur.execute('''
                SELECT user_id, username FROM contest_participants
                WHERE contest_id = ?
                ORDER BY RANDOM()
                LIMIT ?
            ''', (contest_id, winners_count))
            return await cur.fetchall()

    @staticmethod
    async def add_winner(contest_id: int, user_id: int, place: int, 
                        prize_type: str, prize_amount: float):
        async with DB.con.cursor() as cur:
            await cur.execute('''
                INSERT INTO contest_winners 
                (contest_id, user_id, place, prize_type, prize_amount)
                VALUES (?, ?, ?, ?, ?)
            ''', (contest_id, user_id, place, prize_type, prize_amount))
            await DB.con.commit()

    @staticmethod
    async def update_contest_status(contest_id: int, status: str):
        async with DB.con.cursor() as cur:
            await cur.execute('''
                UPDATE contests SET status = ? WHERE id = ?
            ''', (status, contest_id))
            await DB.con.commit()

    @staticmethod
    async def get_finished_contests() -> list:
        async with DB.con.cursor() as cur:
            await cur.execute('''
                SELECT id FROM contests 
                WHERE status = 'active' AND end_date <= datetime('now')
            ''')
            return [row[0] for row in await cur.fetchall()]
        
    @staticmethod
    async def update_contest_message_id(contest_id: int, message_id: int):
        async with DB.con.cursor() as cur:
            await cur.execute('''
                UPDATE contests SET message_id = ? WHERE id = ?
            ''', (message_id, contest_id))
            await DB.con.commit()
            
    async def update_contest_message_text(contest_id: int, message_id: int):
        async with DB.con.cursor() as cur:
            await cur.execute('''
                UPDATE contests SET message_text = ? WHERE id = ?
            ''', (message_id, contest_id))
            await DB.con.commit()

    @classmethod
    async def get_active_contests_before(cls, date: datetime) -> list[dict]:
        """Получает активные конкурсы с истекшим сроком с учетом часового пояса"""
        from datetime import timezone
        async with DB.con.cursor() as cur:
            await cur.execute('''
                SELECT * FROM contests 
                WHERE status = 'active'
            ''')
            rows = await cur.fetchall()
            columns = [desc[0] for desc in cur.description]
            
            valid_contests = []
            for row in rows:
                contest = dict(zip(columns, row))
                try:
                    # Парсим дату с учетом того, что она в локальном времени
                    end_date = datetime.strptime(contest['end_date'], "%d.%m.%Y %H:%M")
                    # Конвертируем в UTC для сравнения
                    end_date_utc = end_date.replace(tzinfo=timezone.utc)
                    
                    if date.replace(tzinfo=timezone.utc) >= end_date_utc:
                        valid_contests.append(contest)
                except ValueError:
                    continue
                    
            return valid_contests


    async def get_waiting_contests_before(datetime_now) -> list[dict]:
        """Получает активные конкурсы с истекшим сроком"""
        async with DB.con.cursor() as cur:
            await cur.execute('''
                    SELECT * FROM contests WHERE status = 'waiting' AND start_date <= :now
            ''', {"now": datetime_now.strftime("%d.%m.%Y %H:%M")})
            rows = await cur.fetchall()
            
            # Получаем названия столбцов
            columns = [desc[0] for desc in cur.description]
            
            # Преобразуем каждую строку в словарь
            return [dict(zip(columns, row)) for row in rows]     

    async def get_participants(contest_id: int) -> list:
        """Получает список участников конкурса в формате [(user_id, username), ...]"""
        async with DB.con.cursor() as cur:
            await cur.execute('''
                SELECT user_id, username FROM contest_participants
                WHERE contest_id = ?
            ''', (contest_id,))
            return await cur.fetchall()

    @staticmethod
    async def create_recurring_contest(**data) -> int:
        """Создает новый повторяющийся конкурс и возвращает его ID"""
        query = """
        INSERT INTO contests (
            channel_url, winners_count, prizes, start_date, end_date, 
            conditions, contest_text, image_path, status, frequency,
            selected_days, total_occurrences, current_occurrence, start_time
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        try:
            start_time = datetime.strptime(data['start_date'], "%d.%m.%Y %H:%M").strftime("%H:%M")
            selected_days = json.dumps(data.get('selected_days', []))
            
            async with DB.con.cursor() as cur:
                await cur.execute(query, (
                    data['channel_url'], 
                    data['winners_count'], 
                    json.dumps(data['prizes']),
                    data['start_date'], 
                    data['end_date'], 
                    data['conditions'],
                    data.get('contest_text'), 
                    data.get('image_path'), 
                    data['status'],
                    data.get('frequency', 'once'), 
                    selected_days,
                    data.get('total_occurrences', 1), 
                    1,  # current_occurrence
                    start_time
                ))
                await cur.execute("SELECT last_insert_rowid()")
                return (await cur.fetchone())[0]
        except Exception as e:
            print(f"Ошибка при создании конкурса: {e}")
            raise

    @staticmethod
    async def get_active_recurring_contests() -> list:
        """Получает активные повторяющиеся конкурсы"""
        query = """
        SELECT * FROM contests 
        WHERE status = 'recurring' 
        AND current_occurrence < total_occurrences
        """
        async with DB.con.cursor() as cur:
            await cur.execute(query)
            return await cur.fetchall()

    @staticmethod
    async def clone_contest_for_recurring_run(contest_id: int) -> int:
        """Клонирует конкурс для нового запуска и возвращает ID нового конкурса"""
        query = """
        INSERT INTO contests (
            channel_url, winners_count, prizes, start_date, end_date, 
            conditions, contest_text, image_path, status, frequency,
            selected_days, total_occurrences, current_occurrence, start_time,
            parent_contest_id
        )
        SELECT 
            channel_url, winners_count, prizes, 
            date('now') || ' ' || start_time as start_date,
            date('now', '+' || (julianday(end_date) - julianday(start_date)) || ' days') as end_date,
            conditions, contest_text, image_path, 'waiting', frequency,
            selected_days, total_occurrences, current_occurrence, start_time,
            id
        FROM contests WHERE id = ?
        """
        try:
            async with DB.con.cursor() as cur:
                await cur.execute(query, (contest_id,))
                await cur.execute("SELECT last_insert_rowid()")
                return (await cur.fetchone())[0]
        except Exception as e:
            print(f"Ошибка при клонировании конкурса: {e}")
            raise

    @staticmethod
    async def update_recurring_contest_after_run(contest_id: int, current_occurrence: int, last_run: datetime) -> None:
        """Обновляет данные после запуска повторяющегося конкурса"""
        query = """
        UPDATE contests 
        SET current_occurrence = ?, last_run = ?
        WHERE id = ?
        """
        async with DB.con.cursor() as cur:
            await cur.execute(query, (current_occurrence, last_run, contest_id))


class Boost():
    @staticmethod
    async def add_user_boost(user_id: int, chat_id: int, status=False):
        """Добавляет запись о бусте пользователя канала"""
        async with DB.con.cursor() as cur:
            await cur.execute('''
                INSERT INTO user_boosts (user_id, chat_id, reward_given) 
                VALUES (?, ?, ?)
                ON CONFLICT(user_id, chat_id) DO UPDATE SET 
                    date = CURRENT_TIMESTAMP,
                    reward_given = excluded.reward_given
            ''', (user_id, chat_id, status))
        await DB.con.commit()

    @staticmethod
    async def remove_user_boost(user_id: int, chat_id: int):
        """Удаляет запись о бусте, если пользователь убрал его"""
        async with DB.con.cursor() as cur:
            await cur.execute('''
                DELETE FROM user_boosts WHERE user_id = ? AND chat_id = ?
            ''', (user_id, chat_id))
        await DB.con.commit()

    @staticmethod
    async def has_user_boosted(user_id: int, chat_id: int) -> bool:
        """Проверяет, бустил ли пользователь этот канал"""
        async with DB.con.cursor() as cur:
            await cur.execute('''
                SELECT 1 FROM user_boosts WHERE user_id = ? AND chat_id = ?
            ''', (user_id, chat_id))
            result = await cur.fetchone()
            return result is not None
        
    @staticmethod    
    async def mark_boost_reward_given(user_id: int, chat_id: int):
        """Помечает, что награда за буст выдана"""
        async with DB.con.cursor() as cur:
            await cur.execute('''
                UPDATE user_boosts 
                SET reward_given = TRUE
                WHERE user_id = ? AND chat_id = ?
            ''', (user_id, chat_id))
        await DB.con.commit()

    @staticmethod
    async def has_user_boosted_without_reward(user_id: int, chat_id: int) -> bool:
        """Проверяет, есть ли неотмеченный буст пользователя этого канала"""
        async with DB.con.cursor() as cur:
            await cur.execute('''
                SELECT 1 FROM user_boosts 
                WHERE user_id = ? AND chat_id = ? AND reward_given = FALSE
            ''', (user_id, chat_id))
            result = await cur.fetchone()
            return result is not None
        
    async def create_task(user_id: int, target_id: int, amount: int, task_type: int, max_amount: int = None, other: int = 0) -> int:
        """Создает новое задание и возвращает его ID"""
        async with DB.con.cursor() as cur:
            if max_amount is None:
                max_amount = amount
            await cur.execute('''
                INSERT INTO tasks (user_id, target_id, amount, type, max_amount, other, time)
                VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
            ''', (user_id, target_id, amount, task_type, max_amount, other))
            await DB.con.commit()
            return cur.lastrowid

    async def get_task_by_id(task_id: int) -> tuple:
        """Получает задание по его ID"""
        async with DB.con.cursor() as cur:
            await cur.execute('SELECT * FROM tasks WHERE task_id = ?', (task_id,))
            return await cur.fetchone()

    async def get_tasks_by_user(user_id: int) -> list:
        """Получает все задания пользователя"""
        async with DB.con.cursor() as cur:
            await cur.execute('SELECT * FROM tasks WHERE user_id = ? ORDER BY time DESC', (user_id,))
            return await cur.fetchall()

    async def get_active_boost_tasks() -> list:
        """Получает все активные задания на буст (type=6) с незавершенным сроком"""
        async with DB.con.cursor() as cur:
            await cur.execute('''
                SELECT * FROM tasks 
                WHERE type = 6 AND (other > 0 OR amount > 0)
                ORDER BY time DESC
            ''')
            return await cur.fetchall()

    async def update_task_amount(task_id: int, new_amount: int = None) -> bool:
        """Обновляет количество оставшихся выполнений задания"""
        async with DB.con.cursor() as cur:
            if new_amount is not None:
                await cur.execute('UPDATE tasks SET amount = ? WHERE task_id = ?', (new_amount, task_id))
            else:
                await cur.execute('UPDATE tasks SET amount = amount - 1 WHERE task_id = ?', (task_id,))
            await DB.con.commit()
            return cur.rowcount > 0

    async def update_boost_task_days(task_id: int, days_paid: int) -> bool:
        """Обновляет количество оплаченных дней для задания на буст (использует поле other)"""
        async with DB.con.cursor() as cur:
            await cur.execute('UPDATE tasks SET other = ? WHERE task_id = ?', (days_paid, task_id))
            await DB.con.commit()
            return cur.rowcount > 0


    async def get_paid_days_for_boost(task_id: int) -> int:
        """Возвращает количество оплаченных дней для задания на буст (значение из поля other)"""
        async with DB.con.cursor() as cur:
            await cur.execute('SELECT other FROM tasks WHERE task_id = ?', (task_id,))
            result = await cur.fetchone()
            return result[0] if result else 0

    async def select_boost_tasks() -> list:
        """Получает все задания на буст (type=6)"""
        async with DB.con.cursor() as cur:
            await cur.execute('SELECT * FROM tasks WHERE type = 6 ORDER BY time DESC')
            return await cur.fetchall()

    async def get_completed_boost_task(user_id: int, task_id: int) -> tuple:
        """Получает запись о выполненном задании на буст (тип 6)"""
        async with DB.con.cursor() as cur:
            await cur.execute('''
                SELECT ct.* 
                FROM completed_tasks ct
                JOIN tasks t ON ct.task_id = t.task_id
                WHERE ct.user_id = ? 
                AND ct.task_id = ? 
                AND t.type = 6  -- Проверка, что это задание на буст
            ''', (user_id, task_id))
            return await cur.fetchone()

    async def update_completed_task_days(user_id: int, task_id: int, days: int) -> bool:
        """Обновляет счетчик дней в выполненном задании (использует поле other)"""
        async with DB.con.cursor() as cur:
            await cur.execute('''
                UPDATE completed_tasks 
                SET other = ?
                WHERE user_id = ? AND task_id = ? AND task_type = 6
            ''', (days, user_id, task_id))
            await DB.con.commit()
            return cur.rowcount > 0

    async def get_boosters_for_task(task_id: int) -> list:
        """Получает список исполнителей для задания на буст"""
        async with DB.con.cursor() as cur:
            await cur.execute('''
                SELECT user_id FROM completed_tasks 
                WHERE task_id = ? AND task_type = 6
            ''', (task_id,))
            return await cur.fetchall()
        

DB = DataBase()
