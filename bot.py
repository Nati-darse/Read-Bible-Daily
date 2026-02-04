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
    level=logging.DEBUG
)
logger = logging.getLogger(__name__)

# Conversation states
CHOOSING_LANGUAGE, CHOOSING_PLAN, CHOOSING_TRANSLATION, CHOOSING_TIMES = range(4)


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
        
    context.user_data['translation'] = translation
    
    # Save partial user data to context to persist through next step
    # Ask for first notification time
    await update.message.reply_text(
        MESSAGES['choose_times_1'][lang],
        reply_markup=Menu.get_time_selection_menu()
    )
    
    return CHOOSING_TIMES

async def times_chosen_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle notification time selection (Callback)"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    time_selected = data.split('_')[1]
    
    user_times = context.user_data.get('notification_times', [])
    
    # Check if this is the first or second selection
    if len(user_times) == 0:
        user_times.append(time_selected)
        context.user_data['notification_times'] = user_times
        lang = context.user_data.get('language', 'en')
        
        # Ask for second time
        await query.message.reply_text(
            MESSAGES['choose_times_2'][lang],
            reply_markup=Menu.get_time_selection_menu(selected_times=user_times)
        )
        return CHOOSING_TIMES
        
    else:
        # Second time selected
        if time_selected not in user_times:
            user_times.append(time_selected)
        
        # Save everything to DB
        user = update.effective_user
        lang = context.user_data.get('language', 'en')
        
        # Combine times into string
        times_str = ",".join(user_times)
        
        # If user exists, just update times. If new, add user.
        existing = db.get_user(user.id)
        if existing:
             db.update_notification_times(user.id, times_str)
        else:
            db.add_user(
                user_id=user.id,
                username=user.username,
                first_name=user.first_name,
                plan_name=context.user_data['plan'],
                translation=context.user_data['translation'],
                language=lang
            )
            db.update_notification_times(user.id, times_str)
            
        plan_name = READING_PLANS[context.user_data['plan']]['name'][lang]
        trans_name = BIBLE_TRANSLATIONS.get(context.user_data['translation'], context.user_data['translation'])
        
        await query.message.reply_text(
            MESSAGES['registration_complete'][lang].format(plan=plan_name, translation=trans_name),
            reply_markup=Menu.get_main_menu(lang)
        )
        
        # Show reading
        user_data = db.get_user(user.id)
        if user_data:
            await show_todays_reading(query, context, user_data)
            
        return ConversationHandler.END



async def handle_menu_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle main menu button clicks"""
    text = update.message.text
    user_id = update.effective_user.id
    logger.info(f"Menu click from {user_id}: {text}")
    
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

        msg = "⚠️ Are you sure you want to restart your plan from Day 1? This cannot be undone." if lang == 'en' else "⚠️ እቅድዎን ከቀን 1 እንደገና መጀመር ይፈልጋሉ? ይህን እርምጃ መቀልበስ አይቻልም።"
        await update.message.reply_text(msg, reply_markup=Menu.get_yes_no_menu(lang, 'restart'))

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
    logger.info(f"Reading for {user_id} (Day {user_data['current_day']}): {reading}")
    
    if reading:
        book = reading['book']
        chapters = reading['chapters']
        logger.info(f"Targeting: {book} Chapters {chapters}")
        
        # Translate book name for display if Amharic
        book_display = reading_plans.amharic_book_names.get(book, book) if lang == 'am' else book
        
        try:
            for chapter in chapters:
                text = bible_api.get_text(book, chapter, user_data['translation'])
                logger.info(f"Fetched text for {book} {chapter} ({user_data['translation']}), length: {len(text)}")
                
                # Add share button
                share_label = "📤 አጋራ" if lang == 'am' else "📤 Share"
                keyboard = [[InlineKeyboardButton(share_label, callback_data=f"share_{book}_{chapter}")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text(text, reply_markup=reply_markup)
                
            # Update progress and get current streak
            streak = db.update_user_progress(user_id, user_data['current_day'], book, chapters[0])
            
            # Check for achievements
            await check_achievements(update, context, user_id, streak, user_data['current_day'], lang)
            
            completion_msg = "✅ Reading marked as complete!" if lang == 'en' else "✅ ንባቡ ተጠናቅቋል ተብሎ ተመዝግቧል!"
            streak_label = "ቀናት" if lang == 'am' else "days"
            completion_msg += f"\n🔥 Streak: {streak} {streak_label}"
            await update.message.reply_text(completion_msg)

        except Exception as e:
            logger.error(f"Error in show_todays_reading for user {user_id}: {e}")
            error_msg = "❌ Sorry, an error occurred while fetching your reading. Please try again or /start."
            if lang == 'am':
                error_msg = "❌ የዛሬውን ንባብ በማቅረብ ላይ ስህተት ተከስቷል። እባክዎ እንደገና ይሞክሩ።"
            await update.message.reply_text(error_msg)
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

async def settings_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle settings menu button clicks to start configuration flow"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = update.effective_user.id
    user_data = db.get_user(user_id)
    lang = user_data['language'] if user_data else 'en'
    
    # Ensure language is in context for next steps
    context.user_data['language'] = lang
    if user_data:
        context.user_data['plan'] = user_data.get('plan_name', 'bible_in_one_year')
    
    if data == 'set_lang':
        keyboard = [["English", "አማርኛ (Amharic)"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        await query.message.reply_text(
            MESSAGES['choose_language'][lang],
            reply_markup=reply_markup
        )
        return CHOOSING_LANGUAGE
        
    elif data == 'set_plan':
        await query.message.reply_text(
            MESSAGES['welcome'][lang].format(name=update.effective_user.first_name),
            reply_markup=Menu.get_plan_menu(lang)
        )
        return CHOOSING_PLAN
        
    elif data == 'set_trans':
        # Ensure we have a plan in context, otherwise default or ask
        if 'plan' not in context.user_data:
             context.user_data['plan'] = 'bible_in_one_year'
             
        await query.message.reply_text(
            MESSAGES['choose_translation'][lang],
            reply_markup=Menu.get_translation_menu(lang)
        )
        return CHOOSING_TRANSLATION

    elif data == 'set_times':
        context.user_data['notification_times'] = [] # Reset selection
        await query.message.reply_text(
            MESSAGES['choose_times_1'][lang],
            reply_markup=Menu.get_time_selection_menu()
        )
        return CHOOSING_TIMES


async def handle_share_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle share button click"""
    query = update.callback_query
    await query.answer()
    
    # Format: share_Book_Chapter
    try:
        _, book, chapter = query.data.split('_', 2)
        lang = context.user_data.get('language', 'en')
        
        # In a real app, this would generate a deep link or share text
        # For now, just provide a copyable text
        share_text = f"Read {book} {chapter} with me on Daily Bible Bot! @{context.bot.username}"
        if lang == 'am':
            share_text = f"በ Daily Bible Bot ላይ {book} {chapter} አብረን እናንብብ! @{context.bot.username}"
            
        await query.message.reply_text(share_text)
    except Exception as e:
        logger.error(f"Share callback error: {e}")

