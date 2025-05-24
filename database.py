import sqlite3
from contextlib import contextmanager

DATABASE_NAME = 'inventory.db'

def init_db():
    with get_db() as db:
        db.execute('''
            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_name TEXT NOT NULL,
                price REAL NOT NULL
            )
        ''')

@contextmanager
def get_db():
    conn = sqlite3.connect(DATABASE_NAME)
    try:
        yield conn
    finally:
        conn.commit()
        conn.close()

def add_item(item_name, price):
    with get_db() as db:
        db.execute('INSERT INTO inventory (item_name, price) VALUES (?, ?)',
                  (item_name, price))

def update_item_price(item_name, new_price):
    with get_db() as db:
        db.execute('UPDATE inventory SET price = ? WHERE item_name = ?',
                  (new_price, item_name))

def update_item_name(old_name, new_name):
    with get_db() as db:
        db.execute('UPDATE inventory SET item_name = ? WHERE item_name = ?',
                  (new_name, old_name))

def delete_item(item_name):
    with get_db() as db:
        db.execute('DELETE FROM inventory WHERE item_name = ?', (item_name,))

def get_all_items():
    with get_db() as db:
        cursor = db.execute('SELECT item_name, price FROM inventory ORDER BY item_name')
        return cursor.fetchall()

# Initialize the database when the module is imported
init_db() 