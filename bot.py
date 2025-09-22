# bot.py - Main Telegram bot
import os
import logging
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters, 
    ContextTypes, ConversationHandler
)

# Import our modules
from config import READING_PLANS, BIBLE_TRANSLATIONS
from database import db
from reading_plans import reading_plans

# Load environment variables
load_dotenv()

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation states
CHOOSING_PLAN, CHOOSING_TRANSLATION = range(2)

# Bible API function
def get_bible_text(book, chapter, translation='ESV'):
    """Fetch Bible text from free API"""
    import requests
    
    # Format book name for API (replace spaces with +)
    book_formatted = book.replace(' ', '+')
    
    try:
        url = f"https://bible-api.com/{book_formatted}+{chapter}?translation={translation}"
        response = requests.get(url)
        data = response.json()
        
        if 'error' in data:
            return f"Sorry, couldn't fetch {book} {chapter}. Please try again later."
        
        verses = data.get('verses', [])
        text = f"📖 {book} Chapter {chapter} ({translation})\n\n"
        
        for verse in verses:
            text += f"{verse['verse']}. {verse['text']}\n"
        
        return text[:4000]  # Telegram message limit
        
    except Exception as e:
        logger.error(f"Error fetching Bible text: {e}")
        return f"❌ Error fetching {book} {chapter}. Please try again later."

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message and show plan options"""
    user = update.effective_user
    user_id = user.id
    
    # Check if user already exists
    existing_user = db.get_user(user_id)
    
    if existing_user:
        # User already registered, show today's reading
        await show_todays_reading(update, context, user_id)
        return ConversationHandler.END
    
    # New user - show plan options
    keyboard = [
        ["📖 Bible in One Year", "🙏 Psalms in One Month"],
        ["✝️ New Testament in 6 Months"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    
    await update.message.reply_text(
        f"👋 Welcome {user.first_name} to Daily Bible Reader!\n\n"
        "📚 Choose your reading plan:",
        reply_markup=reply_markup
    )
    
    return CHOOSING_PLAN

async def plan_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle plan selection"""
    plan_choice = update.message.text
    
    # Map display names to plan keys
    plan_mapping = {
        "📖 Bible in One Year": "bible_in_one_year",
        "🙏 Psalms in One Month": "psalms_in_one_month",
        "✝️ New Testament in 6 Months": "new_testament_in_six_months"
    }
    
    plan_key = plan_mapping.get(plan_choice, "bible_in_one_year")
    context.user_data['plan'] = plan_key
    
    # Show translation options
    keyboard = [["ESV", "KJV", "NIV"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    
    await update.message.reply_text(
        "📖 Choose your preferred Bible translation:",
        reply_markup=reply_markup
    )
    
    return CHOOSING_TRANSLATION

async def translation_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle translation selection and complete registration"""
    translation = update.message.text
    user = update.effective_user
    
    if translation not in ["ESV", "KJV", "NIV"]:
        translation = "ESV"  # Default
    
    # Save user to database
    db.add_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        plan_name=context.user_data['plan'],
        translation=translation
    )
    
    await update.message.reply_text(
        f"✅ Registration complete!\n\n"
        f"📚 Plan: {READING_PLANS[context.user_data['plan']]['name']}\n"
        f"📖 Translation: {translation}\n\n"
        f"Use /today to get today's reading\n"
        f"Use /progress to see your progress\n"
        f"Use /settings to change your plan",
        reply_markup=ReplyKeyboardRemove()
    )
    
    # Show today's reading
    await show_todays_reading(update, context, user.id)
    
    return ConversationHandler.END

async def show_todays_reading(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id=None):
    """Show today's Bible reading"""
    if user_id is None:
        user_id = update.effective_user.id
    
    user_data = db.get_user(user_id)
    
    if not user_data:
        await update.message.reply_text("Please use /start to register first!")
        return
    
    # Check if already read today
    already_read = db.get_todays_reading(user_id)
    
    if already_read:
        await update.message.reply_text("You've already read today's passage! 📖")
        return
    
    # Get today's reading
    reading = reading_plans.get_todays_reading(
        user_data['plan_name'], 
        user_data['current_day']
    )
    
    if reading:
        book = reading['book']
        chapters = reading['chapters']
        
        # Send each chapter
        for chapter in chapters:
            bible_text = get_bible_text(book, chapter, user_data['translation'])
            
            # Add share button at the end
            share_text = f"\n\n📤 Share this verse: /share_{book}_{chapter}"
            full_text = bible_text + share_text
            
            await update.message.reply_text(full_text)
        
        # Update progress
        db.update_user_progress(user_id, user_data['current_day'], book, chapters[0])
        
        # Show progress
        total_days = READING_PLANS[user_data['plan_name']]['total_days']
        progress = f"📊 Day {user_data['current_day']} of {total_days} "
        progress += f"({(user_data['current_day']/total_days)*100:.1f}%)"
        
        await update.message.reply_text(progress)
    else:
        await update.message.reply_text("🎉 Congratulations! You've completed your reading plan!")

async def today_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /today command"""
    await show_todays_reading(update, context)

async def progress_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /progress command"""
    user_id = update.effective_user.id
    user_data = db.get_user(user_id)
    
    if not user_data:
        await update.message.reply_text("Please use /start to register first!")
        return
    
    total_days = READING_PLANS[user_data['plan_name']]['total_days']
    percentage = (user_data['current_day'] / total_days) * 100
    
    progress_text = f"📊 Your Reading Progress\n\n"
    progress_text += f"📚 Plan: {READING_PLANS[user_data['plan_name']]['name']}\n"
    progress_text += f"📖 Translation: {user_data['translation']}\n"
    progress_text += f"📅 Started: {user_data['start_date']}\n"
    progress_text += f"🔢 Current Day: {user_data['current_day']} of {total_days}\n"
    progress_text += f"📈 Progress: {percentage:.1f}%\n\n"
    
    # Progress bar
    bars = 20
    filled_bars = int(percentage / 100 * bars)
    progress_bar = "█" * filled_bars + "░" * (bars - filled_bars)
    progress_text += f"{progress_bar}"
    
    await update.message.reply_text(progress_text)

async def share_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle share command"""
    # Extract book and chapter from command
    command_text = update.message.text
    if '_' in command_text:
        parts = command_text.split('_')
        if len(parts) >= 3:
            book = parts[1]
            chapter = parts[2]
            
            share_text = f"📖 {book} Chapter {chapter}\n\n"
            share_text += f"Shared via Daily Bible Reader Bot\n"
            share_text += f"Start your reading plan with /start"
            
            await update.message.reply_text(share_text)
            return
    
    await update.message.reply_text("Use /today to get today's reading and share it!")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel the conversation"""
    await update.message.reply_text(
        'Registration cancelled. Use /start to begin again.',
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

def main():
    """Start the bot"""
    # Get token from environment
    token = os.getenv('BOT_TOKEN')
    
    if not token:
        print("❌ ERROR: BOT_TOKEN not found in .env file!")
        return
    
    # Create application
    application = Application.builder().token(token).build()
    
    # Conversation handler for registration
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSING_PLAN: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, plan_chosen)
            ],
            CHOOSING_TRANSLATION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, translation_chosen)
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    
    # Add handlers
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler('today', today_command))
    application.add_handler(CommandHandler('progress', progress_command))
    application.add_handler(CommandHandler('share', share_command))
    
    # Start the bot
    print("🤖 Bible Bot is starting...")
    application.run_polling()

if __name__ == '__main__':
    main()