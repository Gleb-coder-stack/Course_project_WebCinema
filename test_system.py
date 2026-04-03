from main import app
from fastapi.testclient import TestClient

client = TestClient(app)


# =====================================================
# МОДУЛЬНОЕ ТЕСТИРОВАНИЕ (2 позитивных + 2 негативных)
# =====================================================

class TestModuleMovies:

    # ПОЗИТИВНЫЙ ТЕСТ 1: Получение списка фильмов
    def test_get_movies_positive(self):
        response = client.get("/api/movies")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        print("✅ Позитивный тест 1 пройден: Список фильмов получен")

    # ПОЗИТИВНЫЙ ТЕСТ 2: Получение списка сеансов
    def test_get_sessions_positive(self):
        response = client.get("/api/sessions")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        print("✅ Позитивный тест 2 пройден: Список сеансов получен")

    # НЕГАТИВНЫЙ ТЕСТ 1: Получение несуществующего сеанса
    def test_get_session_not_found_negative(self):
        response = client.get("/api/session/99999")
        # API возвращает 200 с None при отсутствии сеанса
        assert response.status_code == 200
        assert response.json() is None
        print("✅ Негативный тест 1 пройден: Несуществующий сеанс не найден")

    # НЕГАТИВНЫЙ ТЕСТ 2: Получение несуществующего зала
    def test_get_seats_wrong_hall_negative(self):
        response = client.get("/api/seats/99999")
        # API возвращает 200 с пустым массивом при неверном зале
        assert response.status_code == 200
        assert response.json() == []
        print("✅ Негативный тест 2 пройден: Несуществующий зал возвращает пустой массив")


class TestModuleTickets:

    # ПОЗИТИВНЫЙ ТЕСТ 3: Авторизация администратора
    def test_login_admin_positive(self):
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        response = client.post("/api/login", json=login_data)
        assert response.status_code == 200
        assert response.json()["success"] == True
        assert response.json()["user"]["role"] == "admin"
        print("✅ Позитивный тест 3 пройден: Авторизация администратора успешна")

    # ПОЗИТИВНЫЙ ТЕСТ 4: Авторизация кассира
    def test_login_cashier_positive(self):
        login_data = {
            "username": "cashier1",
            "password": "cash123"
        }
        response = client.post("/api/login", json=login_data)
        assert response.status_code == 200
        assert response.json()["success"] == True
        assert response.json()["user"]["role"] == "cashier"
        print("✅ Позитивный тест 4 пройден: Авторизация кассира успешна")

    # НЕГАТИВНЫЙ ТЕСТ 3: Авторизация с неверным паролем
    def test_login_wrong_password_negative(self):
        login_data = {
            "username": "admin",
            "password": "wrongpassword"
        }
        response = client.post("/api/login", json=login_data)
        assert response.status_code == 200
        assert response.json()["success"] == False
        assert "Неверный логин или пароль" in response.json()["error"]
        print("✅ Негативный тест 3 пройден: Неверный пароль отклонен")

    # НЕГАТИВНЫЙ ТЕСТ 4: Авторизация с несуществующим логином
    def test_login_wrong_username_negative(self):
        login_data = {
            "username": "nonexistent",
            "password": "123"
        }
        response = client.post("/api/login", json=login_data)
        assert response.status_code == 200
        assert response.json()["success"] == False
        assert "Неверный логин или пароль" in response.json()["error"]
        print("✅ Негативный тест 4 пройден: Несуществующий логин отклонен")


# =====================================================
# ИНТЕГРАЦИОННОЕ ТЕСТИРОВАНИЕ (1 тест)
# =====================================================

class TestIntegration:

    def test_integration_session_and_seats(self):
        """Тест взаимодействия API и БД: сеанс → зал → места"""

        # 1. Получаем список сеансов
        sessions_response = client.get("/api/sessions")
        assert sessions_response.status_code == 200
        sessions = sessions_response.json()
        assert len(sessions) > 0

        # 2. Берем первый сеанс и получаем его зал
        first_session = sessions[0]
        hall_id = first_session.get("hall_id", 1)

        # 3. Получаем места для этого зала
        seats_response = client.get(f"/api/seats/{hall_id}")
        assert seats_response.status_code == 200
        seats = seats_response.json()

        # 4. Проверяем, что места есть (должно быть 200 мест: 10 рядов × 20 мест)
        assert len(seats) == 200

        # 5. Проверяем структуру места
        if len(seats) > 0:
            first_seat = seats[0]
            assert "id" in first_seat
            assert "row" in first_seat
            assert "seat" in first_seat
            assert "type" in first_seat
            assert "price" in first_seat

        print("✅ Интеграционный тест пройден: Сеанс → Зал → Места работают корректно")


