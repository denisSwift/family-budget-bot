from config import ALLOWED_USERS
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from config import ALLOWED_USERS
import database
from keyboards import get_categories_keyboard, get_subcategories_keyboard, get_main_menu_inline, get_record_date_keyboard

# Состояния диалога
SELECTING_DATE = 0
SELECTING_CATEGORY = 1
SELECTING_SUBCATEGORY = 2
ENTERING_AMOUNT = 3
ENTERING_DESCRIPTION = 4


async def start_add_expense(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        "За какой месяц вносим расход?",
        reply_markup=get_record_date_keyboard()
    )
    return SELECTING_DATE


async def start_add_expense_inline(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        "За какой месяц вносим расход?",
        reply_markup=get_record_date_keyboard()
    )
    return SELECTING_DATE


async def date_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    parts = query.data.split("_")
    year = int(parts[1])
    month = int(parts[2])

    # Сохраняем дату — первое число выбранного месяца
    context.user_data['expense_date'] = f"{year}-{str(month).zfill(2)}-01"

    await query.edit_message_text(
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


async def back_to_categories(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "Выберите категорию:",
        reply_markup=get_categories_keyboard()
    )
    return SELECTING_CATEGORY


async def subcategory_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    subcategory_id = int(query.data.split("_")[1])
    context.user_data['subcategory_id'] = subcategory_id

    await query.edit_message_text("Введите сумму:")
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

    await update.message.reply_text("Введите описание:")
    return ENTERING_DESCRIPTION


async def description_entered(update: Update, context: ContextTypes.DEFAULT_TYPE):
    description = update.message.text

    user_id = update.effective_user.id
    subcategory_id = context.user_data['subcategory_id']
    amount = context.user_data['amount']
    expense_date = context.user_data.get('expense_date')

    database.add_expense(user_id, subcategory_id, amount, description, expense_date)

    context.user_data.clear()

    await update.message.reply_text(
        f"✅ Расход добавлен: {amount} дин",
        reply_markup=get_main_menu_inline()
    )
    return ConversationHandler.END


def get_expenses_handler():
    return ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^💸 Добавить расход$"), start_add_expense),
            CallbackQueryHandler(start_add_expense_inline, pattern="^menu_expense$")
        ],
        states={
            SELECTING_DATE: [
                CallbackQueryHandler(date_selected, pattern="^recdate_")
            ],
            SELECTING_CATEGORY: [
                CallbackQueryHandler(category_selected, pattern="^cat_")
            ],
            SELECTING_SUBCATEGORY: [
                CallbackQueryHandler(subcategory_selected, pattern="^subcat_"),
                CallbackQueryHandler(back_to_categories, pattern="^back_to_categories$")
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
