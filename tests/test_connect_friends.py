import pytest
from app import create_app, db
from app.models import User, Friendship
from flask_login import login_user

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
def setup_users_and_friendships(app):
    # Create users
    user1 = User(username='user1', email='user1@example.com', password='hashed_password')
    user2 = User(username='user2', email='user2@example.com', password='hashed_password')
    user3 = User(username='user3', email='user3@example.com', password='hashed_password')
    admin_user = User(username='admin', email='admin@example.com', password='hashed_password', role='admin')
    
    db.session.add_all([user1, user2, user3, admin_user])
    db.session.commit()

    # Create friendships
    friendship1 = Friendship(user_id=user1.id, friend_id=user2.id, status='accepted', is_blocked=False)
    friendship2 = Friendship(user_id=user1.id, friend_id=user3.id, status='pending', is_blocked=False)
    db.session.add_all([friendship1, friendship2])
    db.session.commit()

    return user1, user2, user3, admin_user

def test_connect_friends_page(client, setup_users_and_friendships):
    """Test accessing the connect friends page."""
    user1, user2, user3, admin_user = setup_users_and_friendships

    # Log in user1
    with client:
        with client.session_transaction() as session:
            session['_user_id'] = str(user1.id)  # Mock the user session

        # Make a GET request to the connect friends page
        response = client.get('/connect_friends')
        assert response.status_code == 200

        # Check that user2 and user3 are correctly handled
        assert b'user3' not in response.data  # user3 should be excluded (pending request)
        assert b'admin' not in response.data  # admin should be excluded (not a regular user)

def test_connect_friends_excludes_blocked(client, setup_users_and_friendships):
    """Test that blocked users are excluded from the connect friends list."""
    user1, user2, user3, admin_user = setup_users_and_friendships

    # Create a blocked friendship
    blocked_friendship = Friendship(user_id=user1.id, friend_id=user3.id, status='accepted', is_blocked=True)
    db.session.add(blocked_friendship)
    db.session.commit()

    # Log in user1
    with client:
        with client.session_transaction() as session:
            session['_user_id'] = str(user1.id)  # Mock the user session

        # Make a GET request to the connect friends page
        response = client.get('/connect_friends')
        assert response.status_code == 200

        # Check that user3 is excluded due to being blocked
        assert b'user3' not in response.data

def test_connect_friends_includes_valid_users(client, setup_users_and_friendships):
    """Test that valid users are included in the connect friends list."""
    user1, user2, user3, admin_user = setup_users_and_friendships

    # Log in user1
    with client:
        with client.session_transaction() as session:
            session['_user_id'] = str(user1.id)  # Mock the user session

        # Make a GET request to the connect friends page
        response = client.get('/connect_friends')
        assert response.status_code == 200

        # Check that users who are not friends, pending, or blocked are included
        assert b'user3' not in response.data  # user3 is pending, should not be included
        assert b'admin' not in response.data  # admin should not be included
