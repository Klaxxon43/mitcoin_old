import aiosqlite
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

        async with self.con.cursor() as cur:
            await cur.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    balance INTEGER DEFAULT 0,
                    referrer_id INTEGER DEFAULT NULL,
                    rub_balance INTEGER DEFAULT 0,
                    premium STRING DEFAULT FALSE,
                    registration_time TIMESTAMP,
                    stars INTEGER DEFAULT 0,
                    max_stars INTEGER DEFAULT 0,
                    dayly_completed_task INTEGER DEFAULT 0,
                    weekly_completed_task INTEGER DEFAULT 0,
                    last_daily_reset TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_weekly_reset TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            await cur.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    task_id INTEGER PRIMARY KEY NOT NULL, 
                    user_id INTEGER,
                    target_id INTEGER,
                    amount INTEGER,
                    type INTEGER,
                    max_amount INTEGER,
                    other INTEGER DEFAULT 0,
                    time TIMESTAMP DEFAULT None,
                    status INTEGER DEFAULT 1 
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
                CREATE TABLE IF NOT EXISTS skeeped_tasks (
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
                    description TEXT,
                    locked_for_user INTEGER,
                    password TEXT,
                    OP_id TEXT,
                    max_amount INTEGER NOT NULL,
                    ref_bonus INTEGER,
                    ref_fund INTEGER,
                    OP_name TEXT DEFAULT NULL
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
                    users INTEGER DEFAULT 0,
                    gift TEXT DEFAULT '0',
                    gifts INTEGER DEFAULT 0,
                    boosts INTEGER DEFAULT 0,
                    likes INTEGER DEFAULT 0,
                    links INTEGER DEFAULT 0,
                    comments INTEGER DEFAULT 0,
                    mined INTEGER DEFAULT 0,
                    game_wins INTEGER DEFAULT 0,
                    game_losses INTEGER DEFAULT 0,
                    dice_played INTEGER DEFAULT 0,
                    basketball_played INTEGER DEFAULT 0,
                    football_played INTEGER DEFAULT 0,
                    darts_played INTEGER DEFAULT 0,
                    casino_played INTEGER DEFAULT 0,
                    withdraw_from_game INTEGER DEFAULT 0
                )
            ''') 


            await cur.execute('''
                INSERT OR IGNORE INTO all_statics (user_id, all_subs_chanel, all_subs_groups, all_taasks, all_see, users, gifts, boosts, likes)
                VALUES (1, 0, 0, 0, 0, 0, 0, 0, 0), (2, 0, 0, 0, 0, 0, 0, 0, 0)
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
                

            await cur.execute('''
                CREATE TABLE IF NOT EXISTS OP_start (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id TEXT NOT NULL UNIQUE,
                channel_name TEXT NOT NULL
                )
            ''')

            await cur.execute("""
                CREATE TABLE IF NOT EXISTS transaction_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                amount REAL NOT NULL,
                description TEXT NOT NULL,
                additional_info TEXT 
                )
            """)

            await cur.execute("""
                CREATE TABLE IF NOT EXISTS pending_reaction_tasks (
                pending_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                task_id INTEGER NOT NULL,
                target_id TEXT NOT NULL,
                post_id INTEGER NOT NULL,
                reaction TEXT,
                screenshot TEXT,
                status INTEGER DEFAULT 0 
                )
            """) # status -- 0: ожидает подтверждения, 1: подтверждено, 2: отклонено

            await cur.execute("""
                CREATE TABLE IF NOT EXISTS failed_tasks (
                user_id INTEGER NOT NULL,  -- ID пользователя, который провалил задание
                task_id INTEGER NOT NULL  -- ID задания, которое провалено
                )
            """)


            await cur.execute("""
                CREATE TABLE IF NOT EXISTS skeep_tasks (
                user_id INTEGER NOT NULL,  -- ID пользователя, который пропустил задание
                task_id INTEGER NOT NULL  -- ID задания, которое пропущено
                )
            """)

            await cur.execute("""
                CREATE TABLE IF NOT EXISTS mining (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    deposit INTEGER DEFAULT 0,
                    time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    earning INTEGER DEFAULT 0,
                    reminder_sent BOOLEAN DEFAULT FALSE 
                )
            """)

            await cur.execute("""
                CREATE TABLE IF NOT EXISTS referral_relations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    referrer_id INTEGER,  -- ID пользователя, который пригласил
                    referred_id INTEGER,  -- ID пользователя, который был приглашен
                    level INTEGER,        -- Уровень реферала (1, 2, 3, 4, 5)
                    FOREIGN KEY (referrer_id) REFERENCES users(user_id),
                    FOREIGN KEY (referred_id) REFERENCES users(user_id)
                );
            """)

            await cur.execute("""
                CREATE TABLE IF NOT EXISTS referral_earnings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,      -- ID пользователя, который получил награду
                    referrer_id INTEGER,  -- ID пользователя, который пригласил
                    referred_id INTEGER,  -- ID пользователя, который был приглашен
                    level INTEGER,        -- Уровень реферала (1, 2, 3, 4, 5)
                    amount INTEGER,       -- Сумма начисления
                    timestamp TIMESTAMP,  -- Время начисления
                    FOREIGN KEY (user_id) REFERENCES users(user_id),
                    FOREIGN KEY (referrer_id) REFERENCES users(user_id),
                    FOREIGN KEY (referred_id) REFERENCES users(user_id)
                );
            """)

            # await cur.execute("""
            #     CREATE TABLE IF NOT EXISTS constants (
            #         MINING_RATE_PER_HOUR INTEGER DEFAULT 100,
            #         MAX_MINING_HOURS INTEGER DEFAULT 2,
            #         MIN_MINIG_TIME_MINUTES INTEGER DEFAULT 5
            #     );
            # """)
            await cur.execute("""
                CREATE TABLE IF NOT EXISTS statics_history (
                    day INTEGER PRIMARY KEY AUTOINCREMENT,
                    add_users INTEGER DEFAULT 0,
                    all_subs_chanel INTEGER DEFAULT 0,
                    all_subs_groups INTEGER DEFAULT 0,
                    all_tasks INTEGER DEFAULT 0,
                    all_see INTEGER DEFAULT 0,
                    gift INTEGER DEFAULT 0,
                    boosts INTEGER DEFAULT 0,
                    likes INTEGER DEFAULT 0,
                    links INTEGER DEFAULT 0,
                    comments INTEGER DEFAULT 0,
                    mined INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)




            # Таблица game
            await cur.execute('''
                CREATE TABLE IF NOT EXISTS game (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    bal INTEGER DEFAULT 0,
                    bal_rub INTEGER DEFAULT 0,
                    prem_bonus REAL DEFAULT 0,
                    bets_count INTEGER DEFAULT 0,
                    bets_won INTEGER DEFAULT 0,
                    bets_lost INTEGER DEFAULT 0,
                    bet INTEGER DEFAULT 1,
                    currency TEXT DEFAULT 'mico'
                )
            ''')
            
            # Таблица game_history
            await cur.execute('''
                CREATE TABLE IF NOT EXISTS game_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    date TIMESTAMP,
                    amount REAL,
                    res TEXT,
                    game_mode TEXT,
                    currency TEXT DEFAULT 'mico',
                    FOREIGN KEY(user_id) REFERENCES game(user_id)
                )
            ''') 

            await cur.execute('''
                CREATE TABLE IF NOT EXISTS promocodes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    creator_id INTEGER,
                    name TEXT UNIQUE,
                    amount REAL,
                    where_to TEXT,
                    count INTEGER,
                    all_count INTEGER,
                    created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    end_time TIMESTAMP,
                    FOREIGN KEY(creator_id) REFERENCES users(user_id)
                )
            ''')
            await cur.execute('''
                CREATE TABLE IF NOT EXISTS activated_promocodes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    promocode_id INTEGER,
                    activation_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES users(user_id),
                    FOREIGN KEY(promocode_id) REFERENCES promocodes(id)
                )
            ''')
            await cur.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    buy_sell_currency INTEGER DEFAULT 0.02
                )
            ''')

            await cur.execute('''
                INSERT OR IGNORE INTO settings (id, buy_sell_currency)
                VALUES (1, 0.2 )
            ''') 

            await cur.execute('''
                CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                order_id INTEGER NOT NULL UNIQUE,
                service_id INTEGER NOT NULL,
                link TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                cost REAL NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')

            await cur.execute('''
                CREATE TABLE IF NOT EXISTS contests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    channel_url TEXT NOT NULL,
                    winners_count INTEGER NOT NULL,
                    prizes TEXT NOT NULL,  -- JSON формата {place: {"type": "MICO", "amount": 100}}
                    start_date TEXT,
                    end_date TEXT NOT NULL,
                    conditions TEXT NOT NULL,  -- JSON список условий
                    contest_text TEXT,
                    image_path TEXT,
                    status TEXT NOT NULL,  -- waiting, active, finished, recurring
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    message_id INTEGER,
                    message_text TEXT,
                    -- Поля для регулярных конкурсов
                    frequency TEXT,  -- once, daily, weekly
                    selected_days TEXT,  -- JSON массив дней недели [1,3,5] (1-Пн, 7-Вс)
                    total_occurrences INTEGER DEFAULT 1,
                    current_occurrence INTEGER DEFAULT 1,
                    start_time TEXT,  -- Время начала в формате "HH:MM"
                    last_run TEXT,  -- Дата последнего запуска
                    parent_contest_id INTEGER  -- ID родительского конкурса для клонов
                )
            ''')

            await cur.execute('''
                CREATE TABLE IF NOT EXISTS contest_participants (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    contest_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    username TEXT,
                    join_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (contest_id) REFERENCES contests (id),
                    UNIQUE(contest_id, user_id)
                )
            ''')

            await cur.execute('''
                CREATE TABLE IF NOT EXISTS contest_winners (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    contest_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    place INTEGER NOT NULL,
                    prize_type TEXT NOT NULL,
                    prize_amount REAL NOT NULL,
                    awarded BOOLEAN DEFAULT FALSE,
                    FOREIGN KEY (contest_id) REFERENCES contests (id),
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')

            await cur.execute('''
                CREATE TABLE IF NOT EXISTS user_boosts (
                    user_id INTEGER,
                    chat_id INTEGER,
                    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    reward_given BOOLEAN DEFAULT FALSE  -- Новая колонка для отметки о выдаче награды
                )
            ''')

            await cur.execute('''
                CREATE TABLE IF NOT EXISTS background_tasks (
                    task_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_type TEXT NOT NULL,
                    task_data TEXT NOT NULL,  -- Will store JSON
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    next_run_at TIMESTAMP,
                    attempts INTEGER DEFAULT 0
                )
            ''')


            await cur.execute('''
                CREATE INDEX IF NOT EXISTS idx_completed_tasks_user_task 
                ON completed_tasks(user_id, task_id)
            ''')
            await cur.execute('''
                CREATE INDEX IF NOT EXISTS idx_failed_tasks_user_task 
                ON failed_tasks(user_id, task_id)
            ''')
            await cur.execute('''
                CREATE INDEX IF NOT EXISTS idx_pending_tasks_user_task 
                ON pending_reaction_tasks(user_id, task_id)
            ''')
            await cur.execute('''
                CREATE INDEX IF NOT EXISTS idx_skeep_tasks_user_task 
                ON skeep_tasks(user_id, task_id)
            ''')
            await cur.execute('''
                CREATE INDEX IF NOT EXISTS idx_tasks_type_amount 
                ON tasks(type, amount)
            ''')
                

            await cur.execute('''
                CREATE TABLE IF NOT EXISTS break (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    status INTEGER DEFAULT 0
                )
            ''')
            
            await cur.execute('''
                INSERT OR IGNORE INTO break (id, status)
                VALUES (1, 1)
            ''') 
            await self.con.commit()



DB = DataBase()
