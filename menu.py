# menu.py - Interactive menu system for the bot
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup

from config import NOTIFICATION_TIMES, READING_PLANS


class Menu:
    @staticmethod
    def get_main_menu(language='en'):
        """Get the main bottom navigation menu."""
        if language == 'am':
            keyboard = [
                ["Today's Reading"],
                ["My Profile", "My Progress"],
                ["Favorites", "History"],
                ["Settings", "Restart Plan"],
                ["Share Bot", "Help"],
            ]
        else:
            keyboard = [
                ["TODAY'S READING"],
                ["My Profile", "My Progress"],
                ["Favorites", "History"],
                ["Settings", "Restart Plan"],
                ["Share Bot", "Help"],
            ]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    @staticmethod
    def get_language_menu():
        """Get language selection menu."""
        keyboard = [
            [InlineKeyboardButton("English", callback_data="lang_en")],
            [InlineKeyboardButton("Amharic", callback_data="lang_am")],
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def get_plan_menu(language='en'):
        """Get reading plan selection menu."""
        icon_cycle = ["1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9.", "10."]
        keyboard = []
        for idx, plan in enumerate(READING_PLANS.values()):
            label = plan['name'].get(language, plan['name'].get('en', 'Plan'))
            keyboard.append([f"{icon_cycle[idx % len(icon_cycle)]} {label}"])
        return ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

    @staticmethod
    def get_translation_menu(language='en'):
        """Get translation selection menu."""
        if language == 'am':
            keyboard = [["AMH", "ESV", "KJV"]]
        else:
            keyboard = [["Amharic", "ESV", "KJV"]]
        return ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

    @staticmethod
    def get_settings_menu(language='en'):
        """Get settings inline menu."""
        if language == 'am':
            keyboard = [
                [InlineKeyboardButton("Change Language", callback_data="set_lang")],
                [InlineKeyboardButton("Change Translation", callback_data="set_trans")],
                [InlineKeyboardButton("Change Plan", callback_data="set_plan")],
                [InlineKeyboardButton("Change Notification Times", callback_data="set_times")],
            ]
        else:
            keyboard = [
                [InlineKeyboardButton("Change Language", callback_data="set_lang")],
                [InlineKeyboardButton("Change Translation", callback_data="set_trans")],
                [InlineKeyboardButton("Change Plan", callback_data="set_plan")],
                [InlineKeyboardButton("Change Notification Times", callback_data="set_times")],
            ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def get_time_selection_menu(selected_times=None, language='en'):
        """Get notification time selection menu."""
        if selected_times is None:
            selected_times = []

        keyboard = []
        row = []
        for time in NOTIFICATION_TIMES:
            label = f"Selected {time}" if time in selected_times else time
            row.append(InlineKeyboardButton(label, callback_data=f"time_{time}"))
            if len(row) == 3:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)

        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def get_yes_no_menu(language='en', action='restart'):
        """Get Yes/No confirmation menu."""
        keyboard = [
            [
                InlineKeyboardButton("Yes", callback_data=f"{action}_yes"),
                InlineKeyboardButton("No", callback_data=f"{action}_no"),
            ]
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def get_help_text(language='en'):
        """Get help message text."""
        return (
            "**Help & FAQ**\n\n"
            "This bot helps you stay consistent with Bible reading:\n"
            "- **Today's Reading**: Get your daily passages\n"
            "- **My Profile**: View your streaks and achievements\n"
            "- **My Progress**: View plan progress and reading stats\n"
            "- **Favorites**: View saved readings, or use /favorites\n"
            "- **History**: View recently completed readings, or use /history\n"
            "- **Settings**: Change language, translation, plan, or notification times\n\n"
            "Use /start any time to open the menu again."
        )
