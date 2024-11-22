import pytest
from app import create_app, db
from app.models import User, Tool

# Fixture to set up the app in testing mode
@pytest.fixture
def app():
    app = create_app()  # Use your create_app() function
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
def setup_user_and_tools(app):
    # Set up a test user and their tools
    user = User(username='testuser', email='test@example.com', password='hashed_password')
    db.session.add(user)
    db.session.commit()

    # Add some tools for the user
    tool1 = Tool(name='Cup', unit='ml', owner_id=user.id)
    tool2 = Tool(name='Spoon', unit='tbsp', owner_id=user.id)
    db.session.add_all([tool1, tool2])
    db.session.commit()

    return user

def test_automatic_conversion_get(client, setup_user_and_tools):
    """Test accessing the automatic conversion tool page."""
    user = setup_user_and_tools

    # Log in the user using Flask-Login
    with client:
        with client.session_transaction() as session:
            session['_user_id'] = str(user.id)  # Mock the user session

        response = client.get('/automatic_conversion')
        assert response.status_code == 200

def test_automatic_conversion_post_valid(client, setup_user_and_tools):
    """Test a valid recipe conversion submission."""
    user = setup_user_and_tools

    # Log in the user using Flask-Login
    with client:
        with client.session_transaction() as session:
            session['_user_id'] = str(user.id)  # Mock the user session

        # Make a POST request with valid recipe text and selected tool
        response = client.post('/automatic_conversion', data={
            'recipe_text': '1.5 cups of milk',
            'to_unit': 'Cup - ml'
        }, follow_redirects=True)
        assert response.status_code == 200