# Import necessary modules from Flask and other libraries
from flask import Flask  # Flask is a micro web framework used to create web applications
from flask_sqlalchemy import SQLAlchemy  # SQLAlchemy is used to manage database operations in Flask
from flask_bcrypt import Bcrypt  # Bcrypt is used for hashing passwords for security
from flask_login import LoginManager  # LoginManager manages user session and login
from config import Config  # Importing configuration settings
import os  # Used for file and directory operations

# Initialize SQLAlchemy instance for database operations
db = SQLAlchemy()

# Initialize Bcrypt instance for password hashing
bcrypt = Bcrypt()

# Initialize LoginManager instance for handling user login
login_manager = LoginManager()

# Function to create the Flask application instance
def create_app():
    # Create an instance of the Flask application
    app = Flask(__name__)

    # Configure the application with settings from the Config class
    app.config.from_object(Config)

    # Create the instance folder if it does not exist
    # The instance folder is used to store configuration files or other application data
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
    from app.user_routes import user, add_icons_to_achievements  # User-related routes and functionality
    from app.admin_routes import admin  # Admin-related routes and functionality

    # Register the user blueprint with the application
    app.register_blueprint(user)

    # Register the admin blueprint with a URL prefix of '/admin'
    app.register_blueprint(admin, url_prefix='/admin')

    # Add icons to achievements within the application context
    # This function is called during the application setup to ensure achievements have their icons assigned
    with app.app_context():
        add_icons_to_achievements(app)

    # Return the created application instance
    return app

# User loader function for Flask-Login
# This function is used to reload the user object from the user ID stored in the session
@login_manager.user_loader
def load_user(user_id):
    from app.models import User  # Import the User model to access the user information
    return User.query.get(int(user_id))  # Query the database to get the user with the given user ID
