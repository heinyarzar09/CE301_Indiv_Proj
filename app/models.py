# Import necessary modules for creating database models
from flask_login import UserMixin  # Provides default implementations for user authentication (like is_authenticated)
from datetime import datetime, timezone
from app import db  # Importing the SQLAlchemy instance for database interactions

# Define the User model that extends from SQLAlchemy's Model and Flask-Login's UserMixin
class User(db.Model, UserMixin):
    # Define columns for the User table
    id = db.Column(db.Integer, primary_key=True)  # Unique ID for each user (primary key)
    username = db.Column(db.String(20), unique=True, nullable=False)  # Username (must be unique)
    email = db.Column(db.String(120), unique=True, nullable=False)  # Email (must be unique)
    password = db.Column(db.String(60), nullable=False)  # Password (hashed for security)
    role = db.Column(db.String(10), nullable=False, default='user')  # User role (default: user)

    # Tracking user activity metrics
    completed_recipes = db.Column(db.Integer, default=0)  # Number of recipes the user has completed
    recipes_created = db.Column(db.Integer, default=0)  # Number of recipes the user has created
    recipes_shared = db.Column(db.Integer, default=0)  # Number of recipes the user has shared
    friends_connected = db.Column(db.Integer, default=0)  # Number of friends connected
    shopping_lists_created = db.Column(db.Integer, default=0)  # Number of shopping lists created
    conversion_tool_uses = db.Column(db.Integer, default=0)  # Number of times the conversion tool was used

    posts = db.relationship('Post', backref='author', cascade="all, delete-orphan", lazy=True)
    # Relationship to the Tool model
    tools = db.relationship('Tool', backref='owner', lazy=True, cascade="all, delete-orphan")
    # 'backref' provides access to the 'owner' attribute from the Tool model
    # 'lazy=True' means that related objects are loaded when they are accessed
    # 'cascade="all, delete-orphan"' ensures that tools are deleted if the user is deleted

# Define the Tool model which stores information about users' tools
class Tool(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)  # Unique ID for each tool
    name = db.Column(db.String(100), nullable=False)  # Tool name
    unit = db.Column(db.String(50), nullable=False)  # Unit of measurement for the tool
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Foreign key linking tool to its owner

# Define the Achievement model that stores information about different achievements available in the system
class Achievement(db.Model):
    __tablename__ = 'achievements'  # Custom table name
    id = db.Column(db.Integer, primary_key=True)  # Unique ID for each achievement
    name = db.Column(db.String(100), nullable=False)  # Name of the achievement
    description = db.Column(db.String(200), nullable=False)  # Description of the achievement
    criteria = db.Column(db.String(200), nullable=False)  # Criteria for earning the achievement
    icon_url = db.Column(db.String(255), nullable=True)  # URL to the icon representing the achievement

# Define the UserAchievement model to track which users have earned which achievements
class UserAchievement(db.Model):
    __tablename__ = 'user_achievements'  # Custom table name
    id = db.Column(db.Integer, primary_key=True)  # Unique ID for each user achievement record
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Foreign key linking to the User
    achievement_id = db.Column(db.Integer, db.ForeignKey('achievements.id'), nullable=False)  # Foreign key linking to the Achievement
    date_achieved = db.Column(db.Date, default=datetime.now(timezone.utc))  # Date when the achievement was earned (default: current time)
    
    # Relationship to the Achievement model
    achievement = db.relationship('Achievement', backref='user_achievements', lazy=True)
    # 'backref' provides access to the 'user_achievements' attribute from the Achievement model


from app import db
from datetime import datetime, timezone

# Define the Post model to store users' shared posts, such as recipe posts with images and messages
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # Unique ID for each post
    image_file = db.Column(db.String(100), nullable=False)  # Path to the image associated with the post
    message = db.Column(db.Text, nullable=False)  # Message associated with the post
    date_posted = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())  # Date when the post was created
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Foreign key linking the post to the user


# Define the Friendship model to represent the relationship between users (user friendships)
class Friendship(db.Model):
    __tablename__ = 'friendship'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    friend_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')
    date_created = db.Column(db.DateTime, default=db.func.current_timestamp())  # Date when the friendship was created
    
    # Add fields for block/unfollow functionality
    is_blocked = db.Column(db.Boolean, default=False)  # To track if a user has blocked the other
    is_unfollowed = db.Column(db.Boolean, default=False)  # To track if the user has unfollowed the other
    
    # Relationships to the User model for both users involved in the friendship
    user = db.relationship('User', foreign_keys=[user_id], backref='friendships')
    friend = db.relationship('User', foreign_keys=[friend_id], backref='friends')
    # 'foreign_keys' specifies which foreign key is used for each relationship
    # 'backref' provides convenient access to friendship records and friends from the User model


