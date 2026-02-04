import logging
import os
import asyncio
from database import db
from bible_api import bible_api
from reading_plans import reading_plans
from config import MESSAGES, NOTIFICATION_TIMES

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_database_reset():
    """Test that reset_user_progress clears stats but keeps settings"""
    print("\n--- Testing Database Reset Logic ---")
    
    # 1. Create a dummy user
    user_id = 99999
    db.add_user(user_id, "testuser", "Test", "bible_in_one_year", "AMH", "am")
    
    # 2. Add some custom settings
    expected_times = "06:00,18:00"
    db.update_notification_times(user_id, expected_times)
    
    # 3. Simulate some progress
    db.update_user_progress(user_id, 1, "Genesis", 1)
    
    # Verify pre-reset state
    user = db.get_user(user_id)
    print(f"User pre-reset: Day={user['current_day']}, Streak={user['streak']}")
    
    # 4. Perform Reset
    db.reset_user_progress(user_id)
    
    # 5. Verify post-reset state
    user = db.get_user(user_id)
    times = db.get_notification_times(user_id)
    
    if user['current_day'] == 1 and user['streak'] == 0:
        print("✅ PASS: Progress reset day/streak corrected.")
    else:
        print(f"❌ FAIL: Progress not reset. Day={user['current_day']}")
        
    if times == expected_times:
        print(f"✅ PASS: Notification times preserved: {times}")
    else:
        print(f"❌ FAIL: Notification times lost! Got: {times}")
        
    if user['translation'] == "AMH" and user['language'] == "am":
         print("✅ PASS: Language/Translation settings preserved.")
    else:
         print("❌ FAIL: Language/Translation settings lost.")

def test_amharic_data():
    """Test Amharic data integrity"""
    print("\n--- Testing Amharic Data Integrity ---")
    
    # 1. Check if 'Genesis' maps to 'ኦሪት ዘፍጥረት'
    mapped_name = reading_plans.amharic_book_names.get('Genesis')
    if mapped_name == 'ኦሪት ዘፍጥረት':
        print("✅ PASS: Genesis mapped correctly.")
    else:
        print(f"❌ FAIL: Genesis mapped to {mapped_name}")
        
    # 2. Try to fetch actual text
    text = bible_api.get_amharic_text('Genesis', 1)
    if "ኦሪት ዘፍጥረት" in text and len(text) > 100:
        print("✅ PASS: Fetched Amharic Genesis 1 successfully.")
    else:
        print("❌ FAIL: Could not fetch Genesis 1 text.")

def test_notification_logic():
    """Test finding users for notification"""
    print("\n--- Testing Notification Query ---")
    
    # Create user wanting 06:00
    user_id = 88888
    db.add_user(user_id, "notify_user", "Notify", "bible_in_one_year")
    db.update_notification_times(user_id, "06:00,12:00")
    
    # Query for 06:00
    users = db.get_users_with_notification_time("06:00")
    found = any(u['user_id'] == user_id for u in users)
    
    if found:
        print("✅ PASS: User found for 06:00 notification.")
    else:
         print("❌ FAIL: User not found for 06:00.")

def main():
    print("🤖 RUNNING OFFLINE SYSTEM VERIFICATION 🤖")
    
    try:
        test_database_reset()
        test_amharic_data()
        test_notification_logic()
        print("\n✨ ALL TESTS COMPLETED ✨")
    except Exception as e:
        print(f"\n❌ FATAL ERROR DURING TESTS: {e}")

if __name__ == "__main__":
    main()
