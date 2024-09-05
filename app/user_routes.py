from flask import Flask, render_template, url_for, flash, redirect, request, abort
from flask_login import login_user, current_user, logout_user, login_required
from app import db, bcrypt
from app.forms import RegisterForm, LoginForm, ConversionForm, ToolForm, RecipeConversionForm
from app.models import User, Tool, Achievement, UserAchievement
from app.utils import convert_measurement, process_recipe
from app.forms import AchievementTrackingForm
from app.achievements import check_achievements
from datetime import datetime


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.confirm_password.data:
            flash('Password and Confirm Password do not match.', 'danger')
        else:
            existing_user = User.query.filter_by(username=form.username.data).first()
            existing_email = User.query.filter_by(email=form.email.data).first()
            if existing_user:
                flash('That username is taken. Please choose a different one.', 'danger')
            elif existing_email:
                flash('That email is already in use. Please choose a different one.', 'danger')
            else:
                hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
                new_user = User(username=form.username.data, email=form.email.data, password=hashed_password)
                db.session.add(new_user)
                db.session.commit()
                flash('Your account has been created! You are now able to log in', 'success')
                return redirect(url_for('login'))
    return render_template('register.html', form=form)


@app.route('/logout')
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))


@app.route('/manual_conversion_tool', methods=['GET', 'POST'])
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


@app.route('/automatic_conversion', methods=['GET', 'POST'])
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


@app.route('/my_tools', methods=['GET', 'POST'])
@login_required
def my_tools():
    form = ToolForm(user_id=current_user.id)
    if form.validate_on_submit():
        existing_tool = Tool.query.filter_by(name=form.name.data, unit=form.unit.data, owner_id=current_user.id).first()
        if existing_tool:
            flash('This tool with the same unit already exists. Please choose a different name or unit.', 'danger')
        else:
            tool = Tool(name=form.name.data, unit=form.unit.data, owner_id=current_user.id)
            db.session.add(tool)
            db.session.commit()
            flash('Tool has been added!', 'success')
            return redirect(url_for('my_tools'))
    tools = Tool.query.filter_by(owner_id=current_user.id).all()
    return render_template('my_tools.html', form=form, tools=tools)


@app.route('/delete_tool/<int:tool_id>', methods=['POST'])
@login_required
def delete_tool(tool_id):
    tool = Tool.query.get_or_404(tool_id)
    if tool.owner != current_user:
        abort(403)
    db.session.delete(tool)
    db.session.commit()
    flash('Tool has been deleted.', 'success')
    return redirect(url_for('my_tools'))


@app.route('/complete_recipe/<int:recipe_id>', methods=['POST'])
@login_required
def complete_recipe(recipe_id):
    # Logic to handle recipe completion...
    current_user.completed_recipes += 1
    db.session.commit()
    check_achievements(current_user)
    flash("Recipe completed!", "success")
    return redirect(url_for('my_tools'))


@app.route('/achievements', methods=['GET', 'POST'])
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
        check_achievements(current_user)
        flash('Achievement progress updated!', 'success')
        return redirect(url_for('achievements'))

    return render_template('achievements.html', form=form, user=current_user, achievements=user_achievements)


@app.route('/increment_achievement/<int:achievement_id>', methods=['POST'])
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
    return redirect(url_for('achievements'))











# Placeholder routes for future features
@app.route('/add_recipe')
@login_required
def add_recipe():
    return render_template('placeholder.html', feature="Add Recipes")

@app.route('/edit_recipe')
@login_required
def edit_recipe():
    return render_template('placeholder.html', feature="Edit Recipes")

@app.route('/delete_recipe')
@login_required
def delete_recipe():
    return render_template('placeholder.html', feature="Delete Recipes")

@app.route('/connect_friends')
@login_required
def connect_friends():
    return render_template('placeholder.html', feature="Connect with Friends")

@app.route('/share_recipes')
@login_required
def share_recipes():
    return render_template('placeholder.html', feature="Share Recipes")

@app.route('/comment_recipes')
@login_required
def comment_recipes():
    return render_template('placeholder.html', feature="Comment on Recipes")

@app.route('/create_shopping_list')
@login_required
def create_shopping_list():
    return render_template('placeholder.html', feature="Create Shopping List")

@app.route('/add_to_shopping_list')
@login_required
def add_to_shopping_list():
    return render_template('placeholder.html', feature="Add to Shopping List")

@app.route('/export_shopping_list')
@login_required
def export_shopping_list():
    return render_template('placeholder.html', feature="Export Shopping List")