import aiosqlite
from datetime import datetime, timedelta


class DataBase:
    def __init__(self):
        self.con = None

    async def create(self):
        self.con = await aiosqlite.connect('/data/users.db')
        async with self.con.cursor() as cur:
            await cur.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    balance INTEGER DEFAULT 0,
                    referrer_id INTEGER DEFAULT NULL
                )
            ''')
            await cur.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    task_id INTEGER PRIMARY KEY NOT NULL, 
                    user_id INTEGER,
                    target_id INTEGER,
                    amount INTEGER,
                    type INTEGER
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
                    task_id INTEGER
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
                    user_id INTEGER NOT NULL
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
                    description TEXT,
                    locked_for_user INTEGER,
                    password TEXT,
                    OP_id TEXT
                )
            ''')
            await cur.execute('''
                CREATE TABLE IF NOT EXISTS activated_checks (
                    user_id INTEGER,
                    uid TEXT
                )
            ''')
            await self.con.commit()

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

    async def create_check(self, uid, user_id, type, sum, amount):
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
                INSERT INTO checks (uid, user_id, type, sum, amount)
                VALUES (?, ?, ?, ?, ?)
            ''', (uid, user_id, type, sum, amount))
            await self.con.commit()

    async def update_check(self, check_id, amount=None, description=None, locked_for_user=None, password=None, OP_id=None):
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
            except:
                return None

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

    async def add_report(self, task_id, chat_id, user_id):
        async with self.con.cursor() as cur:
            await cur.execute('SELECT 1 FROM task_reports WHERE chat_id = ?', (chat_id,))
            if await cur.fetchone() is None:
                await cur.execute('INSERT INTO task_reports (task_id, chat_id, user_id) VALUES (?, ?, ?)',
                                  (task_id, chat_id, user_id))
                await self.con.commit()
                return True

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
                INSERT INTO tasks (task_id, user_id, target_id, amount, type)
                VALUES (?, ?, ?, ?, ?)
            ''', (new_task_id, user_id, target_id, amount, task_type))

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

    async def get_tasks_by_user_admin(self, user_id):
        """Метод для получения всех задач из базы данных для конкретного user_id"""
        async with self.con.cursor() as cur:
            await cur.execute('SELECT task_id, type FROM tasks WHERE user_id = ?', (user_id,))
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

    async def add_completed_task(self, user_id, task_id):
        """Добавление выполненного задания в базу"""
        async with self.con.cursor() as cur:
            await cur.execute(
                'INSERT INTO completed_tasks (user_id, task_id) VALUES (?, ?)',
                (user_id, task_id)
            )
            await self.con.commit()

            referrer_id = await self.get_referrer_id(user_id)
            task = await self.get_task_by_id(task_id)
            task_type = task[4]
            if referrer_id:
                bonus = await self.get_tasks_bonus(task_type)
                await self.add_balance(user_id=referrer_id, amount=bonus)
                await self.record_referral_earnings(referrer_id, user_id, bonus)

    async def get_tasks_bonus(self, task_type):
        # Здесь определите бонусы для каждого уровня грузовиков
        bonuses = {1: 150, 2: 225, 3: 15}
        return bonuses.get(task_type, 0)

    async def update_task_amount(self, task_id):
        """Обновление количества (amount) в задании"""
        async with self.con.cursor() as cur:
            await cur.execute('UPDATE tasks SET amount = amount - 1 WHERE task_id = ?', (task_id,))
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
        async with self.con.cursor() as cur:
            await cur.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
            return await cur.fetchone()

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
                    'referrer_id': row[3]
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


DB = DataBase()
