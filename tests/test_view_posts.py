import pytest
from app import create_app, db
from app.models import User, Friendship, Post

# Fixture to set up the app in testing mode
@pytest.fixture
def app():
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # In-memory database
    app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing

    with app.app_context():
        db.create_all()  # Create the tables
        yield app
        db.session.remove()
        db.drop_all()  # Clean up

# Fixture for the test client
@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def setup_users_and_posts(app):
    # Create two users
    user1 = User(username='user1', email='user1@example.com', password='hashed_password')
    user2 = User(username='user2', email='user2@example.com', password='hashed_password')
    db.session.add_all([user1, user2])
    db.session.commit()

    # Create a friendship between the two users
    friendship = Friendship(user_id=user1.id, friend_id=user2.id)
    db.session.add(friendship)
    db.session.commit()

    # Create posts for both users with a default image file
    post1 = Post(message='Hello from user1', user_id=user1.id, image_file='default.jpg')
    post2 = Post(message='Hello from user2', user_id=user2.id, image_file='default.jpg')
    db.session.add_all([post1, post2])
    db.session.commit()

    return user1, user2, [post1, post2]

def test_view_posts(client, setup_users_and_posts):
    """Test viewing posts from friends and the current user."""
    user1, user2, posts = setup_users_and_posts

    # Log in user1
    with client:
        with client.session_transaction() as session:
            session['_user_id'] = str(user1.id)  # Mock the user session

        # Access the view posts page
        response = client.get('/view_posts')
        assert response.status_code == 200
        assert b'Hello from user1' in response.data  # Check that user1's post is displayed
        assert b'Hello from user2' in response.data  # Check that user2's post is displayed

def test_view_posts_no_posts(client, app):
    """Test viewing posts when there are no posts to show."""
    # Create a user with no friends or posts
    user = User(username='user_no_posts', email='no_posts@example.com', password='hashed_password')
    db.session.add(user)
    db.session.commit()

    # Log in the user
    with client:
        with client.session_transaction() as session:
            session['_user_id'] = str(user.id)  # Mock the user session

        # Access the view posts page
        response = client.get('/view_posts')
        assert response.status_code == 200
        assert b'No posts to show' in response.data  # Check for the flash message
