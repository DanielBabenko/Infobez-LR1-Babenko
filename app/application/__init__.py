# app/__init__.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from app.config import Config

db = SQLAlchemy()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)

    # Register blueprints
    from app.application.routes import tasks, auth
    app.register_blueprint(tasks.bp)
    app.register_blueprint(auth.bp)

    return app, db