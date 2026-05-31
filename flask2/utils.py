import os
import json
import hashlib

def load_json(folder_name, file_name):
    """Загружает данные из JSON файла"""
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
    filename = os.path.join(folder_name, file_name)
    if not os.path.exists(filename):
        with open(filename, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=4)
        return []
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(folder_name, file_name, data):
    """Сохраняет данные в JSON файл"""
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
    filename = os.path.join(folder_name, file_name)
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def get_md5(file_path):
    """Вычисляет MD5 хэш файла"""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def get_file_extension(filename):
    """Возвращает расширение файла БЕЗ точки"""
    return os.path.splitext(filename)[1].lower().lstrip('.')