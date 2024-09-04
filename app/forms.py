from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, SelectField, FloatField, TextAreaField, IntegerField
from wtforms.validators import DataRequired, Length, Email, ValidationError, NumberRange
from app.models import User, Tool

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired()])
    role = SelectField('Role', choices=[('user', 'User'), ('admin', 'Admin')], validators=[DataRequired()])
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is taken. Please choose a different one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is already in use. Please choose a different one.')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired()])
    submit = SubmitField('Reset Password')

class ConversionForm(FlaskForm):
    amount = FloatField('Amount', validators=[DataRequired(), NumberRange(min=0)])
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
    submit = SubmitField('Convert')

class ToolForm(FlaskForm):
    name = StringField('Tool Name', validators=[DataRequired()])
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
    submit = SubmitField('Add Tool')

    def __init__(self, *args, **kwargs):
        self.user_id = kwargs.pop('user_id', None)
        super(ToolForm, self).__init__(*args, **kwargs)

    def validate_name(self, name):
        if self.user_id is not None:
            tool = Tool.query.filter_by(name=name.data, unit=self.unit.data, owner_id=self.user_id).first()
            if tool:
                raise ValidationError('This tool with the same unit already exists. Please choose a different name or unit.')

class RecipeConversionForm(FlaskForm):
    recipe_text = TextAreaField('Recipe', validators=[DataRequired()])
    to_unit = SelectField('Convert to', validators=[DataRequired()])
    submit = SubmitField('Convert')

class AchievementTrackingForm(FlaskForm):
    achievement_name = StringField('Achievement Name', validators=[DataRequired()])
    progress = IntegerField('Progress', validators=[DataRequired()])
    submit = SubmitField('Update Achievement')