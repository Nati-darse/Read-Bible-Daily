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
                start_date TEXT,
                current_day INTEGER DEFAULT 1,
                translation TEXT DEFAULT 'ESV',
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
        
        conn.commit()
        conn.close()
        print("Database initialized successfully!")
    
    def add_user(self, user_id, username, first_name, plan_name, translation='ESV'):
        """Add a new user to the database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        start_date = datetime.now().strftime('%Y-%m-%d')
        
        cursor.execute('''
            INSERT OR REPLACE INTO users 
            (user_id, username, first_name, plan_name, start_date, translation, current_day)
            VALUES (?, ?, ?, ?, ?, ?, 1)
        ''', (user_id, username, first_name, plan_name, start_date, translation))
        
        conn.commit()
        conn.close()
        return True
    
    def get_user(self, user_id):
        """Get user data"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        user = cursor.fetchone()
        
        conn.close()
        
        if user:
            return {
                'user_id': user[0],
                'username': user[1],
                'first_name': user[2],
                'plan_name': user[3],
                'start_date': user[4],
                'current_day': user[5],
                'translation': user[6]
            }
        return None
    
    def update_user_progress(self, user_id, day_number, book, chapter):
        """Update user's reading progress"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        today = datetime.now().strftime('%Y-%m-%d')
        
        cursor.execute('''
            INSERT OR REPLACE INTO user_progress 
            (user_id, date, book, chapter, completed)
            VALUES (?, ?, ?, ?, TRUE)
        ''', (user_id, today, book, chapter))
        
        # Update current day
        cursor.execute('''
            UPDATE users SET current_day = ? WHERE user_id = ?
        ''', (day_number, user_id))
        
        conn.commit()
        conn.close()
    
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