from datetime import datetime
from telegram import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
import database
from config import CURRENCY

MONTH_NAMES = [
    "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
    "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
]


def get_main_menu_inline():
    keyboard = [
        [InlineKeyboardButton("💸 Добавить расход", callback_data="menu_expense")],
        [InlineKeyboardButton("💵 Добавить доход", callback_data="menu_income")],
        [InlineKeyboardButton("📊 Отчёт за месяц", callback_data="menu_report")],
        [InlineKeyboardButton("💰 Текущий баланс", callback_data="menu_balance")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_categories_keyboard():
    categories = database.get_categories()

    keyboard = []

    for category in categories:
        button = InlineKeyboardButton(
            text=category['name'],
            callback_data=f"cat_{category['id']}"
        )
        keyboard.append([button])

    return InlineKeyboardMarkup(keyboard)

def get_subcategories_keyboard(category_id):
    subcategories = database.get_subcategories(category_id)

    keyboard = []

    for subcategory in subcategories:
        button = InlineKeyboardButton(
            text=subcategory['name'],
            callback_data=f"subcat_{subcategory['id']}"
        )
        keyboard.append([button])

    keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="back_to_categories")])

    return InlineKeyboardMarkup(keyboard)

def get_record_date_keyboard():
    """Клавиатура выбора месяца для ввода расхода/дохода (текущий + 5 прошлых)"""
    now = datetime.now()
    keyboard = []

    for i in range(6):
        month = now.month - i
        year = now.year
        while month <= 0:
            month += 12
            year -= 1

        label = f"{MONTH_NAMES[month - 1]} {year}"
        if i == 0:
            label = f"✅ {label} (текущий)"

        button = InlineKeyboardButton(label, callback_data=f"recdate_{year}_{month}")
        keyboard.append([button])

    return InlineKeyboardMarkup(keyboard)


def get_months_keyboard(year):
    keyboard = []
    row = []

    for i, month_name in enumerate(MONTH_NAMES, start=1):
        button = InlineKeyboardButton(
            text=month_name,
            callback_data=f"month_{year}_{i}"
        )
        row.append(button)

        if len(row) == 3:
            keyboard.append(row)
            row = []

    return InlineKeyboardMarkup(keyboard)

def get_report_categories_keyboard(categories_data, year, month):
    keyboard = []

    for cat in categories_data:
        button = InlineKeyboardButton(
            text=f"{cat['name']}: {cat['total']:.0f} {CURRENCY}",
            callback_data = f"repcat_{cat['id']}_{year}_{month}"
        )
        keyboard.append([button])

    return InlineKeyboardMarkup(keyboard)

def get_report_subcategories_keyboard(subcategories_data, year, month):
    keyboard = []

    for subcat in subcategories_data:
        button = InlineKeyboardButton(
            text=f"{subcat['name']}: {subcat['total']:.0f} {CURRENCY}",
            callback_data = f"repsubcat_{subcat['id']}_{year}_{month}"
        )

        keyboard.append([button])

    keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data=f"back_report_{year}_{month}")])

    return InlineKeyboardMarkup(keyboard)




