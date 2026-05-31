from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
from wtforms import StringField, TextAreaField, BooleanField, SelectField, SelectMultipleField, PasswordField, \
    SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from models import User, Category, Tag


# Форма регистрации
class RegistrationForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[
        DataRequired(message='Имя пользователя обязательно'),
        Length(min=3, max=80, message='Имя должно быть от 3 до 80 символов')
    ])
    email = StringField('Email', validators=[
        DataRequired(message='Email обязателен'),
        Email(message='Введите корректный email')
    ])
    password = PasswordField('Пароль', validators=[
        DataRequired(message='Пароль обязателен'),
        Length(min=6, message='Пароль должен быть не менее 6 символов')
    ])
    confirm_password = PasswordField('Подтвердите пароль', validators=[
        DataRequired(message='Подтвердите пароль'),
        EqualTo('password', message='Пароли не совпадают')
    ])
    submit = SubmitField('Зарегистрироваться')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Это имя пользователя уже занято')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Этот email уже зарегистрирован')


# Форма входа
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[
        DataRequired(message='Email обязателен'),
        Email(message='Введите корректный email')
    ])
    password = PasswordField('Пароль', validators=[
        DataRequired(message='Пароль обязателен')
    ])
    remember = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


# Форма создания/редактирования поста
class PostForm(FlaskForm):
    title = StringField('Заголовок', validators=[
        DataRequired(message='Заголовок обязателен'),
        Length(max=200, message='Заголовок не должен превышать 200 символов')
    ])
    content = TextAreaField('Содержание', validators=[
        DataRequired(message='Содержание обязательно')
    ])
    category = SelectField('Категория', coerce=int, validators=[
        DataRequired(message='Выберите категорию')
    ])
    tags = SelectMultipleField('Теги', coerce=int, validators=[
        DataRequired(message='Выберите хотя бы один тег')
    ])
    is_private = BooleanField('Приватный пост (только для авторизованных)')
    submit = SubmitField('Сохранить')

    def __init__(self, *args, **kwargs):
        super(PostForm, self).__init__(*args, **kwargs)
        # Загружаем категории и теги при инициализации
        if Category.query.count() > 0:
            self.category.choices = [(c.id, c.name) for c in Category.query.all()]
        else:
            self.category.choices = [(0, 'Нет категорий')]

        if Tag.query.count() > 0:
            self.tags.choices = [(t.id, t.name) for t in Tag.query.all()]
        else:
            self.tags.choices = [(0, 'Нет тегов')]


# Форма для создания категории
class CategoryForm(FlaskForm):
    name = StringField('Название категории', validators=[
        DataRequired(message='Название категории обязательно'),
        Length(max=100, message='Название не должно превышать 100 символов')
    ])
    submit = SubmitField('Создать категорию')

    def validate_name(self, name):
        category = Category.query.filter_by(name=name.data).first()
        if category:
            raise ValidationError('Категория с таким названием уже существует')


# Форма для создания тега
class TagForm(FlaskForm):
    name = StringField('Название тега', validators=[
        DataRequired(message='Название тега обязательно'),
        Length(max=100, message='Название не должно превышать 100 символов')
    ])
    submit = SubmitField('Создать тег')

    def validate_name(self, name):
        tag = Tag.query.filter_by(name=name.data).first()
        if tag:
            raise ValidationError('Тег с таким названием уже существует')


# Форма для импорта дампа (ОНА БЫЛА ОТСУТСТВУЕТ)
class ImportForm(FlaskForm):
    file = FileField('JSON файл с дампом', validators=[
        FileRequired(message='Выберите файл для импорта')
    ])
    overwrite = BooleanField('Перезаписывать существующие посты с тем же ID')
    create_missing = BooleanField('Создавать недостающие категории, теги и авторов', default=True)
    submit = SubmitField('Импортировать')


# Форма для поиска постов
class SearchForm(FlaskForm):
    query = StringField('Поиск', validators=[
        DataRequired(message='Введите поисковый запрос')
    ])
    submit = SubmitField('Найти')


# Форма для фильтрации постов
class FilterForm(FlaskForm):
    category = SelectField('Категория', coerce=int, choices=[(0, 'Все категории')])
    tag = SelectField('Тег', coerce=int, choices=[(0, 'Все теги')])
    author = SelectField('Автор', coerce=int, choices=[(0, 'Все авторы')])
    submit = SubmitField('Применить фильтр')

    def __init__(self, *args, **kwargs):
        super(FilterForm, self).__init__(*args, **kwargs)
        # Добавляем категории в выбор
        for cat in Category.query.all():
            self.category.choices.append((cat.id, cat.name))
        # Добавляем теги в выбор
        for tag in Tag.query.all():
            self.tag.choices.append((tag.id, tag.name))
        # Добавляем авторов в выбор
        for user in User.query.all():
            self.author.choices.append((user.id, user.username))


# Форма для изменения профиля
class ProfileForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[
        DataRequired(message='Имя пользователя обязательно'),
        Length(min=3, max=80, message='Имя должно быть от 3 до 80 символов')
    ])
    email = StringField('Email', validators=[
        DataRequired(message='Email обязателен'),
        Email(message='Введите корректный email')
    ])
    current_password = PasswordField('Текущий пароль')
    new_password = PasswordField('Новый пароль', validators=[
        Length(min=6, message='Пароль должен быть не менее 6 символов')
    ])
    confirm_new_password = PasswordField('Подтвердите новый пароль', validators=[
        EqualTo('new_password', message='Пароли не совпадают')
    ])
    submit = SubmitField('Сохранить изменения')