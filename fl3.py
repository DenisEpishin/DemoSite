import flask
from flask import Flask, request, redirect, send_from_directory, flash, url_for
import os
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = \
    'sqlite:///' + os.path.join(basedir, 'data.sqlite')
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SECRET_KEY'] = '3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6'  # Необходимо для работы flash-сообщений
db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    email = db.Column(db.String(100), unique=True)
    password_hash = db.Column(db.String(128))

    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.set_password(password)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@app.context_processor
def inject_user():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        return dict(current_user=user)
    return dict(current_user=None)

@app.route('/')
def index():
    return flask.render_template('index.html')


@app.route('/user/<name>')
def user(name):
    return '<h1>Hello, %s!</h1>' % name


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')

        if not all([username, password, email]):
            flash('Все поля обязательны для заполнения')
            return redirect(url_for('registration'))

        if User.query.filter_by(username=username).first():
            flash('Это имя пользователя уже занято')
            return redirect(url_for('registration'))

        if User.query.filter_by(email=email).first():
            flash('Этот email уже используется')
            return redirect(url_for('registration'))

        try:
            user = User(username=username, email=email, password=password)
            db.session.add(user)
            db.session.commit()
            flash('Регистрация прошла успешно! Теперь вы можете войти.')
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            flash('Произошла ошибка при регистрации')
            return redirect(url_for('registration'))

    return redirect(url_for('registration'))

from flask import session

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        if not user or not user.check_password(password):
            flash('Неверное имя пользователя или пароль')
            return redirect(url_for('login'))

        # Успешный вход
        session['user_id'] = user.id  # Сохраняем ID пользователя в сессии
        flash('Вы успешно вошли в систему!')
        return redirect(url_for('index'))

    return flask.render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)  # Удаляем данные пользователя из сессии
    flash('Вы вышли из системы')
    return redirect(url_for('index'))

from functools import wraps

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Пожалуйста, войдите в систему')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/profile')
@login_required
def profile():
    user = User.query.get(session['user_id'])
    return f"<h1>Профиль: {user.username}</h1>"


@app.route('/catalog')
def catalog():
    return flask.render_template('catalog.html')


@app.route('/registration')
def registration():
    return flask.render_template('reg.html')


@app.route('/static/images/<path:filename>')
def serve_static(filename):
    return send_from_directory(os.path.join(app.root_path, 'static/images'), filename)

@app.context_processor
def inject_user():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        return dict(current_user=user)
    return dict(current_user=None)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Создаем таблицы, если они не существуют
    if not os.path.exists(os.path.join(basedir, 'static/images')):
        os.makedirs(os.path.join(basedir, 'static/images'))
    app.run(debug=True)
