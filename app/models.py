# Import necessary modules for creating database models
from flask_login import UserMixin  # Provides default implementations for user authentication (like is_authenticated)
from datetime import datetime, timezone, timedelta
from app import db  # Importing the SQLAlchemy instance for database interactions

# Define the User model that extends from SQLAlchemy's Model and Flask-Login's UserMixin
class User(db.Model, UserMixin):
    # Define columns for the User table
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    role = db.Column(db.String(10), nullable=False, default='user')

    # Tracking user activity metrics
    completed_recipes = db.Column(db.Integer, default=0)
    recipes_created = db.Column(db.Integer, default=0)
    recipes_shared = db.Column(db.Integer, default=0)
    friends_connected = db.Column(db.Integer, default=0)
    shopping_lists_created = db.Column(db.Integer, default=0)
    conversion_tool_uses = db.Column(db.Integer, default=0)

    # Credits for creating/joining challenges
    credits = db.Column(db.Integer, default=100)

    # Relationship to tools, posts, and challenges
    tools = db.relationship('Tool', backref='owner', lazy=True, cascade="all, delete-orphan")
    posts = db.relationship('Post', backref='author', lazy=True, cascade="all, delete-orphan")
    
    # Relationship to created challenges
    created_challenges = db.relationship('Challenge', backref='creator', lazy=True, overlaps="challenge_creator,created_challenges")
    
    # Relationship to participated challenges
    participated_challenges = db.relationship('ChallengeParticipant', backref='user_participation', lazy=True, overlaps="participant,challenges_participated")
    
    # New relationship to achievements
    achievements = db.relationship('Achievement', backref='user', lazy=True, cascade="all, delete-orphan")



# Define the Tool model which stores information about users' tools
class Tool(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)  # Unique ID for each tool
    name = db.Column(db.String(100), nullable=False)  # Tool name
    unit = db.Column(db.String(50), nullable=False)  # Unit of measurement for the tool
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Foreign key linking tool to its owner


class Achievement(db.Model):
    __tablename__ = 'achievement'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # ForeignKey to User
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenge.id'), nullable=False)  # ForeignKey to Challenge
    challenge_name = db.Column(db.String(100), nullable=False)
    credits_won = db.Column(db.Integer, nullable=False)
    completion_time = db.Column(db.DateTime, nullable=False)  # Store when the achievement was completed




from app import db
from datetime import datetime, timezone

# Define the Post model to store users' shared posts, such as recipe posts with images and messages
class Post(db.Model):
    __tablename__ = 'post'
    
    id = db.Column(db.Integer, primary_key=True)  # Unique ID for each post
    image_file = db.Column(db.String(100), nullable=False)  # Path to the image associated with the post
    message = db.Column(db.Text, nullable=False)  # Message associated with the post
    date_posted = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())  # Date when the post was created
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Foreign key linking the post to the user who created it
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenge.id'), nullable=True)  # Optional foreign key to link the post to a challenge


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


from datetime import datetime, timedelta

class Challenge(db.Model):
    __tablename__ = 'challenge'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    icon = db.Column(db.String(100))  # Path to the icon
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    credits_required = db.Column(db.Integer, nullable=False)
    duration = db.Column(db.Integer, nullable=False)  # Store duration in seconds
    started_at = db.Column(db.DateTime, nullable=False)  # Track when the challenge starts

    # Relationship to participants
    participants = db.relationship('ChallengeParticipant', backref='challenge_participation', lazy=True, cascade="all, delete-orphan")

    def __init__(self, name, icon, creator_id, credits_required, duration, started_at=None):
        self.name = name
        self.icon = icon
        self.creator_id = creator_id
        self.credits_required = credits_required
        self.duration = duration
        self.started_at = started_at or datetime.utcnow()  # Default to current time if not provided

    @property
    def time_remaining(self):
        # Calculate remaining time by comparing the current time and the end time
        if self.started_at:
            time_passed = (datetime.utcnow() - self.started_at).total_seconds()
            return max(self.duration - time_passed, 0)
        return self.duration

    def get_end_time(self):
        # Calculate the end time based on the start time and duration
        return self.started_at + timedelta(seconds=self.duration)

    def is_active(self):
        # Check if the challenge is still active by comparing current time with end time
        return datetime.utcnow() < self.get_end_time()

    def get_winner(self):
        # Find the participant with the highest progress
        if not self.participants:
            return None
        # Assuming the 'progress' field is the determining factor
        winner = max(self.participants, key=lambda p: p.progress)
        return winner

class ChallengeParticipant(db.Model):
    __tablename__ = 'challenge_participant'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenge.id'), nullable=False)
    wagered_credits = db.Column(db.Integer, nullable=False)
    progress = db.Column(db.Float, default=0)  # Progress for tracking in leaderboard
    date_joined = db.Column(db.DateTime, default=db.func.current_timestamp())
    credited = db.Column(db.Boolean, default=False)
    # Relationship to the user participating in the challenge
    user = db.relationship('User', backref='participations')

    # Relationship to the challenge with a unique backref name
    challenge = db.relationship('Challenge', backref='participants_in_challenge')

