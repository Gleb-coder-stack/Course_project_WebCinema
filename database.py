import psycopg2
from psycopg2.extras import RealDictCursor
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Настройки подключения - ВАШ ПАРОЛЬ
DB_PASSWORD = ""  # ИЗМЕНИТЕ НА СВОЙ ПАРОЛЬ


class Database:
    def __init__(self):
        self.conn = None

    def get_connection(self):
        """Установка соединения с БД"""
        try:
            if not self.conn or self.conn.closed:
                logger.info("Подключение к базе данных...")
                self.conn = psycopg2.connect(
                    dbname='Cinema4',
                    user='postgres',
                    password=DB_PASSWORD,
                    host='127.0.0.1',
                    port='5432'
                )
                logger.info("✅ Подключение успешно установлено")
            return self.conn
        except Exception as e:
            logger.error(f"❌ Ошибка подключения к БД: {e}")
            raise

    def execute_query(self, query, params=None, fetch_one=False, fetch_all=False):
        """Универсальный метод для выполнения запросов"""
        try:
            conn = self.get_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                logger.info(f"Выполнение: {query[:100]}...")
                cur.execute(query, params or ())

                if fetch_one:
                    result = cur.fetchone()
                    conn.commit()  # <-- ВАЖНО: коммит после fetch_one!
                    logger.info(f"fetch_one результат: {result}")
                    return result
                elif fetch_all:
                    result = cur.fetchall()
                    logger.info(f"fetch_all: {len(result) if result else 0} записей")
                    return result
                else:
                    conn.commit()
                    logger.info(f"Затронуто строк: {cur.rowcount}")
                    return cur.rowcount
        except Exception as e:
            logger.error(f"Ошибка: {e}")
            conn.rollback()  # <-- откат при ошибке
            raise

    # ========== ФИЛЬМЫ ==========
    def get_movies(self):
        """Получение всех фильмов"""
        query = "SELECT id, title, duration, genre, age_rating FROM movies ORDER BY id"
        return self.execute_query(query, fetch_all=True) or []

    def add_movie(self, title, duration, genre, age_rating):
        """Добавление нового фильма"""
        query = """
            INSERT INTO movies (title, duration, genre, age_rating) 
            VALUES (%s, %s, %s, %s) 
            RETURNING id
        """
        result = self.execute_query(query, (title, duration, genre, age_rating), fetch_one=True)
        return result['id'] if result else None

    def update_movie(self, movie_id, title, duration, genre, age_rating):
        """Обновление фильма"""
        query = """
            UPDATE movies 
            SET title = %s, duration = %s, genre = %s, age_rating = %s
            WHERE id = %s
        """
        return self.execute_query(query, (title, duration, genre, age_rating, movie_id)) > 0

    def delete_movie(self, movie_id):
        """Удаление фильма"""
        query = "DELETE FROM movies WHERE id = %s"
        return self.execute_query(query, (movie_id,)) > 0

    def delete_movie(self, movie_id, deleted_by=None):
        """Удаление фильма с архивацией"""
        try:
            # Получаем данные фильма перед удалением
            movie = self.execute_query(
                "SELECT * FROM movies WHERE id = %s",
                (movie_id,),
                fetch_one=True
            )

            if not movie:
                return False

            # Архивируем фильм
            archive_query = """
                INSERT INTO movies_archive 
                (original_id, title, duration, genre, age_rating, deleted_by)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            self.execute_query(
                archive_query,
                (movie['id'], movie['title'], movie['duration'],
                 movie['genre'], movie['age_rating'], deleted_by)
            )

            # Логируем действие
            self.log_action(
                user_id=deleted_by,
                username=None,
                action='DELETE',
                entity_type='movie',
                entity_id=movie_id,
                details=f"Удален фильм: {movie['title']}"
            )

            # Удаляем из основной таблицы
            query = "DELETE FROM movies WHERE id = %s"
            return self.execute_query(query, (movie_id,)) > 0

        except Exception as e:
            logger.error(f"Ошибка при удалении фильма: {e}")
            return False

    def delete_movie(self, movie_id, deleted_by=None):
        """Удаление фильма с архивацией"""
        try:
            # Получаем данные фильма перед удалением
            movie = self.execute_query(
                "SELECT * FROM movies WHERE id = %s",
                (movie_id,),
                fetch_one=True
            )

            if not movie:
                return False

            # Архивируем фильм
            archive_query = """
                INSERT INTO movies_archive 
                (original_id, title, duration, genre, age_rating, deleted_by)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            self.execute_query(
                archive_query,
                (movie['id'], movie['title'], movie['duration'],
                 movie['genre'], movie['age_rating'], deleted_by)
            )

            # Логируем действие
            self.log_action(
                user_id=deleted_by,
                username=None,
                action='DELETE',
                entity_type='movie',
                entity_id=movie_id,
                details=f"Удален фильм: {movie['title']}"
            )

            # Удаляем из основной таблицы
            query = "DELETE FROM movies WHERE id = %s"
            return self.execute_query(query, (movie_id,)) > 0

        except Exception as e:
            logger.error(f"Ошибка при удалении фильма: {e}")
            return False

    # ========== СЕАНСЫ (ТОЛЬКО ПОЛЯ ИЗ ИНТЕРФЕЙСА) ==========
    def get_sessions(self):
        """Получение всех сеансов"""
        try:
            query = """
                SELECT 
                    s.id,
                    to_char(s.session_date, 'DD.MM.YYYY') as date,
                    to_char(s.session_date, 'YYYY-MM-DD') as date_raw,
                    to_char(s.start_time, 'HH24:MI') as start_time,
                    to_char(s.end_time, 'HH24:MI') as end_time,
                    m.title as movie,
                    m.duration,
                    m.genre,
                    m.age_rating,
                    h.hall_number as hall
                FROM sessions s
                JOIN movies m ON s.movie_id = m.id
                JOIN halls h ON s.hall_id = h.id
                ORDER BY s.session_date, s.start_time
            """
            result = self.execute_query(query, fetch_all=True)
            logger.info(f"get_sessions: найдено {len(result) if result else 0} сеансов")

            return result or []

        except Exception as e:
            logger.error(f"Ошибка в get_sessions: {e}")
            return []

    def get_session_by_id(self, session_id):
        """Получение информации о конкретном сеансе"""
        try:
            logger.info(f"=== get_session_by_id({session_id}) ===")

            # Проверяем подключение
            conn = self.get_connection()
            if not conn:
                logger.error("Нет подключения к БД")
                return None

            # Выполняем запрос
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                query = """
                    SELECT 
                        s.id,
                        s.session_date,
                        s.start_time,
                        s.end_time,
                        s.movie_id,
                        s.hall_id,
                        m.title as movie_title,
                        m.duration,
                        m.genre,
                        m.age_rating,
                        h.hall_number
                    FROM sessions s
                    LEFT JOIN movies m ON s.movie_id = m.id
                    LEFT JOIN halls h ON s.hall_id = h.id
                    WHERE s.id = %s
                """
                logger.debug(f"SQL: {query}")
                logger.debug(f"Params: {session_id}")

                cur.execute(query, (session_id,))
                row = cur.fetchone()

                if not row:
                    logger.warning(f"Сеанс {session_id} не найден")
                    return None

                # Форматируем результат
                result = {
                    'id': row['id'],
                    'date': row['session_date'].strftime('%d.%m.%Y') if row['session_date'] else None,
                    'date_raw': str(row['session_date']) if row['session_date'] else None,
                    'start_time': row['start_time'].strftime('%H:%M') if row['start_time'] else None,
                    'end_time': row['end_time'].strftime('%H:%M') if row['end_time'] else None,
                    'movie_id': row['movie_id'],
                    'movie': row['movie_title'],
                    'duration': row['duration'],
                    'genre': row['genre'],
                    'age_rating': row['age_rating'],
                    'hall_id': row['hall_id'],
                    'hall': row['hall_number']
                }

                logger.info(f"Найден сеанс: {result}")
                return result

        except Exception as e:
            logger.error(f"❌ Ошибка в get_session_by_id: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None

    def get_seats(self, hall_id):
        """Получение всех мест в зале"""
        try:
            logger.info(f"=== get_seats({hall_id}) ===")

            conn = self.get_connection()
            if not conn:
                logger.error("Нет подключения к БД")
                return []

            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                query = """
                    SELECT 
                        s.id, 
                        s.row_number,
                        s.seat_number,
                        s.tariff_id,
                        t.tariff_name,
                        t.price
                    FROM seats s
                    LEFT JOIN tariffs t ON s.tariff_id = t.id
                    WHERE s.hall_id = %s 
                    ORDER BY s.row_number, s.seat_number
                """
                logger.debug(f"SQL: {query}")
                logger.debug(f"Params: {hall_id}")

                cur.execute(query, (hall_id,))
                rows = cur.fetchall()

                result = []
                for row in rows:
                    result.append({
                        'id': row['id'],
                        'row': row['row_number'],
                        'seat': row['seat_number'],
                        'tariff_id': row['tariff_id'],
                        'type': row['tariff_name'] or 'Стандарт',
                        'price': row['price'] or 350
                    })

                logger.info(f"Найдено мест: {len(result)}")
                return result

        except Exception as e:
            logger.error(f"❌ Ошибка в get_seats: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []

    def authenticate(self, username, password):
        """Авторизация пользователя"""
        try:
            logger.info(f"Поиск пользователя: {username}")

            query = """
                SELECT id, username, role, full_name 
                FROM users 
                WHERE username = %s AND password = %s
            """
            result = self.execute_query(query, (username, password), fetch_one=True)

            if result:
                logger.info(f"Пользователь найден: {result['username']} ({result['role']})")
            else:
                logger.warning(f"Пользователь не найден: {username}")

            return result

        except Exception as e:
            logger.error(f"Ошибка в authenticate: {e}")
            return None

    def get_sold_tickets(self, session_id):
        """Получение проданных билетов на сеанс"""
        try:
            logger.info(f"get_sold_tickets({session_id})")

            query = """
                SELECT 
                    t.id, 
                    t.customer_name, 
                    t.price, 
                    t.payment_method,
                    se.row_number,
                    se.seat_number,
                    se.id as seat_id
                FROM tickets t
                JOIN seats se ON t.seat_id = se.id
                WHERE t.session_id = %s AND t.is_returned = false
            """
            result = self.execute_query(query, (session_id,), fetch_all=True)

            logger.info(f"Найдено билетов: {len(result) if result else 0}")

            if result:
                for ticket in result:
                    logger.info(
                        f"Билет ID {ticket['id']}: ряд={ticket.get('row_number')}, место={ticket.get('seat_number')}")
            else:
                logger.warning(f"Нет билетов для сеанса {session_id}")

            # Переименовываем поля для удобства
            formatted_result = []
            for ticket in result or []:
                formatted_result.append({
                    'id': ticket['id'],
                    'customer_name': ticket['customer_name'],
                    'price': ticket['price'],
                    'payment_method': ticket['payment_method'],
                    'row': ticket['row_number'],
                    'seat': ticket['seat_number'],
                    'seat_id': ticket['seat_id']
                })

            return formatted_result

        except Exception as e:
            logger.error(f"Ошибка в get_sold_tickets: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []

    def add_session(self, session_date, movie_id, start_time, end_time, hall_id):
        """Добавление сеанса с проверкой на конфликт"""
        try:
            # Проверяем, нет ли конфликтующего сеанса
            conflict = self.execute_query("""
                SELECT id FROM sessions 
                WHERE hall_id = %s AND session_date = %s 
                AND start_time = %s
            """, (hall_id, session_date, start_time), fetch_one=True)

            if conflict:
                return {"success": False, "error": "В этом зале уже есть сеанс в указанное время"}

            query = """
                INSERT INTO sessions (session_date, movie_id, start_time, end_time, hall_id) 
                VALUES (%s, %s, %s, %s, %s) 
                RETURNING id
            """
            result = self.execute_query(query, (session_date, movie_id, start_time, end_time, hall_id), fetch_one=True)

            return {"success": True, "id": result['id']} if result else {"success": False, "error": "Ошибка добавления"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def update_session(self, session_id, session_date, movie_id, start_time, end_time, hall_id):
        """Обновление сеанса с проверкой на конфликты"""
        try:
            # Проверяем на пересечение с другими сеансами (исключая текущий)
            has_conflict, conflicts = self.check_session_conflict(
                hall_id, session_date, start_time, end_time, exclude_session_id=session_id
            )

            if has_conflict:
                conflict_times = []
                for c in conflicts or []:
                    conflict_times.append(f"{c['start_time']}-{c['end_time']}")

                error_msg = f"В зале {hall_id} уже есть другой сеанс в это время: {', '.join(conflict_times)}"
                logger.warning(error_msg)
                return {"success": False, "error": error_msg}

            # Если конфликтов нет, обновляем сеанс
            query = """
                UPDATE sessions 
                SET session_date = %s, movie_id = %s, start_time = %s, end_time = %s, hall_id = %s
                WHERE id = %s
            """
            result = self.execute_query(
                query,
                (session_date, movie_id, start_time, end_time, hall_id, session_id)
            )

            if result > 0:
                logger.info(f"Сеанс {session_id} успешно обновлен")
                return {"success": True}
            else:
                return {"success": False, "error": "Сеанс не найден"}

        except Exception as e:
            logger.error(f"Ошибка при обновлении сеанса: {e}")
            return {"success": False, "error": str(e)}

    def delete_session(self, session_id):
        """Удаление сеанса"""
        query = "DELETE FROM sessions WHERE id = %s"
        return self.execute_query(query, (session_id,)) > 0

    def delete_session(self, session_id, deleted_by=None):
        """Удаление сеанса с архивацией"""
        try:
            # Получаем данные сеанса перед удалением
            session = self.execute_query("""
                SELECT s.*, m.title as movie_title 
                FROM sessions s
                JOIN movies m ON s.movie_id = m.id
                WHERE s.id = %s
            """, (session_id,), fetch_one=True)

            if not session:
                return False

            # Архивируем сеанс
            archive_query = """
                INSERT INTO sessions_archive 
                (original_id, session_date, movie_id, start_time, end_time, hall_id, deleted_by)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            self.execute_query(
                archive_query,
                (session['id'], session['session_date'], session['movie_id'],
                 session['start_time'], session['end_time'], session['hall_id'], deleted_by)
            )

            # Логируем действие
            self.log_action(
                user_id=deleted_by,
                username=None,
                action='DELETE',
                entity_type='session',
                entity_id=session_id,
                details=f"Удален сеанс: {session['movie_title']} {session['session_date']}"
            )

            # Удаляем из основной таблицы
            query = "DELETE FROM sessions WHERE id = %s"
            return self.execute_query(query, (session_id,)) > 0

        except Exception as e:
            logger.error(f"Ошибка при удалении сеанса: {e}")
            return False

    def delete_session(self, session_id, deleted_by=None):
        """Удаление сеанса с архивацией"""
        try:
            # Получаем данные сеанса перед удалением
            session = self.execute_query("""
                SELECT s.*, m.title as movie_title 
                FROM sessions s
                JOIN movies m ON s.movie_id = m.id
                WHERE s.id = %s
            """, (session_id,), fetch_one=True)

            if not session:
                return False

            # Архивируем сеанс
            archive_query = """
                INSERT INTO sessions_archive 
                (original_id, session_date, movie_id, start_time, end_time, hall_id, deleted_by)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            self.execute_query(
                archive_query,
                (session['id'], session['session_date'], session['movie_id'],
                 session['start_time'], session['end_time'], session['hall_id'], deleted_by)
            )

            # Логируем действие
            self.log_action(
                user_id=deleted_by,
                username=None,
                action='DELETE',
                entity_type='session',
                entity_id=session_id,
                details=f"Удален сеанс: {session['movie_title']} {session['session_date']}"
            )

            # Удаляем из основной таблицы
            query = "DELETE FROM sessions WHERE id = %s"
            return self.execute_query(query, (session_id,)) > 0

        except Exception as e:
            logger.error(f"Ошибка при удалении сеанса: {e}")
            return False

    # ========== ТАРИФЫ ==========
    def get_tariffs(self):
        """Получение всех тарифов"""
        query = "SELECT id, tariff_name as name, price FROM tariffs ORDER BY id"
        return self.execute_query(query, fetch_all=True) or []

    def add_tariff(self, name, price):
        """Добавление нового тарифа"""
        query = "INSERT INTO tariffs (tariff_name, price) VALUES (%s, %s) RETURNING id"
        result = self.execute_query(query, (name, price), fetch_one=True)
        return result['id'] if result else None

    def update_tariff(self, tariff_id, name, price):
        """Обновление тарифа"""
        query = "UPDATE tariffs SET tariff_name = %s, price = %s WHERE id = %s"
        return self.execute_query(query, (name, price, tariff_id)) > 0

    def delete_tariff(self, tariff_id):
        """Удаление тарифа"""
        query = "DELETE FROM tariffs WHERE id = %s"
        return self.execute_query(query, (tariff_id,)) > 0

    # ========== МЕСТА ==========
    def get_seats(self, hall_id):
        """Получение всех мест в зале с информацией о тарифе"""
        query = """
            SELECT 
                s.id, 
                s.row_number as row, 
                s.seat_number as seat,
                t.tariff_name as type,
                t.price
            FROM seats s
            JOIN tariffs t ON s.tariff_id = t.id
            WHERE s.hall_id = %s 
            ORDER BY s.row_number, s.seat_number
        """
        return self.execute_query(query, (hall_id,), fetch_all=True) or []

    # ========== БИЛЕТЫ ==========
    def get_sold_tickets(self, session_id):
        """Получение проданных билетов на сеанс"""
        try:
            logger.info(f"get_sold_tickets({session_id})")

            query = """
                SELECT 
                    t.id, 
                    t.customer_name, 
                    t.price, 
                    t.payment_method,
                    s.row_number, 
                    s.seat_number,
                    s.id as seat_id
                FROM tickets t
                JOIN seats s ON t.seat_id = s.id
                WHERE t.session_id = %s AND t.is_returned = false
            """
            result = self.execute_query(query, (session_id,), fetch_all=True)
            logger.info(f"Найдено билетов: {len(result) if result else 0}")

            if result:
                for ticket in result:
                    logger.info(f"Проданное место ID: {ticket['seat_id']}")

            return result or []

        except Exception as e:
            logger.error(f"Ошибка в get_sold_tickets: {e}")
            return []

    def buy_ticket(self, session_id, seat_id, customer_name, price, payment_method):
        """Покупка билета"""
        query = """
            INSERT INTO tickets (session_id, seat_id, customer_name, price, payment_method, is_returned) 
            VALUES (%s, %s, %s, %s, %s, false) 
            RETURNING id
        """
        params = (session_id, seat_id, customer_name, price, payment_method)
        result = self.execute_query(query, params, fetch_one=True)
        return result['id'] if result else None

    def return_ticket(self, ticket_id):
        """Возврат билета"""
        query = "UPDATE tickets SET is_returned = true WHERE id = %s"
        return self.execute_query(query, (ticket_id,)) > 0

    def return_ticket(self, ticket_id, returned_by=None):
        """Возврат билета с архивацией"""
        try:
            # Получаем данные билета перед возвратом
            ticket = self.execute_query("""
                SELECT t.*, s.session_date, m.title as movie_title
                FROM tickets t
                JOIN sessions s ON t.session_id = s.id
                JOIN movies m ON s.movie_id = m.id
                WHERE t.id = %s
            """, (ticket_id,), fetch_one=True)

            if not ticket:
                return False

            # Архивируем билет
            archive_query = """
                INSERT INTO tickets_archive 
                (original_id, session_id, seat_id, customer_name, price, 
                 payment_method, sold_at, returned_by)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            self.execute_query(
                archive_query,
                (ticket['id'], ticket['session_id'], ticket['seat_id'],
                 ticket['customer_name'], ticket['price'], ticket['payment_method'],
                 ticket['sold_at'], returned_by)
            )

            # Логируем действие
            self.log_action(
                user_id=returned_by,
                username=None,
                action='RETURN',
                entity_type='ticket',
                entity_id=ticket_id,
                details=f"Возврат билета: {ticket['movie_title']} - {ticket['customer_name']}"
            )

            # Отмечаем билет как возвращенный
            query = "UPDATE tickets SET is_returned = true WHERE id = %s"
            return self.execute_query(query, (ticket_id,)) > 0

        except Exception as e:
            logger.error(f"Ошибка при возврате билета: {e}")
            return False

    def return_ticket(self, ticket_id, returned_by=None):
        """Возврат билета с архивацией"""
        try:
            # Получаем данные билета перед возвратом
            ticket = self.execute_query("""
                SELECT t.*, s.session_date, m.title as movie_title
                FROM tickets t
                JOIN sessions s ON t.session_id = s.id
                JOIN movies m ON s.movie_id = m.id
                WHERE t.id = %s
            """, (ticket_id,), fetch_one=True)

            if not ticket:
                return False

            # Архивируем билет
            archive_query = """
                INSERT INTO tickets_archive 
                (original_id, session_id, seat_id, customer_name, price, 
                 payment_method, sold_at, returned_by)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            self.execute_query(
                archive_query,
                (ticket['id'], ticket['session_id'], ticket['seat_id'],
                 ticket['customer_name'], ticket['price'], ticket['payment_method'],
                 ticket['sold_at'], returned_by)
            )

            # Логируем действие
            self.log_action(
                user_id=returned_by,
                username=None,
                action='RETURN',
                entity_type='ticket',
                entity_id=ticket_id,
                details=f"Возврат билета: {ticket['movie_title']} - {ticket['customer_name']}"
            )

            # Отмечаем билет как возвращенный
            query = "UPDATE tickets SET is_returned = true WHERE id = %s"
            return self.execute_query(query, (ticket_id,)) > 0

        except Exception as e:
            logger.error(f"Ошибка при возврате билета: {e}")
            return False

    # ========== ПОЛЬЗОВАТЕЛИ ==========
    def get_users(self):
        """Получение всех пользователей"""
        query = "SELECT id, username, role, full_name FROM users ORDER BY id"
        result = self.execute_query(query, fetch_all=True)
        logger.info(f"get_users: найдено {len(result) if result else 0} пользователей")
        return result or []

    def authenticate(self, username, password):
        """Авторизация пользователя"""
        query = """
            SELECT id, username, role, full_name 
            FROM users 
            WHERE username = %s AND password = %s
        """
        return self.execute_query(query, (username, password), fetch_one=True)

    def add_user(self, username, password, role, full_name):
        """Добавление нового пользователя с проверкой на дубликат"""
        try:
            # Проверяем, существует ли пользователь
            check = self.execute_query(
                "SELECT id FROM users WHERE username = %s",
                (username,),
                fetch_one=True
            )

            if check:
                logger.warning(f"Пользователь {username} уже существует")
                return {"success": False, "error": "Пользователь с таким логином уже существует"}

            query = """
                INSERT INTO users (username, password, role, full_name) 
                VALUES (%s, %s, %s, %s) 
                RETURNING id
            """
            result = self.execute_query(query, (username, password, role, full_name), fetch_one=True)

            return {"success": True, "id": result['id']} if result else {"success": False, "error": "Ошибка добавления"}

        except Exception as e:
            logger.error(f"Ошибка в add_user: {e}")
            return {"success": False, "error": str(e)}

    def update_user(self, user_id, username, role, full_name, password=None):
        """Обновление пользователя"""
        if password:
            query = "UPDATE users SET username = %s, password = %s, role = %s, full_name = %s WHERE id = %s"
            params = (username, password, role, full_name, user_id)
        else:
            query = "UPDATE users SET username = %s, role = %s, full_name = %s WHERE id = %s"
            params = (username, role, full_name, user_id)
        return self.execute_query(query, params) > 0

    def delete_user(self, user_id, deleted_by=None):
        """Удаление пользователя с архивацией"""
        try:
            # Получаем данные пользователя перед удалением
            user = self.execute_query(
                "SELECT * FROM users WHERE id = %s",
                (user_id,),
                fetch_one=True
            )

            if not user:
                logger.warning(f"Пользователь с ID {user_id} не найден")
                return False

            # Архивируем пользователя
            archive_query = """
                INSERT INTO users_archive 
                (original_id, username, password, role, full_name, deleted_by, archive_reason)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            self.execute_query(
                archive_query,
                (user['id'], user['username'], user['password'],
                 user['role'], user['full_name'], deleted_by, 'Удалено администратором')
            )

            # Логируем действие
            log_query = """
                INSERT INTO action_logs 
                (user_id, username, action, entity_type, entity_id, details)
                VALUES (%s, %s, %s, %s, %s, %s)
            """

            # Получаем имя пользователя, который выполняет удаление
            deleter_name = None
            if deleted_by:
                deleter = self.execute_query(
                    "SELECT username FROM users WHERE id = %s",
                    (deleted_by,),
                    fetch_one=True
                )
                if deleter:
                    deleter_name = deleter['username']

            self.execute_query(
                log_query,
                (deleted_by, deleter_name, 'DELETE', 'user', user_id,
                 f"Удален пользователь: {user['username']} ({user['role']})")
            )

            # Удаляем из основной таблицы
            query = "DELETE FROM users WHERE id = %s"
            result = self.execute_query(query, (user_id,)) > 0

            if result:
                logger.info(f"Пользователь {user['username']} (ID: {user_id}) удален и заархивирован")

            return result

        except Exception as e:
            logger.error(f"Ошибка при удалении пользователя: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False

    def log_action(self, user_id=None, username=None, action=None,
                   entity_type=None, entity_id=None, details=None):
        """Логирование действий пользователей"""
        try:
            query = """
                INSERT INTO action_logs 
                (user_id, username, action, entity_type, entity_id, details)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            self.execute_query(
                query,
                (user_id, username, action, entity_type, entity_id, details)
            )
            return True
        except Exception as e:
            logger.error(f"Ошибка при логировании: {e}")
            return False

    def log_action(self, user_id=None, username=None, action=None,
                   entity_type=None, entity_id=None, details=None):
        """Логирование действий пользователей"""
        try:
            query = """
                INSERT INTO action_logs 
                (user_id, username, action, entity_type, entity_id, details)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            self.execute_query(
                query,
                (user_id, username, action, entity_type, entity_id, details)
            )
            return True
        except Exception as e:
            logger.error(f"Ошибка при логировании: {e}")
            return False

    def check_session_conflict(self, hall_id, session_date, start_time, end_time, exclude_session_id=None):
        """
        Проверка на пересечение сеансов в одном зале
        Возвращает True, если есть конфликт (пересечение)
        """
        try:
            query = """
                SELECT id, start_time, end_time 
                FROM sessions 
                WHERE hall_id = %s 
                  AND session_date = %s
                  AND (
                      (start_time < %s AND end_time > %s) OR  -- новый сеанс начинается внутри существующего
                      (start_time < %s AND end_time > %s) OR  -- новый сеанс заканчивается внутри существующего
                      (start_time >= %s AND end_time <= %s) OR -- новый сеанс полностью внутри существующего
                      (start_time <= %s AND end_time >= %s)    -- существующий сеанс полностью внутри нового
                  )
            """
            params = [hall_id, session_date, end_time, start_time,
                      start_time, end_time, start_time, end_time,
                      start_time, end_time]

            # Если обновляем существующий сеанс, исключаем его из проверки
            if exclude_session_id:
                query += " AND id != %s"
                params.append(exclude_session_id)

            conflicting = self.execute_query(query, tuple(params), fetch_all=True)

            if conflicting:
                logger.warning(f"Найдены конфликтующие сеансы: {conflicting}")
                return True, conflicting

            return False, None

        except Exception as e:
            logger.error(f"Ошибка при проверке конфликтов: {e}")
            return True, None  # В случае ошибки лучше запретить

# Создаем глобальный экземпляр
db = Database()

# Проверяем подключение при запуске
if __name__ == "__main__":
    try:
        conn = db.get_connection()
        logger.info("✅ База данных готова к работе")

        # Проверяем данные
        users = db.get_users()
        sessions = db.get_sessions()
        movies = db.get_movies()
        tariffs = db.get_tariffs()

        logger.info(f"Пользователей: {len(users)}")
        logger.info(f"Сеансов: {len(sessions)}")
        logger.info(f"Фильмов: {len(movies)}")
        logger.info(f"Тарифов: {len(tariffs)}")

    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")