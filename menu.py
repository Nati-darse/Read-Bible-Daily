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
        if language == 'am':
            keyboard = [
                ["📖 መጽሐፍ ቅዱስ በአንድ ዓመት"],
                ["🙏 መዝሙረ ዳዊት በአንድ ወር"],
                ["✝️ አዲስ ኪዳን በ6 ወራት"]
            ]
        else:
            keyboard = [
                ["📖 Bible in One Year"],
                ["🙏 Psalms in One Month"],
                ["✝️ New Testament in 6 Months"]
            ]
        return ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

    @staticmethod
    def get_translation_menu(language='en'):
        """Get translation selection menu"""
        keyboard = [["ESV", "KJV", "NIV"]]
        if language == 'am':
            keyboard[0].append("AMH (አማርኛ)")
        else:
            keyboard[0].append("Amharic")
            
        return ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

    @staticmethod
    def get_settings_menu(language='en'):
        """Get settings inline menu"""
        if language == 'am':
            keyboard = [
                [InlineKeyboardButton("🌐 ቋንቋ ቀይር", callback_data="set_lang")],
                [InlineKeyboardButton("📖 ትርጉም ቀይር", callback_data="set_trans")],
                [InlineKeyboardButton("📚 እቅዱን ቀይር", callback_data="set_plan")]
            ]
        else:
            keyboard = [
                [InlineKeyboardButton("🌐 Change Language", callback_data="set_lang")],
                [InlineKeyboardButton("📖 Change Translation", callback_data="set_trans")],
                [InlineKeyboardButton("📚 Change Plan", callback_data="set_plan")]
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
