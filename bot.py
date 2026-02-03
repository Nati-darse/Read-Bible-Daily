# bot.py - Main Telegram bot for Daily Bible Reader
import os
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters, 
    ContextTypes, ConversationHandler, CallbackQueryHandler
)

# Import our modules
from config import READING_PLANS, BIBLE_TRANSLATIONS, LANGUAGES, MESSAGES, BOT_SETTINGS
from database import db
from reading_plans import reading_plans
from bible_api import bible_api
from menu import Menu

# Load environment variables
load_dotenv()

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation states
CHOOSING_LANGUAGE, CHOOSING_PLAN, CHOOSING_TRANSLATION = range(3)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Entry point: Check if user exists or start onboarding"""
    user = update.effective_user
    user_id = user.id
    
    existing_user = db.get_user(user_id)
    
    if existing_user:
        lang = existing_user.get('language', 'en')
        welcome_back = "👋 " + ("እንኳን በደህና መጡ!" if lang == 'am' else "Welcome back!")
        await update.message.reply_text(welcome_back, reply_markup=Menu.get_main_menu(lang))
        return ConversationHandler.END
    
    # New user: Start with language selection
    keyboard = [["English", "አማርኛ (Amharic)"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    
    await update.message.reply_text(
        MESSAGES['choose_language']['en'],
        reply_markup=reply_markup
    )
    
    return CHOOSING_LANGUAGE

async def language_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle language selection"""
    choice = update.message.text
    lang = 'am' if 'አማርኛ' in choice else 'en'
    context.user_data['language'] = lang
    
    # Show plan options in selected language
    await update.message.reply_text(
        MESSAGES['welcome'][lang].format(name=update.effective_user.first_name),
        reply_markup=Menu.get_plan_menu(lang)
    )
    
    return CHOOSING_PLAN

async def plan_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle plan selection"""
    plan_choice = update.message.text
    lang = context.user_data.get('language', 'en')
    
    # Map choice text back to plan key
    plan_key = 'bible_in_one_year' # Default
    for key, val in READING_PLANS.items():
        if val['name'][lang] in plan_choice:
            plan_key = key
            break
            
    context.user_data['plan'] = plan_key
    
    # Show translation options
    await update.message.reply_text(
        MESSAGES['choose_translation'][lang],
        reply_markup=Menu.get_translation_menu(lang)
    )
    
    return CHOOSING_TRANSLATION

async def translation_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle translation selection and complete registration"""
    choice = update.message.text
    translation = 'ESV' # Default
    
    if 'AMH' in choice or 'Amharic' in choice:
        translation = 'AMH'
    elif 'KJV' in choice:
        translation = 'KJV'
    elif 'NIV' in choice:
        translation = 'NIV'
        
    lang = context.user_data.get('language', 'en')
    user = update.effective_user
    
    # Save user to database
    db.add_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        plan_name=context.user_data['plan'],
        translation=translation,
        language=lang
    )
    
    plan_name = READING_PLANS[context.user_data['plan']]['name'][lang]
    trans_name = BIBLE_TRANSLATIONS.get(translation, translation)
    
    await update.message.reply_text(
        MESSAGES['registration_complete'][lang].format(plan=plan_name, translation=trans_name),
        reply_markup=Menu.get_main_menu(lang)
    )
    
    return ConversationHandler.END

