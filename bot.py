import os
import random
import sqlite3
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

print("🤖 Бот запущен!")

# === Настройки ===
OWNER_ID = int(os.getenv("OWNER_ID"))
BOT_TOKEN = os.getenv("BOT_TOKEN")
last_fact_id = None  # Для антиповтора

# === База данных ===
conn = sqlite3.connect("facts.db")
cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS facts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fact TEXT NOT NULL,
        category TEXT NOT NULL
    )
""")
conn.commit()

# === Наполним начальными фактами ===
def fill_facts():
    facts = [
        ("Антарктида — самая большая пустыня на Земле!", "География"),
        ("Медузы существуют более 500 миллионов лет!", "Биология"),
        ("На Венере день длиннее года.", "Астрономия"),
        ("У осьминога три сердца.", "Биология"),
        ("Человеческий глаз различает до 10 млн оттенков.", "Человек"),
        ("Первое растение в космосе — арабидопсис.", "Космос"),
        ("Самая высокая волна — 31 метр!", "Природа"),
        ("Пчёлы могут узнавать лица людей.", "Биология"),
        ("На дне Марианской впадины давление в 1000 раз выше.", "Океан"),
        ("Слон может плакать.", "Животные"),
        ("Каждую секунду Земля пролетает 30 км!", "Космос"),
        ("Свет звёзд — это прошлое во времени.", "Космос"),
        ("В сердце человека около 5 литров крови.", "Человек"),
        ("Планета Уран вращается лёжа на боку.", "Космос"),
        ("Самое глубокое озеро — Байкал.", "География"),
        ("Киты поют песни для общения.", "Животные"),
        ("На Юпитере шторм длится сотни лет.", "Космос"),
        ("Кошки спят около 70% жизни.", "Животные"),
        ("Вулканы извергают лаву температурой 1200°C.", "Природа"),
        ("Океаны покрывают 71% Земли.", "География"),
    ]
    for fact, category in facts:
        cursor.execute("INSERT INTO facts (fact, category) VALUES (?, ?)", (fact, category))
    conn.commit()

# Только при первом запуске — потом можно закомментить!
# fill_facts()

# === Хендлеры ===

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я — бот фактов. Используй /randomfact, /categories или /addfact."
    )

async def random_fact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global last_fact_id
    cursor.execute("SELECT * FROM facts")
    facts = cursor.fetchall()

    if not facts:
        await update.message.reply_text("Фактов нет.")
        return

    fact = random.choice(facts)
    while len(facts) > 1 and fact[0] == last_fact_id:
        fact = random.choice(facts)

    last_fact_id = fact[0]
    await update.message.reply_text(f"📂 Категория: {fact[2]}\n\n{fact[1]}")

async def add_fact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("⛔ Только владелец может добавлять факты.")
        return

    args = context.args
    if len(args) < 2:
        await update.message.reply_text("Используй: /addfact [Категория] [Текст факта]")
        return

    category = args[0]
    fact_text = " ".join(args[1:])

    cursor.execute("INSERT INTO facts (fact, category) VALUES (?, ?)", (fact_text, category))
    conn.commit()
    await update.message.reply_text(f"✅ Факт добавлен!\n\n📂 Категория: {category}\n{fact_text}")

async def last_fact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cursor.execute("SELECT * FROM facts ORDER BY id DESC LIMIT 1")
    fact = cursor.fetchone()
    if fact:
        await update.message.reply_text(f"📂 Категория: {fact[2]}\n\n{fact[1]}")
    else:
        await update.message.reply_text("Фактов нет.")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cursor.execute("SELECT COUNT(*) FROM facts")
    count = cursor.fetchone()[0]
    await update.message.reply_text(f"📊 Всего фактов в базе: {count}")

async def categories(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cursor.execute("SELECT DISTINCT category FROM facts")
    categories = [row[0] for row in cursor.fetchall()]
    if not categories:
        await update.message.reply_text("Категорий нет.")
        return

    keyboard = [
        [InlineKeyboardButton(cat, callback_data=f"cat_{cat}")] for cat in categories
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Выберите категорию:", reply_markup=reply_markup)

async def category_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    category = query.data.replace("cat_", "")

    cursor.execute("SELECT * FROM facts WHERE category = ?", (category,))
    facts = cursor.fetchall()
    if not facts:
        await query.edit_message_text(f"Фактов для категории {category} нет.")
        return

    fact = random.choice(facts)
    await query.edit_message_text(f"📂 Категория: {fact[2]}\n\n{fact[1]}")

# === Запуск ===

app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("randomfact", random_fact))
app.add_handler(CommandHandler("addfact", add_fact))
app.add_handler(CommandHandler("lastfact", last_fact))
app.add_handler(CommandHandler("stats", stats))
app.add_handler(CommandHandler("categories", categories))
app.add_handler(CallbackQueryHandler(category_callback))

app.run_polling()