async def handle_restart_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle restart confirmation"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = update.effective_user.id
    user_data = db.get_user(user_id)
    lang = user_data['language'] if user_data else 'en'
    
    if data == 'restart_yes':
        # Reset user safely
        db.reset_user_progress(user_id)
        msg = "🔄 Plan restarted from Day 1." if lang == 'en' else "🔄 እቅዱ ከቀን 1 እንደገና ተጀምሯል::"
        await query.message.edit_text(msg)
    else:
        msg = "❌ Restart cancelled." if lang == 'en' else "❌ እንደገና መጀመር ተሰርዟል።"
        await query.message.edit_text(msg)

async def check_notifications(context: ContextTypes.DEFAULT_TYPE):
    """Job to check and send notifications"""
    # Get current time rounded to hour:00 usually
    now_str = datetime.now().strftime('%H:00')
    logger.info(f"Checking notifications for {now_str}")
    
    # Get users who want notifications at this time
    users_to_notify = db.get_users_with_notification_time(now_str)
    
    for user in users_to_notify:
        try:
            # We construct a fake user_data dict to reuse show_todays_reading logic if possible
            # But show_todays_reading takes update object which we don't have.
            # So we manually fetch reading and send.
            user_id = user['user_id']
            lang = user['language']
            
            # Send the reading
            # We can reuse the logic but verify inputs
            if db.get_todays_reading(user_id):
                 logger.info(f"User {user_id} already read today, skipping notification.")
                 continue
                 
            reading = reading_plans.get_todays_reading(user['plan_name'], user['current_day'])
            if reading:
                book = reading['book']
                chapters = reading['chapters']
                book_display = reading_plans.amharic_book_names.get(book, book) if lang == 'am' else book
                
                header = f"🔔 Daily Reminder / ዕለታዊ ማስታወሻ\n\n"
                await context.bot.send_message(user_id, header)
                
                # Fetch text loop
                for chapter in chapters:
                    text = bible_api.get_text(book, chapter, user['translation'])
                    # Share button
                    share_label = "📤 አጋራ" if lang == 'am' else "📤 Share"
                    keyboard = [[InlineKeyboardButton(share_label, callback_data=f"share_{book}_{chapter}")]]
                    await context.bot.send_message(user_id, text, reply_markup=InlineKeyboardMarkup(keyboard))
                    
                # We do NOT mark as read automatically on notification? 
                # Usually better to let them read it. But sending the text IS reading it.
                # Let's mark it done.
                db.update_user_progress(user_id, user['current_day'], book, chapters[0])
                
            logger.error(f"Error sending notification to {user['user_id']}: {e}")



# Dummy server for Render
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is active")

def start_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    logger.info(f"dummy server listening on port {port}")
    server.serve_forever()

def main():
    token = os.getenv('BOT_TOKEN')
    if not token:
        print("❌ BOT_TOKEN missing!")
        return
        
    application = Application.builder().token(token).connect_timeout(60).read_timeout(60).build()
    
    # Onboarding conversation
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('start', start),
            CallbackQueryHandler(settings_entry, pattern='^set_')
        ],
        states={
            CHOOSING_LANGUAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, language_chosen)],
            CHOOSING_PLAN: [MessageHandler(filters.TEXT & ~filters.COMMAND, plan_chosen)],
            CHOOSING_TRANSLATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, translation_chosen)],
            CHOOSING_TIMES: [CallbackQueryHandler(times_chosen_callback, pattern='^time_')]
        },
        fallbacks=[CommandHandler('cancel', cancel)],

    )
    
    application.add_handler(conv_handler)
    
    # Share button handler
    application.add_handler(CallbackQueryHandler(handle_share_callback, pattern='^share_'))
    
    # Main menu handler
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu_click))
    
    # Restart confirmation handler
    application.add_handler(CallbackQueryHandler(handle_restart_callback, pattern='^restart_'))
    
    # Setup job queue
    job_queue = application.job_queue
    # Run every hour to check for notifications
    # First run in 10 seconds
    job_queue.run_repeating(check_notifications, interval=3600, first=10)
    
    # Generic commands

    application.add_handler(CommandHandler('help', lambda u, c: u.message.reply_text(Menu.get_help_text())))
    
    print("🤖 Bible Bot is running...")
    
    # Start dummy server in background thread
    threading.Thread(target=start_dummy_server, daemon=True).start()
    
    application.run_polling()

if __name__ == '__main__':
    main()