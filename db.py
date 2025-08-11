import mysql.connector
from contextlib import contextmanager
from config import Config

def get_db_connection():
    @contextmanager
    def connection():
        conn = mysql.connector.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME
        )
        try:
            yield conn
        finally:
            conn.close()
    return connection()

def execute_query(query, params=None, dictionary=False):
    with get_db_connection() as conn:
        cursor = conn.cursor(dictionary=dictionary)
        cursor.execute(query, params or ())
        result = cursor.fetchall()
        conn.commit()
        return result

def execute_insert(query, params=None):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params or ())
        conn.commit()
        return cursor.lastrowid

def execute_upsert(query, params=None):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params or ())
        conn.commit()