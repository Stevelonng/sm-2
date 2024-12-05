# db_manager.py

import sqlite3
from datetime import datetime

def adapt_datetime(dt):
    """Convert datetime to string for SQLite storage"""
    return dt.isoformat()

def convert_datetime(bytes_val):
    """Convert SQLite datetime string back to Python datetime"""
    try:
        return datetime.fromisoformat(bytes_val.decode())
    except (ValueError, AttributeError):
        return None

class DatabaseManager:
    def __init__(self, db_name="flashcards.db"):
        self.db_name = db_name
        # Register datetime adapters and converters
        sqlite3.register_adapter(datetime, adapt_datetime)
        sqlite3.register_converter("timestamp", convert_datetime)
        self.connect_args = {'detect_types': sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES}
        self.setup_database()

    def setup_database(self):
        with sqlite3.connect(self.db_name, **self.connect_args) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cards (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    front_content TEXT NOT NULL,
                    back_content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS review_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    card_id INTEGER,
                    review_date TIMESTAMP,
                    quality INTEGER,
                    ease_factor REAL,
                    interval REAL,
                    repetition INTEGER,
                    next_review TIMESTAMP,
                    FOREIGN KEY (card_id) REFERENCES cards (id)
                )
            ''')
            conn.commit()

    def add_card(self, front_content, back_content):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO cards (front_content, back_content) VALUES (?, ?)',
                (front_content, back_content)
            )
            return cursor.lastrowid

    def add_review_record(self, card_id, review_data):
        with sqlite3.connect(self.db_name, **self.connect_args) as conn:
            cursor = conn.cursor()
            current_time = datetime.now()

            cursor.execute('''
                INSERT INTO review_history 
                (card_id, review_date, quality, ease_factor, interval, 
                repetition, next_review)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                card_id,
                current_time,
                review_data['quality'],
                review_data['ease_factor'],
                review_data['interval'],
                review_data['repetition'],
                review_data['next_review']
            ))

            print("\n添加复习记录:")
            print(f"卡片ID: {card_id}")
            print(f"复习时间: {current_time}")
            print(f"下次复习: {review_data['next_review']}")

            conn.commit()

    def get_card_state(self, card_id):
        with sqlite3.connect(self.db_name, **self.connect_args) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT ease_factor, interval, repetition, next_review
                FROM review_history
                WHERE card_id = ?
                ORDER BY review_date DESC
                LIMIT 1
            ''', (card_id,))

            result = cursor.fetchone()
            if result:
                return {
                    'ease_factor': result[0],
                    'interval': result[1],
                    'repetition': result[2],
                    'next_review': result[3]
                }
            return None

    def get_review_history(self, card_id):
        with sqlite3.connect(self.db_name, **self.connect_args) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    review_date,
                    quality,
                    ease_factor,
                    interval,
                    next_review
                FROM review_history
                WHERE card_id = ?
                ORDER BY review_date ASC
            ''', (card_id,))

            history = cursor.fetchall()
            if not history:
                print(f"\n未找到卡片 {card_id} 的复习记录")
                return []
            return history

    def get_due_cards(self):
        current_time = datetime.now()
        with sqlite3.connect(self.db_name, **self.connect_args) as conn:
            cursor = conn.cursor()

            cursor.execute('''
                WITH LatestReviews AS (
                    SELECT card_id, MAX(id) as max_id
                    FROM review_history
                    GROUP BY card_id
                )
                SELECT DISTINCT
                    c.id,
                    c.front_content,
                    c.back_content,
                    rh.next_review
                FROM cards c
                LEFT JOIN LatestReviews lr ON c.id = lr.card_id
                LEFT JOIN review_history rh ON lr.max_id = rh.id
                WHERE rh.next_review IS NULL 
                   OR rh.next_review <= ?
                ORDER BY c.id
            ''', (current_time,))

            return cursor.fetchall()