import sqlite3
from datetime import date
from config import DATABASE_PATH, DEFAULT_CATEGORIES

def get_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection

def init_database():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS subcategories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            is_active INTEGER DEFAULT 1, 
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES categories (id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            subcategory_id INTEGER NOT NULL,
            amount REAL NOT NULL, 
            description TEXT,
            expenses_date DATE DEFAULT CURRENT_DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id),
            FOREIGN KEY (subcategory_id) REFERENCES subcategories (id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS incomes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            description TEXT,
            income_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    """)
    # Заполняем категории и подкатегории по умолчанию
    for category_name, subcategories in DEFAULT_CATEGORIES.items():
        # Добавляем категорию если еще нет
        cursor.execute(
            "INSERT OR IGNORE INTO categories (name) VALUES (?)",
            (category_name,)
        )
        # Получаем id категории
        cursor.execute(
            "SELECT id FROM categories WHERE name = ?",
            (category_name,)
        )
        category_id = cursor.fetchone()[0]
        # Добавляем подкатегории
        for subcategory_name in subcategories:
            cursor.execute(
                "INSERT OR IGNORE INTO subcategories (category_id, name) VALUES (?, ?)",
                (category_id, subcategory_name)
            )

    connection.commit()
    connection.close()