from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters

import database
from keyboards import get_main_menu

ENTERING_AMOUNT = 1
ENTERING_DESCRIPTION = 2

async def start_add_income(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Введите сумму:"
    )

    return ENTERING_AMOUNT


async def amount_entered(update: Update, context: ContextTypes.DEFAULT_TYPE):
    amount = int(update.message.text)

    context.user_data['amount'] = amount

    await update.message.reply_text(
        "Введите описание(откуда доход):"
    )

    return ENTERING_DESCRIPTION

async def description_entered(update: Update, context: ContextTypes.DEFAULT_TYPE):

    description = update.message.text

    user_id = update.effective_user.id

    amount = context.user_data['amount']

    database.add_income(user_id, amount, description)

    context.user_data.clear()

    await update.message.reply_text(
        f"✅Добавлена сумма {amount} дин!",
        reply_markup=get_main_menu()
    )

    return ConversationHandler.END

def get_income_handler():

    return ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^💵 Добавить доход$"), start_add_income)
        ],
        states={
            ENTERING_AMOUNT: [
                MessageHandler(filters.TEXT, amount_entered)
            ],
            ENTERING_DESCRIPTION: [
                MessageHandler(filters.TEXT, description_entered)
            ]
        },
        fallbacks=[]
    )


