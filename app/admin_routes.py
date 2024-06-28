from flask import Blueprint, render_template, url_for, flash, redirect, request
from flask_login import current_user, login_required
from app import db, bcrypt
from app.forms import AdminResetPasswordForm
from app.models import User

admin = Blueprint('admin', __name__)

@admin.route('/dashboard')
@login_required
def dashboard():
    if current_user.role != 'admin':
        flash('You do not have permission to view this page.', 'danger')
        return redirect(url_for('user.index'))
    return render_template('admin_dashboard.html')

@admin.route('/manage_users')
@login_required
def manage_users():
    if current_user.role != 'admin':
        flash('You do not have permission to view this page.', 'danger')
        return redirect(url_for('user.index'))
    users = User.query.all()
    return render_template('admin_manage_users.html', users=users)

@admin.route('/manage_recipes')
@login_required
def manage_recipes():
    if current_user.role != 'admin':
        flash('You do not have permission to view this page.', 'danger')
        return redirect(url_for('user.index'))
    # Add logic to manage recipes
    return render_template('admin_manage_recipes.html')

@admin.route('/settings')
@login_required
def settings():
    if current_user.role != 'admin':
        flash('You do not have permission to view this page.', 'danger')
        return redirect(url_for('user.index'))
    return render_template('admin_settings.html')

@admin.route('/reset_password/<int:user_id>', methods=['GET', 'POST'])
@login_required
def admin_reset_password(user_id):
    if current_user.role != 'admin':
        flash('You do not have permission to view this page.', 'danger')
        return redirect(url_for('user.index'))
    user = User.query.get_or_404(user_id)
    form = AdminResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password = hashed_password
        db.session.commit()
        flash(f'Password has been reset for user {user.username}.', 'success')
        return redirect(url_for('admin.manage_users'))
    return render_template('admin_reset_password.html', form=form, user=user)

@admin.route('/delete_user/<int:user_id>', methods=['POST'])
@login_required
def admin_delete_user(user_id):
    if current_user.role != 'admin':
        flash('You do not have permission to perform this action.', 'danger')
        return redirect(url_for('user.index'))
    user = User.query.get_or_404(user_id)
    if user:
        for tool in user.tools:
            db.session.delete(tool)
        db.session.delete(user)
        db.session.commit()
        flash(f'User {user.username} has been deleted.', 'success')
    return redirect(url_for('admin.manage_users'))

