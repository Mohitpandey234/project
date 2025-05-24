import sqlite3
from contextlib import contextmanager
from datetime import datetime
import hashlib
import json

DATABASE_NAME = 'inventory.db'

def init_db():
    with get_db() as db:
        # Inventory table
        db.execute('''
            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_name TEXT NOT NULL,
                price REAL NOT NULL
            )
        ''')
        
        # Bills table
        db.execute('''
            CREATE TABLE IF NOT EXISTS bills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bill_hash TEXT NOT NULL,
                total_amount REAL NOT NULL,
                created_date DATE NOT NULL,
                created_time TIME NOT NULL,
                bill_data TEXT NOT NULL  -- JSON string containing all bill details
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

def save_bill(bill_data):
    """Save a bill to the database"""
    now = datetime.now()
    # Create a unique hash for the bill using timestamp and data
    bill_hash = hashlib.md5(f"{now.timestamp()}{json.dumps(bill_data)}".encode()).hexdigest()[:8]
    
    with get_db() as db:
        db.execute('''
            INSERT INTO bills (bill_hash, total_amount, created_date, created_time, bill_data)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            bill_hash,
            bill_data['total'],
            now.strftime('%Y-%m-%d'),
            now.strftime('%H:%M:%S'),
            json.dumps(bill_data)
        ))
    return bill_hash

def get_bill_history():
    """Get all bills ordered by date and time"""
    with get_db() as db:
        cursor = db.execute('''
            SELECT bill_hash, created_date, created_time, total_amount, bill_data
            FROM bills
            ORDER BY created_date DESC, created_time DESC
        ''')
        return cursor.fetchall()

def get_bill_by_hash(bill_hash):
    """Get a specific bill by its hash"""
    with get_db() as db:
        cursor = db.execute('''
            SELECT bill_data
            FROM bills
            WHERE bill_hash = ?
        ''', (bill_hash,))
        result = cursor.fetchone()
        return json.loads(result[0]) if result else None

# Initialize the database when the module is imported
init_db() 