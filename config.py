import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_PATH = os.getenv("DATABASE_PATH", "family_budget_bot.db")
CURRENCY = os.getenv("CURRENCY", "дин")

ALLOWED_USERS_STR = os.getenv("ALLOWED_USERS", "")
ALLOWED_USERS = []

for user_id in ALLOWED_USERS_STR.split(","):
    try:
        if user_id.strip():
            ALLOWED_USERS.append(int(user_id.strip()))
    except ValueError:
        pass

DEFAULT_CATEGORIES = {
    "📋 Налоги": [
        "Налоги"
    ],
    "🎮 Развлечения": [
        "Концерты, театр, кино",
        "Тусовки с друзьями",
        "Спорт",
        "Подписки",
        "Другое"
    ],
    "🛒 Повседневные расходы": [
        "Базовые",
        "Рестораны и кафе",
        "Одежда и украшения",
        "Уход за собой",
        "Машина",
        "Такси",
        "Другое"
    ],
    "🎁 Подарки": [
        "Подарки"
    ],
    "🏥 Здоровье": [
        "Лечение"
    ],
    "🏠 Дом": [
        "Ипотека",
        "Мебель и бытовая техника",
        "Обслуживание и ремонт",
        "Коммуналка и интернет",
        "Посуда, интерьер, бытовые мелочи"
    ],
    "✈️ Путешествия": [
        "Билеты и отели",
        "Питание",
        "Развлечения",
        "Сплитвайз",
        "Другое"
    ]
}