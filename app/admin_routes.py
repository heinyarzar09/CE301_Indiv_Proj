# Import necessary modules from Flask and other libraries
from flask import Blueprint, render_template, url_for, flash, redirect, request
from flask_login import current_user, login_required  # Flask-Login for managing user authentication
from app import db, bcrypt  # Importing database instance and bcrypt for password hashing
from app.forms import ResetPasswordForm, AdminAddCreditsForm, CreditApprovalForm # Importing form for resetting passwords
from app.models import PasswordResetRequest, Post, User, Friendship, CreditRequest, AdminNotification  # Importing User model for managing user data



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

@admin.route('/manage_posts', methods=['GET', 'POST'])
@login_required
def manage_posts():
    # Fetch all posts to display to the admin
    posts = Post.query.all()

    if request.method == 'POST':
        # Get the post ID to delete
        post_id = request.form.get("post_id")
        post = Post.query.get_or_404(post_id)

        # Delete the post and commit the changes
        db.session.delete(post)
        db.session.commit()

        flash("Post deleted successfully.", "success")
        return redirect(url_for('admin.manage_posts'))

    return render_template('admin_manage_posts.html', posts=posts)

# In admin_routes.py
@admin.route('/view_password_reset_requests')
@login_required
def view_password_reset_requests():
    # Fetch all password reset requests
    reset_requests = PasswordResetRequest.query.order_by(PasswordResetRequest.date_requested.desc()).all()
    return render_template('admin_view_reset_requests.html', reset_requests=reset_requests)

@admin.route('/reject_password_reset/<int:request_id>', methods=['POST'])
@login_required
def reject_password_reset(request_id):
    reset_request = PasswordResetRequest.query.get_or_404(request_id)
    reset_request.status = "Rejected"
    db.session.commit()
    flash("Password reset request has been rejected.", "info")
    return redirect(url_for('admin.view_password_reset_requests'))


# Route for admin to reset a user's password
@admin.route('/admin/reset_password/<int:user_id>', methods=['GET', 'POST'])
@login_required
def admin_reset_password(user_id):
    user = User.query.get_or_404(user_id)
    form = ResetPasswordForm()
    reset_request = PasswordResetRequest.query.filter_by(user_id=user.id, status="Pending").first()  # Get the reset request

    if form.validate_on_submit():
        if form.password.data != form.confirm_password.data:
            flash('Password and Confirm Password do not match.', 'danger')
        elif bcrypt.check_password_hash(user.password, form.password.data):
            flash('New password cannot be the same as the current password.', 'danger')
        else:
            # Update password
            hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
            user.password = hashed_password
            
            # Update reset request status to "Password changed"
            if reset_request:
                reset_request.status = "Password changed"
            
            db.session.commit()
            flash('Password has been updated!', 'success')
            return redirect(url_for('admin.view_password_reset_requests'))

    elif form.errors:
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




@admin.route('/credit_request_history')
@login_required
def credit_request_history():
    # Retrieve all approved and rejected credit requests
    credit_requests = CreditRequest.query.filter(CreditRequest.status.in_(['Approved', 'Rejected'])).order_by(CreditRequest.date_submitted.desc()).all()
    return render_template('admin_credit_request_history.html', credit_requests=credit_requests)




@admin.route('/add_user_credits', methods=['GET', 'POST'])
@login_required
def add_user_credits():
    # Fetch all pending credit requests
    pending_requests = CreditRequest.query.filter_by(status="Pending").all()
    
    if request.method == 'POST':
        # Get data from the form submission
        credit_request_id = request.form.get("credit_request_id")
        action = request.form.get("action")  # "approve" or "reject"
        
        # Retrieve the credit request and associated user
        credit_request = CreditRequest.query.get_or_404(credit_request_id)
        user = credit_request.user
        
        if action == "approve":
            # Approve the request and add the requested credits
            user.credits += credit_request.credits_requested
            credit_request.status = "Approved"
            flash(f"{credit_request.credits_requested} credits added to {user.username}'s account and request approved.", "success")
        
        elif action == "reject":
            # Reject the request without adding credits
            credit_request.status = "Rejected"
            flash(f"Credit request from {user.username} has been rejected.", "info")
        
        # Mark notification as reviewed if any
        notification = AdminNotification.query.filter_by(credit_request_id=credit_request.id).first()
        if notification:
            notification.reviewed = True
        
        # Commit changes to the database
        db.session.commit()
        
        # Redirect back to the same page to show updated list
        return redirect(url_for('admin.add_user_credits'))
    
    # Render the page with pending requests
    return render_template('admin_add_user_credits.html', pending_requests=pending_requests)
