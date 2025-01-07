from contextlib import contextmanager
import mysql.connector
from mysql.connector import Error
from config import get_settings

class DatabaseConnection:
    def __init__(self):
        settings = get_settings()
        self.config = {
            'host': settings.DB_HOST,
            'user': settings.DB_USER,
            'password': settings.DB_PASSWORD,
            'database': settings.DB_NAME,
            'port': settings.DB_PORT
        }

    @contextmanager
    def get_cursor(self):
        conn = None
        try:
            conn = mysql.connector.connect(**self.config)
            cursor = conn.cursor(dictionary=True)
            yield cursor
            conn.commit()
        except Error as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close() 