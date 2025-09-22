# config.py - Configuration settings for your bot

# Bible translation options
BIBLE_TRANSLATIONS = {
    'ESV': 'English Standard Version',
    'KJV': 'King James Version',
    'NIV': 'New International Version'
}

# Reading plans
READING_PLANS = {
    'bible_in_one_year': {
        'name': 'Bible in One Year',
        'description': 'Read the entire Bible in 365 days',
        'total_days': 365
    },
    'psalms_in_one_month': {
        'name': 'Psalms in One Month',
        'description': 'Read the Book of Psalms in 30 days',
        'total_days': 30
    },
    'new_testament_in_six_months': {
        'name': 'New Testament in 6 Months',
        'description': 'Read the New Testament in 180 days',
        'total_days': 180
    }
}

# Bot settings
BOT_SETTINGS = {
    'daily_reminder_time': '08:00',  # 8:00 AM
    'default_translation': 'ESV'
}