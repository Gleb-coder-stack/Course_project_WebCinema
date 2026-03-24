from database import db

print("=" * 50)
print("ПРОВЕРКА ДАННЫХ В БАЗЕ")
print("=" * 50)

# Проверяем фильмы
movies = db.get_movies()
print(f"\nФильмы в БД: {len(movies)}")
if movies:
    for movie in movies:
        print(f"  - {movie}")
else:
    print("  ❌ Фильмов нет!")

# Проверяем пользователей
users = db.get_users()
print(f"\nПользователи в БД: {len(users)}")
if users:
    for user in users:
        print(f"  - {user}")
else:
    print("  ❌ Пользователей нет!")

# Проверяем сеансы
sessions = db.get_sessions()
print(f"\nСеансы в БД: {len(sessions)}")
if sessions:
    for session in sessions:
        print(f"  - {session}")
else:
    print("  ❌ Сеансов нет!")
