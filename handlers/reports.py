from datetime import datetime
from config import ALLOWED_USERS, CURRENCY
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, CallbackQueryHandler, filters

import database

from keyboards import (
    get_months_keyboard,
    get_report_categories_keyboard,
    get_report_subcategories_keyboard
)

# Состояния диалога
SELECTING_MONTH = 1
VIEWING_REPORT = 2
VIEWING_CATEGORY = 3
VIEWING_SUBCATEGORY = 4

MONTH_NAMES = [
    "", "Январь", "Февраль", "Март", "Апрель",
    "Май", "Июнь", "Июль", "Август",
    "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
]


def _build_report_text(year, month, incomes, expenses, categories_data, incomes_detail):
    month_name = MONTH_NAMES[month]
    text = f"📊 Отчёт за {month_name} {year}\n"
    text += "─────────────────────\n"

    if incomes_detail:
        text += f"💵 Доходы: {int(incomes)} {CURRENCY}\n"
        for row in incomes_detail:
            text += f"   • {row['source']}: {int(row['total'])} {CURRENCY}\n"
    else:
        text += f"💵 Доходы: {int(incomes)} {CURRENCY}\n"

    text += f"💸 Расходы: {int(expenses)} {CURRENCY}\n"
    text += f"📈 Разница: {int(incomes - expenses)} {CURRENCY}\n"
    text += "─────────────────────\n"
    return text


async def start_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ALLOWED_USERS:
        await update.message.reply_text("⛔ Доступ запрещён")
        return ConversationHandler.END

    current_year = datetime.now().year
    context.user_data['year'] = current_year

    await update.message.reply_text(
        f"Выберите месяц ({current_year}) года:",
        reply_markup=get_months_keyboard(current_year)
    )
    return SELECTING_MONTH


async def start_report_inline(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if update.effective_user.id not in ALLOWED_USERS:
        await query.edit_message_text("⛔ Доступ запрещён")
        return ConversationHandler.END

    current_year = datetime.now().year
    context.user_data['year'] = current_year

    await query.edit_message_text(
        f"Выберите месяц ({current_year}):",
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

    incomes = database.get_monthly_incomes_total(year, month)
    expenses = database.get_monthly_expenses_total(year, month)
    incomes_detail = database.get_monthly_incomes_detail(year, month)
    categories_data = database.get_monthly_expenses_by_category(year, month)

    text = _build_report_text(year, month, incomes, expenses, categories_data, incomes_detail)

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

    # "repcat_2_2025_1" -> ["repcat", "2", "2025", "1"]
    parts = query.data.split("_")
    category_id = int(parts[1])
    year = int(parts[2])
    month = int(parts[3])

    context.user_data['category_id'] = category_id

    subcategories_data = database.get_monthly_expenses_by_subcategory(year, month, category_id)

    total = sum(sub['total'] for sub in subcategories_data)
    text = "📁 Расходы по подкатегориям:\n"
    text += "─────────────────────\n"
    text += f"💰 Всего: {int(total)} {CURRENCY}\n"
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

    parts = query.data.split("_")
    subcategory_id = int(parts[1])
    year = int(parts[2])
    month = int(parts[3])

    expenses = database.get_expenses_detail(year, month, subcategory_id)

    text = "📝 Детализация расходов:\n"
    text += "─────────────────────\n"

    total = 0
    for expense in expenses:
        date_parts = expense['expense_date'].split("-")
        date_str = f"{date_parts[2]}.{date_parts[1]}"

        text += f"{date_str} — {int(expense['amount'])} {CURRENCY}"
        if expense['description']:
            text += f" — {expense['description']}"
        text += "\n"

        total += expense['amount']

    text += "─────────────────────\n"
    text += f"💰 Итого: {int(total)} {CURRENCY}"

    await query.edit_message_text(text)
    return ConversationHandler.END


async def back_to_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # "back_report_2025_2" -> ["back", "report", "2025", "2"]
    parts = query.data.split("_")
    year = int(parts[2])
    month = int(parts[3])

    context.user_data['year'] = year
    context.user_data['month'] = month

    incomes = database.get_monthly_incomes_total(year, month)
    expenses = database.get_monthly_expenses_total(year, month)
    incomes_detail = database.get_monthly_incomes_detail(year, month)
    categories_data = database.get_monthly_expenses_by_category(year, month)

    text = _build_report_text(year, month, incomes, expenses, categories_data, incomes_detail)

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


def get_report_handler():
    return ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^📊 Отчёт за месяц$"), start_report),
            CallbackQueryHandler(start_report_inline, pattern="^menu_report$")
        ],
        states={
            SELECTING_MONTH: [
                CallbackQueryHandler(month_selected, pattern="^month_")
            ],
            VIEWING_REPORT: [
                CallbackQueryHandler(category_report_selected, pattern="^repcat_")
            ],
            VIEWING_CATEGORY: [
                CallbackQueryHandler(subcategory_report_selected, pattern="^repsubcat_"),
                CallbackQueryHandler(back_to_report, pattern="^back_report_")
            ],
        },
        fallbacks=[],
        allow_reentry=True,
        per_message=False
    )
