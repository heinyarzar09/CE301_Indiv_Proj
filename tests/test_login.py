# tests/test_login.py
import pytest
from app import create_app, db

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False

    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client
        with app.app_context():
            db.session.remove()
            db.drop_all()

def test_login_user(client):
    # First, register a user
    client.post('/register', data={
        'username': 'testuser',
        'email': 'testuser@example.com',
        'password': 'Password123!',
        'confirm_password': 'Password123!',
        'role': 'user'
    }, follow_redirects=True)

    # Attempt to log in with the registered user's credentials
    response = client.post('/login', data={
        'email': 'testuser@example.com',
        'password': 'Password123!'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'Welcome' in response.data  # Check for a message that confirms login
            