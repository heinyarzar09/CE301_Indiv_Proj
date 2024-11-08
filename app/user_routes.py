from flask import Blueprint, render_template, url_for, flash, redirect, request, abort, current_app
from flask_login import login_user, current_user, logout_user, login_required
from PIL import Image
from app import db, bcrypt
from app.forms import ForgotPasswordForm, RegisterForm, LoginForm, ConversionForm, ToolForm, RecipeConversionForm, SharePostForm, JoinChallengeForm, CreditRequestForm, WithdrawForm
from app.models import CreditWithdrawRequest, PasswordResetRequest, PostLike, ShoppingList, User, Tool, Achievement, Friendship, Post, Challenge, ChallengeParticipant, db, CreditRequest, AdminNotification
from app.utils import convert_measurement, process_recipe, get_all_users_except_current, get_friends_for_user, get_incoming_friend_requests, get_outgoing_friend_requests, get_incoming_friend_requests, get_recent_follows
from app.forms import AchievementTrackingForm, ChallengeForm, RegisterForm, LoginForm, ConversionForm, ToolForm, RecipeConversionForm, SharePostForm, ChallengeForm, JoinChallengeForm 
from datetime import datetime, timedelta, timezone
from werkzeug.utils import secure_filename
from sqlalchemy.orm import joinedload
from sqlalchemy import func
from fractions import Fraction  # Import the Fraction class
import os, secrets


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
                # Check if the user selected "Admin" and validate admin password
                if form.role.data == 'admin':
                    special_admin_password = "123456"  # Admin password 
                    if form.admin_password.data != special_admin_password:
                        flash('Invalid admin password. Please try again.', 'danger')
                        return render_template('register.html', title='Register', form=form)
                
                # Hash the password and create a new user
                hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
                new_user = User(
                    username=form.username.data,
                    email=form.email.data,
                    password=hashed_password,
                    role=form.role.data
                )
                db.session.add(new_user)
                db.session.commit()
                flash('Your account has been created! You are now able to log in', 'success')
                return redirect(url_for('user.login'))
    
    elif form.errors:  # Handle any form validation errors
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{error}", 'danger')
    
    return render_template('register.html', title='Register', form=form)


# In user_routes.py
@user.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    form = ForgotPasswordForm()  # A form with fields for username and email
    
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data, email=form.email.data).first()
        
        if user:
            # Create a new password reset request
            reset_request = PasswordResetRequest(user_id=user.id, username=user.username, email=user.email)
            db.session.add(reset_request)
            db.session.commit()
            flash('Your password reset request has been submitted.', 'success')
        else:
            flash('No user found with the provided details.', 'danger')
            
        return redirect(url_for('user.login'))
    
    return render_template('forgot_password.html', form=form)


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

    # Fetch user's tools and populate the form choices
    user_tools = Tool.query.filter_by(owner_id=current_user.id).all()
    form.to_unit.choices = [
        (f"{tool.name} - {tool.unit}", f"{tool.name} ({tool.unit})") for tool in user_tools
    ]

    converted_recipe = None
    if form.validate_on_submit():  # Check if the form is submitted and valid
        recipe_text = form.recipe_text.data.strip()  # Strip whitespace from the recipe text
        to_unit = form.to_unit.data.split(' - ')[1]  # Extract the unit part from the user's tool selection

        if not recipe_text:
            flash("Please provide a recipe text for conversion.", 'warning')
        else:
            try:
                # Convert decimals in the recipe text to fractions before conversion
                recipe_text = convert_decimals_to_fractions(recipe_text)

                # Attempt to convert the recipe
                converted_recipe = process_recipe(recipe_text, to_unit, current_user.id)
                
                if not converted_recipe:
                    flash("The recipe could not be converted. Please check the input.", 'warning')
            except ValueError as e:
                flash(f"Error: {str(e)}", 'danger')
            except Exception as e:
                flash("An unexpected error occurred. Please try again.", 'danger')
    
    return render_template('automatic_conversion_tool.html', form=form, converted_recipe=converted_recipe)

# Helper function to convert decimals to fractions
def convert_decimals_to_fractions(text):
    words = text.split()
    for i, word in enumerate(words):
        try:
            # Try to convert each word to a float, then to a Fraction
            number = float(word)
            fraction = Fraction(number).limit_denominator()  # Limit denominator to get a simplified fraction
            if number != int(number):  # Only convert if the number is not an integer
                words[i] = str(fraction)  # Replace the word with its fraction representation
        except ValueError:
            continue  # Skip words that aren't numbers
    return ' '.join(words)


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


