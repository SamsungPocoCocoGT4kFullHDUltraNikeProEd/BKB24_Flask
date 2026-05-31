from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError


class LoginForm(FlaskForm):
    """Форма для входа"""
    username = StringField('Имя пользователя', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    submit = SubmitField('Войти')


class RegisterForm(FlaskForm):
    """Форма для регистрации нового пользователя (только для админа)"""
    username = StringField('Имя пользователя', validators=[
        DataRequired(),
        Length(min=3, max=30, message='Имя пользователя должно быть от 3 до 30 символов')
    ])
    password = PasswordField('Пароль', validators=[
        DataRequired(),
        Length(min=6, message='Пароль должен быть не менее 6 символов')
    ])
    confirm_password = PasswordField('Подтвердите пароль', validators=[
        DataRequired(),
        EqualTo('password', message='Пароли не совпадают')
    ])
    first_name = StringField('Имя', validators=[Length(max=50)])
    last_name = StringField('Фамилия', validators=[Length(max=50)])
    email = StringField('Email', validators=[Email(), Length(max=100)])
    submit = SubmitField('Зарегистрировать')

    def validate_username(self, field):
        """Проверка на недопустимые символы в username"""
        if not field.data.isalnum():
            raise ValidationError('Имя пользователя должно содержать только буквы и цифры')