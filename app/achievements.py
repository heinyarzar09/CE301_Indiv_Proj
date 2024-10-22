# Import necessary models and database instance
from flask import flash
from app.models import Achievement, UserAchievement  # Import Achievement and UserAchievement models
from app import db  # Import database instance for committing changes

# Function to check and award achievements for a user based on their progress
def check_achievements(user):
    # Check if the user has completed at least 1 recipe
    # Achievement: First Recipe Completed
    if user.completed_recipes >= 1:
        award_achievement(user, 'First Recipe Completed')

    # Check if the user has completed at least 10 recipes
    # Achievement: Master Chef
    if user.completed_recipes >= 10:
        award_achievement(user, 'Master Chef')

    # Check if the user has created at least 1 recipe
    # Achievement: Recipe Creator
    if user.recipes_created >= 1:
        award_achievement(user, 'Recipe Creator')

    # Check if the user has shared at least 1 recipe
    # Achievement: Social Butterfly
    if user.recipes_shared >= 1:
        award_achievement(user, 'Social Butterfly')

# Function to award a specific achievement to a user
def award_achievement(user, achievement_name):
    # Query the database to get the achievement by its name
    achievement = Achievement.query.filter_by(name=achievement_name).first()

    # If the achievement exists
    if achievement:
        # Check if the user has already earned this achievement
        if not UserAchievement.query.filter_by(user_id=user.id, achievement_id=achievement.id).first():
            # Create a new UserAchievement instance if the achievement has not yet been awarded
            user_achievement = UserAchievement(user_id=user.id, achievement_id=achievement.id)
            db.session.add(user_achievement)  # Add the achievement to the database session
            db.session.commit()  # Commit changes to save the achievement

            # Flash a success message to notify the user that they've earned a new achievement
            flash(f"Congratulations! You've earned the '{achievement_name}' achievement.", 'success')
