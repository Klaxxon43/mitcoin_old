# db.py
import sqlite3
import os
from pathlib import Path

# Создаем папку для БД, если ее нет
db_dir = Path('data')
db_dir.mkdir(exist_ok=True)
db_path = db_dir / 'local.db'

# Подключаемся к БД
locCon = sqlite3.connect(db_path, check_same_thread=False)
locCur = locCon.cursor()

# Создаем таблицы, если их нет
def init_db():
    locCur.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        wallet TEXT DEFAULT 'none'
    )''')
    
    locCur.execute('''
    CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        value TEXT,
        comment TEXT UNIQUE,
        status TEXT DEFAULT 'pending',
        air_type TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )''')
    
    locCon.commit()

init_db()

def check_user(user_id, username, first_name):
    locCur.execute('SELECT id FROM users WHERE id = ?', (user_id,))
    if locCur.fetchone() is None:
        locCur.execute('INSERT INTO users (id, username, first_name) VALUES (?, ?, ?)',
                      (user_id, username, first_name))
        locCon.commit()
        return False
    return True

def save_pending_payment(user_id, amount, comment_code):
    locCur.execute('''
    INSERT INTO payments (user_id, value, comment, status)
    VALUES (?, ?, ?, 'pending')
    ''', (user_id, amount, comment_code))
    locCon.commit()

def update_payment_status(comment_code, status):
    locCur.execute('''
    UPDATE payments SET status = ? WHERE comment = ?
    ''', (status, comment_code))
    locCon.commit()

def get_user_payments(user_id):
    locCur.execute('''
    SELECT value, comment, status FROM payments WHERE user_id = ? ORDER BY created_at DESC
    ''', (user_id,))
    result = locCur.fetchall()
    
    payments = []
    for row in result:
        payments.append({
            'value': row[0],
            'comment': row[1],
            'status': row[2]
        })
    return payments