# Route to handle the post sharing
@user.route('/share_post', methods=['GET', 'POST'])
@login_required
def share_post():

    form = SharePostForm()

    # Retrieve all challenges that the user has joined (without filtering by active status)
    active_challenges = Challenge.query.join(ChallengeParticipant).filter(
        ChallengeParticipant.user_id == current_user.id,
        ChallengeParticipant.challenge_id == Challenge.id
    ).all()

    # Debugging line: Print the list of challenges the user has joined
    print("Joined Challenges for User:", [(challenge.id, challenge.name) for challenge in active_challenges])

    # Populate the challenge dropdown with joined challenges
    form.challenge.choices = [(0, "No Challenge")] + [(challenge.id, challenge.name) for challenge in active_challenges]

    if form.validate_on_submit():
        challenge_id = form.challenge.data if form.challenge.data != 0 else None

        # Handle image upload
        if form.image.data:
            image_file = save_image(form.image.data)
        else:
            image_file = 'default.jpg'

        # Create a new post
        post = Post(
            image_file=image_file,
            message=form.message.data,
            user_id=current_user.id,
            challenge_id=challenge_id  # Use None if "No Challenge" is selected
        )
        db.session.add(post)

        # Increment progress if a challenge was tagged
        if challenge_id:
            participation = ChallengeParticipant.query.filter_by(
                challenge_id=challenge_id,
                user_id=current_user.id
            ).first()
            
            if participation:
                # Increment progress
                participation.progress += 1
            else:
                flash("You're not part of this challenge.", "danger")
                db.session.rollback()  # Rollback the post creation if not part of the challenge
                return redirect(url_for('user.share_post'))

        db.session.commit()
        flash('Your post has been shared!', 'success')
        return redirect(url_for('user.index'))

    # Debug: Check if form validation failed and why
    if form.errors:
        print("Form errors:", form.errors)

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
    # Friend request notifications
    incoming_requests = Friendship.query.filter_by(friend_id=current_user.id, status='pending').all()
    outgoing_requests = Friendship.query.filter_by(user_id=current_user.id, status='pending').all()
    recent_follows = Friendship.query.filter_by(user_id=current_user.id, status='accepted') \
                                     .order_by(Friendship.date_created.desc()).limit(10).all()

    # Challenge notifications
    new_challenges = Challenge.query.filter(Challenge.started_at > current_user.last_login).all()
    won_challenges = ChallengeParticipant.query.filter_by(user_id=current_user.id, credited=True).all()
    
    # Payment notifications (assuming you have a way to track these)
    credited_payments = CreditRequest.query.filter_by(user_id=current_user.id, status='Approved').all()
    rejected_payments = CreditRequest.query.filter_by(user_id=current_user.id, status='Rejected').all()

    # Withdrawal notifications
    approved_withdrawals = CreditWithdrawRequest.query.filter_by(user_id=current_user.id, status='Approved').all()
    rejected_withdrawals = CreditWithdrawRequest.query.filter_by(user_id=current_user.id, status='Rejected').all()

    return render_template(
        'notifications.html',
        incoming_requests=incoming_requests,
        outgoing_requests=outgoing_requests,
        recent_follows=recent_follows,
        new_challenges=new_challenges,
        won_challenges=won_challenges,
        credited_payments=credited_payments,
        rejected_payments=rejected_payments,
        approved_withdrawals=approved_withdrawals,
        rejected_withdrawals=rejected_withdrawals
    )


@user.route('/like_post/<int:post_id>', methods=['POST'])
@login_required
def like_post(post_id):
    post = Post.query.get_or_404(post_id)
    existing_like = PostLike.query.filter_by(post_id=post_id, user_id=current_user.id).first()

    if existing_like:
        db.session.delete(existing_like)
        flash("You have unliked this post.", "info")
    else:
        like = PostLike(post_id=post_id, user_id=current_user.id)
        db.session.add(like)
        flash("You have liked this post!", "success")
    
    db.session.commit()
    return redirect(request.referrer or url_for('user.posts'))


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
        # Calculate duration in seconds
        duration = (form.days.data * 86400) + (form.hours.data * 3600) + (form.minutes.data * 60) + form.seconds.data

        # Handle file upload, specifying the folder as 'challenge'
        if form.icon.data:
            icon_filename = save_image(form.icon.data, folder='challenges')  # Save to 'static/challenge'
        else:
            icon_filename = 'default_icon.png'

        # Get the current time in UTC for the start time
        started_at = datetime.now(timezone.utc)

        # Create new challenge and set start time and duration (without end_time)
        challenge = Challenge(
            name=form.name.data,
            icon=icon_filename,
            creator_id=current_user.id,
            credits_required=form.credits_required.data,
            duration=duration,
            started_at=started_at  # Start the timer immediately in UTC
        )
        
        db.session.add(challenge)
        db.session.commit()
        flash('Challenge created successfully!', 'success')
        return redirect(url_for('user.challenges'))
    
    return render_template('create_challenge.html', form=form)

