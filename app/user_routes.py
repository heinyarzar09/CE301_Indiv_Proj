# Import necessary modules from Flask and other libraries
from flask import Blueprint, render_template, url_for, flash, redirect, request, abort, current_app
from flask_login import login_user, current_user, logout_user, login_required
from app import db, bcrypt
from app.forms import RegisterForm, LoginForm, ConversionForm, ToolForm, RecipeConversionForm, SharePostForm
from app.models import User, Tool, Achievement, UserAchievement, Friendship, Post, Challenge, ChallengeParticipant
from app.utils import convert_measurement, process_recipe, get_all_users_except_current, get_friends_for_user, get_incoming_friend_requests, get_outgoing_friend_requests, get_incoming_friend_requests, get_recent_follows
from app.forms import AchievementTrackingForm, ChallengeForm, RegisterForm, LoginForm, ConversionForm, ToolForm, RecipeConversionForm, SharePostForm, ChallengeForm, JoinChallengeForm
from app.achievements import check_achievements 
from datetime import datetime, timedelta, timezone
from werkzeug.utils import secure_filename
from sqlalchemy.orm import joinedload
import os

# Create a blueprint for user-related routes
user = Blueprint('user', __name__)

# Route for the index page (home page) of the user
@user.route('/')
@login_required  # Requires user login
def index():
    users = User.query.all()  # Get all users for display
    added_friend = request.args.get('added_friend')  # Get the name of the friend added, if any
    return render_template('index.html', users=users, added_friend=added_friend)

