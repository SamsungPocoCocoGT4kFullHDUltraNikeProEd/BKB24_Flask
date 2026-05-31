from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file
from flask_login import login_required, current_user
from datetime import datetime
import json
from io import BytesIO

from models import db, User, Post, Category, Tag
from forms import ImportForm

admin_bp = Blueprint('admin', __name__)


# Декоратор для проверки прав администратора
def admin_required(func):
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Доступ только для администраторов', 'danger')
            return redirect(url_for('index'))
        return func(*args, **kwargs)

    wrapper.__name__ = func.__name__
    return wrapper


# ============ УПРАВЛЕНИЕ КАТЕГОРИЯМИ ============

@admin_bp.route('/categories')
@login_required
@admin_required
def categories():
    """Страница управления категориями"""
    all_categories = Category.query.all()
    return render_template('categories.html', categories=all_categories)


@admin_bp.route('/create_category', methods=['POST'])
@login_required
@admin_required
def create_category():
    """Создание новой категории"""
    name = request.form.get('name')
    if name:
        # Проверка на существующую категорию
        existing = Category.query.filter_by(name=name).first()
        if existing:
            flash(f'Категория "{name}" уже существует', 'warning')
        else:
            category = Category(name=name)
            db.session.add(category)
            db.session.commit()
            flash(f'Категория "{name}" создана', 'success')
    else:
        flash('Название категории не может быть пустым', 'danger')

    return redirect(url_for('admin.categories'))


@admin_bp.route('/delete_category/<int:category_id>')
@login_required
@admin_required
def delete_category(category_id):
    """Удаление категории"""
    category = Category.query.get_or_404(category_id)

    # У постов этой категории устанавливаем category_id = None
    for post in category.posts:
        post.category_id = None

    db.session.delete(category)
    db.session.commit()
    flash('Категория удалена', 'success')
    return redirect(url_for('admin.categories'))


# ============ УПРАВЛЕНИЕ ТЕГАМИ ============

@admin_bp.route('/tags')
@login_required
@admin_required
def tags():
    """Страница управления тегами"""
    all_tags = Tag.query.all()
    return render_template('tags.html', tags=all_tags)


@admin_bp.route('/create_tag', methods=['POST'])
@login_required
@admin_required
def create_tag():
    """Создание нового тега"""
    name = request.form.get('name')
    if name:
        existing = Tag.query.filter_by(name=name).first()
        if existing:
            flash(f'Тег "{name}" уже существует', 'warning')
        else:
            tag = Tag(name=name)
            db.session.add(tag)
            db.session.commit()
            flash(f'Тег "{name}" создан', 'success')
    else:
        flash('Название тега не может быть пустым', 'danger')

    return redirect(url_for('admin.tags'))


@admin_bp.route('/delete_tag/<int:tag_id>')
@login_required
@admin_required
def delete_tag(tag_id):
    """Удаление тега"""
    tag = Tag.query.get_or_404(tag_id)
    db.session.delete(tag)
    db.session.commit()
    flash('Тег удален', 'success')
    return redirect(url_for('admin.tags'))


# ============ УПРАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯМИ ============

@admin_bp.route('/users')
@login_required
@admin_required
def users():
    """Список всех пользователей"""
    all_users = User.query.all()
    return render_template('admin_users.html', users=all_users)