# =====================================================
# ФУНКЦИОНАЛЬНОЕ ТЕСТИРОВАНИЕ (1 тест)
# =====================================================

class TestFunctional:

    def test_functional_full_workflow(self):
        """Полный сценарий: авторизация → просмотр сеансов → просмотр схемы зала"""

        # 1. Авторизация как кассир
        login_response = client.post("/api/login", json={
            "username": "cashier1",
            "password": "cash123"
        })
        assert login_response.status_code == 200
        assert login_response.json()["success"] == True
        print("  1️⃣ Авторизация кассира - OK")

        # 2. Получение списка сеансов
        sessions_response = client.get("/api/sessions")
        assert sessions_response.status_code == 200
        sessions = sessions_response.json()
        assert len(sessions) > 0
        print("  2️⃣ Получение списка сеансов - OK")

        # 3. Получение схемы зала для первого сеанса
        first_session = sessions[0]
        hall_id = first_session.get("hall_id", 1)
        seats_response = client.get(f"/api/seats/{hall_id}")
        assert seats_response.status_code == 200
        seats = seats_response.json()
        assert len(seats) > 0
        print("  3️⃣ Получение схемы зала - OK")

        # 4. Проверка типов мест (должны быть Стандарт, VIP, Премиум)
        seat_types = set([seat.get("type") for seat in seats])
        assert "Стандарт" in seat_types or "standard" in str(seat_types).lower()
        print("  4️⃣ Проверка типов мест - OK")

        print("\n✅ Функциональный тест пройден: Сценарий работы кассира выполнен")


# =====================================================
# ЗАПУСК ВСЕХ ТЕСТОВ
# =====================================================

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("ЗАПУСК ТЕСТИРОВАНИЯ СИСТЕМЫ WebCinema")
    print("=" * 60 + "\n")

    # Создаем экземпляры тестов
    test_movies = TestModuleMovies()
    test_tickets = TestModuleTickets()
    test_integration = TestIntegration()
    test_functional = TestFunctional()

    # Запускаем модульные тесты
    print("--- МОДУЛЬНОЕ ТЕСТИРОВАНИЕ ---")
    tests_passed = 0
    tests_failed = 0

    try:
        test_movies.test_get_movies_positive()
        tests_passed += 1
    except AssertionError as e:
        tests_failed += 1
        print(f"❌ Ошибка: {e}")

    try:
        test_movies.test_get_sessions_positive()
        tests_passed += 1
    except AssertionError as e:
        tests_failed += 1
        print(f"❌ Ошибка: {e}")

    try:
        test_movies.test_get_session_not_found_negative()
        tests_passed += 1
    except AssertionError as e:
        tests_failed += 1
        print(f"❌ Ошибка: {e}")

    try:
        test_movies.test_get_seats_wrong_hall_negative()
        tests_passed += 1
    except AssertionError as e:
        tests_failed += 1
        print(f"❌ Ошибка: {e}")

    try:
        test_tickets.test_login_admin_positive()
        tests_passed += 1
    except AssertionError as e:
        tests_failed += 1
        print(f"❌ Ошибка: {e}")

    try:
        test_tickets.test_login_cashier_positive()
        tests_passed += 1
    except AssertionError as e:
        tests_failed += 1
        print(f"❌ Ошибка: {e}")

    try:
        test_tickets.test_login_wrong_password_negative()
        tests_passed += 1
    except AssertionError as e:
        tests_failed += 1
        print(f"❌ Ошибка: {e}")

    try:
        test_tickets.test_login_wrong_username_negative()
        tests_passed += 1
    except AssertionError as e:
        tests_failed += 1
        print(f"❌ Ошибка: {e}")

    print(f"\n📊 Модульные тесты: {tests_passed} пройдено, {tests_failed} не пройдено")

    print("\n--- ИНТЕГРАЦИОННОЕ ТЕСТИРОВАНИЕ ---")
    try:
        test_integration.test_integration_session_and_seats()
        print("✅ Интеграционный тест пройден")
    except AssertionError as e:
        print(f"❌ Ошибка: {e}")

    print("\n--- ФУНКЦИОНАЛЬНОЕ ТЕСТИРОВАНИЕ ---")
    try:
        test_functional.test_functional_full_workflow()
        print("✅ Функциональный тест пройден")
    except AssertionError as e:
        print(f"❌ Ошибка: {e}")

    print("\n" + "=" * 60)
    print("ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
    print("=" * 60)