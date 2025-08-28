import random
from database.db_config import Database

class UserManager:
    @staticmethod
    def create_user(user_id, username, first_name):
        db = Database()
        try:
            query = """
                INSERT INTO users (user_id, username, first_name) 
                VALUES (%s, %s, %s)
                ON CONFLICT (user_id) DO NOTHING
            """
            db.cursor.execute(query, (user_id, username, first_name))
            db.connection.commit()
            return True
        except Exception as e:
            db.connection.rollback()
            print(f"User creation error: {e}")
            return False
        finally:
            db.close()

    @staticmethod
    def get_user_words_count(user_id):
        db = Database()
        try:
            query = """
                SELECT COUNT(DISTINCT w.word_id) as count
                FROM words w
                LEFT JOIN user_words uw ON w.word_id = uw.word_id AND uw.user_id = %s
                WHERE w.is_default = TRUE OR uw.user_id = %s
            """
            db.cursor.execute(query, (user_id, user_id))
            result = db.cursor.fetchone()
            return result['count'] if result else 0
        except Exception as e:
            print(f"Error getting word count: {e}")
            return 0
        finally:
            db.close()

class WordManager:
    @staticmethod
    def get_available_words(user_id):
        db = Database()
        try:
            query = """
                SELECT DISTINCT w.word_id, w.english_word, w.russian_word, w.is_default
                FROM words w
                LEFT JOIN user_words uw ON w.word_id = uw.word_id AND uw.user_id = %s
                WHERE w.is_default = TRUE OR uw.user_id = %s
            """
            db.cursor.execute(query, (user_id, user_id))
            return db.cursor.fetchall()
        except Exception as e:
            print(f"Error getting words: {e}")
            return []
        finally:
            db.close()

    @staticmethod
    def get_random_word_with_options(user_id):
        available_words = WordManager.get_available_words(user_id)

        if len(available_words) < 4:
            return None

        correct_word = random.choice(available_words)
        other_words = [w for w in available_words if w['word_id'] != correct_word['word_id']]
        wrong_options = random.sample(other_words, min(3, len(other_words)))

        all_options = [correct_word] + wrong_options
        random.shuffle(all_options)

        return {
            'correct_word': correct_word,
            'all_options': all_options,
            'russian_word': correct_word['russian_word']
        }

    @staticmethod
    def add_user_word(user_id, english_word, russian_word):
        db = Database()
        try:
            query_word = """
                INSERT INTO words (english_word, russian_word, is_default, created_by)
                VALUES (%s, %s, FALSE, %s)
                RETURNING word_id
            """
            db.cursor.execute(query_word, (english_word, russian_word, user_id))
            result = db.cursor.fetchone()

            if result:
                word_id = result['word_id']
                query_user_word = """
                    INSERT INTO user_words (user_id, word_id)
                    VALUES (%s, %s)
                    ON CONFLICT (user_id, word_id) DO NOTHING
                """
                db.cursor.execute(query_user_word, (user_id, word_id))
                db.connection.commit()
                return True
            return False
        except Exception as e:
            db.connection.rollback()
            print(f"Error adding word: {e}")
            return False
        finally:
            db.close()

    @staticmethod
    def get_user_personal_words(user_id):
        db = Database()
        try:
            query = """
                SELECT w.word_id, w.english_word, w.russian_word
                FROM words w
                JOIN user_words uw ON w.word_id = uw.word_id
                WHERE uw.user_id = %s AND w.created_by = %s
                ORDER BY w.english_word
            """
            db.cursor.execute(query, (user_id, user_id))
            return db.cursor.fetchall()
        except Exception as e:
            print(f"Error getting personal words: {e}")
            return []
        finally:
            db.close()

    @staticmethod
    def delete_user_word(user_id, word_id):
        db = Database()
        try:
            query_user_words = """
                DELETE FROM user_words 
                WHERE user_id = %s AND word_id = %s
            """
            db.cursor.execute(query_user_words, (user_id, word_id))

            query_word = """
                DELETE FROM words 
                WHERE word_id = %s AND created_by = %s AND is_default = FALSE
            """
            db.cursor.execute(query_word, (word_id, user_id))
            db.connection.commit()
            return True
        except Exception as e:
            db.connection.rollback()
            print(f"Error deleting word: {e}")
            return False
        finally:
            db.close()