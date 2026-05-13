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
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        return conn
    
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

        self._ensure_column(cursor, 'users', 'language', "TEXT DEFAULT 'en'")
        self._ensure_column(cursor, 'users', 'streak', 'INTEGER DEFAULT 0')
        self._ensure_column(cursor, 'users', 'max_streak', 'INTEGER DEFAULT 0')
        self._ensure_column(cursor, 'users', 'last_read_date', 'TEXT')
        self._ensure_column(cursor, 'users', 'notification_times', 'TEXT')
        
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

        # Daily chapter completion state (checkbox-style progress)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_chapter_status (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                plan_day INTEGER NOT NULL,
                book TEXT NOT NULL,
                chapter INTEGER NOT NULL,
                completed BOOLEAN DEFAULT FALSE,
                sent_count INTEGER DEFAULT 0,
                last_sent_at TEXT,
                completed_at TEXT,
                UNIQUE (user_id, date, plan_day, book, chapter)
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

    def _ensure_column(self, cursor, table_name, column_name, column_definition):
        """Add a missing column when upgrading an existing SQLite database."""
        cursor.execute(f'PRAGMA table_info({table_name})')
        columns = {column[1] for column in cursor.fetchall()}
        if column_name not in columns:
            cursor.execute(
                f'ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}'
            )
    
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
            return {
                'user_id': user_row['user_id'],
                'username': user_row['username'],
                'first_name': user_row['first_name'],
                'plan_name': user_row['plan_name'],
                'language': user_row['language'] or 'en',
                'translation': user_row['translation'] or 'ESV',
                'start_date': user_row['start_date'],
                'current_day': user_row['current_day'] or 1,
                'streak': user_row['streak'] or 0,
                'max_streak': user_row['max_streak'] or 0,
                'last_read_date': user_row['last_read_date'],
                'notification_times': user_row['notification_times']
            }
        return None

    def delete_user(self, user_id):
        """Delete a user completely from the database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM users WHERE user_id = ?', (user_id,))
        cursor.execute('DELETE FROM user_progress WHERE user_id = ?', (user_id,))
        cursor.execute('DELETE FROM daily_chapter_status WHERE user_id = ?', (user_id,))
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
        cursor.execute('DELETE FROM daily_chapter_status WHERE user_id = ?', (user_id,))
        
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

    def get_reading_history(self, user_id, limit=10):
        """Get recently completed reading days for a user."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT date, book, chapter
            FROM user_progress
            WHERE user_id = ? AND completed = TRUE
            ORDER BY date DESC
            LIMIT ?
        ''', (user_id, limit))
        rows = cursor.fetchall()
        conn.close()
        return rows

    def upsert_daily_chapter(self, user_id, plan_day, book, chapter):
        """Ensure a daily chapter status row exists for today's plan day."""
        today = datetime.now(ET_TZ).strftime('%Y-%m-%d')
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR IGNORE INTO daily_chapter_status
            (user_id, date, plan_day, book, chapter, completed, sent_count)
            VALUES (?, ?, ?, ?, ?, FALSE, 0)
        ''', (user_id, today, plan_day, book, chapter))
        conn.commit()
        conn.close()

    def increment_daily_chapter_send(self, user_id, plan_day, book, chapter):
        """Track how many times today's chapter has been sent to the user."""
        today = datetime.now(ET_TZ).strftime('%Y-%m-%d')
        now_ts = datetime.now(ET_TZ).isoformat()
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE daily_chapter_status
            SET sent_count = sent_count + 1, last_sent_at = ?
            WHERE user_id = ? AND date = ? AND plan_day = ? AND book = ? AND chapter = ?
        ''', (now_ts, user_id, today, plan_day, book, chapter))
        conn.commit()
        conn.close()

    def get_daily_chapter(self, user_id, plan_day, book, chapter):
        """Get today's chapter status row."""
        today = datetime.now(ET_TZ).strftime('%Y-%m-%d')
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, completed, sent_count
            FROM daily_chapter_status
            WHERE user_id = ? AND date = ? AND plan_day = ? AND book = ? AND chapter = ?
        ''', (user_id, today, plan_day, book, chapter))
        row = cursor.fetchone()
        conn.close()
        if not row:
            return None
        return {
            'id': row[0],
            'completed': bool(row[1]),
            'sent_count': row[2]
        }

    def mark_chapter_completed(self, chapter_status_id, user_id):
        """Mark a specific chapter checkbox as completed."""
        now_ts = datetime.now(ET_TZ).isoformat()
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE daily_chapter_status
            SET completed = TRUE, completed_at = ?
            WHERE id = ? AND user_id = ? AND completed = FALSE
        ''', (now_ts, chapter_status_id, user_id))
        changed = cursor.rowcount > 0
        cursor.execute('''
            SELECT date, plan_day, book, chapter, completed
            FROM daily_chapter_status
            WHERE id = ? AND user_id = ?
        ''', (chapter_status_id, user_id))
        row = cursor.fetchone()
        conn.commit()
        conn.close()
        if not row:
            return None, False
        chapter_data = {
            'date': row[0],
            'plan_day': row[1],
            'book': row[2],
            'chapter': row[3],
            'completed': bool(row[4])
        }
        return chapter_data, changed

    def get_day_completion_summary(self, user_id, plan_day):
        """Return completed/total chapter count for today's plan day."""
        today = datetime.now(ET_TZ).strftime('%Y-%m-%d')
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT COUNT(*), COALESCE(SUM(CASE WHEN completed = TRUE THEN 1 ELSE 0 END), 0)
            FROM daily_chapter_status
            WHERE user_id = ? AND date = ? AND plan_day = ?
        ''', (user_id, today, plan_day))
        row = cursor.fetchone()
        conn.close()
        total = row[0] if row else 0
        completed = row[1] if row else 0
        return {'total': total, 'completed': completed}

    def complete_day_if_ready(self, user_id, plan_day):
        """Advance day only when all today's chapter checkboxes are completed."""
        today = datetime.now(ET_TZ).strftime('%Y-%m-%d')
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT current_day FROM users WHERE user_id = ?', (user_id,))
        user_row = cursor.fetchone()
        if not user_row:
            conn.close()
            return {'completed': False}

        current_day = user_row[0]
        if current_day != plan_day:
            conn.close()
            return {'completed': False}

        cursor.execute('''
            SELECT book, chapter, completed
            FROM daily_chapter_status
            WHERE user_id = ? AND date = ? AND plan_day = ?
            ORDER BY chapter
        ''', (user_id, today, plan_day))
        chapter_rows = cursor.fetchall()
        conn.close()

        if not chapter_rows:
            return {'completed': False}

        if any(not bool(r[2]) for r in chapter_rows):
            return {'completed': False}

        if self.get_todays_reading(user_id):
            return {'completed': False}

        streak = self.update_user_progress(user_id, plan_day, chapter_rows[0][0], chapter_rows[0][1])
        return {
            'completed': True,
            'streak': streak,
            'new_day': plan_day + 1
        }

    def update_notification_times(self, user_id, times):
        """Update notification times for a user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # times should be a comma-separated string or JSON string
        cursor.execute('UPDATE users SET notification_times = ? WHERE user_id = ?', (times, user_id))
        
        conn.commit()
        conn.close()

    def update_user_language(self, user_id, language):
        """Update user's UI language without touching reading progress."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET language = ? WHERE user_id = ?', (language, user_id))
        conn.commit()
        conn.close()

    def update_user_translation(self, user_id, translation):
        """Update user's Bible translation without touching reading progress."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET translation = ? WHERE user_id = ?', (translation, user_id))
        conn.commit()
        conn.close()

    def update_user_plan(self, user_id, plan_name):
        """Update user's reading plan key while preserving current day/streak."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET plan_name = ? WHERE user_id = ?', (plan_name, user_id))
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

    def get_todays_passages(self, user_id):
        """Get today's already-prepared passages for resending same day's word."""
        today = datetime.now(ET_TZ).strftime('%Y-%m-%d')
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT plan_day, book, chapter
            FROM daily_chapter_status
            WHERE user_id = ? AND date = ?
            ORDER BY id ASC
        ''', (user_id, today))
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return None

        plan_day = rows[0][0]
        passages = []
        for _, book, chapter in rows:
            if passages and passages[-1]['book'] == book:
                passages[-1]['chapters'].append(chapter)
            else:
                passages.append({'book': book, 'chapters': [chapter]})
        return {'plan_day': plan_day, 'passages': passages}
    
    def get_users_with_notification_time(self, time_str):
        """Get all user IDs who have selected a specific notification time"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT user_id, language, plan_name, translation, current_day, notification_times
            FROM users
            WHERE notification_times IS NOT NULL
        ''')
        users = cursor.fetchall()
        conn.close()
        matched = []
        for u in users:
            raw_times = (u[5] or '').strip()
            parsed = []
            if not raw_times:
                continue

            # Support legacy formats: CSV, CSV with spaces, or JSON list.
            try:
                if raw_times.startswith('['):
                    loaded = json.loads(raw_times)
                    if isinstance(loaded, list):
                        parsed = [str(t).strip() for t in loaded]
                else:
                    parsed = [t.strip() for t in raw_times.split(',') if t.strip()]
            except Exception:
                parsed = [t.strip() for t in raw_times.replace(';', ',').split(',') if t.strip()]

            if time_str in parsed:
                matched.append({
                    'user_id': u[0],
                    'language': u[1],
                    'plan_name': u[2],
                    'translation': u[3],
                    'current_day': u[4]
                })
        return matched


# Create global database instance
db = Database()
