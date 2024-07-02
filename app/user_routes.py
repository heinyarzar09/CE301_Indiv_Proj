from flask import Blueprint, render_template, url_for, flash, redirect, request, abort
from flask_login import login_user, current_user, logout_user, login_required
from app import db, bcrypt
from app.forms import RegisterForm, LoginForm, ConversionForm, ToolForm, RecipeConversionForm
from app.models import User, Tool
from app.utils import convert_measurement, process_recipe

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
            existing_user = User.query.filter(
                (User.username == form.username.data) | 
                (User.email == form.email.data)
            ).first()
            if existing_user:
                if existing_user.username == form.username.data:
                    flash('That username is taken. Please choose a different one.', 'danger')
                if existing_user.email == form.email.data:
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
