import sqlite3
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)
import random
import os

# ==== Настройки ====
OWNER_ID = int(os.getenv("5757028331"))
BOT_TOKEN = os.getenv("7483963905:AAGsdHReggsvE5PAIr5kAVh-eFiiMeQR4Ok")
last_fact_id = None  # Для антиповтора

# ==== Работа с БД ====
def init_db():
    conn = sqlite3.connect('facts.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS facts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fact TEXT NOT NULL UNIQUE,
            category TEXT DEFAULT 'Общая'
        )
    ''')
    conn.commit()
    conn.close()

def add_fact(fact_text, category="Общая"):
    conn = sqlite3.connect('facts.db')
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO facts (fact, category) VALUES (?, ?)', (fact_text, category))
        conn.commit()
        result = True
    except sqlite3.IntegrityError:
        result = False
    conn.close()
    return result

def get_random_fact_exclude_last():
    global last_fact_id
    conn = sqlite3.connect('facts.db')
    cursor = conn.cursor()
    if last_fact_id is None:
        cursor.execute('SELECT id, fact FROM facts ORDER BY RANDOM() LIMIT 1')
    else:
        cursor.execute('SELECT id, fact FROM facts WHERE id != ? ORDER BY RANDOM() LIMIT 1', (last_fact_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        last_fact_id = row[0]
        return row[1]
    else:
        return "❗ В базе пока нет фактов."

def get_fact_by_category(category):
    global last_fact_id
    conn = sqlite3.connect('facts.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, fact FROM facts WHERE category = ? ORDER BY RANDOM() LIMIT 1', (category,))
    row = cursor.fetchone()
    conn.close()
    if row:
        last_fact_id = row[0]
        return row[1]
    else:
        return "❗ Нет фактов в этой категории."

def get_categories():
    conn = sqlite3.connect('facts.db')
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT category FROM facts')
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]

def get_last_fact():
    conn = sqlite3.connect('facts.db')
    cursor = conn.cursor()
    cursor.execute('SELECT fact, category FROM facts ORDER BY id DESC LIMIT 1')
    row = cursor.fetchone()
    conn.close()
    if row:
        return f"{row[0]}\n📂 Категория: {row[1]}"
    else:
        return "❗ Пока нет фактов!"

def count_facts():
    conn = sqlite3.connect('facts.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM facts')
    count = cursor.fetchone()[0]
    conn.close()
    return count

# ==== Новый набор фактов ====
facts_list = [
    ("Антарктида — самая большая пустыня на Земле.", "Природа"),
    ("На Венере день длится дольше, чем год.", "Космос"),
    ("У осьминога три сердца.", "Животные"),
    ("Человеческий глаз различает до 10 миллионов цветов.", "Человек"),
    ("Пчёлы узнают лица людей.", "Животные"),
    ("Свет звёзд — взгляд в прошлое.", "Космос"),
    ("Слон может плакать и помнить ушедших.", "Животные"),
    ("80% вулканов — под водой.", "Природа"),
    ("Самая высокая волна — 31 метр.", "Природа"),
    ("Земля пролетает 30 км в секунду.", "Космос"),
    ("Человек моргает 15 раз в минуту.", "Человек"),
    ("Эверест растёт на 4 мм в год.", "Природа"),
    ("Мозг человека на 75% из воды.", "Человек"),
    ("Дельфины зовут друг друга по имени.", "Животные"),
    ("На Плутоне есть ледяные вулканы.", "Космос"),
    ("Гренландская акула живёт до 400 лет.", "Животные"),
    ("Человек теряет до 100 волос в день.", "Человек"),
    ("Самая большая пещера — Ханг Сон Дунг.", "Природа"),
    ("Над Землёй летают тысячи спутников.", "Космос"),
    ("У тигров полоски даже на коже.", "Животные"),
    ("Летучие мыши — единственные летающие млекопитающие.", "Животные"),
    ("Океан хранит 95% неразведанных глубин.", "Природа"),
    ("Сердце синего кита — размером с машину.", "Животные"),
]

def fill_facts():
    for fact, category in facts_list:
        add_fact(fact, category)

# ==== Хендлеры ====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📚 Случайный факт", callback_data='get_fact')],
        [InlineKeyboardButton("📂 Категории", callback_data='show_categories')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "👋 Привет! Я бот с интересными фактами!\n\n"
        "Команды:\n"
        "/randomfact — случайный факт\n"
        "/categories — выбрать категорию\n"
        "/addfact — добавить факт (только владелец)\n"
        "/stats — статистика\n"
        "/about — обо мне\n"
        "/lastfact — последний факт\n"
        "/help — помощь",
        reply_markup=reply_markup
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📚 Команды бота:\n"
        "/randomfact — случайный факт\n"
        "/categories — выбрать категорию\n"
        "/addfact — добавить факт (только владелец)\n"
        "/stats — статистика\n"
        "/about — обо мне\n"
        "/lastfact — последний факт\n"
    )

async def random_fact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    fact = get_random_fact_exclude_last()
    await update.message.reply_text(fact)

async def show_categories(update: Update, context: ContextTypes.DEFAULT_TYPE):
    categories = get_categories()
    if not categories:
        await update.message.reply_text("❗ Категорий пока нет.")
        return
    buttons = [[InlineKeyboardButton(cat, callback_data=f'cat_{cat}')] for cat in categories]
    reply_markup = InlineKeyboardMarkup(buttons)
    await update.message.reply_text("📂 Выбери категорию:", reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data == 'get_fact':
        fact = get_random_fact_exclude_last()
        await query.edit_message_text(text=fact)
    elif data == 'show_categories':
        categories = get_categories()
        buttons = [[InlineKeyboardButton(cat, callback_data=f'cat_{cat}')] for cat in categories]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.edit_message_text("📂 Выбери категорию:", reply_markup=reply_markup)
    elif data.startswith('cat_'):
        category = data[4:]
        fact = get_fact_by_category(category)
        await query.edit_message_text(f"📂 Категория: {category}\n\n{fact}")

async def add_fact_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("⛔ Только владелец может добавлять факты.")
        return
    if not context.args:
        await update.message.reply_text("⚙️ Формат: /addfact Категория|Факт")
        return
    text = ' '.join(context.args)
    if "|" not in text:
        await update.message.reply_text("⚙️ Формат: /addfact Категория|Факт")
        return
    category, fact_text = map(str.strip, text.split("|", 1))
    if not category or not fact_text:
        await update.message.reply_text("⚙️ Оба поля должны быть заполнены.")
        return
    if add_fact(fact_text, category):
        await update.message.reply_text(f"✅ Факт добавлен!\nКатегория: {category}")
    else:
        await update.message.reply_text("⚠️ Такой факт уже есть!")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    total = count_facts()
    await update.message.reply_text(f"📊 Всего фактов в базе: {total}")

async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Бот-фактолог, автор — @anikisz")

async def last_fact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    fact = get_last_fact()
    await update.message.reply_text(f"🆕 Последний факт:\n{fact}")

async def categories_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_categories(update, context)

# ==== Запуск ====
if __name__ == '__main__':
    init_db()
    fill_facts()

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("randomfact", random_fact))
    app.add_handler(CommandHandler("categories", categories_command))
    app.add_handler(CommandHandler("addfact", add_fact_command))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("about", about))
    app.add_handler(CommandHandler("lastfact", last_fact))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("🤖 Бот запущен!")
    app.run_polling()