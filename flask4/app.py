from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, current_user
from flask_wtf.csrf import CSRFProtect
from datetime import datetime
from sqlalchemy import func, and_

from models import db, User, Post, Category, Tag, post_tags
from auth import auth_bp
from admin import admin_bp
from blog_posts import posts_bp

app = Flask(__name__)
app.config['SECRET_KEY'] = 'секретный-ключ-смените-его-на-случайный-12345'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Инициализация расширений
db.init_app(app)
csrf = CSRFProtect(app)

# Инициализация LoginManager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Пожалуйста, авторизуйтесь для доступа'
login_manager.login_message_category = 'warning'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Регистрация blueprint'ов
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(posts_bp, url_prefix='/posts')


# Контекстный процессор для всех шаблонов
@app.context_processor
def inject_now():
    return {'now': datetime.utcnow()}


def get_filtered_posts(category_id=None, tag_id=None, author_id=None):
    """Получает отфильтрованные посты с учетом прав доступа"""
    query = Post.query

    # Фильтр по категории
    if category_id:
        query = query.filter(Post.category_id == category_id)

    # Фильтр по автору
    if author_id:
        query = query.filter(Post.author_id == author_id)

    # Фильтр по тегу (через JOIN)
    if tag_id:
        query = query.join(post_tags).filter(post_tags.c.tag_id == tag_id)

    # ПРАВИЛЬНАЯ логика приватности:
    # - Неавторизованные (гости): видят ТОЛЬКО публичные посты (is_private=False)
    # - Авторизованные (любой зарегистрированный пользователь): видят ВСЕ посты (и публичные, и приватные)
    if not current_user.is_authenticated:
        query = query.filter(Post.is_private == False)
    else:
        # Авторизованные пользователи видят все посты без ограничений
        # (и свои приватные, и чужие приватные)
        pass  # никаких дополнительных фильтров

    return query


def get_facet_counts(category_id=None, tag_id=None, author_id=None):
    """Получает количества для фасетных фильтров"""

    # Получаем ID всех постов, соответствующих текущим фильтрам
    base_posts = get_filtered_posts(category_id, tag_id, author_id).with_entities(Post.id).subquery()

    # === КАТЕГОРИИ ===
    categories = db.session.query(
        Category.id,
        Category.name,
        func.count(Post.id).label('count')
    ).outerjoin(
        Post, and_(Category.id == Post.category_id, Post.id.in_(base_posts))
    ).group_by(Category.id).order_by(Category.name).all()

    # === ТЕГИ ===
    tags = db.session.query(
        Tag.id,
        Tag.name,
        func.count(Post.id).label('count')
    ).outerjoin(
        post_tags, Tag.id == post_tags.c.tag_id
    ).outerjoin(
        Post, and_(post_tags.c.post_id == Post.id, Post.id.in_(base_posts))
    ).group_by(Tag.id).order_by(Tag.name).all()

    # === АВТОРЫ ===
    authors = db.session.query(
        User.id,
        User.username,
        func.count(Post.id).label('count')
    ).outerjoin(
        Post, and_(User.id == Post.author_id, Post.id.in_(base_posts))
    ).group_by(User.id).order_by(User.username).all()

    return {
        'categories': categories,
        'tags': tags,
        'authors': authors
    }


# Главная страница
@app.route('/')
def index():
    category_id = request.args.get('category', type=int)
    tag_id = request.args.get('tag', type=int)
    author_id = request.args.get('author', type=int)

    # Обработка "Все" значения
    if category_id == 0:
        category_id = None
    if tag_id == 0:
        tag_id = None
    if author_id == 0:
        author_id = None

    # Получаем все отфильтрованные посты
    posts_query = get_filtered_posts(category_id, tag_id, author_id)
    total_posts = posts_query.count()
    posts = posts_query.order_by(Post.created_at.desc()).all()

    # Получаем фасетные счетчики
    facet_counts = get_facet_counts(category_id, tag_id, author_id)

    # Получаем названия для отображения
    selected_category_name = None
    if category_id:
        cat = Category.query.get(category_id)
        selected_category_name = cat.name if cat else None

    selected_tag_name = None
    if tag_id:
        tag = Tag.query.get(tag_id)
        selected_tag_name = tag.name if tag else None

    selected_author_name = None
    if author_id:
        author = User.query.get(author_id)
        selected_author_name = author.username if author else None

    return render_template('index.html',
                           posts=posts,
                           total_posts=total_posts,
                           facet_counts=facet_counts,
                           selected_category=category_id,
                           selected_tag=tag_id,
                           selected_author=author_id,
                           selected_category_name=selected_category_name,
                           selected_tag_name=selected_tag_name,
                           selected_author_name=selected_author_name)


# Страница поста
@app.route('/post/<int:post_id>')
def post_detail(post_id):
    post = Post.query.get_or_404(post_id)

    # Проверка доступа к приватному посту:
    # - Неавторизованные (гости) НЕ видят приватные посты
    # - Авторизованные (любой зарегистрированный) видят все посты
    if post.is_private and not current_user.is_authenticated:
        flash('Этот пост приватный. Пожалуйста, авторизуйтесь для просмотра', 'warning')
        return redirect(url_for('auth.login'))

    return render_template('post_detail.html', post=post)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()

        # Создаем тестового админа
        if User.query.count() == 0:
            from werkzeug.security import generate_password_hash

            admin = User(
                username='admin',
                email='admin@example.com',
                password_hash=generate_password_hash('admin123'),
                is_admin=True
            )
            db.session.add(admin)
            db.session.commit()
            print('✅ Создан тестовый администратор: admin@example.com / admin123')

        # Создаем тестового обычного пользователя
        if User.query.filter_by(username='user').count() == 0:
            from werkzeug.security import generate_password_hash

            user = User(
                username='user',
                email='user@example.com',
                password_hash=generate_password_hash('user123'),
                is_admin=False
            )
            db.session.add(user)
            db.session.commit()
            print('✅ Создан тестовый пользователь: user@example.com / user123')

        # Создаем тестовые категории
        if Category.query.count() == 0:
            categories = ['Новости', 'Статьи', 'Обзоры', 'Учебные материалы']
            for cat_name in categories:
                cat = Category(name=cat_name)
                db.session.add(cat)
            db.session.commit()
            print('✅ Созданы тестовые категории')

        # Создаем тестовые теги
        if Tag.query.count() == 0:
            tags = ['Python', 'Flask', 'Web', 'Базы данных', 'Уроки']
            for tag_name in tags:
                tag = Tag(name=tag_name)
                db.session.add(tag)
            db.session.commit()
            print('✅ Созданы тестовые теги')

    app.run(debug=True)