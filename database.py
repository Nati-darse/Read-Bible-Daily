# database.py - Handle user data storage
import sqlite3
import json
from datetime import datetime, timedelta

class Database:
    def __init__(self, db_name='bible_bot.db'):
        self.db_name = db_name
        self.init_database()
    
    def get_connection(self):
        return sqlite3.connect(self.db_name)
    
    def init_database(self):
        """Initialize database tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                plan_name TEXT,
                language TEXT DEFAULT 'en',
                translation TEXT DEFAULT 'ESV',
                start_date TEXT,
                current_day INTEGER DEFAULT 1,
                streak INTEGER DEFAULT 0,
                max_streak INTEGER DEFAULT 0,
                last_read_date TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # User progress table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_progress (
                user_id INTEGER,
                date TEXT,
                book TEXT,
                chapter INTEGER,
                completed BOOLEAN DEFAULT FALSE,
                PRIMARY KEY (user_id, date)
            )
        ''')

        # Achievements table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS achievements (
                user_id INTEGER,
                achievement_id TEXT,
                date_earned TEXT,
                PRIMARY KEY (user_id, achievement_id)
            )
        ''')

        # Favorites table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS favorites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                book TEXT,
                chapter INTEGER,
                verse INTEGER,
                text TEXT,
                date_saved TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        
        conn.commit()
        conn.close()
        print("Database initialized successfully!")
    
    def add_user(self, user_id, username, first_name, plan_name, translation='ESV', language='en'):
        """Add a new user to the database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        start_date = datetime.now().strftime('%Y-%m-%d')
        
        cursor.execute('''
            INSERT OR REPLACE INTO users 
            (user_id, username, first_name, plan_name, start_date, translation, language, current_day, streak, max_streak)
            VALUES (?, ?, ?, ?, ?, ?, ?, 1, 0, 0)
        ''', (user_id, username, first_name, plan_name, start_date, translation, language))
        
        conn.commit()
        conn.close()
        return True

    
    def get_user(self, user_id):
        """Get user data"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        user_row = cursor.fetchone()
        
        conn.close()
        
        if user_row:
            # Match columns with the table structure
            return {
                'user_id': user_row[0],
                'username': user_row[1],
                'first_name': user_row[2],
                'plan_name': user_row[3],
                'language': user_row[4],
                'translation': user_row[5],
                'start_date': user_row[6],
                'current_day': user_row[7],
                'streak': user_row[8],
                'max_streak': user_row[9],
                'last_read_date': user_row[10]
            }
        return None

    
    def update_user_progress(self, user_id, day_number, book, chapter):
        """Update user's reading progress and streaks"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        today = datetime.now().strftime('%Y-%m-%d')
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        # Get current user data for streak calculation
        cursor.execute('SELECT streak, max_streak, last_read_date FROM users WHERE user_id = ?', (user_id,))
        user_data = cursor.fetchone()
        
        streak, max_streak, last_read_date = user_data if user_data else (0, 0, None)
        
        if last_read_date == yesterday:
            streak += 1
        elif last_read_date == today:
            pass # Already read today, no change to streak
        else:
            streak = 1
        
        max_streak = max(streak, max_streak)
        
        cursor.execute('''
            INSERT OR REPLACE INTO user_progress 
            (user_id, date, book, chapter, completed)
            VALUES (?, ?, ?, ?, TRUE)
        ''', (user_id, today, book, chapter))
        
        # Update current day, streak, and last_read_date
        cursor.execute('''
            UPDATE users SET 
            current_day = ?, 
            streak = ?, 
            max_streak = ?, 
            last_read_date = ?
            WHERE user_id = ?
        ''', (day_number + 1, streak, max_streak, today, user_id))
        
        conn.commit()
        conn.close()
        return streak
    
    def add_favorite(self, user_id, book, chapter, verse, text):
        """Save a favorite verse"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO favorites (user_id, book, chapter, verse, text)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, book, chapter, verse, text))
        conn.commit()
        conn.close()
    
    def get_favorites(self, user_id):
        """Get all favorites for a user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT book, chapter, verse, text FROM favorites WHERE user_id = ?', (user_id,))
        favorites = cursor.fetchall()
        conn.close()
        return favorites

    def add_achievement(self, user_id, achievement_id):
        """Earn an achievement"""
        conn = self.get_connection()
        cursor = conn.cursor()
        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute('''
            INSERT OR IGNORE INTO achievements (user_id, achievement_id, date_earned)
            VALUES (?, ?, ?)
        ''', (user_id, achievement_id, today))
        conn.commit()
        conn.close()

    def get_achievements(self, user_id):
        """Get all achievements for a user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT achievement_id, date_earned FROM achievements WHERE user_id = ?', (user_id,))
        achievements = cursor.fetchall()
        conn.close()
        return achievements

    
    def get_todays_reading(self, user_id):
        """Check if user has read today's passage"""
        today = datetime.now().strftime('%Y-%m-%d')
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM user_progress WHERE user_id = ? AND date = ?
        ''', (user_id, today))
        
        result = cursor.fetchone()
        conn.close()
        return result is not None

# Create global database instance
db = Database()