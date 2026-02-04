# reading_plans.py - Calculate daily readings based on plans

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
        
        # Amharic Book Names Mapping (Must match amharic_bible.json titles)
        self.amharic_book_names = {
            "Genesis": "ኦሪት ዘፍጥረት", "Exodus": "ኦሪት ዘጸአት", "Leviticus": "ኦሪት ዘሌዋውያን", 
            "Numbers": "ኦሪት ዘኍልቍ", "Deuteronomy": "ኦሪት ዘዳግም", "Joshua": "መጽሐፈ ኢያሱ ወልደ ነዌ", 
 
            "Judges": "መጽሐፈ መሣፍንት", "Ruth": "መጽሐፈ ሩት", "1 Samuel": "መጽሐፈ ሳሙኤል ቀዳማዊ", 
 
            "2 Samuel": "መጽሐፈ ሳሙኤል ካል", "1 Kings": "መጽሐፈ ነገሥት ቀዳማዊ።", 
            "2 Kings": "መጽሐፈ ነገሥት ካልዕ።", "1 Chronicles": "መጽሐፈ ዜና መዋዕል ቀዳማዊ።", 
            "2 Chronicles": "መጽሐፈ ዜና መዋዕል ካልዕ።", "Ezra": "መጽሐፈ ዕዝራ።", 
            "Nehemiah": "መጽሐፈ ነህምያ።", "Esther": "መጽሐፈ አስቴር።", "Job": "መጽሐፈ ኢዮብ።", 
 
            "Psalms": "መዝሙረ ዳዊት", "Proverbs": "መጽሐፈ ምሳሌ", "Ecclesiastes": "መጽሐፈ መክብብ", 
            "Song of Solomon": "መኃልየ መኃልይ ዘሰሎሞን", "Isaiah": "ትንቢተ ኢሳይያስ", "Jeremiah": "ትንቢተ ኤርምያስ", 
 
            "Lamentations": "ሰቆቃው ኤርምያስ", "Ezekiel": "ትንቢተ ሕዝቅኤል", "Daniel": "ትንቢተ ዳንኤል", 
            "Hosea": "ትንቢተ ሆሴዕ", "Joel": "ትንቢተ ኢዮኤል", "Amos": "ትንቢተ አሞጽ", 
 
            "Obadiah": "ትንቢተ አብድዩ", "Jonah": "ትንቢተ ዮናስ", "Micah": "ትንቢተ ሚክያስ", 
            "Nahum": "ትንቢተ ናሆም", "Habakkuk": "ትንቢተ ዕንባቆም", "Zephaniah": "ትንቢተ ሶፎንያስ", 
            "Haggai": "ትንቢተ ሐጌ", "Zechariah": "ትንቢተ ዘካርያስ", "Malachi": "ትንቢተ ሚልክያ",

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
        
        # Chapter counts
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

    def get_sequential_reading(self, day_number, books, target_days):
        """Generic logic for sequential reading plans"""
        # Calculate total chapters in the selected books
        total_chapters = sum(self.book_chapters[b] for b in books)
        chapters_per_day = max(1, total_chapters // target_days)
        
        # Find start and end chapter indices
        start_idx = (day_number - 1) * chapters_per_day
        end_idx = start_idx + chapters_per_day
        
        # If it's the last day, include all remaining chapters
        if day_number == target_days:
            end_idx = total_chapters
            
        current_idx = 0
        reading_list = [] # List of {book, chapters}
        
        for book in books:
            num_chapters = self.book_chapters[book]
            for chapter in range(1, num_chapters + 1):
                if current_idx >= start_idx and current_idx < end_idx:
                    # check if we already have this book in the list
                    if reading_list and reading_list[-1]['book'] == book:
                        reading_list[-1]['chapters'].append(chapter)
                    else:
                        reading_list.append({'book': book, 'chapters': [chapter]})
                current_idx += 1
                
        # Return the first entry of the day (simplified for bot structure)
        # The bot currently expects a single book per day message
        if reading_list:
            return {
                'book': reading_list[0]['book'],
                'chapters': reading_list[0]['chapters'],
                'day': day_number,
                'total_days': target_days
            }
        return None

    def get_todays_reading(self, plan_name, day_number):
        """Get today's reading based on plan"""
        if plan_name == 'psalms_in_one_month':
            return self.get_sequential_reading(day_number, ["Psalms"], 30)
        elif plan_name == 'bible_in_one_year':
            return self.get_sequential_reading(day_number, self.bible_books, 365)
        elif plan_name == 'new_testament_in_six_months':
            nt_books = self.bible_books[39:] # Matthew to Revelation
            return self.get_sequential_reading(day_number, nt_books, 180)
        else:
            return self.get_sequential_reading(day_number, self.bible_books, 365) # Default

# Create global instance
reading_plans = ReadingPlans()