# Route for user login
@user.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:  # Redirect already logged-in users to the index page
        return redirect(url_for('user.index'))
    form = LoginForm()
    if form.validate_on_submit():  # When the login form is submitted and validated
        user = User.query.filter_by(email=form.email.data).first()  # Fetch the user by email
        # Check if user exists and password matches
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)  # Log the user in
            next_page = request.args.get('next')  # Get the next page if redirected
            if user.role == 'admin':
                return redirect(url_for('admin.dashboard'))  # Admin users redirected to the admin dashboard
            return redirect(next_page) if next_page else redirect(url_for('user.index'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')  # Error message for login failure
    elif form.errors:  # Handle any form validation errors
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{error}", 'danger')
    return render_template('login.html', form=form)

# Route for user registration
@user.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if request.method == 'POST' and form.validate():  # Validate form data on POST
        # Check if passwords match
        if form.password.data != form.confirm_password.data:
            flash('Password and Confirm Password do not match.', 'danger')
        else:
            # Check for existing users by username or email
            existing_user_by_username = User.query.filter_by(username=form.username.data).first()
            existing_user_by_email = User.query.filter_by(email=form.email.data).first()
            if existing_user_by_username:
                flash('That username is taken. Please choose a different one.', 'danger')
            elif existing_user_by_email:
                flash('That email is already in use. Please choose a different one.', 'danger')
            else:
                # Hash the password and create a new user
                hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
                new_user = User(username=form.username.data, email=form.email.data, password=hashed_password, role=form.role.data)
                db.session.add(new_user)
                db.session.commit()
                flash('Your account has been created! You are now able to log in', 'success')
                return redirect(url_for('user.login'))
    elif form.errors:  # Handle any form validation errors
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{error}", 'danger')
    return render_template('register.html', title='Register', form=form)

# Route for user logout
@user.route('/logout')
def logout():
    logout_user()  # Log the user out
    flash('You have been logged out.', 'info')
    return redirect(url_for('user.index'))

# Route for manual unit conversion tool
@user.route('/manual_conversion_tool', methods=['GET', 'POST'])
@login_required
def manual_conversion_tool():
    form = ConversionForm()
    result = None
    if form.validate_on_submit():  # If the form is submitted and validated
        amount = form.amount.data
        from_unit = form.from_unit.data
        to_unit = form.to_unit.data
        try:
            # Perform the unit conversion and generate the result
            converted_amount = convert_measurement(amount, from_unit, to_unit)
            result = f"{amount} {from_unit} is {converted_amount} {to_unit}"
        except ValueError as e:  # Handle unsupported conversions
            flash(str(e), 'danger')
    return render_template('manual_conversion_tool.html', form=form, result=result)

# Route for automatic recipe conversion based on user's tools
@user.route('/automatic_conversion', methods=['GET', 'POST'])
@login_required
def automatic_conversion():
    form = RecipeConversionForm()
    
    # Get user's tools and populate the form choices with them
    user_tools = Tool.query.filter_by(owner_id=current_user.id).all()
    form.to_unit.choices = [(f"{tool.name} - {tool.unit}", f"{tool.name} - {tool.unit}") for tool in user_tools]
    
    converted_recipe = None
    if form.validate_on_submit():  # If the form is submitted and validated
        recipe_text = form.recipe_text.data
        to_unit = form.to_unit.data.split(' - ')[1]  # Extract the unit part from the user's tool
        try:
            # Perform the recipe conversion and generate the result
            converted_recipe = process_recipe(recipe_text, to_unit, current_user.id)
        except ValueError as e:
            flash(str(e), 'danger')
    return render_template('automatic_conversion_tool.html', form=form, converted_recipe=converted_recipe)

# Route to manage user's tools
@user.route('/my_tools', methods=['GET', 'POST'])
@login_required
def my_tools():
    form = ToolForm(user_id=current_user.id)
    if form.validate_on_submit():  # If the form is submitted and validated
        # Check if the tool already exists for the user
        existing_tool = Tool.query.filter_by(name=form.name.data, unit=form.unit.data, owner_id=current_user.id).first()
        if existing_tool:
            flash('This tool with the same unit already exists. Please choose a different name or unit.', 'danger')
        else:
            # Add the new tool to the database
            tool = Tool(name=form.name.data, unit=form.unit.data, owner_id=current_user.id)
            db.session.add(tool)
            db.session.commit()
            flash('Tool has been added!', 'success')
            return redirect(url_for('user.my_tools'))
    elif form.errors:  # Handle any form validation errors
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{error}", 'danger')
    tools = Tool.query.filter_by(owner_id=current_user.id).all()  # Get all tools for the user
    return render_template('my_tools.html', title='My Tools', form=form, tools=tools)

# Route to delete a tool
@user.route('/delete_tool/<int:tool_id>', methods=['POST'])
@login_required
def delete_tool(tool_id):
    tool = Tool.query.get_or_404(tool_id)  # Get the tool by its ID, or return 404 if not found
    if tool.owner != current_user:  # Ensure the current user owns the tool
        abort(403)  # Return forbidden if not authorized
    db.session.delete(tool)  # Delete the tool from the database
    db.session.commit()
    flash('Tool has been deleted.', 'success')
    return redirect(url_for('user.my_tools'))

# Route to complete a recipe
@user.route('/complete_recipe/<int:recipe_id>', methods=['POST'])
@login_required
def complete_recipe(recipe_id):
    # Logic to handle recipe completion (omitted for now)
    
    # Update the user's completed recipes count
    current_user.completed_recipes += 1
    db.session.commit()
    
    # Check for and award any applicable achievements
    check_achievements(current_user)
    
    flash("Recipe completed!", "success")
    return redirect(url_for('user.my_tools'))

# Function to check for achievements based on user's progress
def check_achievements(user):
    achievements = Achievement.query.all()
    # Iterate through available achievements and check if user qualifies
    for achievement in achievements:
        if achievement.criteria == 'Complete 20 Recipes' and user.completed_recipes >= 20:
            if not UserAchievement.query.filter_by(user_id=user.id, achievement_id=achievement.id).first():
                new_achievement = UserAchievement(user_id=user.id, achievement_id=achievement.id, date_achieved=datetime.utcnow())
                db.session.add(new_achievement)
                db.session.commit()

    # Check and award various achievements based on the user's progress
    if user.completed_recipes >= 1:
        award_achievement(user, 'First Recipe Completed')
    if user.completed_recipes >= 10:
        award_achievement(user, 'Master Chef')
    if user.recipes_created >= 1:
        award_achievement(user, 'Recipe Creator')
    if user.recipes_shared >= 1:
        award_achievement(user, 'Social Butterfly')
    if user.shopping_lists_created >= 3:
        award_achievement(user, 'Shopping Expert')
    if user.conversion_tool_uses >= 5:
        award_achievement(user, 'Conversion Master')

# Function to award a specific achievement to a user
def award_achievement(user, achievement_name):
    achievement = Achievement.query.filter_by(name=achievement_name).first()
    if achievement:
        # Ensure the user hasn't already earned the achievement
        if not UserAchievement.query.filter_by(user_id=user.id, achievement_id=achievement.id).first():
            user_achievement = UserAchievement(user_id=user.id, achievement_id=achievement.id)
            db.session.add(user_achievement)
            db.session.commit()
            flash(f"Congratulations! You've earned the '{achievement_name}' achievement.", 'success')

# Function to add icons to achievements
def add_icons_to_achievements(app):
    with app.app_context():
        achievements = Achievement.query.all()
        for achievement in achievements:
            if achievement.name == 'Complete 20 Recipes':
                achievement.icon_url = '/static/icons/completed_20_recipes.png'
            elif achievement.name == 'Create 10 Recipes':
                achievement.icon_url = '/static/icons/create_10_recipes.png'
            # Add more conditions for other achievements here
            db.session.commit()

@user.route('/manage_achievements')
@login_required
def manage_achievements():
    if current_user.role != 'admin':
        abort(403)
    add_icons_to_achievements()
    flash("Achievements icons updated successfully.", "success")
    return redirect(url_for('user.index'))

@user.route('/track_achievement', methods=['POST'])
@login_required
def track_achievement():
    form = AchievementTrackingForm()
    if form.validate_on_submit():
        # Assuming you have a UserAchievement model and criteria to check against
        achievement_name = form.achievement_name.data
        progress = form.progress.data

        # Here you can add logic to update or track the user's achievement progress
        # For example, update an existing UserAchievement or create a new one

        flash(f"Your progress for {achievement_name} has been updated to {progress}!", "success")
        return redirect(url_for('user.achievements'))
    
    flash("Failed to track achievement.", "danger")
    return redirect(url_for('user.achievements'))

@user.route('/achievements', methods=['GET', 'POST'])
@login_required
def achievements():
    form = AchievementTrackingForm()
    user_achievements = UserAchievement.query.filter_by(user_id=current_user.id).all()

    if form.validate_on_submit():
        achievement_name = form.achievement_name.data
        progress = form.progress.data

        # Update the user's progress for the specified achievement
        if achievement_name == 'Completed Recipes':
            current_user.completed_recipes += progress
        elif achievement_name == 'Recipes Created':
            current_user.recipes_created += progress
        elif achievement_name == 'Recipes Shared':
            current_user.recipes_shared += progress

        db.session.commit()

        # Check if the user has earned any new achievements
        check_achievements(current_user)

        flash('Achievement progress updated!', 'success')
        return redirect(url_for('user.achievements'))

    return render_template('achievements.html', form=form, user=current_user, achievements=user_achievements)

@user.route('/increment_achievement/<int:achievement_id>', methods=['POST'])
@login_required
def increment_achievement(achievement_id):
    if achievement_id == 1:
        current_user.completed_recipes += 1
    elif achievement_id == 2:
        current_user.recipes_created += 1
    elif achievement_id == 3:
        current_user.recipes_shared += 1

    db.session.commit()
    check_achievements(current_user)
    
    flash("Achievement progress incremented!", "success")
    return redirect(url_for('user.achievements'))

@user.route('/connect_friends', methods=['GET', 'POST'])
@login_required
def connect_friends():
    # Subquery to get users who have a pending or accepted friend request from or to the current user
    pending_or_accepted = db.session.query(Friendship.friend_id).filter(
        (Friendship.user_id == current_user.id) & (Friendship.status.in_(['pending', 'accepted']))
    ).union(
        db.session.query(Friendship.user_id).filter(
            (Friendship.friend_id == current_user.id) & (Friendship.status.in_(['pending', 'accepted']))
        )
    ).subquery()

    # Subquery to get users who have blocked the current user or have been blocked by the current user
    blocked_users = db.session.query(Friendship.friend_id).filter(
        (Friendship.user_id == current_user.id) & (Friendship.is_blocked == True)
    ).union(
        db.session.query(Friendship.user_id).filter(
            (Friendship.friend_id == current_user.id) & (Friendship.is_blocked == True)
        )
    ).subquery()

    # Exclude users who are already friends, have a pending request, or are blocked
    users = User.query.filter(
        User.id != current_user.id, 
        User.role != 'admin',
        ~User.id.in_(pending_or_accepted),  # Exclude users with pending/accepted requests
        ~User.id.in_(blocked_users)        # Exclude blocked users
    ).all()

    # Get current user's friends (both directions)
    friends = User.query.join(Friendship, ((Friendship.user_id == current_user.id) & (Friendship.friend_id == User.id)) |
                                          ((Friendship.friend_id == current_user.id) & (Friendship.user_id == User.id)))\
                        .filter(Friendship.status == 'accepted', Friendship.is_blocked == False).all()

    added_friend = request.args.get('added_friend')  # Get the friend added, if any

    return render_template('connect_friends.html', users=users, friends=friends, added_friend=added_friend)






@user.route('/add_friend/<int:friend_id>', methods=['POST'])
@login_required
def add_friend(friend_id):
    if friend_id == current_user.id:
        flash("You can't add yourself as a friend!", 'warning')
        return redirect(url_for('user.connect_friends'))
    
    friend = User.query.get_or_404(friend_id)
    existing_friendship = Friendship.query.filter_by(user_id=current_user.id, friend_id=friend.id).first()
    
    if existing_friendship:
        flash(f'{friend.username} is already your friend.', 'warning')
    else:
        new_friendship = Friendship(user_id=current_user.id, friend_id=friend.id)
        db.session.add(new_friendship)
        db.session.commit()
        flash(f'You have added {friend.username} as your friend!', 'success')
    
    return redirect(url_for('user.connect_friends', added_friend=friend.username))




@user.route('/users')
@login_required
def list_users():
    users = User.query.all()
    return render_template('list_users.html', users=users)

# Helper function to save the image
def save_image(image_data):
    filename = secure_filename(image_data.filename)
    image_path = os.path.join(current_app.root_path, 'static/uploads', filename)
    image_data.save(image_path)
    return filename

# Route to handle the post sharing
@user.route('/share_post', methods=['GET', 'POST'])
@login_required
def share_post():
    form = SharePostForm()
    if form.validate_on_submit():
        if form.image.data:
            image_file = save_image(form.image.data)
        else:
            image_file = 'default.jpg'  # Provide a default image or handle as needed

        # Create a new post with the image file path
        post = Post(image_file=image_file, message=form.message.data, user_id=current_user.id)
        db.session.add(post)
        db.session.commit()
        flash('Your post has been shared!', 'success')
        return redirect(url_for('user.index'))
    return render_template('share_post.html', form=form)

# Route to view posts from friends
@user.route('/view_posts')
@login_required
def view_posts():
    friends = Friendship.query.filter_by(user_id=current_user.id).all()
    friend_ids = [friend.friend_id for friend in friends]
    friend_ids.append(current_user.id)  # Include the current user in the posts
    
    posts = Post.query.filter(Post.user_id.in_(friend_ids)).order_by(Post.date_posted.desc()).all()
    
    if not posts:
        flash('No posts to show', 'info')
    
    return render_template('view_posts.html', posts=posts)

@user.route('/notifications')
@login_required
def notifications():
    # Get incoming friend requests (where the current user is the recipient)
    incoming_requests = Friendship.query.filter_by(friend_id=current_user.id, status='pending').all()

    # Get outgoing friend requests (where the current user is the sender)
    outgoing_requests = Friendship.query.filter_by(user_id=current_user.id, status='pending').all()

    # Get recent follows (accepted friend requests)
    recent_follows = Friendship.query.filter_by(user_id=current_user.id, status='accepted')\
                                     .order_by(Friendship.date_created.desc()).limit(10).all()

    return render_template('notifications.html', 
                           incoming_requests=incoming_requests, 
                           outgoing_requests=outgoing_requests, 
                           recent_follows=recent_follows)

@user.route('/approve_friend_request/<int:request_id>', methods=['POST'])
@login_required
def approve_friend_request(request_id):
    request = Friendship.query.get(request_id)
    if request and request.friend_id == current_user.id:
        request.status = 'accepted'
        db.session.commit()
        flash(f'You are now friends with {request.user.username}!', 'success')
    return redirect(url_for('user.notifications'))



@user.route('/reject_friend_request/<int:request_id>', methods=['POST'])
@login_required
def reject_friend_request(request_id):
    # Use joinedload to eagerly load 'user' and 'friend' relationships
    request = Friendship.query.options(joinedload(Friendship.user), joinedload(Friendship.friend)).get(request_id)
    
    if request and request.friend_id == current_user.id:
        db.session.delete(request)  # Delete the friendship request
        db.session.commit()
        flash('Friend request has been rejected.', 'info')
    return redirect(url_for('user.notifications'))  # Redirect to notifications page


@user.route('/send_friend_request/<int:friend_id>', methods=['POST'])
@login_required
def send_friend_request(friend_id):
    friend = User.query.get(friend_id)
    if not friend:
        flash('User not found.', 'danger')
        return redirect(url_for('user.connect_friends'))
    
    # Check if friendship already exists
    existing_request = Friendship.query.filter_by(user_id=current_user.id, friend_id=friend_id).first()
    
    if existing_request:
        flash('Friend request already sent.', 'info')
    else:
        # Set the status to 'pending'
        new_request = Friendship(user_id=current_user.id, friend_id=friend_id, status='pending')
        db.session.add(new_request)
        db.session.commit()
        flash(f'Friend request sent to {friend.username}!', 'success')

    return redirect(url_for('user.connect_friends'))  # Redirect back to Connect with Friends


@user.route('/unfollow_friend/<int:friend_id>', methods=['POST'])
@login_required
def unfollow_friend(friend_id):
    # Find the friendship entry between the current user and the friend
    friendship = Friendship.query.filter(
        ((Friendship.user_id == current_user.id) & (Friendship.friend_id == friend_id)) |
        ((Friendship.friend_id == current_user.id) & (Friendship.user_id == friend_id))
    ).first()
    
    if friendship:
        db.session.delete(friendship)  # Fully delete the friendship
        db.session.commit()
        flash('You have unfollowed this user. You can send a new friend request.', 'success')
    else:
        flash('Friendship not found.', 'danger')

    return redirect(url_for('user.connect_friends'))





@user.route('/block_friend/<int:friend_id>', methods=['POST'])
@login_required
def block_friend(friend_id):
    # Find the friendship entry between the current user and the friend
    friendship = Friendship.query.filter(
        ((Friendship.user_id == current_user.id) & (Friendship.friend_id == friend_id)) |
        ((Friendship.friend_id == current_user.id) & (Friendship.user_id == friend_id))
    ).first()

    if friendship:
        # Delete the friendship since it's a one-sided block
        db.session.delete(friendship)
        db.session.commit()

        # Create a new friendship record to track the block status
        new_block = Friendship(user_id=current_user.id, friend_id=friend_id, is_blocked=True, status='blocked')
        db.session.add(new_block)
        db.session.commit()
        flash('You have blocked this user.', 'success')
    else:
        flash('Friendship not found.', 'danger')

    return redirect(url_for('user.manage_friends'))


@user.route('/unblock_friend/<int:friend_id>', methods=['POST'])
@login_required
def unblock_friend(friend_id):
    # Find the block entry
    block_entry = Friendship.query.filter_by(user_id=current_user.id, friend_id=friend_id, is_blocked=True).first()

    if block_entry:
        # Remove the block
        db.session.delete(block_entry)
        db.session.commit()
        flash('You have unblocked this user. You can now send friend requests again.', 'success')
    else:
        flash('Block entry not found.', 'danger')

    return redirect(url_for('user.manage_friends'))



@user.route('/manage_friends', methods=['GET'])
@login_required
def manage_friends():
    # Get current user's friends, excluding blocked users
    friends = User.query.join(Friendship, ((Friendship.user_id == current_user.id) & (Friendship.friend_id == User.id)) |
                                          ((Friendship.friend_id == current_user.id) & (Friendship.user_id == User.id)))\
                        .filter(Friendship.status == 'accepted', Friendship.is_blocked == False).all()

    # Get current user's blocked friends
    blocked_friends = User.query.join(Friendship, (Friendship.friend_id == User.id))\
                        .filter(Friendship.user_id == current_user.id, Friendship.is_blocked == True).all()

    return render_template('manage_friends.html', friends=friends, blocked_friends=blocked_friends)


@user.route('/create_challenge', methods=['GET', 'POST'])
@login_required
def create_challenge():
    form = ChallengeForm()
    if form.validate_on_submit():
        # Calculate the duration from the form input
        duration = timedelta(days=form.days.data, hours=form.hours.data, minutes=form.minutes.data)
        
        # Handle file upload for the challenge icon
        if form.icon.data:
            icon_filename = secure_filename(form.icon.data.filename)
            form.icon.data.save(os.path.join('static/images/challenges', icon_filename))
        else:
            icon_filename = None

        # Create a new challenge
        challenge = Challenge(
            name=form.name.data,
            icon=icon_filename,
            creator_id=current_user.id,
            credits_required=form.credits_required.data,
            duration=duration
        )

        # Add the challenge to the database
        db.session.add(challenge)
        db.session.commit()
        
        flash(f'Challenge "{form.name.data}" created successfully!', 'success')
        return redirect(url_for('user.challenges'))

    return render_template('create_challenge.html', form=form)


@user.route('/join_challenge/<int:challenge_id>', methods=['POST'])
@login_required
def join_challenge(challenge_id):
    challenge = Challenge.query.get_or_404(challenge_id)

    if challenge.is_active and current_user.credits >= challenge.credits_required:
        participant = ChallengeParticipant(
            user_id=current_user.id,
            challenge_id=challenge_id,
            wagered_credits=challenge.credits_required
        )
        db.session.add(participant)
        db.session.commit()

        # Deduct credits from the user
        current_user.credits -= challenge.credits_required
        db.session.commit()

        flash(f'You have joined the challenge: {challenge.name}!', 'success')
    else:
        flash('You don’t have enough credits or the challenge has ended.', 'danger')

    return redirect(url_for('user.challenges'))


@user.route('/challenges')
@login_required
def challenges():
    # Get all challenges
    challenges = Challenge.query.all()
    return render_template('challenges.html', challenges=challenges)

@user.route('/leaderboard')
@login_required
def leaderboard():
    # Get all challenges with participants
    challenges = Challenge.query.all()
    return render_template('leaderboard.html', challenges=challenges)


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

@user.route('/share_recipes')
@login_required
def share_recipes():
    return render_template('placeholder.html', feature="Share Recipes")

@user.route('/comment_recipes')
@login_required
def comment_recipes():
    return render_template('placeholder.html', feature="Comment on Recipes")

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