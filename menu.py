# menu.py - Interactive menu system for the bot
from telegram import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from config import LANGUAGES, READING_PLANS

class Menu:
    @staticmethod
    def get_main_menu(language='en'):
        """Get the main bottom navigation menu"""
        if language == 'am':
            keyboard = [
                ["📖 የዛሬው ንባብ"],
                ["👤 የእኔ ፕሮፋይል", "📊 የእኔ ግስጋሴ"],
                ["⚙️ ቅንብሮች", "🔄 እቅድ ይጀምሩ"],
                ["📤 ቦቱን ያጋሩ", "❓ እርዳታ"]
            ]
        else:
            keyboard = [
                ["📖 TODAY'S READING"],
                ["👤 My Profile", "📊 My Progress"],
                ["⚙️ Settings", "🔄 Restart Plan"],
                ["📤 Share Bot", "❓ Help"]
            ]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    @staticmethod
    def get_language_menu():
        """Get language selection menu"""
        keyboard = [
            [InlineKeyboardButton("English 🇺🇸", callback_data="lang_en")],
            [InlineKeyboardButton("አማርኛ 🇪🇹", callback_data="lang_am")]
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def get_plan_menu(language='en'):
        """Get reading plan selection menu"""
        # Build dynamically from config so new plans appear automatically.
        icon_cycle = ["1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9.", "10."]
        keyboard = []
        for idx, plan in enumerate(READING_PLANS.values()):
            label = plan['name'].get(language, plan['name'].get('en', 'Plan'))
            keyboard.append([f"{icon_cycle[idx % len(icon_cycle)]} {label}"])
        return ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

    @staticmethod
    def get_translation_menu(language='en'):
        """Get translation selection menu"""
        if language == 'am':
            keyboard = [["AMH (አማርኛ)", "ESV", "KJV"]]
        else:
            keyboard = [["Amharic", "ESV", "KJV"]]
            
        return ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

    @staticmethod
    def get_settings_menu(language='en'):
        """Get settings inline menu"""
        if language == 'am':
            keyboard = [
                [InlineKeyboardButton("🌐 ቋንቋ ቀይር", callback_data="set_lang")],
                [InlineKeyboardButton("📖 ትርጉም ቀይር", callback_data="set_trans")],
                [InlineKeyboardButton("📚 እቅዱን ቀይር", callback_data="set_plan")],
                [InlineKeyboardButton("⏰ ማስታወሻዎችን ቀይር", callback_data="set_times")]
            ]

        else:
            keyboard = [
                [InlineKeyboardButton("🌐 Change Language", callback_data="set_lang")],
                [InlineKeyboardButton("📖 Change Translation", callback_data="set_trans")],
                [InlineKeyboardButton("📚 Change Plan", callback_data="set_plan")],
                [InlineKeyboardButton("⏰ Change Notification Times", callback_data="set_times")]
            ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def get_time_selection_menu(selected_times=None, language='en'):
        """Get notification time selection menu"""
        if selected_times is None:
            selected_times = []
            
        from config import NOTIFICATION_TIMES
        
        keyboard = []
        row = []
        for time in NOTIFICATION_TIMES:
            # Mark selected times with checkmark or disable
            label = f"✅ {time}" if time in selected_times else time
            # If already 2 selected, maybe allow deselecting? 
            # For simplicity, we assume sequential selection of 2 different times.
            
            row.append(InlineKeyboardButton(label, callback_data=f"time_{time}"))
            if len(row) == 3:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)
            
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def get_yes_no_menu(language='en', action='restart'):
        """Get Yes/No confirmation menu"""
        yes_lbl = "አዎ" if language == 'am' else "Yes"
        no_lbl = "አይ" if language == 'am' else "No"
        
        keyboard = [
            [
                InlineKeyboardButton(f"✅ {yes_lbl}", callback_data=f"{action}_yes"),
                InlineKeyboardButton(f"❌ {no_lbl}", callback_data=f"{action}_no")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)


    @staticmethod
    def get_help_text(language='en'):
        """Get help message text"""
        if language == 'am':
            return (
                "❓ **እርዳታ**\n\n"
                "ይህ ቦት መጽሐፍ ቅዱስን በየቀኑ እንዲያነቡ ይረዳዎታል፦\n"
                "• **የዛሬው ንባብ**: የዕለቱን ጥቅሶች ያግኙ\n"
                "• **ፕሮፋይል**: የእርስዎን ግስጋሴ እና ሽልማቶች ይመልከቱ\n"
                "• **ቅንብሮች**: ቋንቋ ወይም ትርጉም ይቀይሩ\n\n"
                "ማንኛውም ጥያቄ ካለዎት እባክዎ ያነጋግሩን።"
            )
        else:
            return (
                "❓ **Help & FAQ**\n\n"
                "This bot helps you stay consistent with Bible reading:\n"
                "• **Today's Reading**: Get your daily passages\n"
                "• **My Profile**: View your streaks and achievements\n"
                "• **Settings**: Change language or translation\n\n"
                "If you have any issues, feel free to reach out!"
            )
