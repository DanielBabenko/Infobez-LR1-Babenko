# app/routes/auth.py
from flask import Blueprint, jsonify, request, current_app
from app.application import db
from app.application.models import User
from app.application.utils import generate_access_token, generate_refresh_token
import jwt
from werkzeug.security import generate_password_hash, check_password_hash

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/register', methods=['POST'])
def register():
    if not request.json or not 'username' in request.json or not 'password' in request.json:
        return jsonify({'error': 'Missing username or password'}), 400

    username = request.json['username']
    password = request.json['password']

    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username already exists'}), 400

    user = User(username=username)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return jsonify({'message': 'User registered successfully'}), 201

@bp.route('/login', methods=['POST'])
def login():
    if not request.json or not 'username' in request.json or not 'password' in request.json:
        return jsonify({'error': 'Missing username or password'}), 400

    username = request.json['username']
    password = request.json['password']

    user = User.query.filter_by(username=username).first()

    if user and user.check_password(password):
        access_token = generate_access_token(user)
        refresh_token = generate_refresh_token(user)
        return jsonify({'access_token': access_token, 'refresh_token': refresh_token}), 200
    else:
        return jsonify({'error': 'Invalid credentials'}), 401

@bp.route('/refresh', methods=['POST'])
def refresh():
    if not request.json or not 'refresh_token' in request.json:
        return jsonify({'message': 'Refresh token is missing!'}), 400

    refresh_token = request.json['refresh_token']

    try:
        data = jwt.decode(refresh_token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
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