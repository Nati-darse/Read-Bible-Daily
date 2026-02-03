# bible_api.py - Fetch Bible text from online API and local data
import requests
import json
import os
import logging

logger = logging.getLogger(__name__)

class BibleAPI:
    def __init__(self, amharic_file='amharic_bible.json'):
        self.amharic_file = amharic_file
        self.amharic_data = None
        self._load_amharic_data()

    def _load_amharic_data(self):
        """Load local Amharic Bible data"""
        if os.path.exists(self.amharic_file):
            try:
                with open(self.amharic_file, 'r', encoding='utf-8') as f:
                    self.amharic_data = json.load(f)
                logger.info("Amharic Bible data loaded successfully.")
            except Exception as e:
                logger.error(f"Error loading Amharic Bible data: {e}")
        else:
            logger.warning(f"Amharic Bible file {self.amharic_file} not found.")

    def get_text(self, book, chapter, translation='ESV'):
        """Fetch Bible text based on translation"""
        if translation == 'AMH':
            return self.get_amharic_text(book, chapter)
        else:
            return self.get_english_text(book, chapter, translation)

    def get_english_text(self, book, chapter, translation='ESV'):
        """Fetch English Bible text from bible-api.com"""
        book_formatted = book.replace(' ', '+')
        try:
            url = f"https://bible-api.com/{book_formatted}+{chapter}?translation={translation}"
            response = requests.get(url)
            data = response.json()
            
            if 'error' in data:
                return f"Sorry, couldn't fetch {book} {chapter}. Please try again later."
            
            verses = data.get('verses', [])
            text = f"📖 {book} Chapter {chapter} ({translation})\n\n"
            
            # Format verses for Telegram
            for verse in verses:
                text += f"{verse['verse']}. {verse['text']}\n"
            
            return text[:4000]  # Telegram message limit
            
        except Exception as e:
            logger.error(f"Error fetching Bible text: {e}")
            return f"❌ Error fetching {book} {chapter}. Please try again later."

    def get_amharic_text(self, book, chapter):
        """Fetch Amharic Bible text from local JSON"""
        if not self.amharic_data:
            return "❌ Amharic Bible data not loaded. Please contact admin."
        
        # Check if book and chapter exist
        book_data = self.amharic_data.get(book)
        if not book_data:
            return f"❌ መጽሐፉ አልተገኘም፦ {book}"
        
        chapter_data = book_data.get(str(chapter))
        if not chapter_data:
            return f"❌ ምዕራፉ አልተገኘም፦ {book} {chapter}"
        
        text = f"📖 {book} ምዕራፍ {chapter} (አማርኛ)\n\n"
        
        # chapter_data should be a dictionary of {verse_num: text}
        for verse_num, verse_text in sorted(chapter_data.items(), key=lambda x: int(x[0])):
            text += f"{verse_num}. {verse_text}\n"
            
        return text[:4000]

# Create global instance
bible_api = BibleAPI()
