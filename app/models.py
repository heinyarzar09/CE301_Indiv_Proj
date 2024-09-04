from flask_login import UserMixin
from datetime import datetime
from app import db

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    role = db.Column(db.String(10), nullable=False, default='user')
    
    # Track user activity
    completed_recipes = db.Column(db.Integer, default=0)
    recipes_created = db.Column(db.Integer, default=0)
    recipes_shared = db.Column(db.Integer, default=0)
    friends_connected = db.Column(db.Integer, default=0) 
    shopping_lists_created = db.Column(db.Integer, default=0)
    conversion_tool_uses = db.Column(db.Integer, default=0)
    
    tools = db.relationship('Tool', backref='owner', lazy=True, cascade="all, delete-orphan")


class Tool(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    unit = db.Column(db.String(50), nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Achievement(db.Model):
    __tablename__ = 'achievements'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    criteria = db.Column(db.String(200), nullable=False)
    icon_url = db.Column(db.String(255), nullable=True)  # URL to the achievement icon

class UserAchievement(db.Model):
    __tablename__ = 'user_achievements'  # Ensure this matches your database table name
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    achievement_id = db.Column(db.Integer, db.ForeignKey('achievements.id'), nullable=False)
    date_achieved = db.Column(db.Date, default=datetime.utcnow)
    achievement = db.relationship('Achievement', backref='user_achievements', lazy=True)
