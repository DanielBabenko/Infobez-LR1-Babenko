#!flask/bin/python
from cffi.backend_ctypes import unicode
from flask import abort, url_for, make_response
import bleach
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