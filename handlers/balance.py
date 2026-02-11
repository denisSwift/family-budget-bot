from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters

import database
from keyboards import get_main_menu
from config import CURRENCY

# Состояние диалога
ENTERING_INITIAL_BALANCE = 1


async def show_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Получаем текущий баланс
    balance = database.get_current_balance()

    # Если баланс не установлен — просим установить
    if balance is None:
        await update.message.reply_text(
            "💰 Начальный баланс не установлен.\n\n"
            "Введите текущий остаток средств (сколько денег у вас сейчас):"
        )
        return ENTERING_INITIAL_BALANCE

    # Сохраняем в историю
    database.save_balance_to_history()

    # Показываем текущий баланс
    await update.message.reply_text(
        f"💰 Текущий баланс: {int(balance)} {CURRENCY}",
        reply_markup=get_main_menu()
    )

    return ConversationHandler.END


async def initial_balance_entered(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Получаем сумму
    balance = int(update.message.text)

    # Устанавливаем начальный баланс
    database.set_current_balance(balance)

    # Сохраняем в историю
    database.save_balance_to_history()

    await update.message.reply_text(
        f"✅ Начальный баланс установлен: {balance} {CURRENCY}",
        reply_markup=get_main_menu()
    )

    return ConversationHandler.END


def get_balance_handler():
    return ConversationHandler(
        # Начало диалога — кнопка "💰 Текущий баланс"
        entry_points=[
            MessageHandler(filters.Regex("^💰 Текущий баланс$"), show_balance)
        ],

        # Состояния
        states={
            # Ждём ввод начального баланса
            ENTERING_INITIAL_BALANCE: [
                MessageHandler(filters.TEXT, initial_balance_entered)
            ],
        },

        fallbacks=[],

        allow_reentry=True
    )