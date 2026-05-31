from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

# Создаем объект для работы с БД
db = SQLAlchemy()

# Таблица для связи постов и тегов (многие ко многим)
post_tags = db.Table('post_tags',
                     db.Column('post_id', db.Integer, db.ForeignKey('post.id'), primary_key=True),
                     db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True)
                     )


# Модель пользователя
class User(UserMixin, db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Связь с постами (один пользователь - много постов)
    posts = db.relationship('Post', backref='author', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<User {self.username}>'

    def get_post_count(self):
        """Количество постов пользователя"""
        return self.posts.count()

    def is_authenticated(self):
        """Переопределение для Flask-Login"""
        return True

    def is_active(self):
        """Переопределение для Flask-Login"""
        return True

    def is_anonymous(self):
        """Переопределение для Flask-Login"""
        return False


# Модель категории
class Category(db.Model):
    __tablename__ = 'category'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Связь с постами (одна категория - много постов)
    posts = db.relationship('Post', backref='category', lazy=True)

    def __repr__(self):
        return f'<Category {self.name}>'

    def get_post_count(self):
        """Количество постов в категории"""
        return self.posts.count()


# Модель тега
class Tag(db.Model):
    __tablename__ = 'tag'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Связь с постами (через вспомогательную таблицу)
    posts = db.relationship('Post', secondary=post_tags, backref='tags', lazy='dynamic')

    def __repr__(self):
        return f'<Tag {self.name}>'

    def get_post_count(self):
        """Количество постов с этим тегом"""
        return self.posts.count()


# Модель поста
class Post(db.Model):
    __tablename__ = 'post'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_private = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Внешние ключи
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)

    def __repr__(self):
        return f'<Post {self.title}>'

    def get_preview(self, length=300):
        """Возвращает превью поста (первые N символов)"""
        if len(self.content) > length:
            return self.content[:length] + '...'
        return self.content

    def get_tags_list(self):
        """Возвращает список тегов поста"""
        return [tag.name for tag in self.tags]

    def can_edit(self, user):
        """Проверяет, может ли пользователь редактировать пост"""
        if not user or not user.is_authenticated:
            return False
        return user.id == self.author_id or user.is_admin

    def can_delete(self, user):
        """Проверяет, может ли пользователь удалить пост"""
        return self.can_edit(user)

    def is_visible_to(self, user):
        """Проверяет, виден ли пост пользователю"""
        if not self.is_private:
            return True
        if user and user.is_authenticated:
            return user.id == self.author_id or user.is_admin
        return False