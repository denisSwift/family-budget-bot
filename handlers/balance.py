from datetime import datetime
from config import ALLOWED_USERS
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, CallbackQueryHandler, filters
from keyboards import get_main_menu_inline

import database
from config import CURRENCY

# Состояние диалога
ENTERING_INITIAL_BALANCE = 1


async def show_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    # Проверяем доступ
    if update.effective_user.id not in ALLOWED_USERS:
        await update.message.reply_text("⛔ Доступ запрещён")
        return ConversationHandler.END
        
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
        reply_markup=get_main_menu_inline()
    )

    return ConversationHandler.END

async def show_balance_inline(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показ баланса через inline-кнопку"""
    query = update.callback_query
    await query.answer()

    # Проверяем доступ
    if update.effective_user.id not in ALLOWED_USERS:
        await query.edit_message_text("⛔ Доступ запрещён")
        return ConversationHandler.END

    # Получаем текущий баланс
    balance = database.get_current_balance()

    # Если баланс не установлен — просим установить
    if balance is None:
        await query.edit_message_text(
            "💰 Начальный баланс не установлен.\n\n"
            "Введите текущий остаток средств (сколько денег у вас сейчас):"
        )
        return ENTERING_INITIAL_BALANCE

    # Сохраняем в историю
    database.save_balance_to_history()

    # Показываем текущий баланс
    try:
        await query.edit_message_text(
            f"💰 Текущий баланс: {int(balance)} {CURRENCY}",
            reply_markup=get_main_menu_inline()
        )
    except Exception:
        pass  # Игнорируем если сообщение не изменилось

    return ConversationHandler.END

async def initial_balance_entered(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        balance = int(update.message.text)
        if balance < 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("❌ Введите корректную сумму (целое число):")
        return ENTERING_INITIAL_BALANCE

    # Устанавливаем начальный баланс
    database.set_current_balance(balance)

    # Сохраняем в историю
    database.save_balance_to_history()

    await update.message.reply_text(
        f"✅ Начальный баланс установлен: {balance} {CURRENCY}",
        reply_markup=get_main_menu_inline()
    )

    return ConversationHandler.END


def get_balance_handler():
    return ConversationHandler(
        # Начало диалога — кнопка "💰 Текущий баланс"
        entry_points=[
            MessageHandler(filters.Regex("^💰 Текущий баланс$"), show_balance),
            CallbackQueryHandler(show_balance_inline, pattern="^menu_balance$")

        ],

        # Состояния
        states={
            # Ждём ввод начального баланса
            ENTERING_INITIAL_BALANCE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, initial_balance_entered)
            ],
        },

        fallbacks=[],

        allow_reentry=True,
        per_message=False
    )