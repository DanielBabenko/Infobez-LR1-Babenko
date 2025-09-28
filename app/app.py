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
from models import *
from jwt_authentification import *
from config import *

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

@app.route('/tasks', methods=['GET'])
@token_required
def get_tasks(current_user):
    tasks = Task.query.all()
    return jsonify({'tasks': list(map(make_public_task, tasks))})

@app.route('/tasks/<int:task_id>', methods=['GET'])
def get_task(task_id):
    task = Task.query.get(task_id)
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

    user = User.query.filter_by(username=username).first()

    if user and user.check_password(password):
        access_token = generate_access_token(user)
        refresh_token = generate_refresh_token(user)
        return jsonify({'access_token': access_token, 'refresh_token': refresh_token}), 200
    else:
        return jsonify({'error': 'Invalid credentials'}), 401

# Регистрация
@app.route('/auth/register', methods=['POST'])
def register():
    if not request.json or not 'username' in request.json or not 'password' in request.json:
        abort(400)

    username = request.json['username']
    password = request.json['password']

    if User.query.filter_by(username=username).first():
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