async def handle_menu_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle main menu button clicks"""
    text = update.message.text
    user_id = update.effective_user.id
    user_data = db.get_user(user_id)
    
    if not user_data:
        await start(update, context)
        return

    lang = user_data['language']
    
    # Check which button was clicked
    if text in ["📖 TODAY'S READING", "📖 የዛሬው ንባብ"]:
        await show_todays_reading(update, context, user_data)
    elif text in ["👤 My Profile", "👤 የእኔ ፕሮፋይል"]:
        await show_profile(update, context, user_data)
    elif text in ["📊 My Progress", "📊 የእኔ ግስጋሴ"]:
        await show_progress(update, context, user_data)
    elif text in ["⚙️ Settings", "⚙️ ቅንብሮች"]:
        await update.message.reply_text(
            "⚙️ " + ("ቅንብሮች" if lang == 'am' else "Settings"),
            reply_markup=Menu.get_settings_menu(lang)
        )
    elif text in ["🔄 Restart Plan", "🔄 እቅድ ይጀምሩ"]:
        # Logic to restart - simplified for now
        db.add_user(user_id, user_data['username'], user_data['first_name'], user_data['plan_name'], user_data['translation'], lang)
        msg = "🔄 Plan restarted from Day 1" if lang == 'en' else "🔄 እቅዱ ከቀን 1 እንደገና ተጀምሯል"
        await update.message.reply_text(msg)
    elif text in ["📤 Share Bot", "📤 ቦቱን ያጋሩ"]:
        bot_link = f"https://t.me/{context.bot.username}"
        share_msg = ("Invite your friends to read the Bible with you!\n\n" if lang == 'en' else "ጓደኞችዎ አብረውዎት መጽሐፍ ቅዱስን እንዲያነቡ ይጋብዙ!\n\n") + bot_link
        await update.message.reply_text(share_msg)
    elif text in ["❓ Help", "❓ እርዳታ"]:
        await update.message.reply_text(Menu.get_help_text(lang), parse_mode='Markdown')

async def show_todays_reading(update: Update, context: ContextTypes.DEFAULT_TYPE, user_data):
    """Show today's reading for the user"""
    user_id = user_data['user_id']
    lang = user_data['language']
    
    # Check if already read today
    if db.get_todays_reading(user_id):
        msg = "You've already completed today's reading! Keep it up! 🔥" if lang == 'en' else "የዛሬውን ንባብ አስቀድመው ጨርሰዋል! በርቱ! 🔥"
        await update.message.reply_text(msg)
        return

    reading = reading_plans.get_todays_reading(user_data['plan_name'], user_data['current_day'])
    
    if reading:
        book = reading['book']
        chapters = reading['chapters']
        
        # Translate book name for display if Amharic
        book_display = reading_plans.amharic_book_names.get(book, book) if lang == 'am' else book
        
        for chapter in chapters:
            text = bible_api.get_text(book, chapter, user_data['translation'])
            # Add share button
            keyboard = [[InlineKeyboardButton("📤 Share", callback_data=f"share_{book}_{chapter}")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(text, reply_markup=reply_markup)
            
        # Update progress and get current streak
        streak = db.update_user_progress(user_id, user_data['current_day'], book, chapters[0])
        
        # Check for achievements
        await check_achievements(update, context, user_id, streak, user_data['current_day'], lang)
        
        completion_msg = "✅ Reading marked as complete!" if lang == 'en' else "✅ ንባቡ ተጠናቅቋል ተብሎ ተመዝግቧል!"
        completion_msg += f"\n🔥 Streak: {streak} days"
        await update.message.reply_text(completion_msg)
    else:
        congrats = "🎉 Congratulations! You've finished your reading plan." if lang == 'en' else "🎉 እንኳን ደስ አለዎት! የንባብ እቅድዎን ጨርሰዋል።"
        await update.message.reply_text(congrats)

async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE, user_data):
    """Show user profile, stats, and achievements"""
    lang = user_data['language']
    user_id = user_data['user_id']
    
    achievements = db.get_achievements(user_id)
    ach_list = ""
    if not achievements:
        ach_list = "No achievements yet." if lang == 'en' else "እስካሁን ምንም ሽልማት የለም።"
    else:
        for ach in achievements:
            ach_list += f"• {ach[0]} ({ach[1]})\n"
            
    if lang == 'am':
        text = (
            f"👤 **ፕሮፋይል፦ {user_data['first_name']}**\n\n"
            f"🔥 ወቅታዊ ግስጋሴ፦ {user_data['streak']} ቀናት\n"
            f"🏆 ከፍተኛ ግስጋሴ፦ {user_data['max_streak']} ቀናት\n"
            f"📚 እቅድ፦ {READING_PLANS[user_data['plan_name']]['name'][lang]}\n"
            f"📖 ትርጉም፦ {BIBLE_TRANSLATIONS.get(user_data['translation'], user_data['translation'])}\n\n"
            f"🏅 **የተገኙ ሽልማቶች፦**\n{ach_list}"
        )
    else:
        text = (
            f"👤 **Profile: {user_data['first_name']}**\n\n"
            f"🔥 Current Streak: {user_data['streak']} days\n"
            f"🏆 Longest Streak: {user_data['max_streak']} days\n"
            f"📚 Plan: {READING_PLANS[user_data['plan_name']]['name'][lang]}\n"
            f"📖 Translation: {BIBLE_TRANSLATIONS.get(user_data['translation'], user_data['translation'])}\n\n"
            f"🏅 **Achievements:**\n{ach_list}"
        )
        
    await update.message.reply_text(text, parse_mode='Markdown')

async def show_progress(update: Update, context: ContextTypes.DEFAULT_TYPE, user_data):
    """Show detailed progress charts/stats"""
    lang = user_data['language']
    total_days = READING_PLANS[user_data['plan_name']]['total_days']
    current_day = user_data['current_day']
    percentage = (current_day / total_days) * 100
    
    # Progress bar
    bars = 15
    filled = int((current_day / total_days) * bars)
    bar = "🟩" * filled + "⬜" * (bars - filled)
    
    if lang == 'am':
        text = (
            f"📊 **የንባብ ግስጋሴ**\n\n"
            f"እቅድ፦ {READING_PLANS[user_data['plan_name']]['name'][lang]}\n"
            f"ቀን፦ {current_day} ከ {total_days}\n"
            f"በመቶኛ፦ {percentage:.1f}%\n\n"
            f"{bar}"
        )
    else:
        text = (
            f"📊 **Reading Progress**\n\n"
            f"Plan: {READING_PLANS[user_data['plan_name']]['name'][lang]}\n"
            f"Day: {current_day} of {total_days}\n"
            f"Completion: {percentage:.1f}%\n\n"
            f"{bar}"
        )
        
    await update.message.reply_text(text, parse_mode='Markdown')

async def check_achievements(update, context, user_id, streak, total_reads, lang):
    """Check and award achievements"""
    awards = []
    
    if streak == 7:
        awards.append("🔥 7-Day Flame" if lang == 'en' else "🔥 የ7 ቀን እሳት")
    elif streak == 30:
        awards.append("⭐ Monthly Star" if lang == 'en' else "⭐ የወር ኮከብ")
        
    if total_reads == 1:
        awards.append("🌱 First Step" if lang == 'en' else "🌱 የመጀመሪያው እርምጃ")
    elif total_reads == 100:
        awards.append("🏆 Century Club" if lang == 'en' else "🏆 የመቶዎች ክለብ")

    for award in awards:
        db.add_achievement(user_id, award)
        celebration = "🎊 New Achievement Unlocked! 🎊\n\n" if lang == 'en' else "🎊 አዲስ ሽልማት ተገኝቷል! 🎊\n\n"
        await update.message.reply_text(celebration + award)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel registration"""
    await update.message.reply_text("Cancelled.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def main():
    token = os.getenv('BOT_TOKEN')
    if not token:
        print("❌ BOT_TOKEN missing!")
        return
        
    application = Application.builder().token(token).build()
    
    # Onboarding conversation
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSING_LANGUAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, language_chosen)],
            CHOOSING_PLAN: [MessageHandler(filters.TEXT & ~filters.COMMAND, plan_chosen)],
            CHOOSING_TRANSLATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, translation_chosen)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    
    application.add_handler(conv_handler)
    
    # Main menu handler
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu_click))
    
    # Generic commands
    application.add_handler(CommandHandler('help', lambda u, c: u.message.reply_text(Menu.get_help_text())))
    
    print("🤖 Bible Bot is running...")
    application.run_polling()

if __name__ == '__main__':
    main()