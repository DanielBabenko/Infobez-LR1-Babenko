# app/utils.py
import jwt
import datetime
from functools import wraps

import pytz
from flask import request, jsonify, current_app
from app.application.models import User

def generate_access_token(user):
    payload = {
        'user_id': user.id,
        'exp': datetime.datetime.now(pytz.timezone('Europe/Moscow')) + current_app.config['JWT_ACCESS_TOKEN_EXPIRES'],
        'type': 'access'
    }

    token = jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')
    return token

def generate_refresh_token(user):
    payload = {
        'user_id': user.id,
        'exp': datetime.datetime.now(pytz.timezone('Europe/Moscow')) + current_app.config['JWT_REFRESH_TOKEN_EXPIRES'],
        'type': 'refresh'
    }
    token = jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')
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
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
            if data['type'] != 'access':
                return jsonify({'message': 'Invalid token type!'}), 401
            current_user = User.query.get(data['user_id'])
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Access token has expired!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Access token is invalid!'}), 401
        except Exception as e:
            print(f"Token verification error: {e}")
            return jsonify({'message': 'Something went wrong with token verification!'}), 500

        return f(current_user, *args, **kwargs)

    return decorated