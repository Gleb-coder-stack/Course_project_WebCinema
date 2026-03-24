import psycopg2
from psycopg2.extras import RealDictCursor
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Настройки для подключения без пароля
DB_NAME = "cinema_db"
DB_USER = "postgres"
DB_PASSWORD = ""  # Пустой пароль
DB_HOST = "localhost"
DB_PORT = "5432"


class Database:
    def __init__(self):
        self.conn = None

    def get_connection(self):
        """Установка соединения с БД"""
        try:
            if not self.conn or self.conn.closed:
                logger.info("Подключение к базе данных...")

                # Подключение с пустым паролем
                self.conn = psycopg2.connect(
                    database=DB_NAME,
                    user=DB_USER,
                    password=DB_PASSWORD,
                    host=DB_HOST,
                    port=DB_PORT
                )

                logger.info("✅ Подключение успешно установлено")
            return self.conn
        except Exception as e:
            logger.error(f"❌ Ошибка подключения к БД: {e}")
            raise

    def test_connection(self):
        """Простой тест подключения"""
        try:
            conn = self.get_connection()
            with conn.cursor() as cur:
                cur.execute("SELECT version();")
                version = cur.fetchone()
                logger.info(f"Версия PostgreSQL: {version[0]}")

                cur.execute("SELECT COUNT(*) FROM movies;")
                count = cur.fetchone()
                logger.info(f"Количество фильмов: {count[0]}")

            return True
        except Exception as e:
            logger.error(f"Ошибка теста: {e}")
            return False


# Создаем экземпляр
db = Database()

if __name__ == "__main__":
    print("=" * 50)
    print("ТЕСТ ПОДКЛЮЧЕНИЯ К БАЗЕ ДАННЫХ")
    print("=" * 50)
    print(f"База данных: {DB_NAME}")
    print(f"Пользователь: {DB_USER}")
    print(f"Пароль: [пустой]")
    print(f"Хост: {DB_HOST}")
    print(f"Порт: {DB_PORT}")
    print("-" * 50)

    # Тестируем подключение
    if db.test_connection():
        print("\n✅ БАЗА ДАННЫХ РАБОТАЕТ!")
    else:
        print("\n❌ ОШИБКА ПОДКЛЮЧЕНИЯ К БД")
