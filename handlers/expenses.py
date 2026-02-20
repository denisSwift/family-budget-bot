from pyexpat.errors import messages

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from config import ALLOWED_USERS
import database
from keyboards import get_categories_keyboard, get_subcategories_keyboard, get_main_menu

# Состояния диалога
SELECTING_CATEGORY = 1
SELECTING_SUBCATEGORY = 2
ENTERING_AMOUNT = 3
ENTERING_DESCRIPTION = 4


async def start_add_expense(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Проверяем доступ
    if update.effective_user.id not in ALLOWED_USERS:
        await update.message.reply_text("⛔ Доступ запрещён")
        return ConversationHandler.END

    # Проверяем установлен ли начальный баланс
    balance = database.get_current_balance()

    if balance is None:
        await update.message.reply_text(
            "⚠️ Сначала установите начальный баланс!\n\n"
            "Нажмите кнопку «💰 Текущий баланс»",
            reply_markup=get_main_menu()
        )
        return ConversationHandler.END

    await update.message.reply_text(
        "Выберите категорию:",
        reply_markup=get_categories_keyboard()
    )

    return SELECTING_CATEGORY

async def category_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    category_id = int(query.data.split("_")[1])

    context.user_data['category_id'] = category_id

    await query.edit_message_text(
        "Выберите подкатегорию:",
        reply_markup=get_subcategories_keyboard(category_id)
    )

    return SELECTING_SUBCATEGORY

async def subcategory_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    subcategory_id = int(query.data.split("_")[1])

    context.user_data['subcategory_id'] = subcategory_id

    await query.edit_message_text(
        "Введите сумму:"
    )

    return ENTERING_AMOUNT

async def amount_entered(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    # Проверяем, не нажал ли пользователь кнопку меню
    if text in ["💸 Добавить расход", "💵 Добавить доход", "📊 Отчёт за месяц", "💰 Текущий баланс"]:
        await update.message.reply_text(
            "❌ Ввод отменён",
            reply_markup=get_main_menu()
        )
        return ConversationHandler.END

    # Получаем сумму
    amount = int(text)

    context.user_data['amount'] = amount

    await update.message.reply_text(
        "Введите описание:"
    )

    return ENTERING_DESCRIPTION

async def description_entered(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    # Проверяем, не нажал ли пользователь кнопку меню
    if text in ["💸 Добавить расход", "💵 Добавить доход", "📊 Отчёт за месяц", "💰 Текущий баланс"]:
        await update.message.reply_text(
            "❌ Ввод отменён",
            reply_markup=get_main_menu()
        )
        return ConversationHandler.END

    # Получаем описание
    description = text

    user_id = update.effective_user.id

    subcategory_id = context.user_data['subcategory_id']
    amount = context.user_data['amount']

    database.add_expense(user_id, subcategory_id, amount, description)

    context.user_data.clear()

    await update.message.reply_text(
        f"✅ Расход добавлен: {amount} дин",
        reply_markup=get_main_menu()
    )

    return ConversationHandler.END

def get_expenses_handler():

    return ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^💸 Добавить расход$"), start_add_expense)
        ],
        states={
            SELECTING_CATEGORY: [
                CallbackQueryHandler(category_selected, pattern="^cat_")
            ],

            SELECTING_SUBCATEGORY: [
                CallbackQueryHandler(subcategory_selected, pattern="^subcat_")
            ],

            ENTERING_AMOUNT: [
                MessageHandler(filters.TEXT, amount_entered)
            ],

            ENTERING_DESCRIPTION: [
                MessageHandler(filters.TEXT, description_entered)
            ]
        },
        fallbacks=[],
        allow_reentry = True
    )




