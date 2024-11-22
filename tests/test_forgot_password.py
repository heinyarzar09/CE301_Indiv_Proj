import pytest
import warnings
from sqlalchemy.exc import SAWarning
from app import create_app, db
from app.models import User

# Suppress specific SQLAlchemy warnings
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=RuntimeWarning)
warnings.filterwarnings("ignore", category=PendingDeprecationWarning)
warnings.filterwarnings(
    "ignore",
    message="relationship.*will copy column.*conflicts with relationship.*",
    category=UserWarning,
)
warnings.filterwarnings(
    "ignore",
    message="relationship.*will copy column.*conflicts with relationship.*",
    category=SAWarning,
)

@pytest.fixture
def app():
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

def test_forgot_password(client):
    """Test the forgot password form submission."""
    # Create a test user
    user = User(username='testuser', email='testuser@example.com', password='hashedpassword')
    db.session.add(user)
    db.session.commit()

    # Send a POST request to the forgot password endpoint
    response = client.post('/forgot_password', data={
        'username': 'testuser',
        'email': 'testuser@example.com'
    }, follow_redirects=True)

    # Check if the response status code is 200 (OK)
    assert response.status_code == 200
