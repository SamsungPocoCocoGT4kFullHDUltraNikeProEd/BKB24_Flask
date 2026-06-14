from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
from wtforms import StringField, TextAreaField, BooleanField, SelectField, SelectMultipleField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError

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

# Форма для импорта дампа
class ImportForm(FlaskForm):
    file = FileField('JSON файл с дампом', validators=[
        FileRequired(message='Выберите файл для импорта')
    ])
    overwrite = BooleanField('Перезаписывать существующие посты с тем же ID')
    create_missing = BooleanField('Создавать недостающие категории, теги и авторов', default=True)
    submit = SubmitField('Импортировать')