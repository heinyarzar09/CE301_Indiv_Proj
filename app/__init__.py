from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from config import Config
import os

db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)
    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'
    login_manager.login_message_category = 'info'

    from app.routes import main
    app.register_blueprint(main)

    return app

@login_manager.user_loader
def load_user(user_id):
    from app.models import User  # Import inside the function to avoid circular import
    return User.query.get(int(user_id))
