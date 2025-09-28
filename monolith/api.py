#!flask/bin/python
import pytz
from cffi.backend_ctypes import unicode
from flask import Flask, jsonify, abort, make_response, request, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
import bleach
import os
import jwt
import datetime
from functools import wraps

app = Flask(__name__)

app.config['SECRET_KEY'] = 'YuraRuina'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = datetime.timedelta(minutes=15)
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = datetime.timedelta(days=30)

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- Модели БД ---

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return '<User %r>' % self.username


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200))
    done = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return '<Task %r>' % self.title

############################################
@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)

def make_public_task(task):
    new_task = {}
    for field in task.__dict__:
        if field == 'id':
            new_task['uri'] = url_for('get_task', task_id=task.id, _external=True)
        elif not field.startswith('_'):
            value = getattr(task, field)
            if isinstance(value, str):
                new_task[field] = bleach.clean(value)
            else:
                new_task[field] = value
    return new_task

# --- Аутентификация с JWT ---

def generate_access_token(user):
    payload = {
        'user_id': user.id,
        'exp': datetime.datetime.now(pytz.timezone('Europe/Moscow')) + app.config['JWT_ACCESS_TOKEN_EXPIRES'],
        'type': 'access'
    }

    token = jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')
    return token

def generate_refresh_token(user):
    payload = {
        'user_id': user.id,
        'exp': datetime.datetime.now(pytz.timezone('Europe/Moscow')) + app.config['JWT_REFRESH_TOKEN_EXPIRES'],
        'type': 'refresh'
    }
    token = jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')
    return token

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(" ")[1]

        if not token:
            return jsonify({'message': 'Access token is missing!'}), 401

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            if data['type'] != 'access': # Ensure it's an access token
                return jsonify({'message': 'Invalid token type!'}), 401
            print(data['exp'])
            print(datetime.datetime.now(pytz.timezone('Europe/Moscow')).timestamp())
            current_user = User.query.get(data['user_id'])
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Access token has expired!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Access token is invalid!'}), 401
        except Exception as e:
            print(f"Token verification error: {e}") # Log the exception
            return jsonify({'message': 'Something went wrong with token verification!'}), 500

        return f(current_user, *args, **kwargs)

    return decorated

###################################################

@app.route('/tasks', methods=['GET'])
@token_required
def get_tasks(current_user):
    tasks = Task.query.all()  # Получаем все задачи из БД
    return jsonify({'tasks': list(map(make_public_task, tasks))})

@app.route('/tasks/<int:task_id>', methods=['GET'])
def get_task(task_id):
    task = Task.query.get(task_id) #Task.query.filter_by(id=task_id).first()
    if task is None:
        abort(404)
    return jsonify({'task': make_public_task(task)})

@app.route('/tasks', methods=['POST'])
@token_required
def create_task(current_user):
    if not request.json or not 'title' in request.json:
        abort(400)

    task = Task(title=request.json['title'], description=request.json.get('description', ""))
    db.session.add(task)
    db.session.commit()
    return jsonify({'task': make_public_task(task)}), 201

@app.route('/tasks/<int:task_id>', methods=['PUT'])
@token_required
def update_task(current_user, task_id):
    task = Task.query.get(task_id)
    if task is None:
        abort(404)

    if not request.json:
        abort(400)

    if 'title' in request.json and type(request.json['title']) != unicode:
        abort(400)
    if 'description' in request.json and type(request.json['description']) is not unicode:
        abort(400)
    if 'done' in request.json and type(request.json['done']) is not bool:
        abort(400)

    task.title = request.json.get('title', task.title)
    task.description = request.json.get('description', task.description)
    task.done = request.json.get('done', task.done)
    db.session.commit()
    return jsonify({'task': make_public_task(task)})

@app.route('/tasks/<int:task_id>', methods=['DELETE'])
@token_required
def delete_task(current_user, task_id):
    task = Task.query.get(task_id)
    if task is None:
        abort(404)
    db.session.delete(task)
    db.session.commit()
    return jsonify({'result': True})

# Аутентификация
@app.route('/auth/login', methods=['POST'])
def login():
    if not request.json or not 'username' in request.json or not 'password' in request.json:
        abort(400)

    username = request.json['username']
    password = request.json['password']

    user = User.query.filter_by(username=username).first()  # Ищем пользователя в БД

    if user and user.check_password(password):
        access_token = generate_access_token(user)
        refresh_token = generate_refresh_token(user)
        return jsonify({'access_token': access_token, 'refresh_token': refresh_token}), 200
    else:
        return jsonify({'error': 'Invalid credentials'}), 401

# Обновить токен
@app.route('/auth/refresh', methods=['POST'])
def refresh():
    if not request.json or not 'refresh_token' in request.json:
        return jsonify({'message': 'Refresh token is missing!'}), 400

    refresh_token = request.json['refresh_token']

    try:
        data = jwt.decode(refresh_token, app.config['SECRET_KEY'], algorithms=['HS256'])
        if data['type'] != 'refresh':
            return jsonify({'message': 'Invalid token type!'}), 400
        user = User.query.get(data['user_id'])
        if not user:
            return jsonify({'message': 'Invalid user!'}), 400

        access_token = generate_access_token(user)
        return jsonify({'access_token': access_token}), 200

    except jwt.ExpiredSignatureError:
        return jsonify({'message': 'Refresh token has expired!'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'message': 'Refresh token is invalid!'}), 401
    except Exception as e:
        print(f"Refresh token verification error: {e}")
        return jsonify({'message': 'Something went wrong with refresh token verification!'}), 500

# Регистрация
@app.route('/auth/register', methods=['POST'])
def register():
    if not request.json or not 'username' in request.json or not 'password' in request.json:
        abort(400)

    username = request.json['username']
    password = request.json['password']

    if User.query.filter_by(username=username).first(): # Проверяем, существует ли пользователь
        return jsonify({'error': 'Username already exists'}), 400

    user = User(username=username)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return jsonify({'message': 'User registered successfully'}), 201

#
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
