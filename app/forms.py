# Import necessary modules from Flask-WTF and WTForms
from flask_wtf import FlaskForm  # Base class for creating forms in Flask
from wtforms import StringField, PasswordField, SubmitField, BooleanField, SelectField, FloatField, TextAreaField, IntegerField, FileField, HiddenField # Different types of form fields
from wtforms.validators import DataRequired, Length, Email, ValidationError, NumberRange, Optional  # Validators for form fields
from app.models import User, Tool, Challenge  # Import models for validation
from flask_wtf.file import FileField, FileAllowed  # File fields for handling file uploads

# Form for user registration
class RegisterForm(FlaskForm):
    # Username field with required data and length between 2 and 20 characters
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    # Email field with required data and email validation
    email = StringField('Email', validators=[DataRequired(), Email()])
    # Password field with required data and minimum length of 6
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    # Confirm password field for password verification
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired()])
    # Role selection field for user or admin role
    role = SelectField('Role', choices=[('user', 'User'), ('admin', 'Admin')], validators=[DataRequired()])
    # Submit button for the registration form
    submit = SubmitField('Sign Up')

    # Custom validator to check if the username is already taken
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is taken. Please choose a different one.')

    # Custom validator to check if the email is already registered
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is already in use. Please choose a different one.')

# Form for user login
class LoginForm(FlaskForm):
    # Email field with required data and email validation
    email = StringField('Email', validators=[DataRequired(), Email()])
    # Password field with required data
    password = PasswordField('Password', validators=[DataRequired()])
    # Remember me checkbox for staying logged in across sessions
    remember = BooleanField('Remember Me')
    # Submit button for the login form
    submit = SubmitField('Login')

# Form for resetting password
class ResetPasswordForm(FlaskForm):
    # Password field with required data and minimum length of 6
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    # Confirm password field for password verification
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired()])
    # Submit button for the reset password form
    submit = SubmitField('Reset Password')

# Form for manual unit conversion
class ConversionForm(FlaskForm):
    # Amount field with required data and number range to ensure a non-negative value
    amount = FloatField('Amount', validators=[DataRequired(), NumberRange(min=0)])
    # Drop-down field for selecting the unit to convert from
    from_unit = SelectField('From Unit', choices=[
        ('tsp', 'Teaspoon (tsp)'),
        ('tbsp', 'Tablespoon (tbsp)'),
        ('cup', 'Cup (cup)'),
        ('fl oz', 'Fluid Ounce (fl oz)'),
        ('pt', 'Pint (pt)'),
        ('qt', 'Quart (qt)'),
        ('gal', 'Gallon (gal)'),
        ('oz', 'Ounce (oz)'),
        ('lb', 'Pound (lb)'),
        ('ml', 'Milliliter (ml)'),
        ('g', 'Gram (g)'),
    ], validators=[DataRequired()])
    # Drop-down field for selecting the unit to convert to
    to_unit = SelectField('To Unit', choices=[
        ('tsp', 'Teaspoon (tsp)'),
        ('tbsp', 'Tablespoon (tbsp)'),
        ('cup', 'Cup (cup)'),
        ('fl oz', 'Fluid Ounce (fl oz)'),
        ('pt', 'Pint (pt)'),
        ('qt', 'Quart (qt)'),
        ('gal', 'Gallon (gal)'),
        ('oz', 'Ounce (oz)'),
        ('lb', 'Pound (lb)'),
        ('ml', 'Milliliter (ml)'),
        ('g', 'Gram (g)'),
    ], validators=[DataRequired()])
    # Submit button for the conversion form
    submit = SubmitField('Convert')

