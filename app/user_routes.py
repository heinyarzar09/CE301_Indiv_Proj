from flask import Blueprint, render_template, url_for, flash, redirect, request
from flask_login import login_user, current_user, logout_user, login_required
from app import db, bcrypt
from app.forms import RegistrationForm, LoginForm, ConversionForm, ToolForm
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

@user.route('/conversion_tool', methods=['GET', 'POST'])
@login_required
def conversion_tool():
    form = ConversionForm()
    result = None
    if form.validate_on_submit():
        amount = form.amount.data
        from_unit = form.from_unit.data
        to_unit = form.to_unit.data
        result = convert_measurement(amount, from_unit, to_unit)
        flash(f'{amount} {from_unit} is {result} {to_unit}', 'success')
    return render_template('conversion_tool.html', form=form, result=result)

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
    conversion_factors = {
        'teaspoon': 1,
        'tablespoon': 3,
        'cup': 48,
    }
    amount_in_teaspoons = amount * conversion_factors[from_unit]
    converted_amount = amount_in_teaspoons / conversion_factors[to_unit]
    return converted_amount

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
