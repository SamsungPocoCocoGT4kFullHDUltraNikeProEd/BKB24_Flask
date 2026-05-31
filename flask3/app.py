from flask import Flask, render_template, request, redirect, url_for, flash, session
from forms import LoginForm, RegisterForm
from utils import (
    find_user_by_username, check_password, create_user,
    update_last_access, load_users, is_bad_password
)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here-change-it'


@app.route('/')
def index():
    """Главная страница"""
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Страница входа"""
    if 'username' in session:
        return redirect(url_for('dashboard'))

    form = LoginForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        user = find_user_by_username(username)

        if user and check_password(user['password_hash'], password):
            session['username'] = username
            session['user_id'] = user['id']
            update_last_access(username)
            flash(f'Добро пожаловать, {username}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Неверное имя пользователя или пароль', 'danger')

    return render_template('login.html', form=form)


@app.route('/dashboard')
def dashboard():
    """Панель администратора (список пользователей)"""
    if 'username' not in session:
        flash('Пожалуйста, войдите в систему', 'warning')
        return redirect(url_for('login'))

    users = load_users()
    current_user = session['username']

    return render_template('dashboard.html', users=users, current_user=current_user)


@app.route('/register', methods=['GET', 'POST'])
def register():
    """Страница регистрации новых пользователей (только для админа)"""
    if 'username' not in session:
        flash('Пожалуйста, войдите в систему', 'warning')
        return redirect(url_for('login'))

    # ПРОВЕРКА: является ли текущий пользователь администратором
    current_user_data = find_user_by_username(session['username'])
    if not current_user_data or not current_user_data.get('is_admin', False):
        flash('Доступ запрещён. Только администратор может создавать пользователей.', 'danger')
        return redirect(url_for('dashboard'))

    form = RegisterForm()

    if form.validate_on_submit():
        success, result = create_user(
            username=form.username.data,
            password=form.password.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            email=form.email.data,
            is_admin=False
        )

        if success:
            flash(f'Пользователь {form.username.data} успешно создан!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash(result, 'danger')

    return render_template('register.html', form=form)

@app.route('/logout')
def logout():
    """Выход из системы"""
    session.clear()
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)