# Function to save images (like post images, challenge icons, or payment proofs)
def save_image(form_image, folder='uploads'):
    try:
        # Generate a random filename to avoid duplicates
        random_hex = secrets.token_hex(8)
        _, f_ext = os.path.splitext(form_image.filename)
        image_filename = random_hex + f_ext
        
        # Construct folder path based on the specified folder (e.g., static/challenge)
        folder_path = os.path.join(current_app.root_path, 'static', folder)
        os.makedirs(folder_path, exist_ok=True)  # Ensure the directory exists
        
        # Full image path
        image_path = os.path.join(folder_path, image_filename)

        # Debugging print statements to confirm paths
        print(f"Folder Path: {folder_path}")
        print(f"Image Path: {image_path}")

        # Resize and save the image
        output_size = (200, 200)
        img = Image.open(form_image)
        img.thumbnail(output_size)
        img.save(image_path)

        return image_filename  # Return filename to be saved in the database

    except Exception as e:
        print(f"Error saving image: {e}")
        return None


@user.route('/join_challenge/<int:challenge_id>', methods=['POST'])
@login_required
def join_challenge(challenge_id):
    # Retrieve the challenge
    challenge = Challenge.query.get_or_404(challenge_id)

    # Check if the user is already a participant in the challenge
    existing_participation = ChallengeParticipant.query.filter_by(user_id=current_user.id, challenge_id=challenge_id).first()
    if existing_participation:
        flash('You have already joined this challenge.', 'info')
        return redirect(url_for('user.challenges'))

    # Check if the user has enough credits
    if current_user.credits < challenge.credits_required:
        flash('You do not have enough credits to join this challenge.', 'danger')
        return redirect(url_for('user.challenges'))

    # Deduct credits and add user as a participant
    current_user.credits -= challenge.credits_required
    participant = ChallengeParticipant(user_id=current_user.id, challenge_id=challenge_id, wagered_credits=challenge.credits_required)
    db.session.add(participant)
    db.session.commit()

    flash(f'You have successfully joined the challenge: {challenge.name}!', 'success')
    return redirect(url_for('user.challenges'))


@user.route('/challenges')
@login_required
def challenges():
    # Fetch all challenges and check their end status
    challenges = Challenge.query.all()
    
    # Update the 'ended' status of each challenge if the timer has expired
    for challenge in challenges:
        if not challenge.ended and challenge.get_end_time() <= datetime.now(timezone.utc):
            challenge.ended = True
            db.session.add(challenge)
    db.session.commit()

    # Only include active challenges (not ended)
    active_challenges = Challenge.query.filter_by(ended=False).all()
    
    # Get IDs of challenges the current user has joined
    joined_challenge_ids = [p.challenge_id for p in current_user.participations]
    
    # Prepare data for rendering
    challenge_data = [{
        'id': challenge.id,
        'name': challenge.name,
        'credits_required': challenge.credits_required,
        'time_remaining': max(0, (challenge.get_end_time() - datetime.now(timezone.utc)).total_seconds()),
        'icon': challenge.icon
    } for challenge in active_challenges]

    return render_template('challenges.html', challenges=challenge_data, joined_challenge_ids=joined_challenge_ids, remaining_credits=current_user.credits)