@admin_bp.route('/toggle_admin/<int:user_id>')
@login_required
@admin_required
def toggle_admin(user_id):
    """Переключение прав администратора"""
    user = User.query.get_or_404(user_id)

    # Нельзя изменять права самого себя
    if user.id == current_user.id:
        flash('Нельзя изменять свои права администратора', 'warning')
        return redirect(url_for('admin.users'))

    user.is_admin = not user.is_admin
    db.session.commit()
    status = 'администратором' if user.is_admin else 'обычным пользователем'
    flash(f'Пользователь {user.username} назначен {status}', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/delete_user/<int:user_id>')
@login_required
@admin_required
def delete_user(user_id):
    """Удаление пользователя"""
    user = User.query.get_or_404(user_id)

    if user.id == current_user.id:
        flash('Нельзя удалить самого себя', 'warning')
        return redirect(url_for('admin.users'))

    db.session.delete(user)
    db.session.commit()
    flash(f'Пользователь {user.username} удален', 'success')
    return redirect(url_for('admin.users'))


# ============ ЭКСПОРТ И ИМПОРТ ============

@admin_bp.route('/export')
@login_required
@admin_required
def export_dump():
    """Экспорт всех постов в JSON"""
    posts = Post.query.all()
    data = []

    for post in posts:
        data.append({
            'id': post.id,
            'title': post.title,
            'content': post.content,
            'author': post.author.username,
            'author_id': post.author_id,
            'category': post.category.name if post.category else None,
            'category_id': post.category_id,
            'tags': [tag.name for tag in post.tags],
            'is_private': post.is_private,
            'created_at': post.created_at.isoformat(),
            'updated_at': post.updated_at.isoformat() if post.updated_at else None
        })

    json_data = json.dumps(data, ensure_ascii=False, indent=2)
    output = BytesIO()
    output.write(json_data.encode('utf-8'))
    output.seek(0)

    return send_file(
        output,
        as_attachment=True,
        download_name=f'blog_dump_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json',
        mimetype='application/json'
    )


@admin_bp.route('/import', methods=['GET', 'POST'])
@login_required
@admin_required
def import_dump():
    """Импорт постов из JSON"""
    form = ImportForm()

    if form.validate_on_submit():
        file = form.file.data
        if file:
            try:
                content = file.read().decode('utf-8')
                posts_data = json.loads(content)

                imported_count = 0
                skipped_count = 0

                for post_data in posts_data:
                    existing = Post.query.get(post_data.get('id'))

                    # Пропускаем существующие, если не нужно перезаписывать
                    if existing and not form.overwrite.data:
                        skipped_count += 1
                        continue

                    # Поиск или создание категории
                    category = None
                    if post_data.get('category_id'):
                        category = Category.query.get(post_data['category_id'])
                    if not category and post_data.get('category'):
                        category = Category.query.filter_by(name=post_data['category']).first()
                        if not category and form.create_missing.data:
                            category = Category(name=post_data['category'])
                            db.session.add(category)
                            db.session.commit()

                    # Поиск или создание автора
                    author = None
                    if post_data.get('author_id'):
                        author = User.query.get(post_data['author_id'])
                    if not author and post_data.get('author'):
                        author = User.query.filter_by(username=post_data['author']).first()
                        if not author and form.create_missing.data:
                            # Создаем временного пользователя
                            author = User(
                                username=post_data['author'],
                                email=f"{post_data['author']}@imported.com",
                                password_hash='temporary'
                            )
                            db.session.add(author)
                            db.session.commit()

                    if existing and form.overwrite.data:
                        # Обновляем существующий пост
                        post = existing
                        post.title = post_data['title']
                        post.content = post_data['content']
                        post.category_id = category.id if category else None
                        post.is_private = post_data['is_private']
                        post.updated_at = datetime.utcnow()
                        post.tags = []
                    else:
                        # Создаем новый пост
                        post = Post(
                            title=post_data['title'],
                            content=post_data['content'],
                            author_id=author.id if author else None,
                            category_id=category.id if category else None,
                            is_private=post_data['is_private']
                        )
                        db.session.add(post)
                        db.session.flush()

                    # Добавляем теги
                    for tag_name in post_data.get('tags', []):
                        tag = Tag.query.filter_by(name=tag_name).first()
                        if not tag and form.create_missing.data:
                            tag = Tag(name=tag_name)
                            db.session.add(tag)
                            db.session.commit()
                        if tag and tag not in post.tags:
                            post.tags.append(tag)

                    imported_count += 1

                db.session.commit()

                message = f'Импортировано {imported_count} постов'
                if skipped_count > 0:
                    message += f', пропущено {skipped_count} (существующие)'
                flash(message, 'success')
                return redirect(url_for('index'))

            except json.JSONDecodeError as e:
                flash(f'Ошибка парсинга JSON: {str(e)}', 'danger')
            except Exception as e:
                flash(f'Ошибка при импорте: {str(e)}', 'danger')

    return render_template('dump_import.html', form=form)