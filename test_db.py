from database import db

try:
    conn = db.get_connection()
    print("✅ База данных подключена")

    result = db.execute_query("SELECT 1 as test", fetch_one=True)
    print(f"✅ Запрос выполнен: {result}")

    movies = db.get_movies()
    print(f"✅ Фильмов в БД: {len(movies)}")

except Exception as e:
    print(f"❌ Ошибка: {e}")