# Form for adding a user's cooking tool
class ToolForm(FlaskForm):
    # Tool name field with required data
    name = StringField('Tool Name', validators=[DataRequired()])
    # Drop-down field for selecting the unit associated with the tool
    unit = SelectField('Unit', choices=[
        ('tsp', 'Teaspoon (tsp)'),
        ('tbsp', 'Tablespoon (tbsp)'),
        ('cup', 'Cup (cup)'),
        ('fl oz', 'Fluid Ounce (fl oz)'),
        ('pt', 'Pint (pt)'),
        ('qt', 'Quart (qt)'),
        ('gal', 'Gallon (gal)'),
        ('oz', 'Ounce (oz)'),
        ('lb', 'Pound (lb)'),
        ('ml', 'Milliliter (ml)'),
        ('g', 'Gram (g)'),
    ], validators=[DataRequired()])
    # Submit button for the tool form
    submit = SubmitField('Add Tool')

    # Custom constructor to accept user_id as a parameter for validation purposes
    def __init__(self, *args, **kwargs):
        self.user_id = kwargs.pop('user_id', None)
        super(ToolForm, self).__init__(*args, **kwargs)

    # Custom validator to check if the tool already exists for the user
    def validate_name(self, name):
        if self.user_id is not None:
            tool = Tool.query.filter_by(name=name.data, unit=self.unit.data, owner_id=self.user_id).first()
            if tool:
                raise ValidationError('This tool with the same unit already exists. Please choose a different name or unit.')

# Form for recipe conversion
class RecipeConversionForm(FlaskForm):
    # Text area for entering the recipe text to be converted
    recipe_text = TextAreaField('Recipe', validators=[DataRequired()])
    # Drop-down field for selecting the unit to convert the recipe to
    to_unit = SelectField('Convert to', validators=[DataRequired()])
    # Submit button for the recipe conversion form
    submit = SubmitField('Convert')

# Form for tracking achievements
class AchievementTrackingForm(FlaskForm):
    # Achievement name field with required data
    achievement_name = StringField('Achievement Name', validators=[DataRequired()])
    # Progress field for updating the user's progress on an achievement
    progress = IntegerField('Progress', validators=[DataRequired()])
    # Submit button for the achievement tracking form
    submit = SubmitField('Update Achievement')

# Form for sharing a post
class SharePostForm(FlaskForm):
    # File field for uploading an image (optional)
    image = FileField('Upload Image', validators=[DataRequired()])
    # Text area for writing a message to accompany the post
    message = TextAreaField('Message', validators=[DataRequired()])
    # Dropdown to select the challenge associated with the post
    challenge = SelectField('Tag a Challenge', coerce=int, validators=[Optional()])
    # Submit button for the post sharing form
    submit = SubmitField('Share Post')

class AddCreditsForm(FlaskForm):
    credits = IntegerField('Credits to Add', validators=[DataRequired()])
    submit = SubmitField('Add Credits')

class ChallengeForm(FlaskForm):
    name = StringField('Challenge Name', validators=[DataRequired(), Length(min=2, max=100)])
    icon = FileField('Challenge Icon', validators=[DataRequired(), FileAllowed(['jpg', 'png', 'gif'])])
    credits_required = IntegerField('Credits Required', validators=[DataRequired()])
    days = IntegerField('Days', default=0)
    hours = IntegerField('Hours', default=0)
    minutes = IntegerField('Minutes', default=0)
    seconds = IntegerField('Seconds', default=0)
    submit = SubmitField('Create Challenge')



class JoinChallengeForm(FlaskForm):
    submit = SubmitField('Join Challenge')

class AdminAddCreditsForm(FlaskForm):
    user = SelectField('User', coerce=int, validators=[DataRequired()])
    credits_to_add = IntegerField('Credits to Add', validators=[DataRequired()])
    submit = SubmitField('Add Credits')

    def __init__(self, users, *args, **kwargs):
        super(AdminAddCreditsForm, self).__init__(*args, **kwargs)
        self.user.choices = [(user.id, user.username) for user in users]

class CreditRequestForm(FlaskForm):
    proof = FileField('Upload Proof of Payment', validators=[DataRequired(), FileAllowed(['jpg', 'jpeg', 'png'], 'Images only!')])
    credits_requested = IntegerField('Credits Requested', validators=[DataRequired(), NumberRange(min=1)])
    submit = SubmitField('Submit')


class CreditApprovalForm(FlaskForm):
    credit_request_id = HiddenField()
    approve = BooleanField('Approve')
    submit = SubmitField('Update Status')