@user.route('/achievements')
@login_required
def achievements():
    # Fetch only challenges marked as ended to avoid premature display
    completed_challenges = Challenge.query.filter_by(ended=True).all()

    for challenge in completed_challenges:
        # Calculate total wagered credits for this challenge
        total_wagered_credits = db.session.query(
            db.func.sum(ChallengeParticipant.wagered_credits)
        ).filter_by(challenge_id=challenge.id).scalar() or 0

        # Determine the winner by highest progress
        winner = ChallengeParticipant.query.filter_by(
            challenge_id=challenge.id
        ).order_by(ChallengeParticipant.progress.desc()).first()

        # Credit the winner if applicable
        if winner and winner.user_id == current_user.id and not winner.credited:
            current_user.credits += total_wagered_credits
            winner.credited = True
            db.session.add(current_user)
            db.session.add(winner)
            db.session.commit()

            # Create an achievement if one does not already exist
            existing_achievement = Achievement.query.filter_by(user_id=current_user.id, challenge_id=challenge.id).first()
            if not existing_achievement:
                new_achievement = Achievement(
                    user_id=current_user.id,
                    challenge_id=challenge.id,
                    challenge_name=challenge.name,
                    credits_won=total_wagered_credits,
                    completion_time=challenge.started_at + timedelta(seconds=challenge.duration)
                )
                db.session.add(new_achievement)
                db.session.commit()

    # Retrieve all achievements for the current user to display permanently
    user_achievements = Achievement.query.filter_by(user_id=current_user.id).all()

    # Prepare data for achievements display
    completed_challenges_data = []
    for achievement in user_achievements:
        challenge = Challenge.query.get(achievement.challenge_id)
        completed_challenges_data.append({
            'name': achievement.challenge_name,
            'completion_time': achievement.completion_time.strftime('%Y-%m-%d %H:%M:%S'),
            'image': challenge.icon if challenge else 'default_icon.jpg',
            'credits': achievement.credits_won
        })

    return render_template('achievements.html', completed_challenges=completed_challenges_data)


@user.route('/challenge_history')
@login_required
def challenge_history():
    # Retrieve all ended challenges that the user joined
    joined_challenges = ChallengeParticipant.query.filter_by(user_id=current_user.id).join(Challenge).filter(
        Challenge.ended == True
    ).all()

    # Prepare data for display
    history_data = []
    for participation in joined_challenges:
        challenge = participation.challenge
        history_data.append({
            'name': challenge.name,
            'completion_time': (challenge.started_at + timedelta(seconds=challenge.duration)).strftime('%Y-%m-%d %H:%M:%S'),
            'image': challenge.icon if challenge.icon else 'default_icon.jpg'
        })

    return render_template('challenge_history.html', history_data=history_data)

def get_leaderboard_data():
    # Assuming you want to show all challenges and participants sorted by their progress
    leaderboard_data = []

    # Get all challenges
    challenges = Challenge.query.all()

    for challenge in challenges:
        # Get all participants for the current challenge, ordered by their progress (highest first)
        participants = ChallengeParticipant.query.filter_by(challenge_id=challenge.id).order_by(ChallengeParticipant.progress.desc()).all()

        # Add each participant's info to the leaderboard
        for participant in participants:
            leaderboard_data.append({
                'username': participant.user.username,  # Assuming ChallengeParticipant has a reference to the User
                'challenge_name': challenge.name,
                'progress': participant.progress,
                'wagered_credits': participant.wagered_credits
            })

    return leaderboard_data


@user.route('/leaderboard', methods=['GET'])
@login_required
def leaderboard():
    # Fetch only active challenges (those that haven't ended)
    active_challenges = Challenge.query.filter_by(ended=False).all()
    
    # Prepare leaderboard data
    leaderboard_data = []
    for challenge in active_challenges:
        # Calculate time remaining
        time_remaining = max(0, (challenge.get_end_time() - datetime.now(timezone.utc)).total_seconds())
        
        # Sort participants by progress in descending order (for leaderboard ranking)
        sorted_participants = sorted(challenge.participants, key=lambda p: p.progress, reverse=True)
        
        # Prepare data for each challenge with sorted participants
        challenge_data = {
            'challenge': challenge,
            'time_remaining': time_remaining,
            'participants': sorted_participants  # Sorted by progress for leaderboard display
        }
        leaderboard_data.append(challenge_data)

    # Render the leaderboard template with the leaderboard data
    return render_template('leaderboard.html', leaderboard_data=leaderboard_data)

def get_challenge_winner(challenge):
    # Get the participant with the highest progress in the challenge
    winner = ChallengeParticipant.query.filter_by(challenge_id=challenge.id).order_by(ChallengeParticipant.progress.desc()).first()
    
    return winner  # Return the participant object with the highest progress

