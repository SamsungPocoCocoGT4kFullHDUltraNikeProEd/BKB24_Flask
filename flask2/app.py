from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
import os
import uuid
import datetime
from werkzeug.utils import secure_filename
from forms import UploadForm
from utils import load_json, save_json, get_md5, get_file_extension

app = Flask(__name__)
app.config["SECRET_KEY"] = os.urandom(256)

# Настройки загрузки
UPLOAD_FOLDER = "upload"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB максимум

# Запрещенные расширения (черный список)
FORBIDDEN_EXTENSIONS = {'.exe', '.sh', '.php', '.js', '.bat', '.cmd', '.py', '.pl', '.cgi'}

def is_allowed_file(filename):
    """Проверка разрешенных расширений (белый список из формы)"""
    ext = get_file_extension(filename)  # возвращает .jpg
    # Убираем точку для сравнения
    ext_without_dot = ext.lstrip('.')
    return ext_without_dot in UploadForm.allowed_extensions

def is_forbidden_file(filename):
    """Проверка запрещенных расширений (черный список)"""
    ext = get_file_extension(filename)
    return ext in FORBIDDEN_EXTENSIONS

def is_duplicate(file_path, md5_hash):
    """Проверка, существует ли файл с таким же MD5"""
    files_data = load_json("data", "files.json")
    for file_info in files_data:
        if file_info.get("md5") == md5_hash:
            return True
    return False

def generate_uuid_path(original_filename):
    """Генерирует путь вида upload/ab/cd/ab_cd_uuid.ext"""
    file_uuid = str(uuid.uuid4()).replace("-", "")
    ext = get_file_extension(original_filename)
    
    # Берем первые 2 и следующие 2 символа UUID для создания подпапок
    part1 = file_uuid[:2]
    part2 = file_uuid[2:4]
    
    # Создаем вложенные папки
    upload_dir = app.config["UPLOAD_FOLDER"]
    subdir = os.path.join(upload_dir, part1, part2)
    os.makedirs(subdir, exist_ok=True)
    
    # Итоговое имя файла: UUID.расширение (С ТОЧКОЙ!)
    new_filename = f"{file_uuid}.{ext}"
    file_path = os.path.join(subdir, new_filename)
    
    # Относительный путь для отображения
    relative_path = os.path.join(part1, part2, new_filename).replace("\\", "/")
    
    return relative_path, file_path

@app.route("/", methods=["GET", "POST"])
def index():
    form = UploadForm()
    
    # Загружаем список файлов
    files_data = load_json("data", "files.json")
    
    if request.method == "POST" and form.validate_on_submit():
        file = form.file.data
        
        if file and file.filename:
            original_filename = secure_filename(file.filename)
            
            # Проверка 1: запрещенные расширения
            if is_forbidden_file(original_filename):
                flash(f"Загрузка файлов типа {get_file_extension(original_filename)} запрещена!", "error")
                return redirect(url_for("index"))
            
            # Проверка 2: разрешенные расширения
            if not is_allowed_file(original_filename):
                flash(f"Тип файла {get_file_extension(original_filename)} не поддерживается. Разрешены: {', '.join(UploadForm.allowed_extensions)}", "error")
                return redirect(url_for("index"))
            
            # Сохраняем временно для вычисления MD5
            temp_path = os.path.join(app.config["UPLOAD_FOLDER"], "_temp_" + original_filename)
            os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
            file.save(temp_path)
            
            # Вычисляем MD5
            md5_hash = get_md5(temp_path)
            
            # Проверка 3: дубликат
            if is_duplicate(temp_path, md5_hash):
                os.remove(temp_path)
                flash("Файл с таким содержимым уже существует (дубликат)!", "error")
                return redirect(url_for("index"))
            
            # Генерируем путь для сохранения
            relative_path, final_path = generate_uuid_path(original_filename)
            
            # Перемещаем файл
            os.rename(temp_path, final_path)
            
            # Сохраняем информацию о файле
            new_file_info = {
                "id": str(uuid.uuid4()),
                "original_name": original_filename,
                "uuid_name": os.path.basename(final_path),
                "path": f"upload/{relative_path}",
                "extension": get_file_extension(original_filename),
                "md5": md5_hash,
                "size": os.path.getsize(final_path),
                "upload_date": datetime.datetime.now().isoformat()
            }
            
            files_data.append(new_file_info)
            save_json("data", "files.json", files_data)
            
            flash(f"Файл '{original_filename}' успешно загружен!", "success")
            return redirect(url_for("index"))
    
    return render_template("index.html", form=form, files=files_data)
@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory('upload', filename)

if __name__ == "__main__":
    app.run(debug=True)