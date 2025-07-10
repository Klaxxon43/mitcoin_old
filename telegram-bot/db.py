import sqlite3, datetime, pytz

locCon = sqlite3.connect('local.db', check_same_thread=False)
cur = locCon.cursor()

cur.execute('''CREATE TABLE IF NOT EXISTS transactions (
  source VARCHAR(48) NOT NULL,
  hash VARCHAR(50) UNIQUE NOT NULL,
  value INTEGER NOT NULL,
  comment VARCHAR(50)
)''')
locCon.commit()

cur.execute('''CREATE TABLE IF NOT EXISTS users (
  id INTEGER UNIQUE NOT NULL,
  username VARCHAR(33),
  first_name VARCHAR(300),
  wallet VARCHAR(50) DEFAULT 'none'
)''')
locCon.commit()

def add_v_transaction(source, hash, value, comment):
    cur.execute("INSERT INTO transactions (source, hash, value, comment) VALUES (?, ?, ?, ?)",
                (source, hash, value, comment))
    locCon.commit()

def check_transaction(hash):
    cur.execute(f"SELECT hash FROM transactions WHERE hash = '{hash}'")
    return bool(cur.fetchone())

def check_user(user_id, username, first_name):
    cur.execute(f"SELECT id FROM users WHERE id = '{user_id}'")
    exists = cur.fetchone()
    if not exists:
        cur.execute("INSERT INTO users (id, username, first_name) VALUES (?, ?, ?)",
                    (user_id, username, first_name))
        locCon.commit()
        return False
    return True

def v_wallet(user_id, wallet):
    cur.execute(f"SELECT wallet FROM users WHERE id = '{user_id}'")
    res = cur.fetchone()
    if res and res[0] == "none":
        cur.execute(f"UPDATE users SET wallet = '{wallet}' WHERE id = '{user_id}'")
        locCon.commit()
        return True
    return res[0] if res else False

def get_user_wallet(user_id):
    cur.execute(f"SELECT wallet FROM users WHERE id = '{user_id}'")
    return cur.fetchone()[0]

def get_user_payments(user_id):
    wallet = get_user_wallet(user_id)
    if wallet == "none":
        return "You have no wallet"
    cur.execute(f"SELECT * FROM transactions WHERE source = '{wallet}'")
    return [{"value": r[2], "comment": r[3]} for r in cur.fetchall()]
