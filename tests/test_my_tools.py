import pytest
from app import create_app, db
from app.models import User, Tool
from flask_login import login_user

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
def setup_user(app):
    # Set up a test user
    user = User(username='testuser', email='test@example.com', password='hashed_password')
    db.session.add(user)
    db.session.commit()
    return user

def test_my_tools_get(client, setup_user):
    """Test accessing the my tools page."""
    user = setup_user

    # Log in the user using Flask-Login
    with client:
        with client.session_transaction() as session:
            session['_user_id'] = str(user.id)  # Mock the user session

        # Make a GET request to the /my_tools page
        response = client.get('/my_tools')
        assert response.status_code == 200

def test_my_tools_post_add_tool(client, setup_user):
    """Test adding a new tool successfully."""
    user = setup_user

    # Log in the user using Flask-Login
    with client:
        with client.session_transaction() as session:
            session['_user_id'] = str(user.id)  # Mock the user session

        # Make a POST request to add a new tool
        response = client.post('/my_tools', data={
            'name': 'Measuring Cup',
            'unit': 'ml'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b"Tool has been added!" in response.data

def test_my_tools_post_duplicate_tool(client, setup_user):
    """Test adding a duplicate tool."""
    user = setup_user

    # Log in the user using Flask-Login and add an existing tool
    with client:
        with client.session_transaction() as session:
            session['_user_id'] = str(user.id)  # Mock the user session

        # Add a tool to the database
        tool = Tool(name='Measuring Cup', unit='ml', owner_id=user.id)
        db.session.add(tool)
        db.session.commit()

        # Attempt to add the same tool again
        response = client.post('/my_tools', data={
            'name': 'Measuring Cup',
            'unit': 'ml'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b"This tool with the same unit already exists." in response.data

def test_my_tools_post_invalid_data(client, setup_user):
    """Test adding a tool with invalid data."""
    user = setup_user

    # Log in the user using Flask-Login
    with client:
        with client.session_transaction() as session:
            session['_user_id'] = str(user.id)  # Mock the user session

        # Make a POST request with invalid data
        response = client.post('/my_tools', data={
            'name': '',  # Invalid: name should not be empty
            'unit': ''
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b"This field is required." in response.data
