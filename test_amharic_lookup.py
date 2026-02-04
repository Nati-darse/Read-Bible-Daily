import logging
from bible_api import bible_api

# Configure logging to show errors/warnings
logging.basicConfig(level=logging.INFO)

def test_amharic_lookup():
    print("Testing Amharic Bible Lookup...")
    
    test_cases = [
        ("Genesis", 1),      # First book
        ("Psalms", 23),      # Middle book
        ("Matthew", 6),      # New Testament start
        ("Revelation", 22)   # Last book
    ]
    
    for book, chapter in test_cases:
        print(f"\n--- Fetching {book} Chapter {chapter} (Amharic) ---")
        text = bible_api.get_text(book, chapter, translation='AMH')
        
        if "❌" in text:
            print(f"FAILED: {text}")
        else:
            print(f"SUCCESS. Length: {len(text)} chars")
            print(f"Preview: {text[:100]}...")

if __name__ == "__main__":
    test_amharic_lookup()
