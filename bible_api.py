# bible_api.py - Fetch Bible text from online API and local data
import requests
import json
import os
import logging

logger = logging.getLogger(__name__)

class BibleAPI:
    def __init__(self, amharic_file='amharic_bible.json'):
        self.amharic_file = amharic_file
        self.base_url = os.getenv('BIBLE_API_BASE_URL', 'https://bible-api.com').rstrip('/')
        self.amharic_data = None
        self._load_amharic_data()
        self.amharic_book_names = {
            "Genesis": "ኦሪት ዘዘፍጥረት", "Exodus": "ኦሪት ዘጸአት", "Leviticus": "ኦሪት ዘሌዋውያን", 
            "Numbers": "ኦሪት ዘኍልኍ", "Deuteronomy": "ኦሪት ዘዳግም", "Joshua": "መጽሐፈ ኢያሱ", 
            "Judges": "መጽሐፈ መሳፍንት", "Ruth": "መጽሐፈ ሩት", "1 Samuel": "መጽሐፈ ሳሙኤል ቀዳማዊ", 
            "2 Samuel": "መጽሐፈ ሳሙኤል ካልዕ", "1 Kings": "መጽሐፈ ነገሥት ቀዳማዊ", 
            "2 Kings": "መጽሐፈ ነገሥት ካልዕ", "1 Chronicles": "መጽሐፈ ዜና መዋዕል ቀዳማዊ", 
            "2 Chronicles": "መጽሐፈ ዜና መዋዕል ካልዕ", "Ezra": "መጽሐፈ ዕዝራ", 
            "Nehemiah": "መጽሐፈ ነህምያ", "Esther": "መጽሐፈ አስቴር", "Job": "መጽሐፈ ኢዮብ", 
            "Psalms": "መዝሙረ ዳዊት", "Proverbs": "መጽሐፈ ምሳሌ", "Ecclesiastes": "መጽሐፈ መክብብ", 
            "Song of Solomon": "ማኅልየ ማኅልይ", "Isaiah": "ትንቢተ ኢሳይያስ", "Jeremiah": "ትንቢተ ኤርምያስ", 
            "Lamentations": "ሰቆቃው ኤርምያስ", "Ezekiel": "ትንቢተ ሕዝቅኤል", "Daniel": "ትንቢተ ዳንኤል", 
            "Hosea": "ትንቢተ ሆሴዕ", "Joel": "ትንቢተ ኢዩኤል", "Amos": "ትንቢተ አሞጽ", 
            "Obadiah": "ትንቢተ አብድዩ", "Jonah": "ትንቢተ ዮናስ", "Micah": "ትንቢተ ሚክያስ", 
            "Nahum": "ትንቢተ ናሆም", "Habakkuk": "ትንቢተ ዕንባቆም", "Zephaniah": "ትንቢተ ሶፎንያስ", 
            "Haggai": "ትንቢተ ሐጌ", "Zechariah": "ትንቢተ ዘካርያስ", "Malachi": "ትንቢተ ሚልክያስ",
            "Matthew": "የማቴዎስ ወንጌል", "Mark": "የማርቆስ ወንጌል", "Luke": "የሉቃስ ወንጌል", 
            "John": "የዮሐንስ ወንጌል", "Acts": "የሐዋርያት ሥራ", "Romans": "ወደ ሮሜ ሰዎች", 
            "1 Corinthians": "1ኛ ወደ ቆሮንቶስ ሰዎች", "2 Corinthians": "2ኛ ወደ ቆሮንቶስ ሰዎች", 
            "Galatians": "ወደ ገላትያ ሰዎች", "Ephesians": "ወደ ኤፌሶን ሰዎች", "Philippians": "ወደ ፊልጵስዩስ ሰዎች", 
            "Colossians": "ወደ ቆላስይስ ሰዎች", "1 Thessalonians": "1ኛ ወደ ተሰሎንቄ ሰዎች", 
            "2 Thessalonians": "2ኛ ወደ ተሰሎንቄ ሰዎች", "1 Timothy": "1ኛ ወደ ጢሞቴዎስ", 
            "2 Timothy": "2ኛ ወደ ጢሞቴዎስ", "Titus": "ወደ ቲቶ", "Philemon": "ወደ ፊልሞና", 
            "Hebrews": "ወደ ዕብራውያን", "James": "የያዕቆብ መልእክት", "1 Peter": "1ኛ የጴጥሮስ መልእክት", 
            "2 Peter": "2ኛ የጴጥሮስ መልእክት", "1 John": "1ኛ የዮሐንስ መልእክት", 
            "2 John": "2ኛ የዮሐንስ መልእክት", "3 John": "3ኛ የዮሐንስ መልእክት", "Jude": "የይሁዳ መልእክት", 
            "Revelation": "የዮሐንስ ራእይ"
        }


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
            url = f"{self.base_url}/{book_formatted}+{chapter}?translation={translation}"
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

    def get_amharic_text(self, book_en, chapter_num):
        """Fetch Amharic Bible text using index-based lookup"""
        if not self.amharic_data or 'books' not in self.amharic_data:
            return "❌ Amharic Bible data not loaded. Please contact admin."
        
        # Standard Bible book order
        bible_books_order = [
            "Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy", "Joshua", "Judges", "Ruth",
            "1 Samuel", "2 Samuel", "1 Kings", "2 Kings", "1 Chronicles", "2 Chronicles", "Ezra", "Nehemiah", "Esther", "Job",
            "Psalms", "Proverbs", "Ecclesiastes", "Song of Solomon", "Isaiah", "Jeremiah", "Lamentations", "Ezekiel", "Daniel",
            "Hosea", "Joel", "Amos", "Obadiah", "Jonah", "Micah", "Nahum", "Habakkuk", "Zephaniah", "Haggai", "Zechariah", "Malachi",
            "Matthew", "Mark", "Luke", "John", "Acts", "Romans", "1 Corinthians", "2 Corinthians", "Galatians", "Ephesians", "Philippians", "Colossians",
            "1 Thessalonians", "2 Thessalonians", "1 Timothy", "2 Timothy", "Titus", "Philemon", "Hebrews", "James", "1 Peter", "2 Peter", "1 John", "2 John", "3 John", "Jude", "Revelation"
        ]
        
        try:
            book_index = bible_books_order.index(book_en)
            book_data = self.amharic_data['books'][book_index]
        except (ValueError, IndexError):
            logger.warning(f"Book not found or index out of range: {book_en}")
            return f"❌ መጽሐፉ አልተገኘም፦ {book_en}"
        
        # Find the chapter
        chapter_data = None
        for c in book_data['chapters']:
            if str(c['chapter']) == str(chapter_num):
                chapter_data = c
                break
                
        if not chapter_data:
            return f"❌ ምዕራፉ አልተገኘም፦ {book_data['title']} {chapter_num}"
        
        # Use the title from the JSON for the header
        text = f"📖 {book_data['title']} ምዕራፍ {chapter_num} (አማርኛ)\n\n"
        
        for i, verse_text in enumerate(chapter_data['verses'], 1):
            text += f"{i}. {verse_text}\n"
            
        return text[:4000]



# Create global instance
bible_api = BibleAPI()

