from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, CallbackQueryHandler, filters
from config import ALLOWED_USERS
from keyboards import get_main_menu_inline, get_record_date_keyboard

import database

SELECTING_DATE = 0
ENTERING_AMOUNT = 1
ENTERING_DESCRIPTION = 2


async def start_add_income(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ALLOWED_USERS:
        await update.message.reply_text("⛔ Доступ запрещён")
        return ConversationHandler.END

    balance = database.get_current_balance()
    if balance is None:
        await update.message.reply_text(
            "⚠️ Сначала установите начальный баланс!\n\n"
            "Нажмите кнопку «💰 Текущий баланс»",
            reply_markup=get_main_menu_inline()
        )
        return ConversationHandler.END

    await update.message.reply_text(
        "За какой месяц вносим доход?",
        reply_markup=get_record_date_keyboard()
    )
    return SELECTING_DATE


async def start_add_income_inline(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if update.effective_user.id not in ALLOWED_USERS:
        await query.edit_message_text("⛔ Доступ запрещён")
        return ConversationHandler.END

    balance = database.get_current_balance()
    if balance is None:
        await query.edit_message_text(
            "⚠️ Сначала установите начальный баланс!\n\n"
            "Нажмите кнопку «💰 Текущий баланс»",
            reply_markup=get_main_menu_inline()
        )
        return ConversationHandler.END

    await query.edit_message_text(
        "За какой месяц вносим доход?",
        reply_markup=get_record_date_keyboard()
    )
    return SELECTING_DATE


async def date_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    parts = query.data.split("_")
    year = int(parts[1])
    month = int(parts[2])

    context.user_data['income_date'] = f"{year}-{str(month).zfill(2)}-01"

    await query.edit_message_text("Введите сумму дохода:")
    return ENTERING_AMOUNT


async def amount_entered(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    try:
        amount = int(text)
        if amount <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("❌ Введите корректную сумму (целое положительное число):")
        return ENTERING_AMOUNT

    context.user_data['amount'] = amount

    await update.message.reply_text("Введите описание (откуда доход):")
    return ENTERING_DESCRIPTION


async def description_entered(update: Update, context: ContextTypes.DEFAULT_TYPE):
    description = update.message.text

    user_id = update.effective_user.id
    amount = context.user_data['amount']
    income_date = context.user_data.get('income_date')

    database.add_income(user_id, amount, description, income_date)

    context.user_data.clear()

    await update.message.reply_text(
        f"✅ Добавлена сумма {amount} дин!",
        reply_markup=get_main_menu_inline()
    )
    return ConversationHandler.END


def get_income_handler():
    return ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^💵 Добавить доход$"), start_add_income),
            CallbackQueryHandler(start_add_income_inline, pattern="^menu_income$")
        ],
        states={
            SELECTING_DATE: [
                CallbackQueryHandler(date_selected, pattern="^recdate_")
            ],
            ENTERING_AMOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, amount_entered)
            ],
            ENTERING_DESCRIPTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, description_entered)
            ]
        },
        fallbacks=[],
        allow_reentry=True,
        per_message=False
    )
