from flask import Blueprint, render_template, url_for, flash, redirect, request, abort
from flask_login import login_user, current_user, logout_user, login_required
from app import db, bcrypt
from app.forms import RegisterForm, LoginForm, ConversionForm, ToolForm, RecipeConversionForm
from app.models import User, Tool, Achievement, UserAchievement
from app.utils import convert_measurement, process_recipe
from app.forms import AchievementTrackingForm
from app.achievements import check_achievements 

user = Blueprint('user', __name__)

@user.route('/')
def index():
    return render_template('index.html')

@user.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('user.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            if user.role == 'admin':
                return redirect(url_for('admin.dashboard'))
            return redirect(next_page) if next_page else redirect(url_for('user.index'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    elif form.errors:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{error}", 'danger')
    return render_template('login.html', form=form)

@user.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if request.method == 'POST' and form.validate():
        if form.password.data != form.confirm_password.data:
            flash('Password and Confirm Password do not match.', 'danger')
        else:
            existing_user_by_username = User.query.filter_by(username=form.username.data).first()
            existing_user_by_email = User.query.filter_by(email=form.email.data).first()
            if existing_user_by_username:
                flash('That username is taken. Please choose a different one.', 'danger')
            elif existing_user_by_email:
                flash('That email is already in use. Please choose a different one.', 'danger')
            else:
                hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
                new_user = User(username=form.username.data, email=form.email.data, password=hashed_password, role=form.role.data)
                db.session.add(new_user)
                db.session.commit()
                flash('Your account has been created! You are now able to log in', 'success')
                return redirect(url_for('user.login'))
    elif form.errors:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{error}", 'danger')
    return render_template('register.html', title='Register', form=form)

@user.route('/logout')
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('user.index'))

@user.route('/manual_conversion_tool', methods=['GET', 'POST'])
@login_required
def manual_conversion_tool():
    form = ConversionForm()
    result = None
    if form.validate_on_submit():
        amount = form.amount.data
        from_unit = form.from_unit.data
        to_unit = form.to_unit.data
        try:
            converted_amount = convert_measurement(amount, from_unit, to_unit)
            result = f"{amount} {from_unit} is {converted_amount} {to_unit}"
        except ValueError as e:
            flash(str(e), 'danger')
    return render_template('manual_conversion_tool.html', form=form, result=result)

@user.route('/automatic_conversion', methods=['GET', 'POST'])
@login_required
def automatic_conversion():
    form = RecipeConversionForm()
    
    # Get user's tools
    user_tools = Tool.query.filter_by(owner_id=current_user.id).all()
    form.to_unit.choices = [(f"{tool.name} - {tool.unit}", f"{tool.name} - {tool.unit}") for tool in user_tools]
    
    converted_recipe = None
    if form.validate_on_submit():
        recipe_text = form.recipe_text.data
        to_unit = form.to_unit.data.split(' - ')[1]  # Extract the unit part
        try:
            converted_recipe = process_recipe(recipe_text, to_unit, current_user.id)
        except ValueError as e:
            flash(str(e), 'danger')
    return render_template('automatic_conversion_tool.html', form=form, converted_recipe=converted_recipe)

@user.route('/my_tools', methods=['GET', 'POST'])
@login_required
def my_tools():
    form = ToolForm(user_id=current_user.id)
    if form.validate_on_submit():
        # Check for duplicate tool
        existing_tool = Tool.query.filter_by(name=form.name.data, unit=form.unit.data, owner_id=current_user.id).first()
        if existing_tool:
            flash('This tool with the same unit already exists. Please choose a different name or unit.', 'danger')
        else:
            tool = Tool(name=form.name.data, unit=form.unit.data, owner_id=current_user.id)
            db.session.add(tool)
            db.session.commit()
            flash('Tool has been added!', 'success')
            return redirect(url_for('user.my_tools'))
    elif form.errors:
        # Handle other form errors
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{error}", 'danger')
    tools = Tool.query.filter_by(owner_id=current_user.id).all()
    return render_template('my_tools.html', title='My Tools', form=form, tools=tools)

@user.route('/delete_tool/<int:tool_id>', methods=['POST'])
@login_required
def delete_tool(tool_id):
    tool = Tool.query.get_or_404(tool_id)
    if tool.owner != current_user:
        abort(403)
    db.session.delete(tool)
    db.session.commit()
    flash('Tool has been deleted.', 'success')
    return redirect(url_for('user.my_tools'))

@user.route('/complete_recipe/<int:recipe_id>', methods=['POST'])
@login_required
def complete_recipe(recipe_id):
    # Logic to handle recipe completion...
    
    # Update the user's completed recipes count
    current_user.completed_recipes += 1
    db.session.commit()
    
    # Check for achievements (ensure check_achievements is implemented)
    check_achievements(current_user)
    
    flash("Recipe completed!", "success")
    return redirect(url_for('user.my_tools'))

def check_achievements(user):
    achievements = Achievement.query.all()
    for achievement in achievements:
        if achievement.criteria == 'Complete 20 Recipes' and user.completed_recipes >= 20:
            if not UserAchievement.query.filter_by(user_id=user.id, achievement_id=achievement.id).first():
                new_achievement = UserAchievement(user_id=user.id, achievement_id=achievement.id, date_achieved=datetime.utcnow())
                db.session.add(new_achievement)
                db.session.commit()

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

    # Comment out or remove the following block if 'friends_connected' is not used
    # Achievement: Friend Connector
    # if user.friends_connected >= 5:
    #     award_achievement(user, 'Friend Connector')

    # Achievement: Shopping Expert
    if user.shopping_lists_created >= 3:
        award_achievement(user, 'Shopping Expert')

    # Achievement: Conversion Master
    if user.conversion_tool_uses >= 5:
        award_achievement(user, 'Conversion Master')

def award_achievement(user, achievement_name):
    achievement = Achievement.query.filter_by(name=achievement_name).first()
    if achievement:
        # Check if the user already has this achievement
        if not UserAchievement.query.filter_by(user_id=user.id, achievement_id=achievement.id).first():
            user_achievement = UserAchievement(user_id=user.id, achievement_id=achievement.id)
            db.session.add(user_achievement)
            db.session.commit()
            flash(f"Congratulations! You've earned the '{achievement_name}' achievement.", 'success')

def add_icons_to_achievements(app):
    with app.app_context():
        achievements = Achievement.query.all()
        for achievement in achievements:
            if achievement.name == 'Complete 20 Recipes':
                achievement.icon_url = '/static/icons/completed_20_recipes.png'
            elif achievement.name == 'Create 10 Recipes':
                achievement.icon_url = '/static/icons/create_10_recipes.png'
            # Add more conditions for other achievements here
            db.session.commit()

@user.route('/manage_achievements')
@login_required
def manage_achievements():
    if current_user.role != 'admin':
        abort(403)
    add_icons_to_achievements()
    flash("Achievements icons updated successfully.", "success")
    return redirect(url_for('user.index'))

@user.route('/track_achievement', methods=['POST'])
@login_required
def track_achievement():
    form = AchievementTrackingForm()
    if form.validate_on_submit():
        # Assuming you have a UserAchievement model and criteria to check against
        achievement_name = form.achievement_name.data
        progress = form.progress.data

        # Here you can add logic to update or track the user's achievement progress
        # For example, update an existing UserAchievement or create a new one

        flash(f"Your progress for {achievement_name} has been updated to {progress}!", "success")
        return redirect(url_for('user.achievements'))
    
    flash("Failed to track achievement.", "danger")
    return redirect(url_for('user.achievements'))

@user.route('/achievements', methods=['GET', 'POST'])
@login_required
def achievements():
    form = AchievementTrackingForm()
    user_achievements = UserAchievement.query.filter_by(user_id=current_user.id).all()

    if form.validate_on_submit():
        achievement_name = form.achievement_name.data
        progress = form.progress.data

        # Update the user's progress for the specified achievement
        if achievement_name == 'Completed Recipes':
            current_user.completed_recipes += progress
        elif achievement_name == 'Recipes Created':
            current_user.recipes_created += progress
        elif achievement_name == 'Recipes Shared':
            current_user.recipes_shared += progress

        db.session.commit()

        # Check if the user has earned any new achievements
        check_achievements(current_user)

        flash('Achievement progress updated!', 'success')
        return redirect(url_for('user.achievements'))

    return render_template('achievements.html', form=form, user=current_user, achievements=user_achievements)

@user.route('/increment_achievement/<int:achievement_id>', methods=['POST'])
@login_required
def increment_achievement(achievement_id):
    if achievement_id == 1:
        current_user.completed_recipes += 1
    elif achievement_id == 2:
        current_user.recipes_created += 1
    elif achievement_id == 3:
        current_user.recipes_shared += 1

    db.session.commit()
    check_achievements(current_user)
    
    flash("Achievement progress incremented!", "success")
    return redirect(url_for('user.achievements'))










# Placeholder routes for future features
@user.route('/add_recipe')
@login_required
def add_recipe():
    return render_template('placeholder.html', feature="Add Recipes")

@user.route('/edit_recipe')
@login_required
def edit_recipe():
    return render_template('placeholder.html', feature="Edit Recipes")

@user.route('/delete_recipe')
@login_required
def delete_recipe():
    return render_template('placeholder.html', feature="Delete Recipes")

@user.route('/connect_friends')
@login_required
def connect_friends():
    return render_template('placeholder.html', feature="Connect with Friends")

@user.route('/share_recipes')
@login_required
def share_recipes():
    return render_template('placeholder.html', feature="Share Recipes")

@user.route('/comment_recipes')
@login_required
def comment_recipes():
    return render_template('placeholder.html', feature="Comment on Recipes")

@user.route('/create_shopping_list')
@login_required
def create_shopping_list():
    return render_template('placeholder.html', feature="Create Shopping List")

@user.route('/add_to_shopping_list')
@login_required
def add_to_shopping_list():
    return render_template('placeholder.html', feature="Add to Shopping List")

@user.route('/export_shopping_list')
@login_required
def export_shopping_list():
    return render_template('placeholder.html', feature="Export Shopping List")