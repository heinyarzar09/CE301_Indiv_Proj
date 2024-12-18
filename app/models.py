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
    date_created = db.Column(db.DateTime, default=datetime.now(timezone.utc))

    # Tracking user activity metrics
    completed_recipes = db.Column(db.Integer, default=0)
    recipes_created = db.Column(db.Integer, default=0)
    recipes_shared = db.Column(db.Integer, default=0)
    friends_connected = db.Column(db.Integer, default=0)
    shopping_lists_created = db.Column(db.Integer, default=0)
    conversion_tool_uses = db.Column(db.Integer, default=0)
    last_login = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Credits for creating/joining challenges
    credits = db.Column(db.Integer, default=0)

    # Relationship to tools, posts, and challenges
    tools = db.relationship('Tool', backref='owner', lazy=True, cascade="all, delete-orphan")
    posts = db.relationship('Post', backref='author', lazy=True, cascade="all, delete-orphan")
    
    # Relationship to created challenges
    created_challenges = db.relationship('Challenge', backref='creator', lazy=True, overlaps="challenge_creator,created_challenges")
    
    # Relationship to participated challenges
    participated_challenges = db.relationship('ChallengeParticipant', backref='user_participation', lazy=True, overlaps="participant,challenges_participated")
    
    # New relationship to achievements
    achievements = db.relationship('Achievement', backref='user', lazy=True, cascade="all, delete-orphan")


# In your models.py file
class PasswordResetRequest(db.Model):
    __tablename__ = 'password_reset_request'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Link to user requesting reset
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    status = db.Column(db.String(20), default='Pending')  # "Pending", "Approved", or "Rejected"
    date_requested = db.Column(db.DateTime, default=db.func.current_timestamp())

    # Relationship to User
    user = db.relationship('User', backref=db.backref('reset_requests', cascade="all, delete-orphan"))


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


# Define the association table for users who reported posts
post_reports = db.Table('post_reports',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), primary_key=True),
    db.Column('post_id', db.Integer, db.ForeignKey('post.id', ondelete='CASCADE'), primary_key=True)
)

# Define the Post model to store users' shared posts, such as recipe posts with images and messages
class Post(db.Model):
    __tablename__ = 'post'
    
    id = db.Column(db.Integer, primary_key=True)
    image_file = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenge.id'), nullable=True)
    reports = db.Column(db.Integer, default=0)

    # Relationships
    likes = db.relationship('PostLike', backref='liked_post', cascade="all, delete-orphan")
    user = db.relationship('User', backref='user_posts')
    challenge = db.relationship('Challenge', backref='posts', lazy=True)
    
    # New relationship to track users who reported the post
    reported_by = db.relationship('User', secondary=post_reports, backref='reported_posts')

    def is_liked_by(self, user):
        return any(like.user_id == user.id for like in self.likes)

    def is_reported_by(self, user):
        return user in self.reported_by

    # Method to decrement challenge progress
    def decrement_challenge_progress(self):
        if self.challenge_id:
            challenge = Challenge.query.get(self.challenge_id)
            if challenge and challenge.progress > 0:
                challenge.progress -= 1
                db.session.commit()

                
class PostLike(db.Model):
    __tablename__ = 'post_likes'

    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # Relationship to user
    user = db.relationship('User', backref='liked_posts')

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

