# reading_plans.py - Calculate daily readings based on plans
from datetime import datetime, timedelta

class ReadingPlans:
    def __init__(self):
        self.bible_books = [
            # Old Testament
            "Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy",
            "Joshua", "Judges", "Ruth", "1 Samuel", "2 Samuel",
            "1 Kings", "2 Kings", "1 Chronicles", "2 Chronicles", "Ezra",
            "Nehemiah", "Esther", "Job", "Psalms", "Proverbs",
            "Ecclesiastes", "Song of Solomon", "Isaiah", "Jeremiah", "Lamentations",
            "Ezekiel", "Daniel", "Hosea", "Joel", "Amos",
            "Obadiah", "Jonah", "Micah", "Nahum", "Habakkuk",
            "Zephaniah", "Haggai", "Zechariah", "Malachi",
            # New Testament
            "Matthew", "Mark", "Luke", "John", "Acts",
            "Romans", "1 Corinthians", "2 Corinthians", "Galatians", "Ephesians",
            "Philippians", "Colossians", "1 Thessalonians", "2 Thessalonians", "1 Timothy",
            "2 Timothy", "Titus", "Philemon", "Hebrews", "James",
            "1 Peter", "2 Peter", "1 John", "2 John", "3 John",
            "Jude", "Revelation"
        ]
        
        # Approximate chapter counts for each book
        self.book_chapters = {
            "Genesis": 50, "Exodus": 40, "Leviticus": 27, "Numbers": 36, "Deuteronomy": 34,
            "Joshua": 24, "Judges": 21, "Ruth": 4, "1 Samuel": 31, "2 Samuel": 24,
            "1 Kings": 22, "2 Kings": 25, "1 Chronicles": 29, "2 Chronicles": 36, "Ezra": 10,
            "Nehemiah": 13, "Esther": 10, "Job": 42, "Psalms": 150, "Proverbs": 31,
            "Ecclesiastes": 12, "Song of Solomon": 8, "Isaiah": 66, "Jeremiah": 52, "Lamentations": 5,
            "Ezekiel": 48, "Daniel": 12, "Hosea": 14, "Joel": 3, "Amos": 9,
            "Obadiah": 1, "Jonah": 4, "Micah": 7, "Nahum": 3, "Habakkuk": 3,
            "Zephaniah": 3, "Haggai": 2, "Zechariah": 14, "Malachi": 4,
            "Matthew": 28, "Mark": 16, "Luke": 24, "John": 21, "Acts": 28,
            "Romans": 16, "1 Corinthians": 16, "2 Corinthians": 13, "Galatians": 6, "Ephesians": 6,
            "Philippians": 4, "Colossians": 4, "1 Thessalonians": 5, "2 Thessalonians": 3, "1 Timothy": 6,
            "2 Timothy": 4, "Titus": 3, "Philemon": 1, "Hebrews": 13, "James": 5,
            "1 Peter": 5, "2 Peter": 3, "1 John": 5, "2 John": 1, "3 John": 1,
            "Jude": 1, "Revelation": 22
        }
    
    def get_psalms_plan(self, day_number):
        """Get Psalms reading for the day (30-day plan)"""
        # Psalms has 150 chapters, spread over 30 days = 5 chapters per day
        start_chapter = (day_number - 1) * 5 + 1
        end_chapter = min(start_chapter + 4, 150)
        
        return {
            'book': 'Psalms',
            'chapters': list(range(start_chapter, end_chapter + 1)),
            'day': day_number,
            'total_days': 30
        }
    
    def get_bible_year_plan(self, day_number):
        """Get Bible reading for the day (365-day plan)"""
        # Simplified plan: Read books in order
        total_chapters = sum(self.book_chapters.values())
        chapters_per_day = total_chapters // 365
        
        current_day = 1
        current_chapter = 1
        
        for book in self.bible_books:
            book_chapters = self.book_chapters[book]
            
            for chapter in range(1, book_chapters + 1):
                if current_day == day_number:
                    return {
                        'book': book,
                        'chapters': [chapter],
                        'day': day_number,
                        'total_days': 365
                    }
                
                current_chapter += 1
                if current_chapter > chapters_per_day:
                    current_day += 1
                    current_chapter = 1
        
        return None
    
    def get_todays_reading(self, plan_name, day_number):
        """Get today's reading based on plan"""
        if plan_name == 'psalms_in_one_month':
            return self.get_psalms_plan(day_number)
        elif plan_name == 'bible_in_one_year':
            return self.get_bible_year_plan(day_number)
        else:
            return self.get_bible_year_plan(day_number)  # Default

# Create global instance
reading_plans = ReadingPlans()