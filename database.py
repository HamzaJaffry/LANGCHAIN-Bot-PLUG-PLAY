import sqlite3
from sqlite3 import Error
import logging

logging.basicConfig(level=logging.DEBUG)

class Database:
    def __init__(self):
        self.conn = None
        self.get_connection()
        self.create_table()

    def get_connection(self):
        try:
            self.conn = sqlite3.connect('questions.db', check_same_thread=False)
            logging.debug("Database connected")
            return self.conn
        except Error as e:
            logging.error(f"Connection error: {e}")
            return None

    def create_table(self):
        if not self.conn:
            self.get_connection()
        query = '''
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL UNIQUE
        )'''
        try:
            cursor = self.conn.cursor()
            cursor.execute(query)
            self.conn.commit()
            logging.debug("Table created successfully")
        except Error as e:
            logging.error(f"Error creating table: {e}")

    def execute_query(self, query, params=None):
        try:
            cursor = self.conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            self.conn.commit()
            return cursor
        except Error as e:
            logging.error(f"Query execution error: {e}")
            return None

    def add_question(self, question):
        if not self.conn:
            self.get_connection()
            
        if not question or not isinstance(question, str):
            logging.error("Invalid question format")
            return False

        query = 'INSERT OR IGNORE INTO questions (question) VALUES (?)'
        try:
            cursor = self.conn.cursor()
            cursor.execute(query, (question.strip(),))
            self.conn.commit()
            success = cursor.rowcount > 0
            logging.debug(f"Question added successfully: {success}")
            return success
        except sqlite3.IntegrityError:
            logging.debug(f"Duplicate question: {question}")
            return False
        except Error as e:
            logging.error(f"Error adding question: {e}")
            return False

    def verify_question(self, question):
        if not self.conn:
            self.get_connection()
        
        query = 'SELECT question FROM questions WHERE question = ?'
        try:
            cursor = self.conn.cursor()
            cursor.execute(query, (question,))
            result = cursor.fetchone()
            return result is not None
        except Error as e:
            logging.error(f"Error verifying question: {e}")
            return False

    def get_suggestions(self, partial_query):
        if not self.conn:
            self.get_connection()
            
        query = 'SELECT DISTINCT question FROM questions WHERE question LIKE ? LIMIT 5'
        try:
            cursor = self.conn.cursor()
            cursor.execute(query, (f'%{partial_query}%',))
            suggestions = [row[0] for row in cursor.fetchall()]
            logging.debug(f"Found suggestions: {suggestions}")
            return suggestions
        except Error as e:
            logging.error(f"Error getting suggestions: {e}")
            return []

    def verify_storage(self):
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM questions')
            count = cursor.fetchone()[0]
            logging.debug(f"Total questions in DB: {count}")
            return count
        except Error as e:
            logging.error(f"Error checking questions count: {e}")
            return 0

# Test the implementation
if __name__ == "__main__":
    db = Database()
    test_question = "Test question"
    success = db.add_question(test_question)
    print(f"Question added: {success}")