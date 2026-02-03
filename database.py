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
            expense_date DATE DEFAULT CURRENT_DATE,
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

    # Таблица остатков по месяцам
    cursor.execute("""
            CREATE TABLE IF NOT EXISTS balance_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                year INTEGER NOT NULL,
                month INTEGER NOT NULL,
                balance REAL NOT NULL,
                is_manual INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(year, month)
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

def add_user(user_id, username, first_name):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT OR REPLACE INTO users (user_id, username, first_name)
        VALUES (?, ?, ?)
    """, (user_id, username, first_name))
    connection.commit()
    connection.close()

def get_categories():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, name FROM categories
        WHERE is_active = 1
        ORDER BY id
    """)

    categories = cursor.fetchall()
    connection.close()

    return categories

def get_subcategories(category_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, name FROM subcategories
        WHERE category_id = ? AND is_active = 1
        ORDER BY id   
    """, (category_id,))

    subcategories = cursor.fetchall()
    connection.close()

    return subcategories

def add_expenses(user_id, subcategory_id, amount, description = None):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO expenses (user_id, subcategory_id, amount, description)
        VALUES (?, ?, ?, ?)
    """, (user_id, subcategory_id, amount, description))

    connection.commit()
    connection.close()

def add_income(user_id, amount, description=None):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO incomes (user_id, amount, description)
        VALUES (?, ?, ?)
    """, (user_id, amount, description))

    connection.commit()
    connection.close()

def get_monthly_expenses_total(year, month):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT COALESCE(SUM(amount), 0) as total
        FROM expenses
        WHERE strftime('%Y', expense_date) = ?
        AND strftime('%M', expense_date) = ?
    """, (str(year), str(month).zfill(2)))

    result = cursor.fetchone()
    connection.close()

    return result['total']

def get_monthly_incomes_total(year, month):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT COALESCE(SUM(amount), 0) as total
        FROM incomes
        WHERE strftime('%Y', income_date) = ?
        AND strftime('%M', income_date) = ?
    """, (str(year), str(month).zfill(2)))

    result = cursor.fetchone()
    connection.close()

    return result['total']


def get_monthly_expenses_by_category(year, month):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT categories.id, categories.name, SUM(expenses.amount) as total
        FROM categories
        INNER JOIN subcategories ON subcategories.category_id = categories.id
        INNER JOIN expenses ON expenses.subcategory_id = subcategories.id
        WHERE categories.is_active = 1
            AND strftime('%Y', expenses.expense_date) = ?
            AND strftime('%m', expenses.expense_date) = ?
        GROUP BY categories.id, categories.name
        ORDER BY total DESC
    """, (str(year), str(month).zfill(2)))

    results = cursor.fetchall()
    connection.close()

    return results

def get_monthly_expenses_by_subcategory(year, month, category_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT subcategories.id, subcategories.name, SUM(expenses.amount) as total
        FROM subcategories
        INNER JOIN expenses ON expenses.subcategory_id = subcategories.id
        WHERE subcategories.category_id = ?
            AND strftime('%Y', expenses.expense_date) = ?
            AND strftime('%m', expenses.expense_date) = ?
        GROUP BY subcategories.id, subcategories.name
        ORDER BY total DESC
    """, (category_id, str(year), str(month).zfill(2)))

    result = cursor.fetchall()
    cursor.close()

    return result

def get_expenses_detail(year, month, subcategory_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT expenses.id, expenses.amount, expenses.description, expenses.expense_date
        FROM expenses
        WHERE expenses.subcategory_id = ?
            AND strftime('%Y', expenses.expense_date) = ?
            AND strftime('%m', expenses.expense_date) = ?
        ORDER BY expenses.expense_date DESC
    """, (subcategory_id, str(year), str(month).zfill(2)))

    result = cursor.fetchall()
    cursor.close()

    return result

def get_monthly_balance(year, month):
    incomes = get_monthly_incomes_total(year, month)
    expenses = get_monthly_expenses_total(year, month)
    balance = incomes - expenses

    return {
        'incomes': incomes,
        'expenses': expenses,
        'balance': balance
    }

# Установить остаток вручную
def set_balance(year, month, balance):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT OR REPLACE INTO balance_history (year, month, balance, is_manual)
        VALUES (?, ?, ?, 1)
    """, (year, month, balance))

    connection.commit()
    connection.close()


def get_balance(year, month):
    # Вычисляем предыдущий месяц
    if month == 1:
        prev_year = year - 1
        prev_month = 12
    else:
        prev_year = year
        prev_month = month - 1

    connection = get_connection()
    cursor = connection.cursor()

    # Берём баланс предыдущего месяца
    cursor.execute("""
        SELECT balance FROM balance_history
        WHERE year = ? AND month = ?
    """, (prev_year, prev_month))

    result = cursor.fetchone()
    connection.close()

    if not result:
        return None  # Нет начального баланса

    prev_balance = result['balance']

    # Считаем: баланс + доходы − расходы прошлого месяца
    incomes = get_monthly_incomes_total(prev_year, prev_month)
    expenses = get_monthly_expenses_total(prev_year, prev_month)
    new_balance = prev_balance + incomes - expenses

    # Записываем на текущий месяц
    set_balance(year, month, new_balance)

    return new_balance