from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from config import Config
import os

# Initialize SQLAlchemy instance for database operations
db = SQLAlchemy()

# Initialize Bcrypt instance for password hashing
bcrypt = Bcrypt()

# Initialize LoginManager instance for handling user login
login_manager = LoginManager()

def create_app():
    # Create an instance of the Flask application
    app = Flask(__name__)

    # Configure the application with settings from the Config class
    app.config.from_object(Config)

    # Create the instance folder if it does not exist
    os.makedirs(app.instance_path, exist_ok=True)

    # Initialize the database with the application instance
    db.init_app(app)

    # Initialize the Bcrypt instance with the application for password hashing
    bcrypt.init_app(app)

    # Initialize the LoginManager instance with the application to manage user sessions
    login_manager.init_app(app)

    # Set the login view to 'user.login', which is the route that users will be redirected to if they need to log in
    login_manager.login_view = 'user.login'

    # Set the message category for flash messages when users are redirected to the login page
    login_manager.login_message_category = 'info'

    # Import user and admin blueprints from the respective modules
    from app.user_routes import user  # User-related routes and functionality
    from app.admin_routes import admin  # Admin-related routes and functionality

    # Register the user blueprint with the application
    app.register_blueprint(user)

    # Register the admin blueprint with a URL prefix of '/admin'
    app.register_blueprint(admin, url_prefix='/admin')

    # Return the created application instance
    return app

# User loader function for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    from app.models import User
    return User.query.get(int(user_id))
