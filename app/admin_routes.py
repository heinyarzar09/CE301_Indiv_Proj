# Import necessary modules from Flask and other libraries
from flask import Blueprint, render_template, url_for, flash, redirect, request
from flask_login import current_user, login_required  # Flask-Login for managing user authentication
from app import db, bcrypt  # Importing database instance and bcrypt for password hashing
from app.forms import ResetPasswordForm, AdminAddCreditsForm  # Importing form for resetting passwords
from app.models import User, Friendship  # Importing User model for managing user data

# Create a blueprint for admin-related routes
admin = Blueprint('admin', __name__)

# Route for the admin dashboard
@admin.route('/dashboard')
@login_required  # Requires the user to be logged in
def dashboard():
    # Check if the current user is an admin
    if current_user.role != 'admin':
        flash('You do not have permission to view this page.', 'danger')  # Show error message if user is not admin
        return redirect(url_for('user.index'))  # Redirect non-admin users to the user index page
    return render_template('admin_dashboard.html')  # Render the admin dashboard page for admins

# Route for managing users
@admin.route('/manage_users')
@login_required
def manage_users():
    # Check if the current user is an admin
    if current_user.role != 'admin':
        flash('You do not have permission to view this page.', 'danger')  # Show error message if user is not admin
        return redirect(url_for('user.index'))  # Redirect non-admin users to the user index page
    users = User.query.all()  # Query all users from the database
    return render_template('admin_manage_users.html', users=users)  # Render the manage users page for admins

# Route for managing recipes
@admin.route('/manage_recipes')
@login_required
def manage_recipes():
    # Check if the current user is an admin
    if current_user.role != 'admin':
        flash('You do not have permission to view this page.', 'danger')  # Show error message if user is not admin
        return redirect(url_for('user.index'))  # Redirect non-admin users to the user index page
    # Logic to manage recipes can be added here
    return render_template('admin_manage_recipes.html')  # Render the manage recipes page for admins

# Route for admin settings page
@admin.route('/settings')
@login_required
def settings():
    # Check if the current user is an admin
    if current_user.role != 'admin':
        flash('You do not have permission to view this page.', 'danger')  # Show error message if user is not admin
        return redirect(url_for('user.index'))  # Redirect non-admin users to the user index page
    return render_template('admin_settings.html')  # Render the admin settings page for admins

# Route for admin to reset a user's password
@admin.route('/admin/reset_password/<int:user_id>', methods=['GET', 'POST'])
@login_required
def admin_reset_password(user_id):
    user = User.query.get_or_404(user_id)  # Get the user by ID or return 404 if not found
    form = ResetPasswordForm()  # Create an instance of the ResetPasswordForm

    if form.validate_on_submit():  # If the form is submitted and validated
        # Check if password and confirm password match
        if form.password.data != form.confirm_password.data:
            flash('Password and Confirm Password do not match.', 'danger')  # Show error message if passwords do not match
        # Check if the new password is the same as the current password
        elif bcrypt.check_password_hash(user.password, form.password.data):
            flash('New password cannot be the same as the current password.', 'danger')  # Show error message if new password matches current password
        else:
            # Hash the new password and update the user's password
            hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
            user.password = hashed_password
            db.session.commit()  # Commit changes to the database
            flash('Password has been updated!', 'success')  # Show success message
            return redirect(url_for('admin.manage_users'))  # Redirect to the manage users page

    elif form.errors:  # Handle any form validation errors
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{field}: {error}", 'danger')

    return render_template('admin_reset_password.html', title='Reset Password', form=form, user=user)

# Route for admin to delete a user
@admin.route('/delete_user/<int:user_id>', methods=['POST'])
@login_required
def admin_delete_user(user_id):
    if current_user.role != 'admin':
        flash('You do not have permission to perform this action.', 'danger')
        return redirect(url_for('user.index'))

    try:
        user = User.query.get_or_404(user_id)

        # Delete all friendships where the user is involved
        Friendship.query.filter((Friendship.user_id == user.id) | (Friendship.friend_id == user.id)).delete()

        # Optionally delete all tools belonging to the user
        for tool in user.tools:
            db.session.delete(tool)

        # Now delete the user
        db.session.delete(user)
        db.session.commit()
        flash(f'User {user.username} has been deleted.', 'success')
    except Exception as e:
        db.session.rollback()  # Rollback in case of an error
        flash(f'An error occurred while trying to delete the user: {str(e)}', 'danger')

    return redirect(url_for('admin.manage_users'))


@admin.route('/add_credits/<int:user_id>', methods=['POST'])
@login_required
def add_credits(user_id):
    user = User.query.get_or_404(user_id)
    form = AdminAddCreditsForm()
    
    if form.validate_on_submit():
        user.credits += form.credits.data
        db.session.commit()
        flash(f'{form.credits.data} credits added to {user.username}', 'success')
        return redirect(url_for('admin.manage_users'))
    
    return render_template('add_credits.html', form=form, user=user)


