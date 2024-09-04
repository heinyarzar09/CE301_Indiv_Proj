from app.models import Achievement, UserAchievement
from app import db

def check_achievements(user):
    # Achievement: First Recipe Completed
    if user.completed_recipes >= 1:
        award_achievement(user, 'First Recipe Completed')

    # Achievement: Master Chef
    if user.completed_recipes >= 10:
        award_achievement(user, 'Master Chef')

    # Achievement: Recipe Creator
    if user.recipes_created >= 1:
        award_achievement(user, 'Recipe Creator')

    # Achievement: Social Butterfly
    if user.recipes_shared >= 1:
        award_achievement(user, 'Social Butterfly')

def award_achievement(user, achievement_name):
    achievement = Achievement.query.filter_by(name=achievement_name).first()
    if achievement:
        # Check if the user already has this achievement
        if not UserAchievement.query.filter_by(user_id=user.id, achievement_id=achievement.id).first():
            user_achievement = UserAchievement(user_id=user.id, achievement_id=achievement.id)
            db.session.add(user_achievement)
            db.session.commit()
            flash(f"Congratulations! You've earned the '{achievement_name}' achievement.", 'success')
