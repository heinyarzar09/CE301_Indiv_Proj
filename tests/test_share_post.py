import pytest
from app import create_app, db
from app.models import User, Challenge, ChallengeParticipant, Post
from flask_login import current_user
from io import BytesIO

# Fixture to set up the app in testing mode
@pytest.fixture
def app():
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

# Fixture for the test client
@pytest.fixture
def client(app):
    return app.test_client()

# Fixture to set up a user, a challenge, and a challenge participant
@pytest.fixture
def setup_user_and_challenge(app):
    # Create a user
    user = User(username='testuser', email='test@example.com', password='hashed_password')
    db.session.add(user)
    db.session.commit()

    # Create a challenge
    challenge = Challenge(name='Challenge 1', icon='icon1.png', creator_id=user.id, credits_required=10, duration=3600)
    db.session.add(challenge)
    db.session.commit()

    return user, challenge

def test_share_post_without_participation(client, setup_user_and_challenge):
    """Test that a user cannot share a post for a challenge they are not part of."""
    user, challenge = setup_user_and_challenge

    # Log in the user
    with client:
        with client.session_transaction() as session:
            session['_user_id'] = str(user.id)  # Mock the user session

        # Attempt to share a post without being part of the challenge
        response = client.post('/share_post', data={
            'message': 'Trying to share without participation.',
            'challenge': challenge.id,
            'image': (BytesIO(b"fake image data"), "image.jpg")
        }, content_type='multipart/form-data', follow_redirects=True)

        # Verify that the post was not created in the database
        post = Post.query.filter_by(user_id=user.id, message='Trying to share without participation.').first()
        assert post is None  # No post should be created
