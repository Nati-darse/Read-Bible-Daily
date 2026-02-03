# config.py - Configuration settings for your bot

# Supported Languages
LANGUAGES = {
    'en': 'English',
    'am': 'Amharic (አማርኛ)'
}

# Bible translation options
BIBLE_TRANSLATIONS = {
    'ESV': 'English Standard Version',
    'KJV': 'King James Version',
    'NIV': 'New International Version',
    'AMH': 'Amharic Bible (አማርኛ)'
}

# Reading plans
READING_PLANS = {
    'bible_in_one_year': {
        'name': {
            'en': 'Bible in One Year',
            'am': 'መጽሐፍ ቅዱስ በአንድ ዓመት'
        },
        'description': {
            'en': 'Read the entire Bible in 365 days',
            'am': 'መላውን መጽሐፍ ቅዱስ በ365 ቀናት ውስጥ ያንብቡ'
        },
        'total_days': 365
    },
    'psalms_in_one_month': {
        'name': {
            'en': 'Psalms in One Month',
            'am': 'መዝሙረ ዳዊት በአንድ ወር'
        },
        'description': {
            'en': 'Read the Book of Psalms in 30 days',
            'am': 'መዝሙረ ዳዊትን በ30 ቀናት ውስጥ ያንብቡ'
        },
        'total_days': 30
    },
    'new_testament_in_six_months': {
        'name': {
            'en': 'New Testament in 6 Months',
            'am': 'አዲስ ኪዳን በ6 ወራት'
        },
        'description': {
            'en': 'Read the New Testament in 180 days',
            'am': 'አዲስ ኪዳንን በ180 ቀናት ውስጥ ያንብቡ'
        },
        'total_days': 180
    }
}

# UI Text and Messages
MESSAGES = {
    'welcome': {
        'en': "👋 Welcome {name} to Daily Bible Reader!\n\n📚 Choose your reading plan:",
        'am': "👋 እንኳን ወደ ዕለታዊ የመጽሐፍ ቅዱስ ንባብ በደህና መጡ {name}!\n\n📚 የንባብ እቅድዎን ይምረጡ፦"
    },
    'choose_language': {
        'en': "🌍 Choose your language / ቋንቋ ይምረጡ:",
        'am': "🌍 Choose your language / ቋንቋ ይምረጡ:"
    },
    'choose_translation': {
        'en': "📖 Choose your preferred Bible translation:",
        'am': "📖 የሚመርጡትን የመጽሐፍ ቅዱስ ትርጉም ይምረጡ፦"
    },
    'registration_complete': {
        'en': "✅ Registration complete!\n\n📚 Plan: {plan}\n📖 Translation: {translation}\n\nUse the menu below to navigate.",
        'am': "✅ ምዝገባው ተጠናቅቋል!\n\n📚 እቅድ፦ {plan}\n📖 ትርጉም፦ {translation}\n\nለመጠቀም ከታች ያለውን ሜኑ ይጠቀሙ።"
    }
}

# Bot settings
BOT_SETTINGS = {
    'daily_reminder_time': '08:00',  # 8:00 AM
    'default_translation': 'ESV',
    'default_language': 'en'
}
