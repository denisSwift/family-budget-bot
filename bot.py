from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import database
from keyboards import get_main_menu

from handlers.expenses import get_expenses_handler
from handlers.incomes import get_income_handler
from handlers.reports import get_report_handler


from config import BOT_TOKEN, ALLOWED_USERS

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    database.add_user(user.id, user.username, user.first_name)

    await update.message.reply_text(
        f"Привет, {user.first_name}!\n\n"
        f"Я помогу вести семейный бюджет.\n\n"
        f"Выбери действие:",
        reply_markup=get_main_menu()
    )

async def myid_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(f"Твой ID: {user.id}")

def main():

    database.init_database()
    # Создаем приложение бота
    application = Application.builder().token(BOT_TOKEN).build()

    # Регистрируем обработчик команд
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("myid", myid_command))

    application.add_handler(get_expenses_handler())
    application.add_handler(get_income_handler())
    application.add_handler(get_report_handler())

    print("Бот запущен!")
    application.run_polling()

if __name__ == "__main__":
    main()