class Challenge(db.Model):
    __tablename__ = 'challenge'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    icon = db.Column(db.String(100))  # Path to the icon
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    credits_required = db.Column(db.Integer, nullable=False)
    duration = db.Column(db.Integer, nullable=False)  # Duration in seconds
    started_at = db.Column(db.DateTime, nullable=False)  # Start time of the challenge
    ended = db.Column(db.Boolean, default=False)  # Field to mark if the challenge has ended

    # Relationship to participants
    participants = db.relationship('ChallengeParticipant', backref='challenge_participation', lazy=True, cascade="all, delete-orphan")

    def __init__(self, name, icon, creator_id, credits_required, duration, started_at=None):
        self.name = name
        self.icon = icon
        self.creator_id = creator_id
        self.credits_required = credits_required
        self.duration = duration
        self.started_at = started_at or datetime.now(timezone.utc)  # Default to current UTC time if not provided

    @property
    def time_remaining(self):
        # Calculate remaining time by comparing the current time and the end time
        if self.started_at:
            time_passed = (datetime.now(timezone.utc) - self.make_timezone_aware(self.started_at)).total_seconds()
            return max(self.duration - time_passed, 0)
        return self.duration

    def get_end_time(self):
        # Ensure started_at is timezone-aware in UTC
        return self.make_timezone_aware(self.started_at) + timedelta(seconds=self.duration)

    def is_active(self):
        # Check if the challenge is still active by comparing current time with end time
        return datetime.now(timezone.utc) < self.get_end_time()


    def has_ended(self):
        # Check if the challenge has ended and update the ended status
        if datetime.now(timezone.utc) >= self.get_end_time():
            self.ended = True
            return True
        return False

    def get_winner(self):
        # Find the participant with the highest progress
        if not self.participants:
            return None
        # Assuming the 'progress' field is the determining factor
        winner = max(self.participants, key=lambda p: p.progress)
        return winner

    @staticmethod
    def make_timezone_aware(dt):
        # Convert a naive datetime to timezone-aware if it isn’t already
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt

class ChallengeParticipant(db.Model):
    __tablename__ = 'challenge_participant'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenge.id', ondelete='CASCADE'), nullable=False)
    wagered_credits = db.Column(db.Integer, nullable=False)
    progress = db.Column(db.Float, default=0)  # Progress for tracking in leaderboard
    date_joined = db.Column(db.DateTime, default=db.func.current_timestamp())
    credited = db.Column(db.Boolean, default=False)
    
    # Relationship to the user participating in the challenge
    user = db.relationship('User', backref='participations')

    # Relationship to the challenge with a unique backref name
    challenge = db.relationship('Challenge', backref='participants_in_challenge')


class CreditRequest(db.Model):
    __tablename__ = 'credit_request'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    status = db.Column(db.String(20), default='Pending')
    proof_image = db.Column(db.String(200), nullable=False)
    credits_requested = db.Column(db.Integer, nullable=False)
    date_submitted = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationship to user
    user = db.relationship('User', backref=db.backref('credit_requests', passive_deletes=True))

    def __init__(self, user_id, proof_image, credits_requested):
        self.user_id = user_id
        self.proof_image = proof_image
        self.credits_requested = credits_requested

class AdminCreditAction(db.Model):
    __tablename__ = 'admin_credit_action'
    
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('credit_request.id'), nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    action = db.Column(db.String(20), nullable=False)
    added_credits = db.Column(db.Integer, default=0)
    action_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    request = db.relationship('CreditRequest', backref='admin_actions')
    admin = db.relationship('User', backref='admin_actions')

    def __init__(self, request_id, admin_id, action, added_credits=0):
        self.request_id = request_id
        self.admin_id = admin_id
        self.action = action
        self.added_credits = added_credits

class AdminNotification(db.Model):
    __tablename__ = 'admin_notification'
    
    id = db.Column(db.Integer, primary_key=True)
    credit_request_id = db.Column(db.Integer, db.ForeignKey('credit_request.id'), nullable=False)
    reviewed = db.Column(db.Boolean, default=False)

    # Relationship to CreditRequest
    credit_request = db.relationship('CreditRequest', backref='notifications')

class ShoppingList(db.Model):
    __tablename__ = 'shopping_list'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    item_name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.String(50), nullable=True)
    completed = db.Column(db.Boolean, default=False)
    
    # Relationship to User
    user = db.relationship('User', backref='shopping_lists')

class CreditWithdrawRequest(db.Model):
    __tablename__ = 'credit_withdraw_request'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='Pending')
    credits_requested = db.Column(db.Integer, nullable=False)
    payment_mode = db.Column(db.String(20), nullable=False)
    phone_number = db.Column(db.String(15), nullable=True)
    date_requested = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    date_approved = db.Column(db.DateTime)
    
    user = db.relationship('User', backref='credit_withdraw_requests')