def end_challenge(challenge):
    # Mark the challenge as ended
    if not challenge.ended:
        challenge.ended = True
        db.session.add(challenge)

        # Get the winner
        winner = get_challenge_winner(challenge)

        if winner:
            # Calculate total wagered credits
            total_wagered = sum([p.wagered_credits for p in challenge.participants])

            # Award the winner with the total credits
            winner.user.credits += total_wagered
            db.session.add(winner.user)  # Save updated credits for the winner

            # Check if an achievement already exists for this challenge and winner
            existing_achievement = Achievement.query.filter_by(user_id=winner.user.id, challenge_id=challenge.id).first()

            # Create a new achievement if it doesn't already exist
            if not existing_achievement:
                achievement = Achievement(
                    challenge_name=challenge.name,
                    credits_won=total_wagered,
                    challenge_duration=challenge.duration,
                    participants=len(challenge.participants),
                    user_id=winner.user.id
                )
                db.session.add(achievement)
                print(f"Achievement created for user {winner.user.username}: {achievement}")

        db.session.commit()  # Commit all changes after updates
    else:
        print(f"Challenge '{challenge.name}' has already ended.")


@user.route('/add_credits', methods=['GET', 'POST'])
@login_required
def add_credits():
    form = CreditRequestForm()
    
    if form.validate_on_submit():
        # Save the payment proof image
        proof_image_filename = save_image(form.proof.data, folder='payments')  # Make sure 'payments' folder exists in /static

        # Step 1: Create and commit the credit request first to ensure it has an ID
        credit_request = CreditRequest(
            user_id=current_user.id,
            proof_image=proof_image_filename,
            credits_requested=form.credits_requested.data
        )
        db.session.add(credit_request)
        db.session.commit()  # Commit to ensure the credit_request.id is available

        # Step 2: Now, create the notification with a valid credit_request_id
        notification = AdminNotification(credit_request_id=credit_request.id)
        db.session.add(notification)
        db.session.commit()  # Commit the notification

        flash('Your credit request has been submitted for review.', 'success')
        return redirect(url_for('user.add_credit_status'))
    
    return render_template('add_credits.html', form=form)


@user.route('/add_credit_status')
@login_required
def add_credit_status():
    # Fetch the user's credit requests
    credit_requests = CreditRequest.query.filter_by(user_id=current_user.id).order_by(CreditRequest.date_submitted.desc()).all()
    return render_template('add_credit_status.html', credit_requests=credit_requests)


@user.route('/withdraw', methods=['GET', 'POST'])
@login_required
def request_withdraw():
    form = WithdrawForm()
    if form.validate_on_submit():
        if current_user.credits < form.credits_requested.data:
            flash('Insufficient credits for withdrawal.', 'danger')
        else:
            withdraw_request = CreditWithdrawRequest(
                user_id=current_user.id,
                credits_requested=form.credits_requested.data,
                payment_mode=form.payment_mode.data,
                phone_number=form.phone_number.data
            )
            db.session.add(withdraw_request)
            db.session.commit()
            flash('Withdrawal request submitted successfully.', 'success')
            return redirect(url_for('user.track_withdraw'))
    return render_template('withdraw.html', form=form)


@user.route('/track_withdraw')
@login_required
def track_withdraw():
    withdrawals = CreditWithdrawRequest.query.filter_by(user_id=current_user.id).all()
    return render_template('track_withdraw.html', withdrawals=withdrawals)


# Route to view shopping list
@user.route('/shopping_list', methods=['GET', 'POST'])
@login_required
def shopping_list():
    # Fetch user shopping list items
    items = ShoppingList.query.filter_by(user_id=current_user.id).all()

    if request.method == 'POST':
        # Add a new item
        item_name = request.form.get('item_name')
        quantity = request.form.get('quantity')
        
        new_item = ShoppingList(user_id=current_user.id, item_name=item_name, quantity=quantity)
        db.session.add(new_item)
        db.session.commit()
        flash('Item added to your shopping list!', 'success')
        return redirect(url_for('user.shopping_list'))
    
    return render_template('shopping_list.html', items=items)


# Route to mark item as completed
@user.route('/shopping_list/complete/<int:item_id>', methods=['POST'])
@login_required
def complete_item(item_id):
    item = ShoppingList.query.get_or_404(item_id)
    if item.user_id != current_user.id:
        abort(403)  # Unauthorized access
    
    item.completed = not item.completed  # Toggle completion status
    db.session.commit()
    return redirect(url_for('user.shopping_list'))


# Route to delete item
@user.route('/shopping_list/delete/<int:item_id>', methods=['POST'])
@login_required
def delete_item(item_id):
    item = ShoppingList.query.get_or_404(item_id)
    if item.user_id != current_user.id:
        abort(403)
    
    db.session.delete(item)
    db.session.commit()
    flash('Item removed from shopping list!', 'info')
    return redirect(url_for('user.shopping_list'))