import pytest
from app import create_app, db
from app.models import User, Friendship
from flask_login import current_user

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
def setup_users(app):
    # Create users
    user1 = User(username='user1', email='user1@example.com', password='hashed_password')
    user2 = User(username='user2', email='user2@example.com', password='hashed_password')
    db.session.add_all([user1, user2])
    db.session.commit()

    return user1, user2

def test_add_friend_success(client, setup_users):
    """Test successfully adding a friend."""
    user1, user2 = setup_users

    # Log in user1
    with client:
        with client.session_transaction() as session:
            session['_user_id'] = str(user1.id)  # Mock the user session

        # Send a POST request to add user2 as a friend
        response = client.post(f'/add_friend/{user2.id}', follow_redirects=True)
        assert response.status_code == 200

        # Check that the friendship was created
        friendship = Friendship.query.filter_by(user_id=user1.id, friend_id=user2.id).first()
        assert friendship is not None
        assert b'You have added user2 as your friend!' in response.data

def test_add_self_as_friend(client, setup_users):
    """Test attempting to add oneself as a friend."""
    user1, _ = setup_users

    # Log in user1
    with client:
        with client.session_transaction() as session:
            session['_user_id'] = str(user1.id)  # Mock the user session

        # Try to add oneself as a friend
        response = client.post(f'/add_friend/{user1.id}', follow_redirects=True)
        assert response.status_code == 200

def test_add_existing_friend(client, setup_users):
    """Test adding a friend who is already in the friend list."""
    user1, user2 = setup_users

    # Create an existing friendship
    existing_friendship = Friendship(user_id=user1.id, friend_id=user2.id)
    db.session.add(existing_friendship)
    db.session.commit()

    # Log in user1
    with client:
        with client.session_transaction() as session:
            session['_user_id'] = str(user1.id)  # Mock the user session

        # Try to add user2 again
        response = client.post(f'/add_friend/{user2.id}', follow_redirects=True)
        assert response.status_code == 200
        assert b'user2 is already your friend.' in response.data
