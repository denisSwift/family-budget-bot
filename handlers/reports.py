from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, CallbackQueryHandler, filters

import database

from keyboards import (
    get_main_menu,
    get_months_keyboard,
    get_report_categories_keyboard,
    get_report_subcategories_keyboard
)

from config import CURRENCY

# Состояния диалога
SELECTING_MONTH = 1
VIEWING_REPORT = 2
VIEWING_CATEGORY = 3
VIEWING_SUBCATEGORY = 4

async def start_report(update: Update, context: ContextTypes.DEFAULT_TYPE):

    current_year = datetime.now().year

    context.user_data['year'] = current_year

    await update.message.reply_text(
        f"Выберите месяц ({current_year}) года:",
        reply_markup=get_months_keyboard(current_year)
    )

    return SELECTING_MONTH

async def month_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    parts = query.data.split("_")
    month = int(parts[2])
    year = int(parts[1])

    context.user_data['month'] = month
    context.user_data['year'] = year

    balance_data = database.get_monthly_balance(year, month)
    categories_data = database.get_monthly_expenses_by_category(year, month)

    # Названия месяцев
    month_names = [
        "", "Январь", "Февраль", "Март", "Апрель",
        "Май", "Июнь", "Июль", "Август",
        "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
    ]
    month_name = month_names[month]

    # Формируем текст отчёта
    text = f"📊 Отчёт за {month_name} {year}\n"
    text += "─────────────────────\n"
    text += f"💵 Доходы: {balance_data['incomes']} {CURRENCY}\n"
    text += f"💸 Расходы: {balance_data['expenses']} {CURRENCY}\n"
    text += f"💰 Баланс: {balance_data['balance']} {CURRENCY}\n"
    text += "─────────────────────\n"

    if categories_data:
        text += "Нажмите на категорию для детализации:"

        await query.edit_message_text(
            text,
            reply_markup=get_report_categories_keyboard(categories_data, year, month)
        )
    else:
        text += "Расходов за этот месяц нет."
        await query.edit_message_text(text)

    return VIEWING_REPORT


async def category_report_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # Извлекаем данные из callback_data
    # "repcat_2_2025_1" -> ["repcat", "2", "2025", "1"]
    parts = query.data.split("_")
    category_id = int(parts[1])
    year = int(parts[2])
    month = int(parts[3])

    # Сохраняем для следующих шагов
    context.user_data['category_id'] = category_id

    # Получаем данные из базы
    subcategories_data = database.get_monthly_expenses_by_subcategory(year, month, category_id)

    # Формируем текст
    text = "📁 Расходы по подкатегориям:\n"
    text += "─────────────────────\n"

    # Считаем общую сумму по категории
    total = sum(sub['total'] for sub in subcategories_data)
    text += f"💰 Всего: {total} {CURRENCY}\n"
    text += "─────────────────────\n"
    text += "Нажмите для детализации:"

    await query.edit_message_text(
        text,
        reply_markup=get_report_subcategories_keyboard(subcategories_data, year, month)
    )

    return VIEWING_CATEGORY


async def subcategory_report_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # Извлекаем данные из callback_data
    parts = query.data.split("_")
    subcategory_id = int(parts[1])
    year = int(parts[2])
    month = int(parts[3])
    # Получаем детальные траты из базы
    expenses = database.get_expenses_detail(year, month, subcategory_id)
    # Формируем текст
    text = "📝 Детализация расходов:\n"
    text += "─────────────────────\n"

    total = 0
    for expense in expenses:
        # Форматируем дату
        date_parts = expense['expense_date'].split("-")
        date_str = f"{date_parts[2]}.{date_parts[1]}"

        text += f"{date_str} — {expense['amount']} {CURRENCY}"
        if expense['description']:
            text += f" — {expense['description']}"
        text += "\n"

        total += expense['amount']

    text += "─────────────────────\n"
    text += f"💰 Итого: {total} {CURRENCY}"

    await query.edit_message_text(text)

    return ConversationHandler.END


def get_report_handler():
    return ConversationHandler(
        # Начало диалога — кнопка "📊 Отчёт за месяц"
        entry_points=[
            MessageHandler(filters.Regex("^📊 Отчёт за месяц$"), start_report)
        ],

        # Состояния
        states={
            # Ждём выбор месяца
            SELECTING_MONTH: [
                CallbackQueryHandler(month_selected, pattern="^month_")
            ],

            # Смотрим отчёт, можем нажать на категорию
            VIEWING_REPORT: [
                CallbackQueryHandler(category_report_selected, pattern="^repcat_")
            ],

            # Смотрим категорию, можем нажать на подкатегорию
            VIEWING_CATEGORY: [
                CallbackQueryHandler(subcategory_report_selected, pattern="^repsubcat_"),
                CallbackQueryHandler(back_to_report, pattern="^back_report_")
            ],
        },

        fallbacks=[],

        allow_reentry=True

    )


async def back_to_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # Извлекаем год и месяц из callback_data
    # "back_report_2025_2" -> ["back", "report", "2025", "2"]
    parts = query.data.split("_")
    year = int(parts[2])
    month = int(parts[3])

    # Сохраняем
    context.user_data['year'] = year
    context.user_data['month'] = month

    # Получаем данные из базы
    balance_data = database.get_monthly_balance(year, month)
    categories_data = database.get_monthly_expenses_by_category(year, month)

    # Названия месяцев
    month_names = [
        "", "Январь", "Февраль", "Март", "Апрель",
        "Май", "Июнь", "Июль", "Август",
        "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
    ]
    month_name = month_names[month]

    # Формируем текст отчёта
    text = f"📊 Отчёт за {month_name} {year}\n"
    text += "─────────────────────\n"
    text += f"💵 Доходы: {balance_data['incomes']} {CURRENCY}\n"
    text += f"💸 Расходы: {balance_data['expenses']} {CURRENCY}\n"
    text += f"💰 Баланс: {balance_data['balance']} {CURRENCY}\n"
    text += "─────────────────────\n"

    if categories_data:
        text += "Нажмите на категорию для детализации:"
        await query.edit_message_text(
            text,
            reply_markup=get_report_categories_keyboard(categories_data, year, month)
        )
    else:
        text += "Расходов за этот месяц нет."
        await query.edit_message_text(text)

    return VIEWING_REPORT



