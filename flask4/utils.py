import json
from werkzeug.security import generate_password_hash, check_password_hash


def load_users(filename):
    """Загружает пользователей из JSON файла"""
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_user(filename, user_data):
    """Сохраняет нового пользователя в JSON файл"""
    users = load_users(filename)

    # В реальном проекте хэшируйте пароль!
    # user_data['password'] = generate_password_hash(user_data['password'])

    users.append(user_data)
    with open(filename, 'w', encoding='utf-8') as file:
        json.dump(users, file, indent=4, ensure_ascii=False)
    return True


def find_user(users, id=None, email=None):
    """Находит пользователя по ID или email"""
    for user in users:
        if id and user['id'] == id:
            return user
        if email and user['email'] == email:
            return user
    return None


def generate_user_id(users):
    """Генерирует новый ID для пользователя"""
    if not users:
        return 1
    return max(user['id'] for user in users) + 1