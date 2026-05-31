import json
import os
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

# Путь к файлу с данными
USERS_FILE = 'users.json'


def load_users():
    """Загружает список пользователей из JSON-файла"""
    if not os.path.exists(USERS_FILE):
        return []
    with open(USERS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_users(users):
    """Сохраняет список пользователей в JSON-файл"""
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=4)


def find_user_by_username(username):
    """Находит пользователя по username"""
    users = load_users()
    for user in users:
        if user['username'] == username:
            return user
    return None


def find_user_by_id(user_id):
    """Находит пользователя по ID"""
    users = load_users()
    for user in users:
        if user['id'] == user_id:
            return user
    return None


def hash_password(password):
    """Хэширует пароль"""
    return generate_password_hash(password)


def check_password(password_hash, password):
    """Проверяет пароль"""
    return check_password_hash(password_hash, password)


def is_bad_password(password):
    """
    Проверяет, является ли пароль "плохим"
    Плохой пароль: меньше 6 символов, только цифры, слишком простой
    """
    if len(password) < 6:
        return True, "Пароль должен содержать минимум 6 символов"

    if password.isdigit():
        return True, "Пароль не может состоять только из цифр"

    if password.lower() in ['password', '123456', 'qwerty', 'admin', 'password123']:
        return True, "Пароль слишком простой"

    return False, None


def get_next_id():
    """Возвращает следующий доступный ID для нового пользователя"""
    users = load_users()
    if not users:
        return 1
    return max(user['id'] for user in users) + 1


def create_user(username, password, first_name='', last_name='', email='', is_admin=False):
    """Создаёт нового пользователя"""
    users = load_users()

    # Проверка на уникальность username
    if find_user_by_username(username):
        return False, "Пользователь с таким именем уже существует"

    # Проверка пароля
    is_bad, message = is_bad_password(password)
    if is_bad:
        return False, message

    # Создаём пользователя
    user = {
        'id': get_next_id(),
        'username': username,
        'first_name': first_name,
        'last_name': last_name,
        'email': email,
        'password_hash': hash_password(password),
        'created': datetime.now().isoformat(),
        'last_access': None,
        'is_admin': is_admin  # Можно сделать админа
    }

    users.append(user)
    save_users(users)
    return True, user


def update_last_access(username):
    """Обновляет дату последней авторизации"""
    users = load_users()
    for user in users:
        if user['username'] == username:
            user['last_access'] = datetime.now().isoformat()
            save_users(users)
            return True
    return False