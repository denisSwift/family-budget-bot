# Family Budget Telegram Bot

## Overview
A Telegram bot for managing family budgets, built with Python and the `python-telegram-bot` library. It tracks expenses, incomes, categories, and generates reports. Uses SQLite for data storage.

## Project Architecture
- `bot.py` - Main entry point, registers command/conversation handlers
- `config.py` - Configuration loader (env vars, default categories)
- `database.py` - SQLite database layer (users, categories, expenses, incomes, balance)
- `keyboards.py` - Telegram inline keyboard builders
- `handlers/` - Conversation handlers for different features:
  - `expenses.py` - Expense tracking
  - `incomes.py` - Income tracking
  - `reports.py` - Monthly reports
  - `balance.py` - Balance management
  - `categories.py` - Category management

## Environment Variables
- `BOT_TOKEN` (required) - Telegram Bot API token from @BotFather
- `ALLOWED_USERS` - Comma-separated list of allowed Telegram user IDs
- `CURRENCY` - Currency symbol (default: "дин")
- `DATABASE_PATH` - SQLite database file path (default: "family_budget_bot.db")

## Running
The bot runs via `python bot.py` which starts polling for Telegram updates.
