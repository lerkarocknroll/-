import psycopg2
from psycopg2.extras import RealDictCursor


class Database:
    def __init__(self):
        # Импортируем здесь чтобы избежать циклических импортов
        from config import DATABASE_CONFIG

        try:
            self.connection = psycopg2.connect(
                host=DATABASE_CONFIG['host'],
                database=DATABASE_CONFIG['database'],
                user=DATABASE_CONFIG['user'],
                password=DATABASE_CONFIG['password'],
                port=DATABASE_CONFIG['port'],
                cursor_factory=RealDictCursor,
                client_encoding='utf8'
            )

            self.connection.set_client_encoding('UTF8')
            self.cursor = self.connection.cursor()

        except Exception as e:
            print(f"Database connection failed: {e}")
            raise

    def execute_query(self, query, params=None):
        try:
            self.cursor.execute(query, params)
            self.connection.commit()
            return self.cursor.fetchall()
        except Exception as e:
            self.connection.rollback()
            raise

    def execute_one(self, query, params=None):
        try:
            self.cursor.execute(query, params)
            return self.cursor.fetchone()
        except Exception as e:
            raise

    def close(self):
        if hasattr(self, 'cursor') and self.cursor:
            self.cursor.close()
        if hasattr(self, 'connection') and self.connection:
            self.connection.close()