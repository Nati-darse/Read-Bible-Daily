# Daily Bible Reader Bot 📖🇪🇹

A feature-rich Telegram bot designed to help users read the Bible daily in both **English** (ESV, KJV, NIV) and **Amharic** (1954 translation).

## 🚀 Features

- **📚 Multilingual Support**: 
    - Full support for **English** and **Amharic (አማርኛ)**.
    - Localized menus, buttons, and messages.
    - Authentic Amharic Bible text (66 books).
- **📅 Personalized Reading Plans**:
    - **Bible in One Year** (365 days)
    - **Psalms in One Month** (30 days)
    - **New Testament in 6 Months** (180 days)
- **🔔 Daily Notifications**:
    - Users can select **2 preferred times** for daily reminders.
    - Automated delivery of scripture at selected times.
- **📊 Gamification**:
    - Track reading streaks and progress.
    - Earn achievements (e.g., 7-Day Flame, Monthly Star).
- **⚙️ Customization**: 
    - Change translation, language, or plan at any time.
    - Restart plans safely with confirmation.

## 🛠️ Local Setup

1. **Clone the repository**:
    ```bash
    git clone https://github.com/yourusername/daily-bible-bot.git
    cd daily-bible-bot
    ```

2. **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3. **Configure Environment**:
    Create a `.env` file in the root directory:
    ```env
    BOT_TOKEN=your_telegram_bot_token_here
    ```

4. **Run the Bot**:
    ```bash
    python bot.py
    ```

## ☁️ Deployment

### Render / Railway / Heroku

This project is configured for easy deployment.

1.  **Procfile** is included for platforms like Heroku/Render (`worker: python bot.py`).
2.  **runtime.txt** specifies the Python version.
3.  Ensure you add the `BOT_TOKEN` as an Environment Variable in your deployment dashboard.

## 📂 Project Structure

- `bot.py`: Main bot logic and handlers.
- `database.py`: SQLite database management for users, progress, and settings.
- `bible_api.py`: Scripture fetching logic (Online + Local Amharic JSON).
- `reading_plans.py`: Calculation logic for daily readings.
- `menu.py`: Localized keyboard generation.
- `config.py`: Configuration and localized text strings.
- `amharic_bible.json`: Local database of Amharic scriptures.

## 📝 License

This project is open-source. Feel free to use and modify!
