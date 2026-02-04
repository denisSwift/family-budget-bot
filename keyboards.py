from telegram import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
import database

def get_main_menu():
    keyboard = [
        ["💸 Добавить расход"],
        ["💵 Добавить доход"],
        ["📊 Отчёт за месяц"],
        ["💰 Текущий баланс"]
    ]

    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

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

def get_months_keyboard(year):
    months = [
        "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
        "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
    ]

    keyboard = []
    row = []

    for i, month_name in enumerate(months, start=1):
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
            text=f"{cat['name']}: {cat['total']:.0f} дин",
            callback_data = f"repcat_{cat['id']}_{year}_{month}"
        )
        keyboard.append([button])

    return InlineKeyboardMarkup(keyboard)

def get_report_subcategories_keyboard(subcategories_data, year, month):
    keyboard = []

    for subcat in subcategories_data:
        button = InlineKeyboardButton(
            text=f"{subcat['name']}: {subcat['total']:.0f} дин",
            callback_data = f"repsubcat_{subcat['id']}_{year}_{month}"
        )

        keyboard.append([button])

    keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data=f"back_report_{year}_{month}")])

    return InlineKeyboardMarkup(keyboard)




