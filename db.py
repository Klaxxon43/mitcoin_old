import aiosqlite
from datetime import datetime
import pytz
from aiocron import crontab
import asyncio
MOSCOW_TZ = pytz.timezone("Europe/Moscow")

class DataBase:
    def __init__(self):
        self.con = None
        # self.pool = pool 


    async def create(self):
        self.con = await aiosqlite.connect('users.db')
        
        if self.con is None:  # Избегайте повторной инициализации
            self.con = await aiosqlite.connect('users.db')
        print('бд подключена')

        async with self.con.cursor() as cur:
            await cur.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    balance INTEGER DEFAULT 0,
                    referrer_id INTEGER DEFAULT NULL,
                    rub_balance INTEGER DEFAULT 0
                )
            ''')
            await cur.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    task_id INTEGER PRIMARY KEY NOT NULL, 
                    user_id INTEGER,
                    target_id INTEGER,
                    amount INTEGER,
                    type INTEGER,
                    max_amount INTEGER
                )
            ''')
            await cur.execute('''
                CREATE TABLE IF NOT EXISTS deposit (
                    deposit_id INTEGER PRIMARY KEY,
                    user_id INTEGER,
                    amount INTEGER
                )
            ''')
            await cur.execute('''
                CREATE TABLE IF NOT EXISTS completed_tasks (
                    user_id INTEGER,
                    task_id INTEGER,
                    target_id INTEGER DEFAULT NULL,
                    task_sum INTEGER DEFAULT NULL,
                    owner_id INTEGER DEFAULT NULL,
                    status INTEGER DEFAULT 1,
                    rem_days INTEGER DEFAULT 7,
                    id INTEGER PRIMARY KEY NOT NULL
                )
            ''')

            await cur.execute('''
                CREATE TABLE IF NOT EXISTS chating_tasks (
                    task_id INTEGER PRIMARY KEY NOT NULL,
                    chat_id INTEGER,
                    price INTEGER
                )
            ''')
            await cur.execute('''
                CREATE TABLE IF NOT EXISTS op_pr (
                    task_id INTEGER PRIMARY KEY NOT NULL,
                    target_id TEXT NOT NULL,
                    text TEXT NOT NULL
                )
            ''')
            await cur.execute('''
                CREATE TABLE IF NOT EXISTS referral_stats (
                    user_id INTEGER,
                    referred_user_id INTEGER,
                    earned_from_referrals INTEGER DEFAULT 0
                )
            ''')
            await cur.execute('''
                CREATE TABLE IF NOT EXISTS mandatory_subscriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER NOT NULL,
                    channel_id TEXT NOT NULL,
                    expiration_time TIMESTAMP
                )
            ''')
            await cur.execute('''
                CREATE TABLE IF NOT EXISTS task_reports (
                    report_id INTEGER PRIMARY KEY NOT NULL,
                    task_id INTEGER NOT NULL,
                    chat_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    description TEXT
                )
            ''')
            await cur.execute('''
                CREATE TABLE IF NOT EXISTS checks (
                    check_id INTEGER PRIMARY KEY NOT NULL,
                    uid TEXT,
                    user_id INTEGER NOT NULL,
                    type INTEGER,
                    sum INTEGER NOT NULL,
                    amount INTEGER NOT NULL,
                    max_amount INTEGER NOT NULL,
                    description TEXT,
                    locked_for_user INTEGER,
                    password TEXT,
                    OP_id TEXT,
                    ref_bonus INTEGER,
                    ref_fund INTEGER
                )
            ''')

            await cur.execute('''
                CREATE TABLE IF NOT EXISTS activated_checks (
                    user_id INTEGER,
                    uid TEXT
                )
            ''')
            await cur.execute('''
                CREATE TABLE IF NOT EXISTS conversions (
                    user_id INTEGER PRIMARY KEY,
                    last_conversion_date TEXT
                )
            ''')
            await cur.execute('''
                CREATE TABLE IF NOT EXISTS output (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    wallet TEXT,
                    amount REAL,
                    type INTEGER 
                )
            ''')

            await cur.execute('''
                CREATE TABLE IF NOT EXISTS bonus (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    target_id TEXT NOT NULL,
                    link TEXT NOT NULL
                )
            ''')
            await cur.execute('''
                CREATE TABLE IF NOT EXISTS bonus_time (
                    user_id INTEGER PRIMARY KEY UNIQUE,
                    last_bonus_date TEXT
                )
            ''')
            await cur.execute('''
                CREATE TABLE IF NOT EXISTS all_statics (
                    user_id INTEGER PRIMARY KEY,
                    all_subs_chanel INTEGER DEFAULT 0,
                    all_subs_groups INTEGER DEFAULT 0,
                    all_taasks INTEGER DEFAULT 0,
                    all_see INTEGER DEFAULT 0,
                    users INTEGER DEFAULT 0
                )
            ''')


            await cur.execute('''
                INSERT OR IGNORE INTO all_statics (user_id, all_subs_chanel, all_subs_groups, all_taasks, all_see, users)
                VALUES (1, 0, 0, 0, 0, 0), (2, 0, 0, 0, 0, 0)
            ''')

            await cur.execute("""CREATE TABLE IF NOT EXISTS check_referrals (
                id SERIAL PRIMARY KEY,  
                check_id INT NOT NULL, 
                referrer_id BIGINT NOT NULL,  
                referral_link TEXT NOT NULL, 
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP 
            )
        """)
            
            await cur.execute('''
                PRAGMA table_info(completed_tasks)
            ''')
            columns = [info[1] for info in await cur.fetchall()]
            if 'target_id' not in columns:
                await cur.execute('''
                    ALTER TABLE completed_tasks ADD COLUMN target_id INTEGER DEFAULT NULL
                ''')
            if 'task_sum' not in columns:
                await cur.execute('''
                     ALTER TABLE completed_tasks ADD COLUMN task_sum INTEGER DEFAULT NULL
                 ''')
            if 'owner_id' not in columns:
                await cur.execute('''
                     ALTER TABLE completed_tasks ADD COLUMN owner_id INTEGER DEFAULT NULL
                 ''')
            if 'status' not in columns:
                await cur.execute('''
                     ALTER TABLE completed_tasks ADD COLUMN status INTEGER DEFAULT 1
                 ''')
            if 'rem_days' not in columns:
                await cur.execute('''
                     ALTER TABLE completed_tasks ADD COLUMN rem_days INTEGER DEFAULT 7
                 ''')


            
            await self.con.commit()


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





    async def is_task_completed_check(self, user_id, task_id):
        """Проверка, выполнено ли задание пользователем"""
        async with self.con.cursor() as cur:
            await cur.execute(
                'SELECT * FROM completed_tasks WHERE user_id = ? AND task_id = ?',
                (user_id, task_id)
            )
            return await cur.fetchone() is not None
        
    async def add_completed_task(self, user_id, task_id, target_id, task_sum, owner_id, status):
        """Добавление выполненного задания в базу"""
        async with self.con.cursor() as cur:
            await cur.execute(
                'INSERT INTO completed_tasks (user_id, task_id, target_id, task_sum, owner_id, status) VALUES (?, ?, ?, ?, ?, ?)',
                (user_id, task_id, target_id, task_sum, owner_id, status)
            )
            await self.con.commit()

            referrer_id = await self.get_referrer_id(user_id)
            task = await self.get_task_by_id(task_id)
            task_type = task[4]
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
        connection = await self.connect()  # Явно ожидаем результат корутины
        async with connection.execute(
                "SELECT last_bonus_date FROM bonus_time WHERE user_id = ?",
                (user_id,),
        ) as cursor:
            row = await cursor.fetchone()
            return row["last_bonus_date"] if row else None

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



    #ЕЖЕДНЕВНАЯ ОБЩАЯ СТАТИСТИКА
    async def reset_daily_statistics(self):
        async with self.con.cursor() as cur:
            # Обнуление статистики для user_id = 2 
            await cur.execute('''
            UPDATE all_statics
            SET all_subs_chanel = 0, all_subs_groups = 0, all_taasks = 0, all_see = 0
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




    async def all_balance(self):
        try:
            from config import ADMINS_ID
            print(f"ADMINS_ID: {ADMINS_ID}")
            async with self.con.cursor() as cur:
                query = """
                SELECT SUM(balance)
                FROM users
                WHERE user_id NOT IN (:id1, :id2, :id3, :id4);
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

    async def create_check(self, uid, user_id, type, sum, amount, ref_bonus, ref_fund):
        """
        Создает новый чек с обязательными параметрами.

        :param cur: курсор базы данных.
        :param uid: уникальный идентификатор чека.
        :param user_id: ID пользователя, который создает чек.
        :param type: тип чека (1 - сингл, 2 - мульти).
        :param amount: количество активаций (для сингл-чека = 1).
        """
        async with self.con.cursor() as cur:
            await cur.execute('''
                INSERT INTO checks (uid, user_id, type, sum, amount, max_amount, ref_bonus, ref_fund)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (uid, user_id, type, sum, amount, amount, ref_bonus, ref_fund, ))
            await self.con.commit()

    async def update_check(self, check_id, amount=None, description=None, locked_for_user=None, password=None,
                           OP_id=None):
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
        task_prices = {1: 200, 2: 3000, 3: 300}

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

    async def add_task(self, user_id, target_id, amount, task_type):
        """Метод для добавления новой задачи с инкрементом task_id"""
        async with self.con.cursor() as cur:
            await cur.execute('SELECT MAX(task_id) FROM tasks')
            max_task_id_result = await cur.fetchone()

            # Извлекаем максимальный task_id из результата
            max_task_id = max_task_id_result[0] if max_task_id_result else None

            # Если записей в таблице нет, начнем с task_id = 1
            new_task_id = 1 if max_task_id is None else max_task_id + 1

            # Вставляем новую задачу с инкрементированным task_id
            await cur.execute('''
                INSERT INTO tasks (task_id, user_id, target_id, amount, type, max_amount)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (new_task_id, user_id, target_id, amount, task_type, amount,))

            # Сохраняем изменения в базе данных
            await self.con.commit()

    async def get_tasks(self):
        """Метод для получения всех задач из базы данных"""
        async with self.con.cursor() as cur:
            await cur.execute('SELECT * FROM tasks')
            return await cur.fetchall()

    async def get_tasks_by_user(self, user_id):
        """Метод для получения всех задач из базы данных для конкретного user_id"""
        async with self.con.cursor() as cur:
            await cur.execute('SELECT * FROM tasks WHERE user_id = ?', (user_id,))
            return await cur.fetchall()

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
            await cur.execute('SELECT type FROM tasks')
            tasks = await cur.fetchall()

            total_cost = 0
            prices = {1: 1500, 2: 1500, 3: 250}

            # Считаем количество заданий для каждого типа
            task_count = {}
            for task_type in tasks:
                task_count[task_type[0]] = task_count.get(task_type[0], 0) + 1

            # Теперь для каждого типа заданий умножаем количество на цену
            for task_type, count in task_count.items():
                price_per_item = prices.get(task_type, 0)
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

    async def add_deposit(self, user_id, amount):
        async with self.con.cursor() as cur:
            await cur.execute(
                'INSERT INTO deposit (user_id, amount) VALUES (?, ?)',
                (user_id, amount)
            )
            await self.con.commit()

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




    # БАЛАНС

    async def get_user_balance(self, user_id):
        connection = await self.connect()  # Явно ожидаем результат корутины
        async with connection.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row['balance'] if row else 0  # Возвращаем баланс или 0, если записи нет

    async def add_balance(self, user_id, amount):
        async with self.con.cursor() as cur:
            await cur.execute(
                'UPDATE users SET balance = balance + ? WHERE user_id = ?',
                (amount, user_id)
            )
            await self.con.commit()

    async def update_balance(self, user_id, balance):
        async with self.con.cursor() as cur:
            await cur.execute(
                'UPDATE users SET balance = ? WHERE user_id = ?',
                (balance, user_id)
            )
            await self.con.commit()



    # РУБ БАЛАНС

    async def get_user_rub_balance(self, user_id):
        connection = await self.connect()  # Явно ожидаем результат корутины
        async with connection.execute('SELECT rub_balance FROM users WHERE user_id = ?', (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row['rub_balance'] if row else 0  # Возвращаем баланс или 0, если записи нет

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
                    'rub_balance': row[4]
                }
            else:
                return None

    async def add_user(self, user_id, username):
        async with self.con.cursor() as cur:
            await cur.execute('''
                INSERT OR IGNORE INTO users (user_id, username)
                VALUES (?, ?)
            ''', (user_id, username))
            await self.con.commit()

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

import aiosqlite






DB = DataBase()
