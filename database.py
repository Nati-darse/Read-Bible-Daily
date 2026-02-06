# database.py - Handle user data storage
import sqlite3
import json
import os
from datetime import datetime, timedelta
import pytz
import logging

logger = logging.getLogger(__name__)

# Constants
ET_TZ = pytz.timezone('Africa/Addis_Ababa')

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
                notification_times TEXT,
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
        
        start_date = datetime.now(ET_TZ).strftime('%Y-%m-%d')
        
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

    def delete_user(self, user_id):
        """Delete a user completely from the database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM users WHERE user_id = ?', (user_id,))
        cursor.execute('DELETE FROM user_progress WHERE user_id = ?', (user_id,))
        cursor.execute('DELETE FROM achievements WHERE user_id = ?', (user_id,))
        cursor.execute('DELETE FROM favorites WHERE user_id = ?', (user_id,))
        
        conn.commit()
        conn.close()

    
    def update_user_progress(self, user_id, day_number, book, chapter):
        """Update user's reading progress and streaks"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        now_eat = datetime.now(ET_TZ)
        today = now_eat.strftime('%Y-%m-%d')
        yesterday = (now_eat - timedelta(days=1)).strftime('%Y-%m-%d')
        
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

    def reset_user_progress(self, user_id):
        """Reset user progress but keep settings"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Reset user stats in users table
        # We KEEP: plan_name, translation, language, notification_times, username, first_name
        # We RESET: start_date, current_day, streak, max_streak, last_read_date
        
        new_start_date = datetime.now(ET_TZ).strftime('%Y-%m-%d')
        
        cursor.execute('''
            UPDATE users SET 
            start_date = ?, 
            current_day = 1, 
            streak = 0, 
            max_streak = 0, 
            last_read_date = NULL
            WHERE user_id = ?
        ''', (new_start_date, user_id))
        
        # Delete progress history
        cursor.execute('DELETE FROM user_progress WHERE user_id = ?', (user_id,))
        
        # We do NOT delete achievements or favorites? 
        # Usually a "Restart Plan" implies restarting READING checkmarks.
        # Let's keep achievements as "Legacy" or maybe wipe them? 
        # For now, let's WIPE achievements as it's a "Restart".
        cursor.execute('DELETE FROM achievements WHERE user_id = ?', (user_id,))
        
        conn.commit()
        conn.close()
    
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
        today = datetime.now(ET_TZ).strftime('%Y-%m-%d')
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
        today = datetime.now(ET_TZ).strftime('%Y-%m-%d')
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM user_progress WHERE user_id = ? AND date = ?
        ''', (user_id, today))
        
        result = cursor.fetchone()
        conn.close()
        return result is not None

    def update_notification_times(self, user_id, times):
        """Update notification times for a user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # times should be a comma-separated string or JSON string
        cursor.execute('UPDATE users SET notification_times = ? WHERE user_id = ?', (times, user_id))
        
        conn.commit()
        conn.close()

    def get_notification_times(self, user_id):
        """Get notification times for a user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT notification_times FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None
    
    def get_users_with_notification_time(self, time_str):
        """Get all user IDs who have selected a specific notification time"""
        conn = self.get_connection()
        cursor = conn.cursor()
        # Ensure we match the time properly in the comma-separated string
        # Using %time_str% pattern matching
        cursor.execute("SELECT user_id, language, plan_name, translation, current_day FROM users WHERE notification_times LIKE ?", (f'%{time_str}%',))
        users = cursor.fetchall()
        conn.close()
        return [{'user_id': u[0], 'language': u[1], 'plan_name': u[2], 'translation': u[3], 'current_day': u[4]} for u in users]


# Create global database instance
db = Database()