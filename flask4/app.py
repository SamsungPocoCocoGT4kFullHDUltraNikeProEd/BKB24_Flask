from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, current_user
from flask_wtf.csrf import CSRFProtect
from datetime import datetime
from sqlalchemy import func

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


def get_filtered_posts_query(category_id=None, tag_id=None, author_id=None):
    """Возвращает базовый запрос с учетом фильтров и прав доступа"""
    query = Post.query

    # Применяем фильтры
    if category_id:
        query = query.filter_by(category_id=category_id)
    if tag_id:
        query = query.join(post_tags).filter(post_tags.c.tag_id == tag_id)
    if author_id:
        query = query.filter_by(author_id=author_id)

    # Анонимным пользователям скрываем приватные посты
    if not current_user.is_authenticated:
        query = query.filter_by(is_private=False)
    else:
        # Для авторизованных - показываем их приватные посты и все публичные
        query = query.filter(
            (Post.is_private == False) | (Post.author_id == current_user.id)
        )

    return query


def get_facet_counts(category_id=None, tag_id=None, author_id=None):
    """Получает актуальные количества для фасетных фильтров"""

    # Базовый запрос без текущего фильтра по категории (для подсчета категорий)
    base_query_for_cats = get_filtered_posts_query(tag_id=tag_id, author_id=author_id)

    # Подсчет постов в каждой категории
    category_counts = db.session.query(
        Category.id,
        Category.name,
        func.count(Post.id).label('count')
    ).outerjoin(
        Post,
        (Category.id == Post.category_id) &
        (Post.id.in_(base_query_for_cats.with_entities(Post.id)))
    ).group_by(Category.id).all()

    # Базовый запрос без текущего фильтра по тегу (для подсчета тегов)
    base_query_for_tags = get_filtered_posts_query(category_id=category_id, author_id=author_id)

    # Подсчет постов с каждым тегом
    tag_counts = db.session.query(
        Tag.id,
        Tag.name,
        func.count(Post.id).label('count')
    ).outerjoin(
        post_tags, Tag.id == post_tags.c.tag_id
    ).outerjoin(
        Post,
        (post_tags.c.post_id == Post.id) &
        (Post.id.in_(base_query_for_tags.with_entities(Post.id)))
    ).group_by(Tag.id).all()

    # Базовый запрос без текущего фильтра по автору (для подсчета авторов)
    base_query_for_authors = get_filtered_posts_query(category_id=category_id, tag_id=tag_id)

    # Подсчет постов каждого автора
    author_counts = db.session.query(
        User.id,
        User.username,
        func.count(Post.id).label('count')
    ).outerjoin(
        Post,
        (User.id == Post.author_id) &
        (Post.id.in_(base_query_for_authors.with_entities(Post.id)))
    ).group_by(User.id).all()

    return {
        'categories': category_counts,
        'tags': tag_counts,
        'authors': author_counts
    }


# Главная страница
@app.route('/')
@app.route('/page/<int:page>')
def index():
    page = request.args.get('page', 1, type=int)
    category_id = request.args.get('category', type=int)
    tag_id = request.args.get('tag', type=int)
    author_id = request.args.get('author', type=int)

    # Получаем посты с учетом фильтров
    query = get_filtered_posts_query(category_id, tag_id, author_id)
    posts = query.order_by(Post.created_at.desc()).paginate(page=page, per_page=5)

    # Получаем актуальные количества для фасетных фильтров
    facet_counts = get_facet_counts(category_id, tag_id, author_id)

    # Общее количество постов
    total_posts = query.count()

    return render_template('index.html',
                           posts=posts,
                           total_posts=total_posts,
                           facet_counts=facet_counts,
                           selected_category=category_id,
                           selected_tag=tag_id,
                           selected_author=author_id)


# Страница поста
@app.route('/post/<int:post_id>')
def post_detail(post_id):
    post = Post.query.get_or_404(post_id)

    # Проверка приватности
    if post.is_private and not current_user.is_authenticated:
        flash('Этот пост приватный. Пожалуйста, авторизуйтесь', 'warning')
        return redirect(url_for('auth.login'))

    if post.is_private and current_user.is_authenticated and post.author_id != current_user.id and not current_user.is_admin:
        flash('У вас нет доступа к этому посту', 'danger')
        return redirect(url_for('index'))

    return render_template('post_detail.html', post=post)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()

        # Создаем тестового админа, если нет пользователей
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