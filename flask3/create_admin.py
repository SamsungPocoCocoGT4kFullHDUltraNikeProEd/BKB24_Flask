from utils import create_user

# Создаём первого пользователя (администратора)
success, result = create_user(
    username="admin",
    password="admin123",
    first_name="Admin",
    last_name="Adminov",
    email="admin@example.com"
)

if success:
    print(f"✅ Пользователь создан: {result}")
    print("Можете войти с username: admin, password: admin123")
else:
    print(f"❌ Ошибка: {result}")