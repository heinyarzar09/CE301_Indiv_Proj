from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, SelectField, FloatField
from wtforms.widgets import TextArea
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, NumberRange
from app.models import User

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
    name = StringField('Tool Name', validators=[DataRequired(), Length(min=1, max=100)])
    submit = SubmitField('Add Tool')

class RecipeConversionForm(FlaskForm):
    recipe_text = StringField('Recipe', validators=[DataRequired()], widget=TextArea())
    to_unit = SelectField('Convert to Unit', choices=[], validators=[DataRequired()])
    submit = SubmitField('Convert')
