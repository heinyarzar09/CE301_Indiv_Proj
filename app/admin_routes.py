from datetime import datetime, timezone
from flask import Blueprint, render_template, url_for, flash, redirect, request
from flask_login import current_user, login_required  # Flask-Login for managing user authentication
from app import db, bcrypt  # Importing database instance and bcrypt for password hashing
from app.forms import ResetPasswordForm, AdminAddCreditsForm, CreditApprovalForm # Importing form for resetting passwords
from app.models import Challenge, ChallengeParticipant, CreditWithdrawRequest, PasswordResetRequest, Post, PostLike, ShoppingList, User, Friendship, CreditRequest, AdminNotification, post_reports  # Importing User model for managing user data


# Create a blueprint for admin-related routes
admin = Blueprint('admin', __name__)


@admin.route('/dashboard')
@login_required
def dashboard():
    # Check if the current user is an admin
    if current_user.role != 'admin':
        flash('You do not have permission to view this page.', 'danger')
        return redirect(url_for('user.index'))

    # Fetch recent activities without sorting
    recent_credit_requests = CreditRequest.query.limit(5).all()
    recent_withdraw_requests = CreditWithdrawRequest.query.limit(5).all()
    recent_password_resets = PasswordResetRequest.query.limit(5).all()

    # Combine all recent activities (order is undefined)
    recent_activity = (
        recent_credit_requests + recent_withdraw_requests + recent_password_resets
    )

    return render_template(
        'admin_dashboard.html',
        recent_activity=recent_activity
    )

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

        # Store the user_id and challenge_id before deleting the post
        user_id = post.user_id
        challenge_id = post.challenge_id

        # Delete the post
        db.session.delete(post)

        # Query the ChallengeParticipant instance for the post's user and challenge
        challenge_participant = ChallengeParticipant.query.filter_by(
            user_id=user_id, challenge_id=challenge_id
        ).first()

        # Decrement the progress if it's greater than 0
        if challenge_participant and challenge_participant.progress > 0:
            challenge_participant.progress -= 1
            db.session.add(challenge_participant)  # Add the instance to the session

        # Commit the changes
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

        # Delete all related PasswordResetRequest records
        PasswordResetRequest.query.filter_by(user_id=user.id).delete()

        # Delete all related CreditRequest records
        CreditRequest.query.filter_by(user_id=user.id).delete()

        # Delete all related CreditWithdrawRequest records
        CreditWithdrawRequest.query.filter_by(user_id=user.id).delete()

        # Delete all post reports associated with the user's posts
        db.session.execute(
            post_reports.delete().where(post_reports.c.post_id.in_([post.id for post in user.posts]))
        )

        # Delete or reassign all challenges created by the user
        challenges = Challenge.query.filter_by(creator_id=user.id).all()
        for challenge in challenges:
            db.session.delete(challenge)  # Delete the challenge
            # Alternatively, reassign the challenge if needed

        # Delete all related ChallengeParticipant records
        ChallengeParticipant.query.filter_by(user_id=user.id).delete()

        # Delete all friendships where the user is involved
        Friendship.query.filter(
            (Friendship.user_id == user.id) | (Friendship.friend_id == user.id)
        ).delete()

        # Delete all records in post_likes related to the user's posts or the user
        PostLike.query.filter(
            (PostLike.user_id == user.id) | (PostLike.post_id.in_([post.id for post in user.posts]))
        ).delete()

        # Delete all records in shopping_list related to the user
        ShoppingList.query.filter_by(user_id=user.id).delete()

        # Delete all posts made by the user
        for post in user.posts:
            db.session.delete(post)

        # Delete all tools belonging to the user
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


@admin.route('/manage_withdraw_requests', methods=['GET', 'POST'])
@login_required
def manage_withdraw_requests():
    pending_requests = CreditWithdrawRequest.query.filter_by(status='Pending').order_by(
        CreditWithdrawRequest.date_requested.desc()
    ).all()
    
    if request.method == 'POST':
        request_id = request.form.get('request_id')
        action = request.form.get('action')
        withdraw_request = CreditWithdrawRequest.query.get_or_404(request_id)

        if action == 'approve':
            withdraw_request.status = 'Approved'
            withdraw_request.date_approved = datetime.now(timezone.utc)
            withdraw_request.user.credits -= withdraw_request.credits_requested
            flash(f"Approved withdrawal of {withdraw_request.credits_requested} credits for user {withdraw_request.user.username}.", 'success')
        elif action == 'reject':
            withdraw_request.status = 'Rejected'
            flash(f"Rejected withdrawal request for user {withdraw_request.user.username}.", 'danger')
        
        db.session.commit()
        return redirect(url_for('admin.manage_withdraw_requests'))
    
    return render_template('admin_manage_withdraw_requests.html', pending_requests=pending_requests)


# Route to view withdrawal history
@admin.route('/view_withdraw_history')
@login_required
def view_withdraw_history():
    # Only retrieve approved or rejected requests and order them by date_requested descending
    all_requests = CreditWithdrawRequest.query.filter(
        CreditWithdrawRequest.status.in_(['Approved', 'Rejected'])
    ).order_by(CreditWithdrawRequest.date_requested.desc()).all()
    
    return render_template('admin_view_withdraw_history.html', all_requests=all_requests)


@admin.route('/notifications')
@login_required
def admin_notifications():
    # Ensure only admins can access this page
    if current_user.role != 'admin':
        flash('You do not have permission to view this page.', 'danger')
        return redirect(url_for('user.index'))

    # Fetch notifications relevant to the admin
    pending_credit_requests = CreditRequest.query.filter_by(status='Pending').all()
    pending_withdraw_requests = CreditWithdrawRequest.query.filter_by(status='Pending').all()
    pending_password_resets = PasswordResetRequest.query.filter_by(status='Pending').all()

    return render_template(
        'admin_notifications.html',
        pending_credit_requests=pending_credit_requests,
        pending_withdraw_requests=pending_withdraw_requests,
        pending_password_resets=pending_password_resets
    )