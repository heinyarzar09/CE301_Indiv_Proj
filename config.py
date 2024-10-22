# Import the 'os' module to interact with the operating system
import os

# Define the base directory of the project
# 'basedir' represents the absolute path of the directory where this script is located
basedir = os.path.abspath(os.path.dirname(__file__))

# Define the Config class to store configuration settings for the Flask application
class Config:
    # Secret key used by Flask to provide security for sessions and cookies
    # If 'SECRET_KEY' is set in the environment variables, it will use that value; otherwise, it defaults to a hardcoded value
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a_hard_to_guess_string'

    # URI for the database connection
    # If 'DATABASE_URL' is set in the environment variables, it will use that; otherwise, it defaults to a local SQLite database
    # The database file is located in the 'instance' folder inside the base directory
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'instance', 'database.db')

    # Disable the SQLAlchemy event system to save resources
    # This reduces overhead as it prevents tracking of every change in the database objects, which is not needed here
    SQLALCHEMY_TRACK_MODIFICATIONS = False
