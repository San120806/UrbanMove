import time
import pymysql
import pymysql.cursors
from config import Config

class DatabaseHelper:
    def __init__(self):
        self.host = Config.DB_HOST
        self.user = Config.DB_USER
        self.password = Config.DB_PASSWORD
        self.db = Config.DB_NAME
        self.port = Config.DB_PORT

    def get_connection(self, retries=5, delay=3):
        """Attempts to connect to the database with retry logic."""
        for attempt in range(1, retries + 1):
            try:
                conn = pymysql.connect(
                    host=self.host,
                    user=self.user,
                    password=self.password,
                    database=self.db,
                    port=self.port,
                    cursorclass=pymysql.cursors.DictCursor,
                    autocommit=True
                )
                return conn
            except pymysql.MySQLError as e:
                print(f"[DB Connect] Attempt {attempt}/{retries} failed: {e}")
                if attempt == retries:
                    raise e
                time.sleep(delay)

    def check_health(self):
        """Pings the database to check connectivity."""
        try:
            conn = self.get_connection(retries=1, delay=1)
            conn.ping(reconnect=True)
            conn.close()
            return True, "Database is healthy and reachable."
        except Exception as e:
            return False, f"Database unreachable: {str(e)}"

    def execute_query(self, query, params=None):
        """Executes a SELECT query and returns all matching rows."""
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor() as cursor:
                cursor.execute(query, params or ())
                result = cursor.fetchall()
                return result
        except pymysql.MySQLError as e:
            print(f"[DB Query Error] Query: {query} | Error: {e}")
            raise e
        finally:
            if conn:
                conn.close()

    def execute_one(self, query, params=None):
        """Executes a SELECT query and returns the first matching row."""
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor() as cursor:
                cursor.execute(query, params or ())
                result = cursor.fetchone()
                return result
        except pymysql.MySQLError as e:
            print(f"[DB Query Error] Query: {query} | Error: {e}")
            raise e
        finally:
            if conn:
                conn.close()

    def execute_update(self, query, params=None):
        """Executes an INSERT, UPDATE, or DELETE query and returns the lastrowid (for INSERT) or affected row count."""
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor() as cursor:
                cursor.execute(query, params or ())
                # Return the auto-increment ID if it was an insert, else rowcount
                if query.strip().upper().startswith('INSERT'):
                    return cursor.lastrowid
                return cursor.rowcount
        except pymysql.MySQLError as e:
            print(f"[DB Update Error] Query: {query} | Error: {e}")
            raise e
        finally:
            if conn:
                conn.close()

# Singleton instance for the application to import
db_helper = DatabaseHelper()
