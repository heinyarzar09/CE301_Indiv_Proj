from flask import Blueprint, render_template, url_for, flash, redirect, request
from flask_login import login_user, current_user, logout_user, login_required
from app import db, bcrypt
from app.forms import RegistrationForm, LoginForm, ConversionForm, ToolForm, RecipeConversionForm
from app.models import User, Tool

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
    return render_template('login.html', form=form)

@user.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('user.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password, role=form.role.data)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in.', 'success')
        return redirect(url_for('user.login'))
    return render_template('register.html', form=form)

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
            result = str(e)
    return render_template('manual_conversion_tool.html', form=form, result=result)

@user.route('/automatic_conversion', methods=['GET', 'POST'])
@login_required
def automatic_conversion():
    form = RecipeConversionForm()
    converted_recipe = None
    if form.validate_on_submit():
        recipe_text = form.recipe_text.data
        converted_recipe = convert_recipe(recipe_text)
    return render_template('automatic_conversion.html', form=form, converted_recipe=converted_recipe)

@user.route('/my_tools', methods=['GET', 'POST'])
@login_required
def my_tools():
    form = ToolForm()
    if form.validate_on_submit():
        tool = Tool(name=form.name.data, owner=current_user)
        db.session.add(tool)
        db.session.commit()
        flash('Tool has been added!', 'success')
        return redirect(url_for('user.my_tools'))
    user_tools = Tool.query.filter_by(owner=current_user).all()
    return render_template('my_tools.html', form=form, tools=user_tools)

def convert_measurement(amount, from_unit, to_unit):
    conversions = {
        'tsp': {'tbsp': 1/3, 'cup': 1/48, 'fl oz': 1/6, 'ml': 5},
        'tbsp': {'tsp': 3, 'cup': 1/16, 'fl oz': 1/2, 'ml': 15},
        'cup': {'tsp': 48, 'tbsp': 16, 'fl oz': 8, 'pt': 1/2, 'qt': 1/4, 'gal': 1/16, 'ml': 240},
        'fl oz': {'tsp': 6, 'tbsp': 2, 'cup': 1/8, 'pt': 1/16, 'qt': 1/32, 'gal': 1/128, 'ml': 30},
        'pt': {'cup': 2, 'fl oz': 16, 'qt': 1/2, 'gal': 1/8, 'ml': 480},
        'qt': {'cup': 4, 'fl oz': 32, 'pt': 2, 'gal': 1/4, 'ml': 960},
        'gal': {'cup': 16, 'fl oz': 128, 'pt': 8, 'qt': 4, 'ml': 3840},
        'oz': {'lb': 1/16, 'g': 28.35},
        'lb': {'oz': 16, 'g': 453.59},
        'ml': {'tsp': 1/5, 'tbsp': 1/15, 'cup': 1/240, 'fl oz': 1/30, 'pt': 1/480, 'qt': 1/960, 'gal': 1/3840, 'g': 1},
        'g': {'oz': 1/28.35, 'lb': 1/453.59, 'ml': 1},
    }

    if from_unit == to_unit:
        return amount
    
    if from_unit in conversions and to_unit in conversions[from_unit]:
        return amount * conversions[from_unit][to_unit]
    
    # For conversions that require multiple steps
    for intermediate_unit in conversions[from_unit]:
        if intermediate_unit in conversions and to_unit in conversions[intermediate_unit]:
            return amount * conversions[from_unit][intermediate_unit] * conversions[intermediate_unit][to_unit]
    
    raise ValueError(f"Conversion from {from_unit} to {to_unit} not supported.")

def convert_recipe(recipe_text):
    user_tools = [tool.name for tool in Tool.query.filter_by(owner=current_user).all()]
    conversions = {
        'tsp': {'tbsp': 1/3, 'cup': 1/48, 'fl oz': 1/6},
        'tbsp': {'tsp': 3, 'cup': 1/16, 'fl oz': 1/2},
        'cup': {'tsp': 48, 'tbsp': 16, 'fl oz': 8},
        'fl oz': {'tsp': 6, 'tbsp': 2, 'cup': 1/8},
    }
    for original_tool, conversion_rates in conversions.items():
        if original_tool in recipe_text:
            for user_tool in user_tools:
                if user_tool in conversion_rates:
                    amount = float(recipe_text.split()[0])
                    converted_amount = amount * conversion_rates[user_tool]
                    return recipe_text.replace(original_tool, user_tool).replace(str(amount), str(converted_amount))
    return recipe_text

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

@user.route('/earn_achievements')
@login_required
def earn_achievements():
    return render_template('placeholder.html', feature="Earn Achievements")

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
