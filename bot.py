from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import sqlite3
import logging

# Database setup
def init_db():
    conn = sqlite3.connect('bible_bot.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (user_id INTEGER PRIMARY KEY, plan TEXT, start_date TEXT, 
                  current_book TEXT, current_chapter INTEGER)''')
    conn.commit()
    conn.close()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    # Save user to database with default plan
    await update.message.reply_text(
        "Welcome! Choose your reading plan:\n"
        "/oneyear - Bible in One Year\n"
        "/psalmsmonth - Psalms in One Month"
    )

async def set_oneyear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Set user plan to one year
    await update.message.reply_text("Great! You'll receive daily readings.")

if __name__ == '__main__':
    init_db()
    application = Application.builder().token("YOUR_TOKEN").build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("oneyear", set_oneyear))
    
    application.run_polling()